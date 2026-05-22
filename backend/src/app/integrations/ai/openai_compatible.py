"""Client per endpoint OpenAI-compatibili: LM Studio (locale) e provider remoti.

LM Studio espone http://localhost:1234/v1; i provider remoti usano il loro base_url
e una API key. Il formato richiesta/risposta è quello di /v1/chat/completions.
"""

from __future__ import annotations

import base64

import httpx

from app.integrations.ai.base import AIError, clean_ai_output

LMSTUDIO_BASE_URL = "http://localhost:1234/v1"


class OpenAICompatibleClient:
    name = "openai_compatible"

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 120,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def complete(self, system: str, prompt: str, images: list[bytes] | None = None) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if images:
            content: list[dict[str, object]] = [{"type": "text", "text": prompt}]
            for img in images:
                b64 = base64.b64encode(img).decode()
                content.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                )
            user_content: object = content
        else:
            user_content = prompt
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
        except httpx.HTTPError as exc:
            raise AIError(f"Provider AI non raggiungibile su {self._base_url}: {exc}") from exc

        if resp.status_code != 200:
            raise AIError(f"Provider AI ha risposto {resp.status_code}: {resp.text}")
        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIError(f"Risposta AI in formato inatteso: {data}") from exc
        text = clean_ai_output(text or "")
        if not text:
            raise AIError("Il provider AI ha restituito una risposta vuota.")
        return text
