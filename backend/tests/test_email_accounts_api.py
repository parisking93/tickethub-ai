"""Test dell'API account email: creazione, preset provider, validazioni, segreti nascosti."""

import pytest

from app.services import email_account_service


@pytest.fixture(autouse=True)
def _no_imap_verify(monkeypatch):
    # Evita la verifica IMAP reale (chiamata di rete) durante i test.
    monkeypatch.setattr(email_account_service, "verify_imap_account", lambda account: None)


def test_create_gmail_account_uses_preset_and_hides_secret(client):
    resp = client.post(
        "/api/v1/email/accounts",
        json={
            "email": "me@gmail.com",
            "provider": "gmail",
            "auth_type": "password",
            "secret": "app-password",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    # Preset applicato automaticamente
    assert body["imap_host"] == "imap.gmail.com"
    assert body["imap_port"] == 993
    # Il segreto non viene mai esposto; solo i flag derivati
    assert "secret" not in body
    assert body["has_secret"] is True
    assert body["is_authorized"] is True


def test_invalid_credentials_rejected(client, monkeypatch):
    # Se la verifica IMAP fallisce, l'account NON viene creato (niente "autorizzato" fasullo).
    from app.integrations.email.client import ImapConnectionError

    def _boom(account):
        raise ImapConnectionError("login fallito")

    monkeypatch.setattr(email_account_service, "verify_imap_account", _boom)
    resp = client.post(
        "/api/v1/email/accounts",
        json={
            "email": "fake@gmail.com",
            "provider": "gmail",
            "auth_type": "password",
            "secret": "sbagliata",
        },
    )
    assert resp.status_code == 400
    assert client.get("/api/v1/email/accounts").json() == []


def test_password_account_requires_secret(client):
    resp = client.post(
        "/api/v1/email/accounts",
        json={"email": "x@gmail.com", "provider": "gmail", "auth_type": "password"},
    )
    assert resp.status_code == 422  # validazione pydantic


def test_outlook_oauth_account_not_yet_authorized(client):
    resp = client.post(
        "/api/v1/email/accounts",
        json={
            "email": "me@outlook.com",
            "provider": "outlook",
            "auth_type": "oauth2",
            "oauth_client_id": "fake-client-id",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["imap_host"] == "outlook.office365.com"
    assert body["is_authorized"] is False  # manca ancora il refresh token


def test_duplicate_email_conflict(client):
    payload = {
        "email": "dup@gmail.com",
        "provider": "gmail",
        "auth_type": "password",
        "secret": "p",
    }
    assert client.post("/api/v1/email/accounts", json=payload).status_code == 201
    assert client.post("/api/v1/email/accounts", json=payload).status_code == 409


def test_list_and_delete_account(client):
    created = client.post(
        "/api/v1/email/accounts",
        json={"email": "z@gmail.com", "provider": "gmail", "auth_type": "password", "secret": "p"},
    ).json()
    assert len(client.get("/api/v1/email/accounts").json()) == 1

    assert client.delete(f"/api/v1/email/accounts/{created['id']}").status_code == 204
    assert client.get("/api/v1/email/accounts").json() == []
