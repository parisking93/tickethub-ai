"""Accesso dati ai profili AI."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_profile import AIProfile


class AIProfileRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self) -> list[AIProfile]:
        return list(self._db.scalars(select(AIProfile).order_by(AIProfile.name)).all())

    def get(self, profile_id: int) -> AIProfile | None:
        return self._db.get(AIProfile, profile_id)

    def get_by_name(self, name: str) -> AIProfile | None:
        return self._db.scalars(select(AIProfile).where(AIProfile.name == name)).first()

    def get_active(self) -> AIProfile:
        """Profilo attivo; se non esiste alcun profilo ne crea uno di default dall'env."""
        active = self._db.scalars(select(AIProfile).where(AIProfile.is_active.is_(True))).first()
        if active is not None:
            return active
        existing = self.list()
        if existing:
            existing[0].is_active = True
            self._db.commit()
            return existing[0]
        env = get_settings()
        default = AIProfile(
            name="Predefinito",
            provider=env.ai_provider,
            base_url=env.ai_base_url,
            api_key=env.ai_api_key,
            model_email=env.ai_model,
            model_fix=env.ai_model,
            model_feature=env.ai_model,
            model_vision=env.ai_vision_model,
            is_active=True,
        )
        self._db.add(default)
        self._db.commit()
        self._db.refresh(default)
        return default

    def add(self, profile: AIProfile) -> AIProfile:
        self._db.add(profile)
        self._db.commit()
        self._db.refresh(profile)
        return profile

    def save(self, profile: AIProfile) -> AIProfile:
        self._db.commit()
        self._db.refresh(profile)
        return profile

    def delete(self, profile: AIProfile) -> None:
        self._db.delete(profile)
        self._db.commit()

    def set_active(self, profile: AIProfile) -> AIProfile:
        for p in self.list():
            p.is_active = p.id == profile.id
        self._db.commit()
        self._db.refresh(profile)
        return profile
