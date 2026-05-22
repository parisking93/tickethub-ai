"""Model ORM del ticket.

Gli enum devono restare allineati con i contratti TS condivisi
(packages/shared/src/ticket.ts).
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TicketStatus(str, enum.Enum):
    CREATO = "creato"
    IN_LAVORAZIONE = "in_lavorazione"
    IN_ATTESA = "in_attesa"
    APPROVATO = "approvato"
    CONCLUSO = "concluso"
    RIFIUTATO = "rifiutato"


class TicketType(str, enum.Enum):
    EMAIL = "email"
    FIX = "fix"
    FEATURE = "feature"


class TicketSource(str, enum.Enum):
    MANUALE = "manuale"
    EMAIL = "email"
    ODOO = "odoo"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    type: Mapped[TicketType] = mapped_column(Enum(TicketType), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), nullable=False, default=TicketStatus.CREATO, index=True
    )
    source: Mapped[TicketSource] = mapped_column(
        Enum(TicketSource), nullable=False, default=TicketSource.MANUALE
    )

    # Nota prodotta dall'AI (es. "va approvata l'email"); compilata allo Step 3.
    ai_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Output dell'AI da rivedere/approvare: bozza email o piano di modifica codice.
    ai_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Nota dell'utente in caso di rifiuto/revisione.
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Branch git per ticket di tipo fix/feature (Step 4).
    branch_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Riferimento esterno (id email/thread o id ticket Odoo) (Step 2/5).
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Provenienza email (per ticket type=email): a chi rispondere e da quale account ---
    source_address: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="SET NULL"), nullable=True
    )

    # --- Progetto git (per ticket type=fix/feature) ---
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
