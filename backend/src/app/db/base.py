"""Base dichiarativa SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base per tutti i model ORM."""
