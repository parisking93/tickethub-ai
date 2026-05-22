"""Router REST per account email e sincronizzazione (v1)."""

import html

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.api.deps import get_email_account_service, get_email_ingest_service
from app.core.errors import DomainError
from app.schemas.email_account import (
    EmailAccountCreate,
    EmailAccountRead,
    EmailAccountUpdate,
    EmailSyncResult,
)
from app.services.email_account_service import (
    EmailAccountExistsError,
    EmailAccountNotFoundError,
    EmailAccountService,
    OAuthError,
)
from app.services.email_ingest_service import EmailIngestService

router = APIRouter(prefix="/email", tags=["email"])


# --- Account CRUD ---


@router.get("/accounts", response_model=list[EmailAccountRead])
def list_accounts(
    service: EmailAccountService = Depends(get_email_account_service),
) -> list[EmailAccountRead]:
    return service.list()


@router.post("/accounts", response_model=EmailAccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: EmailAccountCreate,
    service: EmailAccountService = Depends(get_email_account_service),
) -> EmailAccountRead:
    try:
        return service.create(payload)
    except EmailAccountExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/accounts/{account_id}", response_model=EmailAccountRead)
def get_account(
    account_id: int,
    service: EmailAccountService = Depends(get_email_account_service),
) -> EmailAccountRead:
    try:
        return service.get(account_id)
    except EmailAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/accounts/{account_id}", response_model=EmailAccountRead)
def update_account(
    account_id: int,
    payload: EmailAccountUpdate,
    service: EmailAccountService = Depends(get_email_account_service),
) -> EmailAccountRead:
    try:
        return service.update(account_id, payload)
    except EmailAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    service: EmailAccountService = Depends(get_email_account_service),
) -> None:
    try:
        service.delete(account_id)
    except EmailAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# --- OAuth2 (Outlook) ---


@router.post("/accounts/{account_id}/oauth/start")
def start_oauth(
    account_id: int,
    service: EmailAccountService = Depends(get_email_account_service),
) -> dict[str, str]:
    """Avvia il flusso OAuth: restituisce l'URL da aprire nel browser."""
    try:
        return {"authorize_url": service.start_oauth(account_id)}
    except EmailAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/oauth/callback", response_class=HTMLResponse)
def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    service: EmailAccountService = Depends(get_email_account_service),
) -> HTMLResponse:
    """Callback del redirect Microsoft: scambia il code e salva i token."""
    if error:
        return _html(f"Autorizzazione negata: {error_description or error}", ok=False)
    if not code or not state:
        return _html("Callback senza 'code' o 'state'.", ok=False)
    try:
        account = service.complete_oauth(state, code)
    except OAuthError as exc:
        return _html(str(exc), ok=False)
    return _html(f"Account {account.email} autorizzato. Puoi chiudere questa finestra.", ok=True)


# --- Sincronizzazione ---


@router.post("/sync", response_model=list[EmailSyncResult])
def sync(
    account_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: EmailIngestService = Depends(get_email_ingest_service),
) -> list[EmailSyncResult]:
    """Scarica le email e crea ticket. Senza account_id sincronizza tutti gli attivi."""
    if account_id is not None:
        return [service.sync_account(account_id, limit=limit)]
    return service.sync_all(limit=limit)


def _html(message: str, ok: bool) -> HTMLResponse:
    color = "#10b981" if ok else "#ef4444"
    icon = "✓" if ok else "✕"
    message = html.escape(message)  # i parametri di redirect non sono fidati
    body = (
        f"<!doctype html><html lang='it'><head><meta charset='utf-8'>"
        f"<title>TicketHub AI — OAuth</title></head>"
        f"<body style='font-family:system-ui;background:#0f1419;color:#e6edf3;"
        f"display:flex;align-items:center;justify-content:center;height:100vh;margin:0'>"
        f"<div style='text-align:center'><div style='font-size:48px;color:{color}'>{icon}</div>"
        f"<p style='font-size:16px'>{message}</p></div></body></html>"
    )
    return HTMLResponse(content=body, status_code=200 if ok else 400)
