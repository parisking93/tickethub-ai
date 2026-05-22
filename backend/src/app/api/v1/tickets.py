"""Router REST dei ticket (v1)."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_ticket_service
from app.core import storage
from app.core.errors import TicketNotFoundError
from app.models.attachment import AttachmentSource
from app.models.ticket import TicketStatus
from app.schemas.ticket import (
    AttachmentRead,
    TicketCreate,
    TicketEventRead,
    TicketMessageRead,
    TicketRead,
    TicketStatusUpdate,
    TicketUpdate,
)
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


@router.get("/{ticket_id}/events", response_model=list[TicketEventRead])
def get_ticket_events(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketEventRead]:
    try:
        return service.list_events(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketRead:
    try:
        return service.update(ticket_id, payload)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{ticket_id}/messages", response_model=list[TicketMessageRead])
def get_ticket_messages(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketMessageRead]:
    try:
        return service.list_messages(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{ticket_id}/attachments", response_model=list[AttachmentRead])
def get_ticket_attachments(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> list[AttachmentRead]:
    try:
        return service.list_attachments(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{ticket_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    service: TicketService = Depends(get_ticket_service),
) -> AttachmentRead:
    try:
        data = file.file.read()
        return service.attach_file(
            ticket_id,
            file.filename or "allegato",
            file.content_type or "application/octet-stream",
            data,
            AttachmentSource.MANUALE,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{ticket_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_attachment(
    ticket_id: int,
    attachment_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> None:
    if not service.delete_attachment(ticket_id, attachment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allegato non trovato")


@router.get("/{ticket_id}/attachments/{attachment_id}/download")
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> FileResponse:
    attachment = service.get_attachment(attachment_id)
    if attachment is None or attachment.ticket_id != ticket_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allegato non trovato")
    path = storage.resolve_path(attachment.storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato")
    return FileResponse(
        path=str(path), filename=attachment.filename, media_type=attachment.content_type
    )


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
