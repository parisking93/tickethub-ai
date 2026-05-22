"""Logica di business delle connessioni Odoo (CRUD)."""

from __future__ import annotations

from app.core.errors import DomainError
from app.models.odoo_connection import OdooConnection
from app.repositories.odoo_connection_repository import OdooConnectionRepository
from app.schemas.odoo_connection import OdooConnectionCreate, OdooConnectionUpdate


class OdooConnectionExistsError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Esiste già una connessione Odoo chiamata '{name}'")


class OdooConnectionNotFoundError(DomainError):
    def __init__(self, connection_id: int) -> None:
        super().__init__(f"Connessione Odoo {connection_id} non trovata")
        self.connection_id = connection_id


class OdooConnectionService:
    def __init__(self, repository: OdooConnectionRepository) -> None:
        self._repo = repository

    def create(self, data: OdooConnectionCreate) -> OdooConnection:
        if self._repo.get_by_name(data.name) is not None:
            raise OdooConnectionExistsError(data.name)
        connection = OdooConnection(
            name=data.name,
            url=data.url,
            db_name=data.db_name,
            username=data.username,
            secret=data.secret,
            ticket_model=data.ticket_model,
            default_type=data.default_type,
            project_id=data.project_id,
        )
        return self._repo.add(connection)

    def get(self, connection_id: int) -> OdooConnection:
        connection = self._repo.get(connection_id)
        if connection is None:
            raise OdooConnectionNotFoundError(connection_id)
        return connection

    def list(self) -> list[OdooConnection]:
        return self._repo.list()

    def update(self, connection_id: int, data: OdooConnectionUpdate) -> OdooConnection:
        connection = self.get(connection_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(connection, field, value)
        return self._repo.save(connection)

    def delete(self, connection_id: int) -> None:
        self._repo.delete(self.get(connection_id))
