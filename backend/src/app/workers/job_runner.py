"""Job runner: raccoglie i ticket pendenti e li affida all'AI worker.

- Da lavorare: ticket in `creato` e `rifiutato` → `process()`.
- Da finalizzare: ticket in `approvato` → `finalize()`.

L'esecuzione è sequenziale o parallela in base ai flag `WORKER_PARALLEL` /
`WORKER_CONCURRENCY`. In parallelo ogni ticket usa una propria sessione DB
(le sessioni SQLAlchemy non sono condivisibili tra thread).
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.ai.base import AIClient
from app.models.ticket import TicketStatus
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService
from app.workers.ai_worker import AIWorker, WorkerResult

# (ticket_id, azione)
_Item = tuple[int, str]


@dataclass
class JobReport:
    processed: int = 0
    finalized: int = 0
    results: list[WorkerResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class JobRunner:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        ai_client: AIClient,
        settings: Settings | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._ai = ai_client
        self._settings = settings or get_settings()

    def run_once(self) -> JobReport:
        items = self._collect()
        report = JobReport()

        if self._settings.worker_parallel and len(items) > 1:
            with ThreadPoolExecutor(max_workers=self._settings.worker_concurrency) as pool:
                outcomes = list(pool.map(self._handle, items))
        else:
            outcomes = [self._handle(item) for item in items]

        for item, outcome in zip(items, outcomes, strict=True):
            action = item[1]
            if isinstance(outcome, WorkerResult):
                report.results.append(outcome)
                if action == "process":
                    report.processed += 1
                else:
                    report.finalized += 1
            else:
                report.errors.append(outcome)
        return report

    def _collect(self) -> list[_Item]:
        session = self._session_factory()
        try:
            repo = TicketRepository(session)
            to_finalize = [(t.id, "finalize") for t in repo.list(TicketStatus.APPROVATO)]
            to_process = [
                (t.id, "process")
                for t in repo.list(TicketStatus.CREATO) + repo.list(TicketStatus.RIFIUTATO)
            ]
            # Prima si finalizzano gli approvati, poi si lavorano i nuovi.
            return to_finalize + to_process
        finally:
            session.close()

    def _handle(self, item: _Item) -> WorkerResult | str:
        ticket_id, action = item
        session = self._session_factory()
        try:
            worker = AIWorker(
                TicketService(TicketRepository(session)),
                self._ai,
                EmailAccountRepository(session),
            )
            if action == "process":
                return worker.process(ticket_id)
            return worker.finalize(ticket_id)
        except Exception as exc:  # noqa: BLE001 — un ticket non deve bloccare gli altri
            return f"Ticket {ticket_id} ({action}): {exc}"
        finally:
            session.close()
