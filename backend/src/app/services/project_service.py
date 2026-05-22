"""Logica di business dei progetti git."""

from __future__ import annotations

from pathlib import Path

from app.core.errors import DomainError
from app.integrations.git.repo import GitError, GitRepo
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectExistsError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Esiste già un progetto chiamato '{name}'")


class ProjectNotFoundError(DomainError):
    def __init__(self, project_id: int) -> None:
        super().__init__(f"Progetto {project_id} non trovato")
        self.project_id = project_id


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repo = repository

    def create(self, data: ProjectCreate) -> Project:
        if self._repo.get_by_name(data.name) is not None:
            raise ProjectExistsError(data.name)

        path = Path(data.repo_path)
        if not path.exists():
            raise DomainError(f"Percorso inesistente: {data.repo_path}")
        try:
            GitRepo(path)  # valida che sia un repo git
        except GitError as exc:
            raise DomainError(str(exc)) from exc

        project = Project(
            name=data.name,
            repo_path=str(path),
            default_branch=data.default_branch,
            test_command=data.test_command,
        )
        return self._repo.add(project)

    def get(self, project_id: int) -> Project:
        project = self._repo.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    def list(self) -> list[Project]:
        return self._repo.list()

    def update(self, project_id: int, data: ProjectUpdate) -> Project:
        project = self.get(project_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        return self._repo.save(project)

    def delete(self, project_id: int) -> None:
        self._repo.delete(self.get(project_id))
