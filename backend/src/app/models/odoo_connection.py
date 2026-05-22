"""Model ORM per le connessioni Odoo (import ticket via XML-RPC).

I segreti (password / API key) sono salvati in locale nel DB SQLite (gitignored).
TODO(sicurezza): cifrare il campo `secret`.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.ticket import TicketType


class OdooConnection(Base):
    __tablename__ = "odoo_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    url: Mapped[str] = mapped_column(String(512), nullable=False)
    db_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    secret: Mapped[str] = mapped_column(String(512), nullable=False)

    # Modello Odoo da leggere (es. helpdesk.ticket, project.task).
    ticket_model: Mapped[str] = mapped_column(
        String(120), nullable=False, default="helpdesk.ticket"
    )
    # Tipo assegnato ai ticket importati (di norma codice: fix/feature).
    default_type: Mapped[TicketType] = mapped_column(
        Enum(TicketType), nullable=False, default=TicketType.FIX
    )
    # Progetto git associato ai ticket di codice importati (opzionale).
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
