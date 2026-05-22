"""Model ORM per gli account email configurati.

Ogni account ha un metodo di autenticazione:
- PASSWORD: IMAP basic con password dedicata (Gmail App Password, iCloud app-specific).
- OAUTH2:  IMAP XOAUTH2 con refresh token (Microsoft/Outlook).

I segreti (password / token) sono salvati in locale nel DB SQLite, che è gitignored.
TODO(sicurezza): cifrare i campi `secret` / `oauth_*` con una chiave gestita dall'app.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailProvider(str, enum.Enum):
    GMAIL = "gmail"
    ICLOUD = "icloud"
    OUTLOOK = "outlook"
    IMAP = "imap"  # IMAP generico (host/porta manuali)


class EmailAuthType(str, enum.Enum):
    PASSWORD = "password"
    OAUTH2 = "oauth2"


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    provider: Mapped[EmailProvider] = mapped_column(Enum(EmailProvider), nullable=False)
    auth_type: Mapped[EmailAuthType] = mapped_column(Enum(EmailAuthType), nullable=False)

    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, nullable=False, default=993)
    # Username IMAP; se assente si usa `email`.
    username: Mapped[str | None] = mapped_column(String(320), nullable=True)
    # Cartella da cui leggere (default INBOX).
    folder: Mapped[str] = mapped_column(String(128), nullable=False, default="INBOX")

    # --- Auth PASSWORD ---
    secret: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # --- Auth OAUTH2 ---
    oauth_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    oauth_refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    oauth_access_token: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    oauth_token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @property
    def login_user(self) -> str:
        return self.username or self.email

    @property
    def is_oauth(self) -> bool:
        return self.auth_type == EmailAuthType.OAUTH2
