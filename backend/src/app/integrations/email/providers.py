"""Preset di configurazione IMAP/OAuth per provider noti."""

from dataclasses import dataclass, field

from app.models.email_account import EmailAuthType, EmailProvider


@dataclass(frozen=True)
class ProviderConfig:
    imap_host: str
    imap_port: int
    default_auth: EmailAuthType
    # Endpoint OAuth2 (solo per provider OAuth)
    oauth_authorize_url: str | None = None
    oauth_token_url: str | None = None
    oauth_scopes: tuple[str, ...] = field(default_factory=tuple)


# Microsoft consente account personali (outlook.com) e aziendali via tenant "common".
_MS_AUTHORIZE = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
_MS_TOKEN = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

PROVIDERS: dict[EmailProvider, ProviderConfig] = {
    EmailProvider.GMAIL: ProviderConfig(
        imap_host="imap.gmail.com",
        imap_port=993,
        default_auth=EmailAuthType.PASSWORD,
    ),
    EmailProvider.ICLOUD: ProviderConfig(
        imap_host="imap.mail.me.com",
        imap_port=993,
        default_auth=EmailAuthType.PASSWORD,
    ),
    EmailProvider.OUTLOOK: ProviderConfig(
        imap_host="outlook.office365.com",
        imap_port=993,
        default_auth=EmailAuthType.OAUTH2,
        oauth_authorize_url=_MS_AUTHORIZE,
        oauth_token_url=_MS_TOKEN,
        # IMAP in lettura. Per l'invio (Step 3) si aggiungerà SMTP.Send.
        oauth_scopes=(
            "https://outlook.office.com/IMAP.AccessAsUser.All",
            "offline_access",
        ),
    ),
}


def resolve_imap(provider: EmailProvider) -> ProviderConfig | None:
    """Config nota per il provider, o None per provider=imap (host manuale)."""
    return PROVIDERS.get(provider)
