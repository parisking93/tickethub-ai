"""Test dell'API connessioni Odoo: creazione, segreto nascosto, conflitto, delete."""


def _payload(name: str = "prod") -> dict:
    return {
        "name": name,
        "url": "https://odoo.example.com",
        "db_name": "mydb",
        "username": "user",
        "secret": "apikey",
    }


def test_create_connection_hides_secret(client):
    resp = client.post("/api/v1/odoo/connections", json=_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert "secret" not in body
    assert body["has_secret"] is True
    assert body["ticket_model"] == "helpdesk.ticket"
    assert body["default_type"] == "fix"


def test_duplicate_name_conflict(client):
    assert client.post("/api/v1/odoo/connections", json=_payload()).status_code == 201
    assert client.post("/api/v1/odoo/connections", json=_payload()).status_code == 409


def test_list_and_delete(client):
    created = client.post("/api/v1/odoo/connections", json=_payload("p2")).json()
    assert len(client.get("/api/v1/odoo/connections").json()) == 1
    assert client.delete(f"/api/v1/odoo/connections/{created['id']}").status_code == 204
    assert client.get("/api/v1/odoo/connections").json() == []
