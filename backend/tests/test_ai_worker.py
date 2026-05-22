"""Test dell'AI worker: lavorazione e finalizzazione dei ticket."""


from tests.conftest import FakeAIClient

from app.integrations.ai.base import AIError
from app.integrations.email.sender import EmailSendError
from app.models.email_account import EmailAccount, EmailAuthType, EmailProvider
from app.models.ticket import TicketStatus, TicketType
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import TicketService
from app.workers import ai_worker as ai_worker_module
from app.workers.ai_worker import AIWorker


def _service(db) -> TicketService:
    return TicketService(TicketRepository(db))


def _worker(db, ai) -> AIWorker:
    return AIWorker(_service(db), ai, EmailAccountRepository(db), ProjectRepository(db))


def _seed_account(db) -> EmailAccount:
    account = EmailAccount(
        email="me@gmail.com",
        provider=EmailProvider.GMAIL,
        auth_type=EmailAuthType.PASSWORD,
        imap_host="imap.gmail.com",
        imap_port=993,
        secret="app-password",
    )
    return EmailAccountRepository(db).add(account)


def test_process_email_creates_draft_and_waits(db):
    svc = _service(db)
    ticket = svc.create(
        TicketCreate(title="Richiesta info", description="Vorrei sapere…", type=TicketType.EMAIL)
    )
    worker = _worker(db, FakeAIClient(response="Gentile cliente, ecco le info…"))

    result = worker.process(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.IN_ATTESA
    assert updated.ai_draft == "Gentile cliente, ecco le info…"
    assert "approva" in updated.ai_note.lower()
    assert result.action == "process"


def test_process_code_without_project_sets_note(db):
    # I ticket fix/feature sono delegati al CodeWorker; senza progetto associato
    # il worker segnala l'assenza e lascia il ticket in lavorazione.
    svc = _service(db)
    ticket = svc.create(TicketCreate(title="Bug crash", type=TicketType.FIX))

    _worker(db, FakeAIClient()).process(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.IN_LAVORAZIONE
    assert "progetto" in updated.ai_note.lower()


def test_process_ai_error_keeps_in_progress(db):
    svc = _service(db)
    ticket = svc.create(TicketCreate(title="X", type=TicketType.EMAIL))
    worker = _worker(db, FakeAIClient(error=AIError("Ollama spento")))

    worker.process(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.IN_LAVORAZIONE
    assert "Errore AI" in updated.ai_note


def test_finalize_email_sends_and_closes(db, monkeypatch):
    account = _seed_account(db)
    svc = _service(db)
    ticket = svc.create(
        TicketCreate(
            title="Domanda",
            type=TicketType.EMAIL,
            external_ref="<orig@x>",
            source_address="cliente@x.com",
            email_account_id=account.id,
        )
    )
    # Porta il ticket fino ad "approvato" con una bozza pronta.
    svc.change_status(ticket.id, TicketStatus.IN_LAVORAZIONE)
    svc.set_ai_fields(ticket.id, ai_draft="Ecco la risposta.")
    svc.change_status(ticket.id, TicketStatus.IN_ATTESA)
    svc.change_status(ticket.id, TicketStatus.APPROVATO)

    sent = {}

    def fake_send(account, to_addr, subject, body, in_reply_to=None):
        sent.update(to=to_addr, subject=subject, body=body, in_reply_to=in_reply_to)

    monkeypatch.setattr(ai_worker_module, "send_reply", fake_send)

    _worker(db, FakeAIClient()).finalize(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.CONCLUSO
    assert sent["to"] == "cliente@x.com"
    assert sent["subject"] == "Re: Domanda"
    assert sent["in_reply_to"] == "<orig@x>"


def test_finalize_email_send_failure_stays_approved(db, monkeypatch):
    account = _seed_account(db)
    svc = _service(db)
    ticket = svc.create(
        TicketCreate(
            title="Domanda",
            type=TicketType.EMAIL,
            source_address="cliente@x.com",
            email_account_id=account.id,
        )
    )
    svc.change_status(ticket.id, TicketStatus.IN_LAVORAZIONE)
    svc.set_ai_fields(ticket.id, ai_draft="Risposta")
    svc.change_status(ticket.id, TicketStatus.IN_ATTESA)
    svc.change_status(ticket.id, TicketStatus.APPROVATO)

    def boom(*a, **kw):
        raise EmailSendError("SMTP ko")

    monkeypatch.setattr(ai_worker_module, "send_reply", boom)

    _worker(db, FakeAIClient()).finalize(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.APPROVATO  # non chiuso
    assert "Invio fallito" in updated.ai_note
