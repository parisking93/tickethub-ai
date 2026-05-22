"""Parsing di un messaggio email grezzo (RFC 822) nei dati utili al ticket."""

from __future__ import annotations

from dataclasses import dataclass
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parseaddr


@dataclass(frozen=True)
class ParsedEmail:
    message_id: str
    subject: str
    from_addr: str
    from_name: str
    body: str

    @property
    def ticket_title(self) -> str:
        return self.subject or f"(senza oggetto) — {self.from_addr}"

    @property
    def ticket_description(self) -> str:
        header = f"Da: {self.from_name or self.from_addr} <{self.from_addr}>"
        return f"{header}\n\n{self.body}".strip()


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except (ValueError, LookupError):
        return value.strip()


def _extract_body(msg: Message) -> str:
    """Estrae il testo: preferisce text/plain, altrimenti il primo testo disponibile."""
    if not msg.is_multipart():
        return _decode_payload(msg)

    plain: str | None = None
    fallback: str | None = None
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disposition = str(part.get("Content-Disposition") or "")
        if "attachment" in disposition.lower():
            continue
        text = _decode_payload(part)
        if ctype == "text/plain" and plain is None:
            plain = text
        elif fallback is None:
            fallback = text
    return (plain or fallback or "").strip()


def _decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, ValueError):
        return payload.decode("utf-8", errors="replace")


def parse_email(raw: bytes, msg: Message) -> ParsedEmail:
    """Costruisce un ParsedEmail dal messaggio già parsato da `email.message_from_bytes`."""
    from_name, from_addr = parseaddr(msg.get("From", ""))
    message_id = (msg.get("Message-ID") or "").strip()
    if not message_id:
        # Fallback deterministico se manca il Message-ID (raro): hash del contenuto.
        from hashlib import sha256

        message_id = f"<no-id-{sha256(raw).hexdigest()[:24]}@tickethub.local>"

    return ParsedEmail(
        message_id=message_id,
        subject=_decode(msg.get("Subject")),
        from_addr=from_addr,
        from_name=_decode(from_name),
        body=_extract_body(msg),
    )
