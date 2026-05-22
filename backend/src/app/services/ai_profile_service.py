"""Logica di business dei profili AI."""

from __future__ import annotations

from app.core.errors import DomainError
from app.models.ai_profile import AIProfile
from app.repositories.ai_profile_repository import AIProfileRepository
from app.schemas.ai_profile import AIProfileCreate, AIProfileUpdate


class AIProfileExistsError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Esiste già un profilo chiamato '{name}'")


class AIProfileNotFoundError(DomainError):
    def __init__(self, profile_id: int) -> None:
        super().__init__(f"Profilo AI {profile_id} non trovato")
        self.profile_id = profile_id


class AIProfileService:
    def __init__(self, repository: AIProfileRepository) -> None:
        self._repo = repository

    def list(self) -> list[AIProfile]:
        self._repo.get_active()  # garantisce almeno il profilo di default
        return self._repo.list()

    def get_active(self) -> AIProfile:
        return self._repo.get_active()

    def create(self, data: AIProfileCreate) -> AIProfile:
        if self._repo.get_by_name(data.name) is not None:
            raise AIProfileExistsError(data.name)
        profile = AIProfile(**data.model_dump())
        # Se è il primo profilo, attivalo.
        created = self._repo.add(profile)
        if len(self._repo.list()) == 1:
            self._repo.set_active(created)
        return created

    def get(self, profile_id: int) -> AIProfile:
        profile = self._repo.get(profile_id)
        if profile is None:
            raise AIProfileNotFoundError(profile_id)
        return profile

    def update(self, profile_id: int, data: AIProfileUpdate) -> AIProfile:
        profile = self.get(profile_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "api_key" and not value:
                continue  # non sovrascrivere la chiave se vuota
            setattr(profile, field, value)
        return self._repo.save(profile)

    def delete(self, profile_id: int) -> None:
        self._repo.delete(self.get(profile_id))

    def activate(self, profile_id: int) -> AIProfile:
        return self._repo.set_active(self.get(profile_id))
