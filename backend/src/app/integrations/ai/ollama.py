"""Client per Ollama in locale (https://ollama.com)."""

from __future__ import annotations

import base64

import httpx

from app.integrations.ai.base import AIError, clean_ai_output

DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaClient:
    name = "ollama"

    def __init__(self, model: str, base_url: str | None = None, timeout: int = 120) -> None:
        self._model = model
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    def complete(self, system: str, prompt: str, images: list[bytes] | None = None) -> str:
        payload: dict[str, object] = {
            "model": self._model,
            "system": system,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            payload["images"] = [base64.b64encode(img).decode() for img in images]
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(f"{self._base_url}/api/generate", json=payload)
        except httpx.HTTPError as exc:
            raise AIError(f"Ollama non raggiungibile su {self._base_url}: {exc}") from exc

        if resp.status_code != 200:
            raise AIError(f"Ollama ha risposto {resp.status_code}: {resp.text}")
        data = resp.json()
        text = clean_ai_output(data.get("response", ""))
        if not text:
            raise AIError("Ollama ha restituito una risposta vuota.")
        return text
