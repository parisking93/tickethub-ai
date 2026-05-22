"""Percorsi di archiviazione dei file (allegati).

La cartella allegati è ricavata dalla posizione del database SQLite, così sta
accanto ai dati (in %APPDATA% per l'app impacchettata) ed è scrivibile.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.core.config import get_settings


def _data_dir() -> Path:
    url = get_settings().database_url
    match = re.match(r"sqlite:///(.+)", url)
    if match:
        return Path(match.group(1)).resolve().parent
    return Path("./data").resolve()


def attachments_root() -> Path:
    root = _data_dir() / "attachments"
    root.mkdir(parents=True, exist_ok=True)
    return root


def store_file(ticket_id: int, filename: str, data: bytes) -> tuple[str, int]:
    """Salva i byte su disco e ritorna (percorso_relativo, dimensione)."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename) or "file"
    folder = attachments_root() / str(ticket_id)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{uuid.uuid4().hex[:8]}_{safe}"
    target.write_bytes(data)
    rel = target.relative_to(attachments_root())
    return str(rel).replace("\\", "/"), len(data)


def resolve_path(relative: str) -> Path:
    return attachments_root() / relative
