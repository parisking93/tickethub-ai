"""Generazione dei nomi di branch a partire dal ticket."""

from __future__ import annotations

import re
import unicodedata

from app.models.ticket import TicketType

# Prefisso del branch per tipo di ticket.
_PREFIX: dict[TicketType, str] = {
    TicketType.FIX: "fix",
    TicketType.FEATURE: "feature",
}


def slugify(text: str, max_len: int = 40) -> str:
    """Trasforma un titolo in uno slug adatto a un nome di branch."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if len(normalized) > max_len:
        normalized = normalized[:max_len].rstrip("-")
    return normalized or "ticket"


def branch_name(ticket_type: TicketType, ticket_id: int, title: str) -> str:
    """Es. fix/123/login-non-funziona oppure feature/45/export-csv."""
    prefix = _PREFIX.get(ticket_type)
    if prefix is None:
        raise ValueError(f"Tipo ticket senza branch git: {ticket_type}")
    return f"{prefix}/{ticket_id}/{slugify(title)}"
