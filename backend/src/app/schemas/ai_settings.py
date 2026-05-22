"""Schemi Pydantic per la configurazione AI."""

from pydantic import BaseModel, ConfigDict, model_validator


class AISettingsUpdate(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_email: str | None = None
    model_fix: str | None = None
    model_feature: str | None = None
    model_vision: str | None = None


class AISettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    base_url: str | None
    model_email: str
    model_fix: str
    model_feature: str
    model_vision: str
    has_api_key: bool = False

    @model_validator(mode="before")
    @classmethod
    def _derive(cls, data: object) -> object:
        fields = (
            "provider",
            "base_url",
            "model_email",
            "model_fix",
            "model_feature",
            "model_vision",
        )
        base = {f: getattr(data, f) for f in fields}
        base["has_api_key"] = bool(getattr(data, "api_key", None))
        return base


class ModelList(BaseModel):
    provider: str
    models: list[str]
