"""Entrypoint dell'applicazione FastAPI."""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import email, tickets, worker
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine

settings = get_settings()
logger = logging.getLogger("tickethub.worker")


async def _worker_loop() -> None:
    """Scheduler automatico del job (attivo solo se WORKER_AUTORUN=true)."""
    from app.integrations.ai.base import AIError
    from app.integrations.ai.factory import build_ai_client
    from app.workers.job_runner import JobRunner

    while True:
        await asyncio.sleep(settings.worker_interval_seconds)
        try:
            ai_client = build_ai_client()
            report = await asyncio.to_thread(JobRunner(SessionLocal, ai_client).run_once)
            if report.processed or report.finalized or report.errors:
                logger.info(
                    "Job: %s lavorati, %s finalizzati, %s errori",
                    report.processed,
                    report.finalized,
                    len(report.errors),
                )
        except AIError as exc:
            logger.warning("Job saltato: %s", exc)
        except Exception:  # noqa: BLE001 — il loop non deve mai morire
            logger.exception("Errore inatteso nel job worker")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Step 1: creazione schema diretta. In seguito passeremo ad Alembic.
    Base.metadata.create_all(bind=engine)

    task: asyncio.Task[None] | None = None
    if settings.worker_autorun:
        task = asyncio.create_task(_worker_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    app.include_router(tickets.router, prefix="/api/v1")
    app.include_router(email.router, prefix="/api/v1")
    app.include_router(worker.router, prefix="/api/v1")
    return app


app = create_app()
