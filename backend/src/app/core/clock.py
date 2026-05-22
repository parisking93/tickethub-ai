"""Orologio applicativo.

`utcnow()` restituisce l'istante UTC come datetime *naive*, coerente con le colonne
SQLAlchemy `DateTime` (senza timezone) usate nei model. Sostituisce
`datetime.utcnow()`, deprecato da Python 3.12+.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
