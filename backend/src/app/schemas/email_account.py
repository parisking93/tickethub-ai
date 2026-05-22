"""Schemi Pydantic per gli account email.

Importante: lo schema di lettura (`EmailAccountRead`) NON espone segreti
(password, token). Espone solo flag booleani sullo stato della configurazione.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.email_account import EmailAuthType, EmailProvider


class EmailAccountCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str | None = None
    provider: EmailProvider
    auth_type: EmailAuthType
    # Sovrascrivono i preset del provider (necessari per provider=imap).
    imap_host: str | None = None
    imap_port: int | None = None
    username: str | None = None
    folder: str = "INBOX"

    # Auth PASSWORD
    secret: str | None = None
    # Auth OAUTH2 (il refresh_token si ottiene dopo, col flusso OAuth)
    oauth_client_id: str | None = None

    @model_validator(mode="after")
    def _check_auth_fields(self) -> "EmailAccountCreate":
        if self.auth_type == EmailAuthType.PASSWORD and not self.secret:
            raise ValueError("Per auth_type=password serve 'secret' (password dedicata).")
        if self.provider == EmailProvider.IMAP and not self.imap_host:
            raise ValueError("Per provider=imap serve 'imap_host'.")
        return self


class EmailAccountUpdate(BaseModel):
    display_name: str | None = None
    folder: str | None = None
    secret: str | None = None
    oauth_client_id: str | None = None
    active: bool | None = None


class EmailAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None
    provider: EmailProvider
    auth_type: EmailAuthType
    imap_host: str
    imap_port: int
    folder: str
    active: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Stato configurazione (derivato, senza esporre i segreti)
    has_secret: bool = False
    is_authorized: bool = False

    @model_validator(mode="before")
    @classmethod
    def _derive_flags(cls, data: object) -> object:
        # `data` è l'istanza ORM (from_attributes); calcoliamo i flag derivati.
        secret = getattr(data, "secret", None)
        refresh = getattr(data, "oauth_refresh_token", None)
        auth_type = getattr(data, "auth_type", None)
        # Non possiamo mutare l'oggetto ORM: restituiamo un dict arricchito.
        base = {
            field: getattr(data, field)
            for field in (
                "id",
                "email",
                "display_name",
                "provider",
                "auth_type",
                "imap_host",
                "imap_port",
                "folder",
                "active",
                "last_synced_at",
                "created_at",
                "updated_at",
            )
        }
        base["has_secret"] = bool(secret)
        base["is_authorized"] = (
            bool(secret)
            if auth_type == EmailAuthType.PASSWORD
            else bool(refresh)
        )
        return base


class EmailSyncResult(BaseModel):
    account_id: int
    fetched: int
    created: int
    skipped: int
    errors: list[str] = []
