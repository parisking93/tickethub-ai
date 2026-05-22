"""Messaggi del thread di un ticket (conversazione email).

Accumula i messaggi in entrata (email ricevute) e in uscita (risposte inviate
dall'AI), così l'intero thread può essere passato all'AI per il contesto.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"  # ricevuto
    OUTBOUND = "outbound"  # inviato (risposta)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection), nullable=False)
    from_addr: Mapped[str | None] = mapped_column(String(320), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Message-ID dell'email, per il threading (match con In-Reply-To/References).
    message_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
