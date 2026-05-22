"""Logica di business dei ticket: stati, modifica, cronologia eventi.

Punto unico usato da API e worker. Le transizioni di stato sono libere (board
in stile kanban: si può spostare il ticket avanti e indietro); ogni cambiamento
viene registrato come evento per la cronologia.
"""

import contextlib

from app.core import storage
from app.core.errors import TicketNotFoundError
from app.models.attachment import Attachment, AttachmentSource
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_event import TicketEvent, TicketEventType
from app.models.ticket_message import MessageDirection, TicketMessage
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate, TicketUpdate

_STATUS_LABELS: dict[TicketStatus, str] = {
    TicketStatus.CREATO: "Creato",
    TicketStatus.IN_LAVORAZIONE: "In lavorazione",
    TicketStatus.IN_ATTESA: "In attesa",
    TicketStatus.APPROVATO: "Approvato",
    TicketStatus.CONCLUSO: "Concluso",
    TicketStatus.RIFIUTATO: "Rifiutato",
}


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self._repo = repository

    def create(self, data: TicketCreate) -> Ticket:
        ticket = Ticket(
            title=data.title,
            description=data.description,
            type=data.type,
            source=data.source,
            external_ref=data.external_ref,
            source_address=data.source_address,
            email_account_id=data.email_account_id,
            project_id=data.project_id,
            status=TicketStatus.CREATO,
        )
        ticket = self._repo.add(ticket)
        self._repo.add_event(
            ticket.id, TicketEventType.CREATED, f"Ticket creato (origine: {data.source.value})."
        )
        return ticket

    def get(self, ticket_id: int) -> Ticket:
        ticket = self._repo.get(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        return ticket

    def list(self, status: TicketStatus | None = None) -> list[Ticket]:
        return self._repo.list(status)

    def list_events(self, ticket_id: int) -> list[TicketEvent]:
        self.get(ticket_id)  # 404 se non esiste
        return self._repo.list_events(ticket_id)

    def exists_external_ref(self, external_ref: str) -> bool:
        """True se esiste già un ticket con quel riferimento esterno (dedup)."""
        return self._repo.exists_by_external_ref(external_ref)

    def update(self, ticket_id: int, data: TicketUpdate) -> Ticket:
        """Modifica i dettagli del ticket; review_note viene registrata come nota utente."""
        ticket = self.get(ticket_id)
        fields = data.model_dump(exclude_unset=True)
        note = fields.pop("review_note", None)

        changed: list[str] = []
        for field, value in fields.items():
            if getattr(ticket, field) != value:
                setattr(ticket, field, value)
                changed.append(field)
        if note is not None:
            ticket.review_note = note
        ticket = self._repo.save(ticket)

        if changed:
            self._repo.add_event(
                ticket_id, TicketEventType.EDIT, f"Dettagli modificati: {', '.join(changed)}."
            )
        if note:
            self._repo.add_event(ticket_id, TicketEventType.USER_NOTE, note)
        return ticket

    def set_ai_fields(
        self,
        ticket_id: int,
        *,
        ai_draft: str | None = None,
        ai_note: str | None = None,
        branch_name: str | None = None,
    ) -> Ticket:
        """Aggiorna gli output prodotti dall'AI (senza cambiare stato) e li registra."""
        ticket = self.get(ticket_id)
        if ai_draft is not None:
            ticket.ai_draft = ai_draft
        if ai_note is not None:
            ticket.ai_note = ai_note
        if branch_name is not None:
            ticket.branch_name = branch_name
        ticket = self._repo.save(ticket)
        if ai_note is not None:
            self._repo.add_event(ticket_id, TicketEventType.AI_NOTE, ai_note)
        if ai_draft is not None:
            self._repo.add_event(ticket_id, TicketEventType.AI_DRAFT, ai_draft)
        return ticket

    def change_status(
        self,
        ticket_id: int,
        target: TicketStatus,
        review_note: str | None = None,
    ) -> Ticket:
        """Cambia stato (transizioni libere) e registra l'evento."""
        ticket = self.get(ticket_id)
        previous = ticket.status
        ticket.status = target
        if review_note:
            ticket.review_note = review_note
        ticket = self._repo.save(ticket)

        if previous != target:
            self._repo.add_event(
                ticket_id,
                TicketEventType.STATUS_CHANGE,
                f"{_STATUS_LABELS[previous]} → {_STATUS_LABELS[target]}",
            )
        if review_note:
            self._repo.add_event(ticket_id, TicketEventType.USER_NOTE, review_note)
        return ticket

    # --- Thread di messaggi ---

    def add_inbound_message(
        self, ticket_id: int, body: str, from_addr: str | None, message_id: str | None
    ) -> None:
        self._repo.add_message(
            ticket_id, MessageDirection.INBOUND, body, from_addr=from_addr, message_id=message_id
        )

    def add_outbound_message(self, ticket_id: int, body: str, from_addr: str | None = None) -> None:
        self._repo.add_message(ticket_id, MessageDirection.OUTBOUND, body, from_addr=from_addr)

    def list_messages(self, ticket_id: int) -> list[TicketMessage]:
        self.get(ticket_id)
        return self._repo.list_messages(ticket_id)

    def message_exists(self, message_id: str) -> bool:
        return self._repo.message_exists(message_id)

    def find_thread_ticket_id(self, message_ids: list[str]) -> int | None:
        return self._repo.find_ticket_id_by_message_ids(message_ids)

    # --- Allegati ---

    def attach_file(
        self,
        ticket_id: int,
        filename: str,
        content_type: str,
        data: bytes,
        source: AttachmentSource,
    ) -> Attachment:
        self.get(ticket_id)
        rel_path, size = storage.store_file(ticket_id, filename, data)
        attachment = self._repo.add_attachment(
            ticket_id, filename, content_type, size, rel_path, source
        )
        self._repo.add_event(ticket_id, TicketEventType.EDIT, f"Allegato aggiunto: {filename}")
        return attachment

    def list_attachments(self, ticket_id: int) -> list[Attachment]:
        self.get(ticket_id)
        return self._repo.list_attachments(ticket_id)

    def get_attachment(self, attachment_id: int) -> Attachment | None:
        return self._repo.get_attachment(attachment_id)

    def delete_attachment(self, ticket_id: int, attachment_id: int) -> bool:
        attachment = self._repo.get_attachment(attachment_id)
        if attachment is None or attachment.ticket_id != ticket_id:
            return False
        with contextlib.suppress(OSError):
            storage.resolve_path(attachment.storage_path).unlink(missing_ok=True)
        filename = attachment.filename
        self._repo.delete_attachment(attachment)
        self._repo.add_event(ticket_id, TicketEventType.EDIT, f"Allegato rimosso: {filename}")
        return True

    # --- Claim del job (delega al repository) ---

    def release_claim(self, ticket_id: int) -> None:
        self._repo.release(ticket_id)
