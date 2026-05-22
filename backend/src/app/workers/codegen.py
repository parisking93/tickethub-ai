"""Parsing e applicazione delle modifiche di codice prodotte dall'AI.

Formato atteso dall'AI (robusto anche per modelli locali): per ogni file da
scrivere, un'intestazione e un blocco di codice con il contenuto COMPLETO:

    ### FILE: percorso/relativo/al/repo.py
    ```python
    <contenuto completo del file>
    ```
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_FILE_BLOCK = re.compile(
    r"###\s*FILE:\s*(?P<path>[^\n]+?)\s*\n```[^\n]*\n(?P<body>.*?)\n```",
    re.DOTALL,
)


class CodegenError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileEdit:
    path: str
    content: str


def parse_file_edits(ai_output: str) -> list[FileEdit]:
    """Estrae le modifiche di file dall'output dell'AI."""
    edits: list[FileEdit] = []
    for match in _FILE_BLOCK.finditer(ai_output):
        path = match.group("path").strip().strip("`").strip()
        edits.append(FileEdit(path=path, content=match.group("body")))
    return edits


def apply_edits(repo_path: str | Path, edits: list[FileEdit]) -> list[str]:
    """Scrive i file nel repo. Ritorna i percorsi modificati.

    Rifiuta percorsi assoluti o che escono dalla cartella del repo (path traversal).
    """
    root = Path(repo_path).resolve()
    written: list[str] = []
    for edit in edits:
        rel = Path(edit.path)
        if rel.is_absolute():
            raise CodegenError(f"Percorso assoluto non ammesso: {edit.path}")
        target = (root / rel).resolve()
        if not str(target).startswith(str(root)):
            raise CodegenError(f"Percorso fuori dal repository: {edit.path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        content = edit.content if edit.content.endswith("\n") else edit.content + "\n"
        target.write_text(content, encoding="utf-8")
        written.append(str(rel).replace("\\", "/"))
    return written
