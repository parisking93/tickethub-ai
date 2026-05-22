"""Entry point dell'eseguibile del backend (impacchettato con PyInstaller).

Avvia uvicorn passando l'oggetto `app` (niente import-string/reload, incompatibili
col freeze). Host/porta dall'ambiente, impostati dall'app desktop che lo lancia.
"""

import os

import uvicorn

from app.main import app


def main() -> None:
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT") or os.environ.get("API_PORT") or "8000")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
