"""Store transitorio (in-memory) per lo stato del flusso OAuth PKCE.

Il flusso authorization-code dura pochi secondi: associamo lo `state` (anti-CSRF)
al code_verifier e all'account, in attesa del redirect di callback. È adeguato a
un'app desktop a singola istanza; non sopravvive al riavvio del processo.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

# Validità massima di un flusso in sospeso (secondi).
_TTL = 600


@dataclass(frozen=True)
class PendingAuth:
    account_id: int
    code_verifier: str
    redirect_uri: str
    created_at: float


_pending: dict[str, PendingAuth] = {}


def put(state: str, account_id: int, code_verifier: str, redirect_uri: str) -> None:
    _purge()
    _pending[state] = PendingAuth(account_id, code_verifier, redirect_uri, time.time())


def pop(state: str) -> PendingAuth | None:
    _purge()
    return _pending.pop(state, None)


def _purge() -> None:
    now = time.time()
    expired = [s for s, p in _pending.items() if now - p.created_at > _TTL]
    for s in expired:
        _pending.pop(s, None)
