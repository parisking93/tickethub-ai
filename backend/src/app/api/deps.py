"""Dependency di FastAPI per il wiring dei layer."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.ai_profile_repository import AIProfileRepository
from app.repositories.email_account_repository import EmailAccountRepository
from app.repositories.odoo_connection_repository import OdooConnectionRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.ai_profile_service import AIProfileService
from app.services.email_account_service import EmailAccountService
from app.services.email_ingest_service import EmailIngestService
from app.services.odoo_connection_service import OdooConnectionService
from app.services.odoo_ingest_service import OdooIngestService
from app.services.project_service import ProjectService
from app.services.ticket_service import TicketService


def get_ticket_service(db: Session = Depends(get_db)) -> Generator[TicketService, None, None]:
    yield TicketService(TicketRepository(db))


def get_email_account_service(
    db: Session = Depends(get_db),
) -> Generator[EmailAccountService, None, None]:
    yield EmailAccountService(EmailAccountRepository(db))


def get_email_ingest_service(
    db: Session = Depends(get_db),
) -> Generator[EmailIngestService, None, None]:
    yield EmailIngestService(EmailAccountRepository(db), TicketService(TicketRepository(db)))


def get_project_service(db: Session = Depends(get_db)) -> Generator[ProjectService, None, None]:
    yield ProjectService(ProjectRepository(db))


def get_ai_profile_service(
    db: Session = Depends(get_db),
) -> Generator[AIProfileService, None, None]:
    yield AIProfileService(AIProfileRepository(db))


def get_odoo_connection_service(
    db: Session = Depends(get_db),
) -> Generator[OdooConnectionService, None, None]:
    yield OdooConnectionService(OdooConnectionRepository(db))


def get_odoo_ingest_service(
    db: Session = Depends(get_db),
) -> Generator[OdooIngestService, None, None]:
    yield OdooIngestService(OdooConnectionRepository(db), TicketService(TicketRepository(db)))
