"""Job runner: raccoglie i ticket pendenti e li affida all'AI worker.

Usa un "claim" (lock) sui ticket: quando un giro prende un ticket gli imposta
`claimed_at`, così i giri successivi NON riprendono i ticket già in lavorazione.
Il claim viene rilasciato a fine elaborazione (anche in caso di errore); i claim
"stale" (worker crashato) vengono recuperati dopo un timeout (vedi repository).

- Da lavorare: ticket `creato` o `in_lavorazione` non presi (process).
- Da finalizzare: ticket `approvato` non presi (finalize).

Sequenziale o parallelo secondo `WORKER_PARALLEL` / `WORKER_CONCURRENCY`.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import Settings, get_settings
from app.repositories.ai_profile_repository import AIProfileRepository
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService
from app.workers.ai_clients import ResolveClient, build_resolver
from app.workers.ai_worker import AIWorker, WorkerResult

# (ticket_id, azione)
_Item = tuple[int, str]

# session -> (operazione -> client). Iniettabile nei test.
ResolverForSession = Callable[[Session], ResolveClient]


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
        settings: Settings | None = None,
        resolver_for_session: ResolverForSession | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings or get_settings()
        self._resolver_for_session = resolver_for_session or self._default_resolver

    @staticmethod
    def _default_resolver(session: Session) -> ResolveClient:
        profile = AIProfileRepository(session).get_active()
        return build_resolver(profile)

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
        """Prende (claim) i ticket pendenti in modo atomico e ne ritorna gli id."""
        session = self._session_factory()
        try:
            repo = TicketRepository(session)
            now = utcnow()
            finalize = [(tid, "finalize") for tid in repo.claim_for_finalize(now)]
            process = [(tid, "process") for tid in repo.claim_for_processing(now)]
            return finalize + process
        finally:
            session.close()

    def _handle(self, item: _Item) -> WorkerResult | str:
        ticket_id, action = item
        session = self._session_factory()
        try:
            tickets = TicketService(TicketRepository(session))
            worker = AIWorker(
                tickets,
                self._resolver_for_session(session),
                EmailAccountRepository(session),
                ProjectRepository(session),
            )
            if action == "process":
                return worker.process(ticket_id)
            return worker.finalize(ticket_id)
        except Exception as exc:  # noqa: BLE001 — un ticket non deve bloccare gli altri
            return f"Ticket {ticket_id} ({action}): {exc}"
        finally:
            # Rilascia sempre il claim, così il ticket può essere ripreso se serve.
            try:
                TicketRepository(session).release(ticket_id)
            finally:
                session.close()
