"""Eccezioni di dominio e relativa mappatura HTTP."""


class DomainError(Exception):
    """Errore di business generico."""


class TicketNotFoundError(DomainError):
    def __init__(self, ticket_id: int) -> None:
        super().__init__(f"Ticket {ticket_id} non trovato")
        self.ticket_id = ticket_id


class InvalidStatusTransitionError(DomainError):
    """Transizione di stato non ammessa dalla macchina a stati."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Transizione di stato non valida: {current} -> {target}")
        self.current = current
        self.target = target
