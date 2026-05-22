"""AI worker: dispatcher che lavora un ticket in base al tipo e allo stato.

- `email`        → bozza di risposta, invio su approvazione (logica qui).
- `fix`/`feature` → delegati al `CodeWorker` (branch git, modifiche, test, commit).

process():  ticket `creato`/`rifiutato` → preparazione → `in_attesa`.
finalize(): ticket `approvato` → azione finale → `concluso`.

Le transizioni di stato passano sempre da TicketService (macchina a stati unica).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.integrations.ai.base import AIClient, AIError
from app.integrations.email.sender import EmailSendError, send_reply
from app.models.ticket import Ticket, TicketStatus, TicketType
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.project_repository import ProjectRepository
from app.services.ticket_service import TicketService
from app.workers import prompts
from app.workers.code_worker import CodeWorker


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
        try:
            draft = self._ai.complete(prompts.EMAIL_SYSTEM, prompts.build_email_prompt(ticket))
        except AIError as exc:
            self._tickets.set_ai_fields(ticket_id, ai_note=f"Errore AI: {exc}")
            return self._result(ticket_id, "process")

        self._tickets.set_ai_fields(
            ticket_id, ai_draft=draft, ai_note="Bozza di risposta pronta — rivedi e approva."
        )
        self._tickets.change_status(ticket_id, TicketStatus.IN_ATTESA)
        return self._result(ticket_id, "process")

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
