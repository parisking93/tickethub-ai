"""Client Odoo via XML-RPC (stdlib, nessuna dipendenza extra).

Odoo espone /xmlrpc/2/common (autenticazione) e /xmlrpc/2/object (chiamate ai model).
"""

from __future__ import annotations

import xmlrpc.client
from dataclasses import dataclass


class OdooError(RuntimeError):
    pass


@dataclass(frozen=True)
class OdooRecord:
    id: int
    name: str
    description: str


class OdooClient:
    def __init__(self, url: str, db: str, username: str, secret: str) -> None:
        self._url = url.rstrip("/")
        self._db = db
        self._username = username
        self._secret = secret
        self._uid: int | None = None

    def _proxy(self, endpoint: str) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/{endpoint}", allow_none=True)

    def authenticate(self) -> int:
        try:
            uid = self._proxy("common").authenticate(
                self._db, self._username, self._secret, {}
            )
        except (xmlrpc.client.Fault, OSError) as exc:
            raise OdooError(f"Connessione/login Odoo fallita: {exc}") from exc
        if not uid:
            raise OdooError("Credenziali Odoo non valide.")
        self._uid = int(uid)
        return self._uid

    def fetch_tickets(self, model: str, limit: int = 50) -> list[OdooRecord]:
        """Legge gli ultimi record del modello indicato (id desc)."""
        uid = self._uid or self.authenticate()
        try:
            rows = self._proxy("object").execute_kw(
                self._db,
                uid,
                self._secret,
                model,
                "search_read",
                [[]],  # domain vuoto: tutti i record
                {"fields": ["id", "name", "description"], "limit": limit, "order": "id desc"},
            )
        except (xmlrpc.client.Fault, OSError) as exc:
            raise OdooError(f"Lettura {model} fallita: {exc}") from exc

        records: list[OdooRecord] = []
        for row in rows:
            desc = row.get("description")
            records.append(
                OdooRecord(
                    id=int(row["id"]),
                    name=str(row.get("name") or f"Ticket {row['id']}"),
                    description="" if desc in (False, None) else str(desc),
                )
            )
        return records
