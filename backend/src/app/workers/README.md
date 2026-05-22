# workers/ — Job runner & AI worker (Step 3)

Qui vivrà:

- **`job_runner.py`** — scheduler che periodicamente raccoglie i ticket in stato
  `creato` (e `rifiutato`) e li passa all'AI worker. Il flag `WORKER_PARALLEL`
  (vedi `app.core.config.Settings`) decide tra lavorazione sequenziale o parallela
  con concorrenza `WORKER_CONCURRENCY`.
- **`ai_worker.py`** — riceve un ticket, sceglie la strategia in base al `type`
  (`email` → prepara bozza e mette `in_attesa`; `fix`/`feature` → lavora il codice
  su un branch git e mette `in_attesa`). Su `approvato` esegue l'azione finale
  (invio email o commit) e chiude il ticket (`concluso`).

L'AI worker userà `TicketService` per le transizioni di stato, così la macchina a
stati resta centralizzata.
