"""Interfaccia comune ai provider AI (locali o remoti)."""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

# Formato "harmony" (gpt-oss): la risposta è divisa in canali; ci interessa 'final'.
_HARMONY_FINAL = "<|channel|>final<|message|>"
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_HARMONY_TOKEN = re.compile(r"<\|[^|]*\|>")


def clean_ai_output(text: str) -> str:
    """Rimuove il 'ragionamento' dei modelli e tiene solo la risposta finale.

    Gestisce il formato harmony di gpt-oss (canali analysis/thought/final) e i blocchi
    <think>…</think> dei modelli reasoning (Qwen/DeepSeek), più i token di controllo.
    """
    if not text:
        return text
    cleaned = text
    if _HARMONY_FINAL in cleaned:
        cleaned = cleaned.split(_HARMONY_FINAL)[-1]
    cleaned = _THINK_BLOCK.sub("", cleaned)
    cleaned = _HARMONY_TOKEN.sub("", cleaned)
    return cleaned.strip()


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
