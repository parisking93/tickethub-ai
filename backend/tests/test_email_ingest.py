"""Test dell'ingest email → ticket, con client IMAP finto e verifica della dedup."""

import pytest

from app.integrations.email.parser import ParsedAttachment, ParsedEmail
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


def test_reply_appends_to_thread(db, seeded_account, monkeypatch):
    svc = TicketService(TicketRepository(db))
    accounts = EmailAccountRepository(db)

    # 1° email
    first = [ParsedEmail("<m1@x>", "Domanda", "cli@x.com", "Cliente", "primo messaggio")]
    monkeypatch.setattr(
        email_ingest_service, "ImapEmailClient", lambda a, **k: _FakeImapClient(first)
    )
    EmailIngestService(accounts, svc).sync_account(seeded_account.id)
    assert len(svc.list()) == 1
    ticket_id = svc.list()[0].id

    # risposta nello stesso thread (In-Reply-To = <m1@x>)
    reply = [
        ParsedEmail(
            "<m2@x>", "Re: Domanda", "cli@x.com", "Cliente", "secondo", in_reply_to="<m1@x>"
        )
    ]
    monkeypatch.setattr(
        email_ingest_service, "ImapEmailClient", lambda a, **k: _FakeImapClient(reply)
    )
    EmailIngestService(accounts, svc).sync_account(seeded_account.id)

    assert len(svc.list()) == 1  # nessun nuovo ticket
    messages = svc.list_messages(ticket_id)
    assert len(messages) == 2
    assert messages[1].body == "secondo"


def test_email_attachment_saved(db, seeded_account, monkeypatch):
    from app.core import storage

    monkeypatch.setattr(
        storage,
        "store_file",
        lambda ticket_id, filename, data: (f"{ticket_id}/{filename}", len(data)),
    )
    sample = [
        ParsedEmail(
            "<a1@x>", "Con allegato", "c@x.com", "C", "corpo",
            attachments=[ParsedAttachment("foto.png", "image/png", b"\x89PNG...")],
        )
    ]
    monkeypatch.setattr(
        email_ingest_service, "ImapEmailClient", lambda a, **k: _FakeImapClient(sample)
    )
    svc = TicketService(TicketRepository(db))
    EmailIngestService(EmailAccountRepository(db), svc).sync_account(seeded_account.id)

    ticket_id = svc.list()[0].id
    atts = svc.list_attachments(ticket_id)
    assert len(atts) == 1
    assert atts[0].filename == "foto.png"
    assert atts[0].content_type == "image/png"


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
