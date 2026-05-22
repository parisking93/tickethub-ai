"""Costruzione del client AI in base alla configurazione."""

from __future__ import annotations

import httpx

from app.integrations.ai.base import AIClient, AIError
from app.integrations.ai.ollama import DEFAULT_BASE_URL as OLLAMA_BASE_URL
from app.integrations.ai.ollama import OllamaClient
from app.integrations.ai.openai_compatible import LMSTUDIO_BASE_URL, OpenAICompatibleClient


def build_client(
    provider: str,
    model: str,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: int = 120,
) -> AIClient:
    """Costruisce un client AI per provider+modello arbitrari (usato per-operazione)."""
    provider = provider.lower()
    if provider == "ollama":
        return OllamaClient(model=model, base_url=base_url, timeout=timeout)
    if provider == "lmstudio":
        return OpenAICompatibleClient(
            model=model, base_url=base_url or LMSTUDIO_BASE_URL, api_key=api_key or "lm-studio",
            timeout=timeout,
        )
    if provider == "openai_compatible":
        if not base_url:
            raise AIError("openai_compatible richiede base_url.")
        return OpenAICompatibleClient(
            model=model, base_url=base_url, api_key=api_key, timeout=timeout
        )
    raise AIError(f"Provider AI non supportato: {provider!r}")


def list_models(
    provider: str, base_url: str | None = None, api_key: str | None = None
) -> list[str]:
    """Elenca i modelli disponibili dal provider (Ollama /api/tags, OpenAI /v1/models)."""
    provider = provider.lower()
    try:
        if provider == "ollama":
            url = f"{(base_url or OLLAMA_BASE_URL).rstrip('/')}/api/tags"
            with httpx.Client(timeout=10) as c:
                data = c.get(url).json()
            return sorted(m["name"] for m in data.get("models", []))
        # lmstudio / openai_compatible
        base = (base_url or LMSTUDIO_BASE_URL).rstrip("/")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        with httpx.Client(timeout=10) as c:
            data = c.get(f"{base}/models", headers=headers).json()
        return sorted(m["id"] for m in data.get("data", []))
    except (httpx.HTTPError, KeyError, TypeError) as exc:
        raise AIError(f"Impossibile elencare i modelli ({provider}): {exc}") from exc
