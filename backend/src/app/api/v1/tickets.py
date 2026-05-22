"""Router REST dei ticket (v1)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_ticket_service
from app.core.errors import InvalidStatusTransitionError, TicketNotFoundError
from app.models.ticket import TicketStatus
from app.schemas.ticket import TicketCreate, TicketRead, TicketStatusUpdate
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketRead])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketRead]:
    return service.list(status_filter)


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketRead:
    return service.create(payload)


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> TicketRead:
    try:
        return service.get(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{ticket_id}/status", response_model=TicketRead)
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketRead:
    try:
        return service.change_status(ticket_id, payload.status, payload.review_note)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
