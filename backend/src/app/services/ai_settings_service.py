"""Logica di business della configurazione AI."""

from __future__ import annotations

from app.models.ai_settings import AISettings
from app.repositories.ai_settings_repository import AISettingsRepository
from app.schemas.ai_settings import AISettingsUpdate


class AISettingsService:
    def __init__(self, repository: AISettingsRepository) -> None:
        self._repo = repository

    def get(self) -> AISettings:
        return self._repo.get_or_create()

    def update(self, data: AISettingsUpdate) -> AISettings:
        row = self._repo.get_or_create()
        for field, value in data.model_dump(exclude_unset=True).items():
            # api_key vuota = non modificare (per non cancellarla involontariamente)
            if field == "api_key" and not value:
                continue
            setattr(row, field, value)
        return self._repo.save(row)
