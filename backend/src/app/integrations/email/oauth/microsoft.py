"""Flusso OAuth2 Authorization Code + PKCE per Microsoft (Outlook IMAP).

Pensato per un'app desktop "public client" (nessun client secret). L'utente
registra un'app su Azure (Microsoft Entra) di tipo client pubblico, con redirect URI
verso il callback locale del backend, e fornisce il `client_id`.

Riferimento token IMAP: l'access token va usato in SASL XOAUTH2 (vedi auth.py).
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.integrations.email.providers import PROVIDERS
from app.models.email_account import EmailProvider

_cfg = PROVIDERS[EmailProvider.OUTLOOK]


@dataclass(frozen=True)
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_in: int  # secondi


def generate_pkce() -> tuple[str, str]:
    """Ritorna (code_verifier, code_challenge) per il flusso PKCE S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def build_authorize_url(
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    login_hint: str | None = None,
) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": " ".join(_cfg.oauth_scopes),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if login_hint:
        params["login_hint"] = login_hint
    return f"{_cfg.oauth_authorize_url}?{urlencode(params)}"


def exchange_code(
    client_id: str,
    redirect_uri: str,
    code: str,
    code_verifier: str,
) -> TokenSet:
    """Scambia l'authorization code con access + refresh token."""
    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "scope": " ".join(_cfg.oauth_scopes),
    }
    return _post_token(data)


def refresh_access_token(client_id: str, refresh_token: str) -> TokenSet:
    """Ottiene un nuovo access token (e refresh token aggiornato) dal refresh token."""
    data = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": " ".join(_cfg.oauth_scopes),
    }
    return _post_token(data)


def _post_token(data: dict[str, str]) -> TokenSet:
    assert _cfg.oauth_token_url is not None
    with httpx.Client(timeout=30) as client:
        resp = client.post(_cfg.oauth_token_url, data=data)
    if resp.status_code != 200:
        raise RuntimeError(f"Errore token Microsoft ({resp.status_code}): {resp.text}")
    payload = resp.json()
    return TokenSet(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        expires_in=int(payload.get("expires_in", 3600)),
    )
