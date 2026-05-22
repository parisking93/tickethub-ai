"""Logica di business degli account email: CRUD e flusso OAuth2."""

from __future__ import annotations

import secrets
from datetime import timedelta

from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.errors import DomainError
from app.integrations.email.oauth import microsoft, state
from app.integrations.email.providers import resolve_imap
from app.models.email_account import EmailAccount, EmailAuthType, EmailProvider
from app.repositories.email_account_repository import EmailAccountRepository
from app.schemas.email_account import EmailAccountCreate, EmailAccountUpdate

settings = get_settings()


class EmailAccountExistsError(DomainError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Esiste già un account per {address}")


class EmailAccountNotFoundError(DomainError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account email {account_id} non trovato")
        self.account_id = account_id


class OAuthError(DomainError):
    pass


class EmailAccountService:
    def __init__(self, repository: EmailAccountRepository) -> None:
        self._repo = repository

    def create(self, data: EmailAccountCreate) -> EmailAccount:
        if self._repo.get_by_email(data.email) is not None:
            raise EmailAccountExistsError(data.email)

        preset = resolve_imap(data.provider)
        host = data.imap_host or (preset.imap_host if preset else None)
        port = data.imap_port or (preset.imap_port if preset else 993)
        if not host:
            raise DomainError("imap_host mancante e nessun preset per il provider.")

        account = EmailAccount(
            email=data.email,
            display_name=data.display_name,
            provider=data.provider,
            auth_type=data.auth_type,
            imap_host=host,
            imap_port=port,
            username=data.username,
            folder=data.folder,
            secret=data.secret if data.auth_type == EmailAuthType.PASSWORD else None,
            oauth_client_id=(
                data.oauth_client_id or settings.ms_oauth_client_id
                if data.auth_type == EmailAuthType.OAUTH2
                else None
            ),
        )
        return self._repo.add(account)

    def get(self, account_id: int) -> EmailAccount:
        account = self._repo.get(account_id)
        if account is None:
            raise EmailAccountNotFoundError(account_id)
        return account

    def list(self) -> list[EmailAccount]:
        return self._repo.list()

    def update(self, account_id: int, data: EmailAccountUpdate) -> EmailAccount:
        account = self.get(account_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)
        return self._repo.save(account)

    def delete(self, account_id: int) -> None:
        self._repo.delete(self.get(account_id))

    # --- Flusso OAuth2 (Outlook) ---

    def start_oauth(self, account_id: int, redirect_uri: str | None = None) -> str:
        """Genera l'URL di autorizzazione Microsoft (PKCE). Restituisce l'URL da aprire."""
        account = self.get(account_id)
        if account.auth_type != EmailAuthType.OAUTH2:
            raise OAuthError("L'account non usa OAuth2.")
        if account.provider != EmailProvider.OUTLOOK:
            raise OAuthError(f"Provider OAuth non supportato: {account.provider}")
        if not account.oauth_client_id:
            raise OAuthError(
                "Manca il client_id OAuth. Impostalo sull'account o in MS_OAUTH_CLIENT_ID."
            )

        redirect = redirect_uri or settings.ms_oauth_redirect_uri
        verifier, challenge = microsoft.generate_pkce()
        st = secrets.token_urlsafe(24)
        state.put(st, account_id, verifier, redirect)
        return microsoft.build_authorize_url(
            client_id=account.oauth_client_id,
            redirect_uri=redirect,
            state=st,
            code_challenge=challenge,
            login_hint=account.email,
        )

    def complete_oauth(self, oauth_state: str, code: str) -> EmailAccount:
        """Completa il flusso: scambia il code e salva i token sull'account."""
        pending = state.pop(oauth_state)
        if pending is None:
            raise OAuthError("State OAuth non valido o scaduto.")

        account = self.get(pending.account_id)
        if not account.oauth_client_id:
            raise OAuthError("client_id OAuth mancante.")

        tokens = microsoft.exchange_code(
            client_id=account.oauth_client_id,
            redirect_uri=pending.redirect_uri,
            code=code,
            code_verifier=pending.code_verifier,
        )
        if not tokens.refresh_token:
            raise OAuthError(
                "Nessun refresh token ricevuto: verifica lo scope 'offline_access'."
            )
        account.oauth_refresh_token = tokens.refresh_token
        account.oauth_access_token = tokens.access_token
        account.oauth_token_expiry = utcnow() + timedelta(seconds=tokens.expires_in)
        return self._repo.save(account)
