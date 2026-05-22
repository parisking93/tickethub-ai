"""Router REST per le connessioni Odoo e la sincronizzazione (v1)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_odoo_connection_service, get_odoo_ingest_service
from app.schemas.odoo_connection import (
    OdooConnectionCreate,
    OdooConnectionRead,
    OdooConnectionUpdate,
    OdooSyncResult,
)
from app.services.odoo_connection_service import (
    OdooConnectionExistsError,
    OdooConnectionNotFoundError,
    OdooConnectionService,
)
from app.services.odoo_ingest_service import OdooIngestService

router = APIRouter(prefix="/odoo", tags=["odoo"])


@router.get("/connections", response_model=list[OdooConnectionRead])
def list_connections(
    service: OdooConnectionService = Depends(get_odoo_connection_service),
) -> list[OdooConnectionRead]:
    return service.list()


@router.post(
    "/connections", response_model=OdooConnectionRead, status_code=status.HTTP_201_CREATED
)
def create_connection(
    payload: OdooConnectionCreate,
    service: OdooConnectionService = Depends(get_odoo_connection_service),
) -> OdooConnectionRead:
    try:
        return service.create(payload)
    except OdooConnectionExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/connections/{connection_id}", response_model=OdooConnectionRead)
def update_connection(
    connection_id: int,
    payload: OdooConnectionUpdate,
    service: OdooConnectionService = Depends(get_odoo_connection_service),
) -> OdooConnectionRead:
    try:
        return service.update(connection_id, payload)
    except OdooConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: int,
    service: OdooConnectionService = Depends(get_odoo_connection_service),
) -> None:
    try:
        service.delete(connection_id)
    except OdooConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/sync", response_model=list[OdooSyncResult])
def sync(
    connection_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: OdooIngestService = Depends(get_odoo_ingest_service),
) -> list[OdooSyncResult]:
    """Importa i ticket da Odoo. Senza connection_id sincronizza tutte le attive."""
    if connection_id is not None:
        return [service.sync_connection(connection_id, limit=limit)]
    return service.sync_all(limit=limit)
