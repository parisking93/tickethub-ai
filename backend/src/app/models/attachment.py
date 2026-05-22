"""Allegati di un ticket (da email, Odoo o caricati manualmente).

I file sono salvati su disco (vedi app.core.storage); qui solo i metadati.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AttachmentSource(str, enum.Enum):
    EMAIL = "email"
    ODOO = "odoo"
    MANUALE = "manuale"


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(255), nullable=False, default="application/octet-stream"
    )
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Percorso relativo alla cartella allegati (vedi storage.py).
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source: Mapped[AttachmentSource] = mapped_column(
        Enum(AttachmentSource), nullable=False, default=AttachmentSource.MANUALE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
