"""Accesso dati ai progetti git. Solo query."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, project: Project) -> Project:
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project

    def get(self, project_id: int) -> Project | None:
        return self._db.get(Project, project_id)

    def get_by_name(self, name: str) -> Project | None:
        return self._db.scalars(select(Project).where(Project.name == name)).first()

    def list(self) -> list[Project]:
        return list(self._db.scalars(select(Project).order_by(Project.name)).all())

    def save(self, project: Project) -> Project:
        self._db.commit()
        self._db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self._db.delete(project)
        self._db.commit()
