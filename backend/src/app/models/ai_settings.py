"""Configurazione AI modificabile dall'utente (riga singola, id=1).

Permette di scegliere provider (ollama/lmstudio/openai_compatible) e un modello
diverso per ogni operazione (email, fix, feature, immagini). Sovrascrive i default
da variabili d'ambiente.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AISettings(Base):
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="ollama")
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Modello per ogni operazione.
    model_email: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-oss:20b")
    model_fix: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-oss:20b")
    model_feature: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-oss:20b")
    model_vision: Mapped[str] = mapped_column(String(120), nullable=False, default="qwen3-vl:30b")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
