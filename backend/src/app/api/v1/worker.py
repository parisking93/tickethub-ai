"""Router del job/AI worker (v1)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.repositories.ai_profile_repository import AIProfileRepository
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.worker import JobRunResponse, WorkerResultItem
from app.services.ticket_service import TicketService
from app.workers.ai_clients import build_resolver
from app.workers.ai_worker import AIWorker
from app.workers.job_runner import JobRunner

router = APIRouter(prefix="/worker", tags=["worker"])


@router.post("/run", response_model=JobRunResponse)
def run_worker() -> JobRunResponse:
    """Esegue un giro del job: finalizza gli approvati e lavora i nuovi/rifiutati."""
    report = JobRunner(SessionLocal).run_once()
    return JobRunResponse(
        processed=report.processed,
        finalized=report.finalized,
        results=[WorkerResultItem(**asdict(r)) for r in report.results],
        errors=report.errors,
    )


@router.post("/tickets/{ticket_id}/process", response_model=WorkerResultItem)
def process_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> WorkerResultItem:
    """Elabora un singolo ticket con l'AI (utile per azione manuale)."""
    resolver = build_resolver(AIProfileRepository(db).get_active())
    worker = AIWorker(
        TicketService(TicketRepository(db)),
        resolver,
        EmailAccountRepository(db),
        ProjectRepository(db),
    )
    result = worker.process(ticket_id)
    return WorkerResultItem(**asdict(result))
