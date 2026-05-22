"""Test dell'ingest email → ticket, con client IMAP finto e verifica della dedup."""

import pytest

from app.integrations.email.parser import ParsedEmail
from app.models.email_account import EmailAccount, EmailAuthType, EmailProvider
from app.models.ticket import TicketSource, TicketStatus, TicketType
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.ticket_repository import TicketRepository
from app.services import email_ingest_service
from app.services.email_ingest_service import EmailIngestService
from app.services.ticket_service import TicketService

SAMPLE = [
    ParsedEmail("<m1@x>", "Bug A", "a@x.com", "Tizio", "corpo A"),
    ParsedEmail("<m2@x>", "Bug B", "b@x.com", "Caio", "corpo B"),
]


class _FakeImapClient:
    def __init__(self, emails):
        self._emails = emails

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def fetch_unseen(self, limit=50):
        return self._emails[:limit]


@pytest.fixture()
def seeded_account(db):
    account = EmailAccount(
        email="me@gmail.com",
        provider=EmailProvider.GMAIL,
        auth_type=EmailAuthType.PASSWORD,
        imap_host="imap.gmail.com",
        imap_port=993,
        secret="app-password",
    )
    return EmailAccountRepository(db).add(account)


def _make_service(db) -> EmailIngestService:
    return EmailIngestService(EmailAccountRepository(db), TicketService(TicketRepository(db)))


def test_sync_creates_tickets(db, seeded_account, monkeypatch):
    monkeypatch.setattr(
        email_ingest_service, "ImapEmailClient", lambda account, **kw: _FakeImapClient(SAMPLE)
    )
    service = _make_service(db)

    result = service.sync_account(seeded_account.id)

    assert result.fetched == 2
    assert result.created == 2
    assert result.skipped == 0
    assert result.errors == []

    tickets = TicketService(TicketRepository(db)).list()
    assert len(tickets) == 2
    assert all(t.type == TicketType.EMAIL for t in tickets)
    assert all(t.source == TicketSource.EMAIL for t in tickets)
    assert all(t.status == TicketStatus.CREATO for t in tickets)


def test_sync_is_idempotent_dedup(db, seeded_account, monkeypatch):
    monkeypatch.setattr(
        email_ingest_service, "ImapEmailClient", lambda account, **kw: _FakeImapClient(SAMPLE)
    )
    service = _make_service(db)

    first = service.sync_account(seeded_account.id)
    second = service.sync_account(seeded_account.id)

    assert first.created == 2
    assert second.created == 0
    assert second.skipped == 2
    assert len(TicketService(TicketRepository(db)).list()) == 2


def test_sync_records_errors_without_crashing(db, seeded_account, monkeypatch):
    def _boom(account, **kw):
        raise OSError("connessione IMAP fallita")

    monkeypatch.setattr(email_ingest_service, "ImapEmailClient", _boom)
    service = _make_service(db)

    result = service.sync_account(seeded_account.id)
    assert result.created == 0
    assert result.errors and "IMAP" in result.errors[0]
