"""Risoluzione del client AI per operazione, dalla configurazione utente.

Un `ResolveClient` mappa il nome dell'operazione (email/fix/feature/vision) al
client AI con il modello scelto dall'utente (vedi AISettings).
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.config import get_settings
from app.integrations.ai.base import AIClient
from app.integrations.ai.factory import build_client
from app.models.ai_settings import AISettings

ResolveClient = Callable[[str], AIClient]


def build_resolver(ai_settings: AISettings) -> ResolveClient:
    timeout = get_settings().ai_timeout
    models = {
        "email": ai_settings.model_email,
        "fix": ai_settings.model_fix,
        "feature": ai_settings.model_feature,
        "vision": ai_settings.model_vision,
    }

    def resolve(operation: str) -> AIClient:
        model = models.get(operation) or ai_settings.model_email
        return build_client(
            provider=ai_settings.provider,
            model=model,
            base_url=ai_settings.base_url,
            api_key=ai_settings.api_key,
            timeout=timeout,
        )

    return resolve
