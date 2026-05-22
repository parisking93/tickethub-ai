"""Test di base sul ciclo di vita del ticket via API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_create_and_list_ticket(client):
    resp = client.post(
        "/api/v1/tickets",
        json={"title": "Bug login", "type": "fix"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "creato"
    assert body["type"] == "fix"

    listing = client.get("/api/v1/tickets")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_valid_status_transition(client):
    ticket_id = client.post(
        "/api/v1/tickets", json={"title": "X", "type": "email"}
    ).json()["id"]

    resp = client.patch(
        f"/api/v1/tickets/{ticket_id}/status", json={"status": "in_lavorazione"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_lavorazione"


def test_status_transitions_are_free(client):
    # La board è kanban: ogni transizione è permessa (anche creato -> concluso).
    ticket_id = client.post(
        "/api/v1/tickets", json={"title": "X", "type": "email"}
    ).json()["id"]
    resp = client.patch(
        f"/api/v1/tickets/{ticket_id}/status", json={"status": "concluso"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "concluso"


def test_update_ticket_details(client):
    ticket_id = client.post(
        "/api/v1/tickets", json={"title": "Vecchio", "type": "fix"}
    ).json()["id"]
    resp = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"title": "Nuovo titolo", "description": "dettagli"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Nuovo titolo"
    assert body["description"] == "dettagli"


def test_ticket_events_timeline(client):
    ticket_id = client.post(
        "/api/v1/tickets", json={"title": "X", "type": "email"}
    ).json()["id"]
    client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "in_lavorazione", "review_note": "rilavora con queste note"},
    )
    events = client.get(f"/api/v1/tickets/{ticket_id}/events").json()
    types = [e["type"] for e in events]
    assert "created" in types
    assert "status_change" in types
    assert "user_note" in types
