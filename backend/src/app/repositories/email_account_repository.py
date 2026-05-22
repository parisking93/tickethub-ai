"""Accesso dati agli account email. Solo query, nessuna logica di business."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_account import EmailAccount


class EmailAccountRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, account: EmailAccount) -> EmailAccount:
        self._db.add(account)
        self._db.commit()
        self._db.refresh(account)
        return account

    def get(self, account_id: int) -> EmailAccount | None:
        return self._db.get(EmailAccount, account_id)

    def get_by_email(self, address: str) -> EmailAccount | None:
        stmt = select(EmailAccount).where(EmailAccount.email == address)
        return self._db.scalars(stmt).first()

    def list(self, active_only: bool = False) -> list[EmailAccount]:
        stmt = select(EmailAccount).order_by(EmailAccount.created_at.desc())
        if active_only:
            stmt = stmt.where(EmailAccount.active.is_(True))
        return list(self._db.scalars(stmt).all())

    def save(self, account: EmailAccount) -> EmailAccount:
        self._db.commit()
        self._db.refresh(account)
        return account

    def delete(self, account: EmailAccount) -> None:
        self._db.delete(account)
        self._db.commit()
