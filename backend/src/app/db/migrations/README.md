# migrations/ — Alembic (dallo Step 3)

Per lo Step 1 lo schema è creato direttamente da `Base.metadata.create_all()` nel
lifespan di FastAPI (vedi `app/main.py`). Quando il modello dati si stabilizza
inizializzeremo Alembic qui:

```bash
alembic init -t async app/db/migrations
```
