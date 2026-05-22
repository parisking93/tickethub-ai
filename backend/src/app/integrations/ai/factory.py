"""Costruzione del client AI in base alla configurazione."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.integrations.ai.base import AIClient, AIError
from app.integrations.ai.ollama import OllamaClient
from app.integrations.ai.openai_compatible import LMSTUDIO_BASE_URL, OpenAICompatibleClient


def build_ai_client(settings: Settings | None = None) -> AIClient:
    """Istanzia il client AI configurato (ai_provider)."""
    settings = settings or get_settings()
    provider = settings.ai_provider.lower()

    if provider == "ollama":
        return OllamaClient(
            model=settings.ai_model,
            base_url=settings.ai_base_url,
            timeout=settings.ai_timeout,
        )
    if provider == "lmstudio":
        return OpenAICompatibleClient(
            model=settings.ai_model,
            base_url=settings.ai_base_url or LMSTUDIO_BASE_URL,
            api_key=settings.ai_api_key or "lm-studio",
            timeout=settings.ai_timeout,
        )
    if provider == "openai_compatible":
        if not settings.ai_base_url:
            raise AIError("ai_provider=openai_compatible richiede AI_BASE_URL.")
        return OpenAICompatibleClient(
            model=settings.ai_model,
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
            timeout=settings.ai_timeout,
        )

    raise AIError(f"ai_provider non supportato o disabilitato: {settings.ai_provider!r}")
