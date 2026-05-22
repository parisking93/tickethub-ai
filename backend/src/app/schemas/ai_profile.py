"""Schemi Pydantic per i profili AI."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AIProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: str = "ollama"
    base_url: str | None = None
    api_key: str | None = None
    model_email: str = "gpt-oss:20b"
    model_fix: str = "gpt-oss:20b"
    model_feature: str = "gpt-oss:20b"
    model_vision: str = "qwen3-vl:30b"


class AIProfileUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_email: str | None = None
    model_fix: str | None = None
    model_feature: str | None = None
    model_vision: str | None = None


class AIProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider: str
    base_url: str | None
    model_email: str
    model_fix: str
    model_feature: str
    model_vision: str
    is_active: bool
    has_api_key: bool = False

    @model_validator(mode="before")
    @classmethod
    def _derive(cls, data: object) -> object:
        fields = (
            "id",
            "name",
            "provider",
            "base_url",
            "model_email",
            "model_fix",
            "model_feature",
            "model_vision",
            "is_active",
        )
        base = {f: getattr(data, f) for f in fields}
        base["has_api_key"] = bool(getattr(data, "api_key", None))
        return base


class ModelList(BaseModel):
    provider: str
    models: list[str]
