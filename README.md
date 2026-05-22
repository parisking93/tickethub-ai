# tickethub-ai

App desktop (e in futuro mobile) per la **gestione automatizzata di ticket via AI**.
I ticket nascono da email (Gmail/Outlook/iCloud), da Odoo o manualmente; un job worker
li passa a un'AI (locale via Ollama/LM Studio, o remota) che li lavora in base al tipo
(`email`, `fix`, `feature`) e li fa avanzare tra gli stati fino all'approvazione manuale.

## Architettura (monorepo)

- **`apps/desktop`** — Electron + React + TypeScript. App scaricabile su Windows. UI a board per stato.
- **`apps/mobile`** — React Native (Step 6). Si connette al backend desktop via API.
- **`backend`** — Python + FastAPI. Job runner, integrazioni AI/email/git/odoo, persistenza SQLite. Layered: `api → services → repositories → models`.
- **`packages/shared`** — Tipi/contratti TypeScript condivisi tra desktop e mobile (stati, tipi ticket).

## Stati del ticket

`creato → in_lavorazione → in_attesa → approvato → concluso`
con ramo di revisione `rifiutato → in_lavorazione`.

## Tipi del ticket

`email` · `fix` · `feature`

## Roadmap

| Step | Contenuto | Stato |
|------|-----------|-------|
| 1 | Scaffold + DB ticket + UI base con stati | ✅ |
| 2 | Integrazione email (IMAP) → crea ticket | ✅ |
| 3 | Job worker + AI worker (Ollama/LM Studio/remoto) | ✅ |
| 4 | Integrazione git (branch `fix/N/titolo`, `feature/N/titolo`) | ✅ |
| 5 | Integrazione Odoo (XML-RPC) | ✅ |
| 6 | App mobile (Expo) + sync desktop | ✅ |

## Sviluppo

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements/dev.txt
copy config\dev.env.example .env
uvicorn app.main:app --reload --app-dir src
```
API su http://127.0.0.1:8000 — docs su http://127.0.0.1:8000/docs

### Desktop
```bash
npm install                   # dalla root (workspaces)
npm run dev -w @tickethub/desktop
```
In sviluppo l'app desktop **avvia da sola il backend** usando il `.venv` di `backend/`.

## Eseguibile Windows (standalone)

Genera un installer `.exe` che include **anche il backend Python** (via PyInstaller):
non serve avere Python installato per usarlo.

```powershell
# prerequisiti una tantum: backend/.venv creato + npm install dalla root
powershell -ExecutionPolicy Bypass -File scripts\build-installer.ps1
```

Output: `apps/desktop/release/Ticket AI Manager-Setup-<versione>.exe`.

Avviando l'app installata, il backend parte automaticamente (porta locale libera,
DB in `%APPDATA%`) e si arresta alla chiusura. L'AI usa Ollama su `localhost:11434`
(modello configurabile via `AI_MODEL`, default `gpt-oss:20b`).
