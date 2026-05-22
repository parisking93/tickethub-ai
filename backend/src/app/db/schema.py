"""Mini-migrazione automatica per SQLite.

`Base.metadata.create_all` crea le tabelle mancanti ma NON aggiunge colonne nuove
a tabelle già esistenti. Questa funzione confronta i model con lo schema reale e
aggiunge via ALTER TABLE le colonne mancanti (solo nullable), evitando errori quando
lo schema evolve tra una versione e l'altra. In futuro si potrà passare ad Alembic.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base import Base

logger = logging.getLogger("tickethub.schema")


def sync_schema(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # tabella nuova: la crea create_all()
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_cols:
                continue
            # Possiamo aggiungere solo colonne nullable (o con default) senza riscrivere la tabella.
            if not column.nullable and column.default is None and column.server_default is None:
                logger.warning(
                    "Colonna %s.%s non aggiungibile automaticamente (NOT NULL).",
                    table.name,
                    column.name,
                )
                continue
            col_type = column.type.compile(dialect=engine.dialect)
            with engine.begin() as conn:
                conn.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}')
                )
            logger.info("Aggiunta colonna %s.%s", table.name, column.name)
