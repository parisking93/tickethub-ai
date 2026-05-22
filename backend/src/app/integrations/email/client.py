"""Client IMAP per leggere i messaggi di un account email.

Non modifica lo stato della casella (apre la cartella in sola lettura e usa
BODY.PEEK): la deduplica dei ticket avviene a valle per Message-ID.
"""

from __future__ import annotations

import contextlib
import email
import imaplib
from types import TracebackType

from app.integrations.email import auth
from app.integrations.email.parser import ParsedEmail, parse_email
from app.models.email_account import EmailAccount


class ImapEmailClient:
    """Context manager: apre la connessione, autentica, e la chiude all'uscita."""

    def __init__(self, account: EmailAccount, timeout: int = 30) -> None:
        self._account = account
        self._timeout = timeout
        self._conn: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> ImapEmailClient:
        self._conn = imaplib.IMAP4_SSL(
            self._account.imap_host, self._account.imap_port, timeout=self._timeout
        )
        auth.login(self._conn, self._account)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._conn is not None:
            with contextlib.suppress(imaplib.IMAP4.error, OSError):
                self._conn.logout()
            self._conn = None

    def fetch_unseen(self, limit: int = 50) -> list[ParsedEmail]:
        """Scarica fino a `limit` messaggi non letti (i più recenti) senza marcarli letti."""
        if self._conn is None:
            raise RuntimeError("Client IMAP non connesso (usare come context manager).")

        self._conn.select(self._account.folder, readonly=True)
        typ, data = self._conn.search(None, "UNSEEN")
        if typ != "OK" or not data or not data[0]:
            return []

        ids = data[0].split()
        if limit > 0:
            ids = ids[-limit:]  # i più recenti

        parsed: list[ParsedEmail] = []
        for msg_id in ids:
            typ, msg_data = self._conn.fetch(msg_id, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue
            raw = msg_data[0][1]
            message = email.message_from_bytes(raw)
            parsed.append(parse_email(raw, message))
        return parsed
