# integrations/ — Integrazioni esterne (Step 2, 3, 4, 5)

Moduli previsti, ognuno con un'interfaccia chiara usata dai worker:

- **`email/`** (Step 2) — IMAP/SMTP per Gmail, Outlook, iCloud. Legge email/thread
  e crea ticket di tipo `email`; invia le bozze approvate.
- **`ai/`** (Step 3) — provider AI dietro un'unica interfaccia:
  - `ollama.py`, `lmstudio.py` (locali)
  - `remote.py` (Anthropic/OpenAI)
  La scelta del provider sarà configurabile.
- **`git/`** (Step 4) — operazioni git: crea branch `fix/<n>/<titolo>` o
  `feature/<n>/<titolo>`, lavora, testa, committa su approvazione.
- **`odoo/`** (Step 5) — client XML-RPC per importare ticket da Odoo.
