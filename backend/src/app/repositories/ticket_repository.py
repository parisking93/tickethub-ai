"""Accesso dati ai ticket. Nessuna logica di business qui: solo query."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, ticket: Ticket) -> Ticket:
        self._db.add(ticket)
        self._db.commit()
        self._db.refresh(ticket)
        return ticket

    def get(self, ticket_id: int) -> Ticket | None:
        return self._db.get(Ticket, ticket_id)

    def list(self, status: TicketStatus | None = None) -> list[Ticket]:
        stmt = select(Ticket).order_by(Ticket.created_at.desc())
        if status is not None:
            stmt = stmt.where(Ticket.status == status)
        return list(self._db.scalars(stmt).all())

    def save(self, ticket: Ticket) -> Ticket:
        """Persiste modifiche su un ticket già tracciato dalla sessione."""
        self._db.commit()
        self._db.refresh(ticket)
        return ticket
