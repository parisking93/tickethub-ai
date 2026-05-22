"""Schemi Pydantic (DTO) per request/response dei ticket."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.attachment import AttachmentSource
from app.models.ticket import TicketSource, TicketStatus, TicketType
from app.models.ticket_event import TicketEventType
from app.models.ticket_message import MessageDirection


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: TicketType
    source: TicketSource = TicketSource.MANUALE
    external_ref: str | None = None
    source_address: str | None = None
    email_account_id: int | None = None
    project_id: int | None = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    review_note: str | None = None


class TicketUpdate(BaseModel):
    """Modifica dei dettagli del ticket (stile Odoo)."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    type: TicketType | None = None
    project_id: int | None = None


class TicketEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TicketEventType
    message: str
    created_at: datetime


class TicketMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direction: MessageDirection
    from_addr: str | None
    body: str
    created_at: datetime


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    size: int
    source: AttachmentSource
    created_at: datetime


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    type: TicketType
    status: TicketStatus
    source: TicketSource
    ai_note: str | None
    ai_draft: str | None
    review_note: str | None
    branch_name: str | None
    external_ref: str | None
    source_address: str | None
    email_account_id: int | None
    project_id: int | None
    created_at: datetime
    updated_at: datetime
