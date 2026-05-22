"""Router per la configurazione AI e l'elenco dei modelli disponibili (v1)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_ai_settings_service
from app.integrations.ai.base import AIError
from app.integrations.ai.factory import list_models
from app.schemas.ai_settings import AISettingsRead, AISettingsUpdate, ModelList
from app.services.ai_settings_service import AISettingsService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/settings", response_model=AISettingsRead)
def get_ai_settings(
    service: AISettingsService = Depends(get_ai_settings_service),
) -> AISettingsRead:
    return service.get()


@router.put("/settings", response_model=AISettingsRead)
def update_ai_settings(
    payload: AISettingsUpdate,
    service: AISettingsService = Depends(get_ai_settings_service),
) -> AISettingsRead:
    return service.update(payload)


@router.get("/models", response_model=ModelList)
def available_models(
    provider: str | None = Query(default=None),
    base_url: str | None = Query(default=None),
    service: AISettingsService = Depends(get_ai_settings_service),
) -> ModelList:
    """Elenca i modelli disponibili dal provider (usa la config salvata se non passato)."""
    current = service.get()
    prov = provider or current.provider
    url = base_url or current.base_url
    try:
        return ModelList(provider=prov, models=list_models(prov, url, current.api_key))
    except AIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
