"""Logica di business dei ticket, inclusa la macchina a stati.

Questo service è il punto unico usato sia dall'API sia (in futuro) dall'AI worker,
così la regola sulle transizioni di stato non viene duplicata.
"""

from app.core.errors import InvalidStatusTransitionError, TicketNotFoundError
from app.models.ticket import Ticket, TicketStatus
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate

# Transizioni ammesse, derivate dal flusso operativo:
#   creato -> in_lavorazione               (il job prende in carico)
#   in_lavorazione -> in_attesa            (l'AI ha preparato qualcosa da approvare)
#   in_attesa -> approvato | rifiutato     (decisione dell'utente)
#   approvato -> concluso                  (l'AI invia email / fa commit e chiude)
#   rifiutato -> in_lavorazione            (il job ripassa il ticket con le note)
ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.CREATO: {TicketStatus.IN_LAVORAZIONE},
    TicketStatus.IN_LAVORAZIONE: {TicketStatus.IN_ATTESA, TicketStatus.CONCLUSO},
    TicketStatus.IN_ATTESA: {TicketStatus.APPROVATO, TicketStatus.RIFIUTATO},
    TicketStatus.APPROVATO: {TicketStatus.CONCLUSO, TicketStatus.IN_LAVORAZIONE},
    TicketStatus.RIFIUTATO: {TicketStatus.IN_LAVORAZIONE},
    TicketStatus.CONCLUSO: set(),
}


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self._repo = repository

    def create(self, data: TicketCreate) -> Ticket:
        ticket = Ticket(
            title=data.title,
            description=data.description,
            type=data.type,
            source=data.source,
            external_ref=data.external_ref,
            status=TicketStatus.CREATO,
        )
        return self._repo.add(ticket)

    def get(self, ticket_id: int) -> Ticket:
        ticket = self._repo.get(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        return ticket

    def list(self, status: TicketStatus | None = None) -> list[Ticket]:
        return self._repo.list(status)

    def exists_external_ref(self, external_ref: str) -> bool:
        """True se esiste già un ticket con quel riferimento esterno (dedup)."""
        return self._repo.exists_by_external_ref(external_ref)

    def change_status(
        self,
        ticket_id: int,
        target: TicketStatus,
        review_note: str | None = None,
    ) -> Ticket:
        ticket = self.get(ticket_id)
        if target not in ALLOWED_TRANSITIONS[ticket.status]:
            raise InvalidStatusTransitionError(ticket.status.value, target.value)

        ticket.status = target
        # La nota di revisione ha senso solo quando si rifiuta/rimanda in lavorazione.
        if review_note is not None:
            ticket.review_note = review_note
        return self._repo.save(ticket)
