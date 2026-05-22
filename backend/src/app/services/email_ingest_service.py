"""Importa le email non lette di un account e crea i relativi ticket.

Ogni email diventa un Ticket(type=email, source=email, status=creato), con
external_ref = Message-ID per evitare duplicati. L'invio della bozza e la chiusura
saranno gestiti dall'AI worker (Step 3).
"""

from __future__ import annotations

from app.core.clock import utcnow
from app.core.errors import DomainError
from app.integrations.email.client import ImapEmailClient
from app.integrations.email.parser import ParsedEmail
from app.models.attachment import AttachmentSource
from app.models.ticket import TicketSource, TicketStatus, TicketType
from app.repositories.email_account_repository import EmailAccountRepository
from app.schemas.email_account import EmailSyncResult
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import TicketService


class EmailAccountNotFoundError(DomainError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account email {account_id} non trovato")
        self.account_id = account_id


class EmailIngestService:
    def __init__(
        self,
        accounts: EmailAccountRepository,
        tickets: TicketService,
    ) -> None:
        self._accounts = accounts
        self._tickets = tickets

    def sync_account(self, account_id: int, limit: int = 50) -> EmailSyncResult:
        account = self._accounts.get(account_id)
        if account is None:
            raise EmailAccountNotFoundError(account_id)

        fetched = created = skipped = 0
        errors: list[str] = []

        try:
            with ImapEmailClient(account) as client:
                emails = client.fetch_unseen(limit=limit)

            for parsed in emails:
                fetched += 1
                if self._tickets.message_exists(parsed.message_id):
                    skipped += 1
                    continue
                if self._ingest_one(parsed, account.id):
                    created += 1
        except Exception as exc:  # noqa: BLE001 — riportiamo l'errore senza interrompere
            errors.append(str(exc))

        # Persiste last_synced_at e gli eventuali token OAuth rinnovati durante la connessione.
        account.last_synced_at = utcnow()
        self._accounts.save(account)

        return EmailSyncResult(
            account_id=account_id,
            fetched=fetched,
            created=created,
            skipped=skipped,
            errors=errors,
        )

    def _ingest_one(self, parsed: ParsedEmail, account_id: int) -> bool:
        """Crea un nuovo ticket o accoda al thread esistente. True se ha aggiunto contenuto."""
        thread_ticket_id = self._tickets.find_thread_ticket_id(parsed.thread_refs)

        if thread_ticket_id is not None:
            # Risposta a un thread esistente: accoda il messaggio e gli allegati.
            self._tickets.add_inbound_message(
                thread_ticket_id, parsed.body, parsed.from_addr or None, parsed.message_id
            )
            self._save_attachments(thread_ticket_id, parsed)
            # Riporta in 'creato' così il job rielabora considerando l'intero thread.
            self._tickets.change_status(thread_ticket_id, TicketStatus.CREATO)
            return True

        ticket = self._tickets.create(
            TicketCreate(
                title=parsed.ticket_title[:255],
                description=parsed.ticket_description,
                type=TicketType.EMAIL,
                source=TicketSource.EMAIL,
                external_ref=parsed.message_id,
                source_address=parsed.from_addr or None,
                email_account_id=account_id,
            )
        )
        self._tickets.add_inbound_message(
            ticket.id, parsed.body, parsed.from_addr or None, parsed.message_id
        )
        self._save_attachments(ticket.id, parsed)
        return True

    def _save_attachments(self, ticket_id: int, parsed: ParsedEmail) -> None:
        for att in parsed.attachments:
            self._tickets.attach_file(
                ticket_id, att.filename, att.content_type, att.data, AttachmentSource.EMAIL
            )

    def sync_all(self, limit: int = 50) -> list[EmailSyncResult]:
        results: list[EmailSyncResult] = []
        for account in self._accounts.list(active_only=True):
            results.append(self.sync_account(account.id, limit=limit))
        return results
