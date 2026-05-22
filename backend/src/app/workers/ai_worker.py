"""AI worker: dispatcher che lavora un ticket in base al tipo e allo stato.

- `email`        → bozza di risposta, invio su approvazione (logica qui).
- `fix`/`feature` → delegati al `CodeWorker` (branch git, modifiche, test, commit).

process():  ticket `creato`/`rifiutato` → preparazione → `in_attesa`.
finalize(): ticket `approvato` → azione finale → `concluso`.

Le transizioni di stato passano sempre da TicketService (macchina a stati unica).
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass

from app.core import storage
from app.integrations.ai.base import AIClient, AIError
from app.integrations.email.sender import EmailSendError, send_reply
from app.models.attachment import Attachment
from app.models.ticket import Ticket, TicketStatus, TicketType
from app.models.ticket_message import MessageDirection
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.project_repository import ProjectRepository
from app.services.ticket_service import TicketService
from app.workers import prompts
from app.workers.code_worker import CodeWorker

_IMAGE_TYPES = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif")
_TEXT_TYPES = ("text/", "application/json", "application/xml")
_MAX_ATT_TEXT = 4000


@dataclass
class WorkerResult:
    ticket_id: int
    action: str  # "process" | "finalize"
    status: str
    note: str


_CODE_TYPES = (TicketType.FIX, TicketType.FEATURE)


class AIWorker:
    def __init__(
        self,
        tickets: TicketService,
        ai: AIClient,
        accounts: EmailAccountRepository,
        projects: ProjectRepository,
    ) -> None:
        self._tickets = tickets
        self._ai = ai
        self._accounts = accounts
        self._projects = projects

    def _code_worker(self) -> CodeWorker:
        return CodeWorker(self._tickets, self._ai, self._projects)

    # --- Lavorazione (creato/rifiutato -> in_attesa) ---

    def process(self, ticket_id: int) -> WorkerResult:
        ticket = self._tickets.get(ticket_id)
        if ticket.type in _CODE_TYPES:
            self._code_worker().process(ticket_id)
            return self._result(ticket_id, "process")

        # type=email
        if ticket.status != TicketStatus.IN_LAVORAZIONE:
            self._tickets.change_status(ticket_id, TicketStatus.IN_LAVORAZIONE)

        conversation = self._build_conversation(ticket)
        attachments_text, images = self._gather_attachments(ticket_id)
        prompt = prompts.build_email_prompt(ticket, conversation, attachments_text)

        try:
            client, imgs = self._pick_client(images)
            draft = client.complete(prompts.EMAIL_SYSTEM, prompt, images=imgs)
        except AIError as exc:
            self._tickets.set_ai_fields(ticket_id, ai_note=f"Errore AI: {exc}")
            return self._result(ticket_id, "process")

        self._tickets.set_ai_fields(
            ticket_id, ai_draft=draft, ai_note="Bozza di risposta pronta — rivedi e approva."
        )
        self._tickets.change_status(ticket_id, TicketStatus.IN_ATTESA)
        return self._result(ticket_id, "process")

    # --- Costruzione contesto (thread + allegati) ---

    def _build_conversation(self, ticket: Ticket) -> str:
        messages = self._tickets.list_messages(ticket.id)
        if not messages:
            return ticket.description or ticket.title
        lines: list[str] = []
        for msg in messages:
            who = "Cliente" if msg.direction == MessageDirection.INBOUND else "Noi"
            sender = f" ({msg.from_addr})" if msg.from_addr else ""
            lines.append(f"[{who}{sender}]\n{msg.body}")
        return "\n\n".join(lines)

    def _gather_attachments(self, ticket_id: int) -> tuple[str, list[bytes]]:
        texts: list[str] = []
        images: list[bytes] = []
        for att in self._tickets.list_attachments(ticket_id):
            data = self._read_attachment(att)
            if data is None:
                continue
            if att.content_type.startswith(_IMAGE_TYPES) or att.content_type in _IMAGE_TYPES:
                images.append(data)
            elif att.content_type.startswith(_TEXT_TYPES):
                text = data.decode("utf-8", errors="replace")[:_MAX_ATT_TEXT]
                texts.append(f"### {att.filename}\n{text}")
        return "\n\n".join(texts), images

    @staticmethod
    def _read_attachment(att: Attachment) -> bytes | None:
        with contextlib.suppress(OSError):
            return storage.resolve_path(att.storage_path).read_bytes()
        return None

    def _pick_client(self, images: list[bytes]) -> tuple[AIClient, list[bytes] | None]:
        """Usa il modello vision se ci sono immagini, altrimenti il client di testo."""
        if images:
            with contextlib.suppress(Exception):
                from app.integrations.ai.factory import build_vision_client

                return build_vision_client(), images
        return self._ai, None

    # --- Finalizzazione (approvato -> concluso) ---

    def finalize(self, ticket_id: int) -> WorkerResult:
        ticket = self._tickets.get(ticket_id)
        if ticket.type in _CODE_TYPES:
            self._code_worker().finalize(ticket_id)
            return self._result(ticket_id, "finalize")
        return self._finalize_email(ticket)

    def _finalize_email(self, ticket: Ticket) -> WorkerResult:
        if not ticket.ai_draft or not ticket.source_address or ticket.email_account_id is None:
            self._fail(ticket.id, "Impossibile inviare: manca bozza, destinatario o account.")
            return self._result(ticket.id, "finalize")

        account = self._accounts.get(ticket.email_account_id)
        if account is None:
            self._fail(ticket.id, "Account email non più disponibile.")
            return self._result(ticket.id, "finalize")

        try:
            send_reply(
                account=account,
                to_addr=ticket.source_address,
                subject=f"Re: {ticket.title}",
                body=ticket.ai_draft,
                in_reply_to=ticket.external_ref,
            )
        except EmailSendError as exc:
            self._fail(ticket.id, f"Invio fallito: {exc}")
            return self._result(ticket.id, "finalize")

        self._tickets.add_outbound_message(ticket.id, ticket.ai_draft, from_addr=account.email)
        self._tickets.set_ai_fields(ticket.id, ai_note=f"Email inviata a {ticket.source_address}.")
        self._tickets.change_status(ticket.id, TicketStatus.CONCLUSO)
        return self._result(ticket.id, "finalize")

    def _fail(self, ticket_id: int, note: str) -> None:
        """Finalizzazione fallita: nota + ritorno in 'in attesa' (niente auto-retry)."""
        self._tickets.set_ai_fields(ticket_id, ai_note=note)
        self._tickets.change_status(ticket_id, TicketStatus.IN_ATTESA)

    def _result(self, ticket_id: int, action: str) -> WorkerResult:
        ticket = self._tickets.get(ticket_id)
        return WorkerResult(
            ticket_id=ticket_id,
            action=action,
            status=ticket.status.value,
            note=ticket.ai_note or "",
        )
