"""Invio email (SMTP) per la finalizzazione dei ticket di tipo email.

Allo Step 3 è supportato l'invio per gli account ad auth **password** (Gmail/iCloud).
Per gli account OAuth2 (Outlook) l'invio SMTP via XOAUTH2 richiede lo scope
`SMTP.Send`: verrà aggiunto in seguito.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.integrations.email.providers import resolve_imap
from app.models.email_account import EmailAccount, EmailAuthType


class EmailSendError(RuntimeError):
    pass


def send_reply(
    account: EmailAccount,
    to_addr: str,
    subject: str,
    body: str,
    in_reply_to: str | None = None,
) -> None:
    """Invia una risposta testuale dall'account indicato."""
    if account.auth_type != EmailAuthType.PASSWORD or not account.secret:
        raise EmailSendError(
            "Invio supportato solo per account con password dedicata (Gmail/iCloud)."
        )

    preset = resolve_imap(account.provider)
    smtp_host = preset.smtp_host if preset else None
    smtp_port = preset.smtp_port if preset else 587
    if not smtp_host:
        raise EmailSendError(f"Nessun server SMTP noto per il provider {account.provider}.")

    message = EmailMessage()
    message["From"] = account.email
    message["To"] = to_addr
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(account.login_user, account.secret)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(f"Invio SMTP fallito: {exc}") from exc
