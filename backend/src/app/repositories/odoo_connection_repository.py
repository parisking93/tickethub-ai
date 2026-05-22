"""Accesso dati alle connessioni Odoo. Solo query."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.odoo_connection import OdooConnection


class OdooConnectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, connection: OdooConnection) -> OdooConnection:
        self._db.add(connection)
        self._db.commit()
        self._db.refresh(connection)
        return connection

    def get(self, connection_id: int) -> OdooConnection | None:
        return self._db.get(OdooConnection, connection_id)

    def get_by_name(self, name: str) -> OdooConnection | None:
        return self._db.scalars(
            select(OdooConnection).where(OdooConnection.name == name)
        ).first()

    def list(self, active_only: bool = False) -> list[OdooConnection]:
        stmt = select(OdooConnection).order_by(OdooConnection.name)
        if active_only:
            stmt = stmt.where(OdooConnection.active.is_(True))
        return list(self._db.scalars(stmt).all())

    def save(self, connection: OdooConnection) -> OdooConnection:
        self._db.commit()
        self._db.refresh(connection)
        return connection

    def delete(self, connection: OdooConnection) -> None:
        self._db.delete(connection)
        self._db.commit()
