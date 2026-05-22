"""Test del parsing email → dati ticket."""

import email
from email.message import EmailMessage

from app.integrations.email.parser import parse_email


def _build(subject: str, from_: str, body: str, msg_id: str | None) -> tuple[bytes, EmailMessage]:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_
    if msg_id:
        msg["Message-ID"] = msg_id
    msg.set_content(body)
    raw = msg.as_bytes()
    return raw, email.message_from_bytes(raw)


def test_parse_basic_email():
    raw, msg = _build(
        "Problema login", "Mario Rossi <mario@example.com>", "Non riesco ad accedere.", "<a1@x>"
    )
    parsed = parse_email(raw, msg)

    assert parsed.subject == "Problema login"
    assert parsed.from_addr == "mario@example.com"
    assert parsed.from_name == "Mario Rossi"
    assert parsed.message_id == "<a1@x>"
    assert "Non riesco ad accedere." in parsed.body
    assert parsed.ticket_title == "Problema login"
    assert "Mario Rossi" in parsed.ticket_description


def test_missing_message_id_gets_deterministic_fallback():
    raw, msg = _build("Ciao", "a@b.com", "corpo", None)
    p1 = parse_email(raw, msg)
    p2 = parse_email(raw, msg)
    assert p1.message_id.startswith("<no-id-")
    assert p1.message_id == p2.message_id  # deterministico sullo stesso contenuto


def test_empty_subject_title_fallback():
    raw, msg = _build("", "a@b.com", "x", "<id@x>")
    parsed = parse_email(raw, msg)
    assert "senza oggetto" in parsed.ticket_title
