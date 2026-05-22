"""Router per i profili AI e l'elenco dei modelli disponibili (v1)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_ai_profile_service
from app.core.errors import DomainError
from app.integrations.ai.base import AIError
from app.integrations.ai.factory import list_models
from app.schemas.ai_profile import AIProfileCreate, AIProfileRead, AIProfileUpdate, ModelList
from app.services.ai_profile_service import (
    AIProfileExistsError,
    AIProfileNotFoundError,
    AIProfileService,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/profiles", response_model=list[AIProfileRead])
def list_profiles(
    service: AIProfileService = Depends(get_ai_profile_service),
) -> list[AIProfileRead]:
    return service.list()


@router.post("/profiles", response_model=AIProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: AIProfileCreate,
    service: AIProfileService = Depends(get_ai_profile_service),
) -> AIProfileRead:
    try:
        return service.create(payload)
    except AIProfileExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/profiles/{profile_id}", response_model=AIProfileRead)
def update_profile(
    profile_id: int,
    payload: AIProfileUpdate,
    service: AIProfileService = Depends(get_ai_profile_service),
) -> AIProfileRead:
    try:
        return service.update(profile_id, payload)
    except AIProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/profiles/{profile_id}/activate", response_model=AIProfileRead)
def activate_profile(
    profile_id: int,
    service: AIProfileService = Depends(get_ai_profile_service),
) -> AIProfileRead:
    try:
        return service.activate(profile_id)
    except AIProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    service: AIProfileService = Depends(get_ai_profile_service),
) -> None:
    try:
        service.delete(profile_id)
    except AIProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/models", response_model=ModelList)
def available_models(
    provider: str | None = Query(default=None),
    base_url: str | None = Query(default=None),
    service: AIProfileService = Depends(get_ai_profile_service),
) -> ModelList:
    """Elenca i modelli disponibili dal provider (default: profilo attivo)."""
    active = service.get_active()
    prov = provider or active.provider
    url = base_url or active.base_url
    try:
        return ModelList(provider=prov, models=list_models(prov, url, active.api_key))
    except AIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
