"""Schemi Pydantic per le connessioni Odoo. La lettura non espone il segreto."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.ticket import TicketType


class OdooConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=512)
    db_name: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    secret: str = Field(min_length=1, max_length=512)
    ticket_model: str = "helpdesk.ticket"
    default_type: TicketType = TicketType.FIX
    project_id: int | None = None


class OdooConnectionUpdate(BaseModel):
    name: str | None = None
    secret: str | None = None
    ticket_model: str | None = None
    default_type: TicketType | None = None
    project_id: int | None = None
    active: bool | None = None


class OdooConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    db_name: str
    username: str
    ticket_model: str
    default_type: TicketType
    project_id: int | None
    active: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
    has_secret: bool = False

    @model_validator(mode="before")
    @classmethod
    def _derive(cls, data: object) -> object:
        fields = (
            "id",
            "name",
            "url",
            "db_name",
            "username",
            "ticket_model",
            "default_type",
            "project_id",
            "active",
            "last_synced_at",
            "created_at",
            "updated_at",
        )
        base = {f: getattr(data, f) for f in fields}
        base["has_secret"] = bool(getattr(data, "secret", None))
        return base


class OdooSyncResult(BaseModel):
    connection_id: int
    fetched: int
    created: int
    skipped: int
    errors: list[str] = []
