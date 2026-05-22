"""Interfaccia comune ai provider AI (locali o remoti)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class AIError(RuntimeError):
    """Errore di comunicazione/elaborazione con il provider AI."""


@runtime_checkable
class AIClient(Protocol):
    """Contratto minimo: dato un prompt di sistema e uno utente, ritorna testo.

    `images`: lista di immagini (byte) per i modelli multimodali (vision).
    """

    name: str

    def complete(self, system: str, prompt: str, images: list[bytes] | None = None) -> str:
        ...
