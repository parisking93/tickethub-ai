"""Profili di configurazione AI (salvabili e selezionabili dall'UI).

Ogni profilo ha provider, endpoint, credenziali e un modello per ogni operazione.
Un solo profilo è attivo alla volta: è quello usato dai worker.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIProfile(Base):
    __tablename__ = "ai_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="ollama")
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    model_email: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-oss:20b")
    model_fix: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-oss:20b")
    model_feature: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-oss:20b")
    model_vision: Mapped[str] = mapped_column(String(120), nullable=False, default="qwen3-vl:30b")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
