"""Accesso dati ai ticket e ai loro eventi. Nessuna logica di business: solo query."""

from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_event import TicketEvent, TicketEventType

# Un claim più vecchio di così è considerato "stale" (worker crashato) e riassegnabile.
_STALE_CLAIM = timedelta(minutes=10)

# Stati da cui il job può prendere un ticket per lavorarlo.
_PROCESS_STATES = (TicketStatus.CREATO, TicketStatus.IN_LAVORAZIONE)


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

    def exists_by_external_ref(self, external_ref: str) -> bool:
        stmt = select(Ticket.id).where(Ticket.external_ref == external_ref).limit(1)
        return self._db.scalars(stmt).first() is not None

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

    # --- Claim del job worker (lock anti-doppio-lavoro) ---

    def claim_for_processing(self, now: datetime) -> list[int]:
        """Marca come 'in lavorazione dal job' i ticket da elaborare e ne ritorna gli id.

        Candidati: stato creato/in_lavorazione, non già presi (o con claim stale).
        """
        return self._claim(now, list(_PROCESS_STATES))

    def claim_for_finalize(self, now: datetime) -> list[int]:
        """Marca i ticket approvati da finalizzare e ne ritorna gli id."""
        return self._claim(now, [TicketStatus.APPROVATO])

    def _claim(self, now: datetime, states: list[TicketStatus]) -> list[int]:
        cutoff = now - _STALE_CLAIM
        stmt = select(Ticket).where(
            Ticket.status.in_(states),
            or_(Ticket.claimed_at.is_(None), Ticket.claimed_at < cutoff),
        )
        tickets = list(self._db.scalars(stmt).all())
        for ticket in tickets:
            ticket.claimed_at = now
        self._db.commit()
        return [t.id for t in tickets]

    def release(self, ticket_id: int) -> None:
        ticket = self.get(ticket_id)
        if ticket is not None:
            ticket.claimed_at = None
            self._db.commit()

    # --- Eventi (timeline) ---

    def add_event(self, ticket_id: int, type_: TicketEventType, message: str) -> None:
        self._db.add(TicketEvent(ticket_id=ticket_id, type=type_, message=message))
        self._db.commit()

    def list_events(self, ticket_id: int) -> list[TicketEvent]:
        stmt = (
            select(TicketEvent)
            .where(TicketEvent.ticket_id == ticket_id)
            .order_by(TicketEvent.created_at.asc(), TicketEvent.id.asc())
        )
        return list(self._db.scalars(stmt).all())
