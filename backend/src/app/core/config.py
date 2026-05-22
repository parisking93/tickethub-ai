"""Configurazione applicativa caricata per ambiente.

L'ambiente è scelto da APP_ENV (dev|staging|prod). Le variabili vengono lette dal
file backend/.env (vedi config/*.env.example) oppure dall'ambiente di sistema.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "staging", "prod"]

# Path assoluto di backend/.env (config.py = backend/src/app/core/config.py).
# Così le impostazioni si caricano da qualsiasi cartella di avvio. Le variabili
# d'ambiente hanno comunque precedenza (usate dall'app desktop impacchettata).
_BACKEND_DIR = Path(__file__).resolve().parents[3]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
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
    # Scheduler automatico del job (oltre al trigger manuale POST /worker/run)
    worker_autorun: bool = False
    worker_interval_seconds: int = 30

    # --- AI provider (Step 3) ---
    # ollama | lmstudio | openai_compatible | none
    ai_provider: str = "ollama"
    # URL base; se None si usa il default del provider
    # (ollama: http://localhost:11434, lmstudio: http://localhost:1234/v1)
    ai_base_url: str | None = None
    ai_model: str = "llama3.1"
    # Modello per gli allegati immagine (vision). Usato solo se ci sono immagini.
    ai_vision_model: str = "qwen3-vl:30b"
    ai_api_key: str | None = None
    ai_timeout: int = 120

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
