"""Fixture condivise per i test: DB temporaneo, TestClient FastAPI, AI finto."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class FakeAIClient:
    """Client AI finto: ritorna un testo prestabilito (o solleva un errore)."""

    name = "fake"

    def __init__(self, response: str = "Testo generato dall'AI.", error: Exception | None = None):
        self._response = response
        self._error = error

    def complete(self, system: str, prompt: str) -> str:
        if self._error is not None:
            raise self._error
        return self._response


@pytest.fixture()
def fake_ai() -> FakeAIClient:
    return FakeAIClient()
