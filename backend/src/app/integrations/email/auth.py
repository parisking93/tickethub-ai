"""Strategie di autenticazione IMAP: password (basic) e OAuth2 (XOAUTH2).

Le funzioni OAuth possono mutare l'access token / la scadenza sull'oggetto
`EmailAccount` (refresh trasparente): è compito del chiamante persistere l'account
dopo l'uso (lo fa l'EmailIngestService al termine del sync).
"""

from __future__ import annotations

import imaplib
from datetime import timedelta

from app.core.clock import utcnow
from app.integrations.email.oauth import microsoft
from app.models.email_account import EmailAccount, EmailProvider

# Margine prima della scadenza entro cui rinnoviamo comunque il token.
_REFRESH_MARGIN = timedelta(minutes=5)


def _xoauth2_bytes(user: str, access_token: str) -> bytes:
    return f"user={user}\x01auth=Bearer {access_token}\x01\x01".encode()


def ensure_oauth_token(account: EmailAccount) -> str:
    """Restituisce un access token valido, rinnovandolo se scaduto/mancante.

    Muta in-memory `account.oauth_access_token`, `oauth_token_expiry` e
    (se ruotato) `oauth_refresh_token`.
    """
    if not account.oauth_client_id or not account.oauth_refresh_token:
        raise RuntimeError(
            f"Account {account.email}: OAuth non configurato (manca client_id o refresh token)."
        )

    now = utcnow()
    token_valid = (
        account.oauth_access_token
        and account.oauth_token_expiry
        and account.oauth_token_expiry - _REFRESH_MARGIN > now
    )
    if token_valid:
        return account.oauth_access_token  # type: ignore[return-value]

    if account.provider != EmailProvider.OUTLOOK:
        raise RuntimeError(f"Provider OAuth non supportato: {account.provider}")

    tokens = microsoft.refresh_access_token(
        account.oauth_client_id, account.oauth_refresh_token
    )
    account.oauth_access_token = tokens.access_token
    account.oauth_token_expiry = now + timedelta(seconds=tokens.expires_in)
    if tokens.refresh_token:
        account.oauth_refresh_token = tokens.refresh_token
    return tokens.access_token


def login(imap: imaplib.IMAP4, account: EmailAccount) -> None:
    """Autentica la connessione IMAP secondo l'auth_type dell'account."""
    if account.is_oauth:
        access_token = ensure_oauth_token(account)
        auth_string = _xoauth2_bytes(account.login_user, access_token)
        imap.authenticate("XOAUTH2", lambda _: auth_string)
    else:
        if not account.secret:
            raise RuntimeError(f"Account {account.email}: password mancante.")
        imap.login(account.login_user, account.secret)
