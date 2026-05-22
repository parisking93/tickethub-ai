"""Schemi Pydantic (DTO) per request/response dei ticket."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketSource, TicketStatus, TicketType


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: TicketType
    source: TicketSource = TicketSource.MANUALE
    external_ref: str | None = None
    source_address: str | None = None
    email_account_id: int | None = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    review_note: str | None = None


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
    created_at: datetime
    updated_at: datetime
