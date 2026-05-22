"""Configurazione applicativa caricata per ambiente.

L'ambiente è scelto da APP_ENV (dev|staging|prod). Le variabili vengono lette dal
file backend/.env (vedi config/*.env.example) oppure dall'ambiente di sistema.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "staging", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Environment = "dev"
    app_name: str = "tickethub-ai"
    debug: bool = True

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # Origini ammesse per CORS (desktop renderer / mobile)
    cors_origins: list[str] = ["http://localhost:5173", "app://."]

    # Database
    database_url: str = "sqlite:///./data/ticket_ai_manager.sqlite3"

    # Flag di esecuzione job (Step 3): lavorazione parallela vs sequenziale
    worker_parallel: bool = False
    worker_concurrency: int = 2

    # OAuth2 Microsoft (Outlook). Redirect URI da registrare in Azure (Entra).
    ms_oauth_redirect_uri: str = "http://localhost:8000/api/v1/email/oauth/callback"
    # client_id di default (può essere sovrascritto per singolo account).
    ms_oauth_client_id: str | None = None

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    """Istanza singleton delle impostazioni (cache per processo)."""
    return Settings()
