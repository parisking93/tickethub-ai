"""Dependency di FastAPI per il wiring dei layer."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService


def get_ticket_service(db: Session = Depends(get_db)) -> Generator[TicketService, None, None]:
    yield TicketService(TicketRepository(db))
