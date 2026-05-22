"""Accesso dati alla configurazione AI (riga singola)."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_settings import AISettings


class AISettingsRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_or_create(self) -> AISettings:
        row = self._db.get(AISettings, 1)
        if row is None:
            env = get_settings()
            row = AISettings(
                id=1,
                provider=env.ai_provider,
                base_url=env.ai_base_url,
                api_key=env.ai_api_key,
                model_email=env.ai_model,
                model_fix=env.ai_model,
                model_feature=env.ai_model,
                model_vision=env.ai_vision_model,
            )
            self._db.add(row)
            self._db.commit()
            self._db.refresh(row)
        return row

    def save(self, row: AISettings) -> AISettings:
        self._db.commit()
        self._db.refresh(row)
        return row
