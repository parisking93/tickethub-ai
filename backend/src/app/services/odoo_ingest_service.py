"""Importa i ticket da Odoo e crea i relativi ticket locali.

Ogni record Odoo diventa un Ticket(status=creato, source=odoo, type=default_type),
con external_ref = "odoo:<connection_id>:<record_id>" per evitare duplicati.
"""

from __future__ import annotations

import contextlib

from app.core.clock import utcnow
from app.core.errors import DomainError
from app.integrations.odoo.client import OdooClient
from app.models.ticket import TicketSource
from app.repositories.odoo_connection_repository import OdooConnectionRepository
from app.schemas.odoo_connection import OdooSyncResult
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import TicketService


class OdooConnectionNotFoundError(DomainError):
    def __init__(self, connection_id: int) -> None:
        super().__init__(f"Connessione Odoo {connection_id} non trovata")
        self.connection_id = connection_id


class OdooIngestService:
    def __init__(
        self,
        connections: OdooConnectionRepository,
        tickets: TicketService,
        client_factory=OdooClient,
    ) -> None:
        self._connections = connections
        self._tickets = tickets
        self._client_factory = client_factory

    def sync_connection(self, connection_id: int, limit: int = 50) -> OdooSyncResult:
        conn = self._connections.get(connection_id)
        if conn is None:
            raise OdooConnectionNotFoundError(connection_id)

        fetched = created = skipped = 0
        errors: list[str] = []
        try:
            client = self._client_factory(conn.url, conn.db_name, conn.username, conn.secret)
            records = client.fetch_tickets(conn.ticket_model, limit=limit)
            for rec in records:
                fetched += 1
                external_ref = f"odoo:{conn.id}:{rec.id}"
                if self._tickets.exists_external_ref(external_ref):
                    skipped += 1
                    continue
                ticket = self._tickets.create(
                    TicketCreate(
                        title=rec.name[:255],
                        description=rec.description or None,
                        type=conn.default_type,
                        source=TicketSource.ODOO,
                        external_ref=external_ref,
                        project_id=conn.project_id,
                    )
                )
                self._save_attachments(client, conn.ticket_model, rec.id, ticket.id)
                created += 1
        except Exception as exc:  # noqa: BLE001 — riportiamo senza interrompere
            errors.append(str(exc))

        conn.last_synced_at = utcnow()
        self._connections.save(conn)

        return OdooSyncResult(
            connection_id=connection_id,
            fetched=fetched,
            created=created,
            skipped=skipped,
            errors=errors,
        )

    def _save_attachments(self, client, model: str, res_id: int, ticket_id: int) -> None:
        from app.models.attachment import AttachmentSource

        with contextlib.suppress(Exception):
            for att in client.fetch_attachments(model, res_id):
                self._tickets.attach_file(
                    ticket_id, att.filename, att.content_type, att.data, AttachmentSource.ODOO
                )

    def sync_all(self, limit: int = 50) -> list[OdooSyncResult]:
        return [
            self.sync_connection(c.id, limit=limit)
            for c in self._connections.list(active_only=True)
        ]
