"""Risoluzione del client AI per operazione, dalla configurazione utente.

Un `ResolveClient` mappa il nome dell'operazione (email/fix/feature/vision) al
client AI con il modello scelto dall'utente (vedi AISettings).
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.config import get_settings
from app.integrations.ai.base import AIClient
from app.integrations.ai.factory import build_client
from app.models.ai_profile import AIProfile

ResolveClient = Callable[[str], AIClient]


def build_resolver(profile: AIProfile) -> ResolveClient:
    timeout = get_settings().ai_timeout
    models = {
        "email": profile.model_email,
        "fix": profile.model_fix,
        "feature": profile.model_feature,
        "vision": profile.model_vision,
    }

    def resolve(operation: str) -> AIClient:
        model = models.get(operation) or profile.model_email
        return build_client(
            provider=profile.provider,
            model=model,
            base_url=profile.base_url,
            api_key=profile.api_key,
            timeout=timeout,
        )

    return resolve
