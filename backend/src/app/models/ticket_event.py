"""Model ORM per la cronologia (timeline) di un ticket.

Registra gli eventi nel tempo — creazione, cambi di stato, note dell'utente,
output dell'AI — così la UI può mostrare le "conversazioni precedenti".
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TicketEventType(str, enum.Enum):
    CREATED = "created"
    STATUS_CHANGE = "status_change"
    USER_NOTE = "user_note"
    AI_NOTE = "ai_note"
    AI_DRAFT = "ai_draft"
    EDIT = "edit"


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[TicketEventType] = mapped_column(Enum(TicketEventType), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
