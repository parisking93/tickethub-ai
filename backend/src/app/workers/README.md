# workers/ — Job runner & AI worker (Step 3)

- **`job_runner.py`** — `JobRunner.run_once()` raccoglie i ticket pendenti e li affida
  all'AI worker. Da lavorare: stati `creato` e `rifiutato`. Da finalizzare: `approvato`.
  Sequenziale o parallelo secondo `WORKER_PARALLEL` / `WORKER_CONCURRENCY` (in parallelo
  ogni ticket usa una sessione DB propria).
- **`ai_worker.py`** — `AIWorker`:
  - `process()`: l'AI prepara una **bozza email** (`type=email`) o un **piano di intervento**
    (`fix`/`feature`); salva l'output in `ticket.ai_draft` e porta il ticket a `in_attesa`.
  - `finalize()`: su `approvato`, per le email **invia** la bozza (SMTP) e chiude (`concluso`);
    per `fix`/`feature` il commit su branch arriva allo **Step 4**.
- **`prompts.py`** — prompt di sistema e builder dei prompt (in italiano).

Le transizioni di stato passano sempre da `TicketService` (macchina a stati unica).

## Provider AI

Configurati via `AI_PROVIDER` (vedi `app.core.config` e `integrations/ai/`):
`ollama` (locale), `lmstudio` (locale, OpenAI-compatible), `openai_compatible` (remoto).

## Esecuzione

- Manuale: `POST /api/v1/worker/run` — un giro completo.
- Singolo ticket: `POST /api/v1/worker/tickets/{id}/process`.
- Automatica: `WORKER_AUTORUN=true` + `WORKER_INTERVAL_SECONDS` (scheduler nel lifespan).
