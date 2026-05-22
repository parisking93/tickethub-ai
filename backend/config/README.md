# config/

Template delle variabili d'ambiente, uno per ambiente:

- `dev.env.example` — sviluppo locale
- `staging.env.example` — staging
- `prod.env.example` — produzione

## Uso

Copia il template dell'ambiente desiderato in `backend/.env`:

```bash
copy config\dev.env.example .env      # Windows
cp   config/dev.env.example .env       # Unix
```

La classe `Settings` (in `src/app/core/config.py`) legge `backend/.env` tramite
`pydantic-settings`. La selezione dell'ambiente avviene con la variabile `APP_ENV`.
I file `.env` reali sono ignorati da git (vedi `.gitignore`).
