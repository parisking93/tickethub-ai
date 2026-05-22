"""Test del job runner: raccolta e dispatch dei ticket pendenti."""


from tests.conftest import FakeAIClient

from app.core.config import Settings
from app.models.ticket import TicketStatus, TicketType
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import TicketService
from app.workers.job_runner import JobRunner


def _seed_creato(session_factory, count: int) -> None:
    # Ticket email: lavorabili dal FakeAI senza bisogno di un progetto git.
    session = session_factory()
    try:
        svc = TicketService(TicketRepository(session))
        for i in range(count):
            svc.create(TicketCreate(title=f"Ticket {i}", type=TicketType.EMAIL))
    finally:
        session.close()


def _statuses(session_factory) -> list[TicketStatus]:
    session = session_factory()
    try:
        return [t.status for t in TicketRepository(session).list()]
    finally:
        session.close()


def test_run_once_processes_new_tickets_sequential(session_factory):
    _seed_creato(session_factory, 3)
    runner = JobRunner(
        session_factory, FakeAIClient(), Settings(worker_parallel=False)
    )

    report = runner.run_once()

    assert report.processed == 3
    assert report.finalized == 0
    assert report.errors == []
    assert all(s == TicketStatus.IN_ATTESA for s in _statuses(session_factory))


def test_run_once_parallel(session_factory):
    _seed_creato(session_factory, 4)
    runner = JobRunner(
        session_factory, FakeAIClient(), Settings(worker_parallel=True, worker_concurrency=3)
    )

    report = runner.run_once()

    assert report.processed == 4
    assert all(s == TicketStatus.IN_ATTESA for s in _statuses(session_factory))


def test_run_once_empty(session_factory):
    runner = JobRunner(session_factory, FakeAIClient(), Settings())
    report = runner.run_once()
    assert report.processed == 0
    assert report.finalized == 0
