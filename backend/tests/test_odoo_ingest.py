"""Test dell'ingest Odoo → ticket, con client XML-RPC finto e dedup."""

from app.integrations.odoo.client import OdooRecord
from app.models.odoo_connection import OdooConnection
from app.models.ticket import TicketSource, TicketStatus, TicketType
from app.repositories.odoo_connection_repository import OdooConnectionRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.odoo_ingest_service import OdooIngestService
from app.services.ticket_service import TicketService

SAMPLE = [
    OdooRecord(id=10, name="Bug import", description="Errore nell'import"),
    OdooRecord(id=11, name="Nuova feature", description=""),
]


class _FakeOdooClient:
    def __init__(self, *args, **kwargs):
        pass

    def fetch_tickets(self, model, limit=50):
        return SAMPLE[:limit]


def _seed_connection(db) -> OdooConnection:
    conn = OdooConnection(
        name="prod",
        url="https://odoo.example.com",
        db_name="mydb",
        username="user",
        secret="apikey",
        ticket_model="helpdesk.ticket",
        default_type=TicketType.FIX,
    )
    return OdooConnectionRepository(db).add(conn)


def _service(db) -> OdooIngestService:
    return OdooIngestService(
        OdooConnectionRepository(db),
        TicketService(TicketRepository(db)),
        client_factory=_FakeOdooClient,
    )


def test_sync_creates_tickets_from_odoo(db):
    conn = _seed_connection(db)
    result = _service(db).sync_connection(conn.id)

    assert result.fetched == 2
    assert result.created == 2
    assert result.errors == []

    tickets = TicketService(TicketRepository(db)).list()
    assert len(tickets) == 2
    assert all(t.source == TicketSource.ODOO for t in tickets)
    assert all(t.type == TicketType.FIX for t in tickets)
    assert all(t.status == TicketStatus.CREATO for t in tickets)
    assert any(t.external_ref == f"odoo:{conn.id}:10" for t in tickets)


def test_sync_dedup(db):
    conn = _seed_connection(db)
    service = _service(db)

    first = service.sync_connection(conn.id)
    second = service.sync_connection(conn.id)

    assert first.created == 2
    assert second.created == 0
    assert second.skipped == 2
    assert len(TicketService(TicketRepository(db)).list()) == 2


def test_sync_records_errors(db):
    conn = _seed_connection(db)

    class _Boom:
        def __init__(self, *a, **k):
            pass

        def fetch_tickets(self, model, limit=50):
            raise OSError("XML-RPC irraggiungibile")

    service = OdooIngestService(
        OdooConnectionRepository(db),
        TicketService(TicketRepository(db)),
        client_factory=_Boom,
    )
    result = service.sync_connection(conn.id)
    assert result.created == 0
    assert result.errors and "XML-RPC" in result.errors[0]
