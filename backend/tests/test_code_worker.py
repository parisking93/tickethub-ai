"""Test del CodeWorker: branch, applicazione modifiche, test, commit."""

from tests.conftest import FakeAIClient

from app.integrations.git.repo import GitRepo
from app.models.project import Project
from app.models.ticket import TicketStatus, TicketType
from app.repositories.project_repository import ProjectRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import TicketService
from app.workers.code_worker import CodeWorker

FILE_BLOCK = "### FILE: hello.py\n```python\nprint('ciao')\n```\n"


def _setup(db, tmp_git_repo, test_command=None):
    project = ProjectRepository(db).add(
        Project(
            name="proj",
            repo_path=str(tmp_git_repo),
            default_branch="main",
            test_command=test_command,
        )
    )
    svc = TicketService(TicketRepository(db))
    ticket = svc.create(
        TicketCreate(title="Aggiungi saluto", type=TicketType.FIX, project_id=project.id)
    )
    return svc, ticket


def test_process_creates_branch_and_applies_edits(db, tmp_git_repo):
    svc, ticket = _setup(db, tmp_git_repo)
    worker = CodeWorker(svc, FakeAIClient(response=FILE_BLOCK), ProjectRepository(db))

    worker.process(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.IN_ATTESA
    assert updated.branch_name == f"fix/{ticket.id}/aggiungi-saluto"
    assert "hello.py" in updated.ai_draft  # il diff cita il file

    repo = GitRepo(tmp_git_repo)
    assert repo.current_branch() == updated.branch_name
    assert (tmp_git_repo / "hello.py").exists()


def test_process_runs_tests_and_reports(db, tmp_git_repo):
    # Comando di test banale che passa sempre.
    svc, ticket = _setup(db, tmp_git_repo, test_command="git --version")
    worker = CodeWorker(svc, FakeAIClient(response=FILE_BLOCK), ProjectRepository(db))

    worker.process(ticket.id)

    updated = svc.get(ticket.id)
    assert "test OK" in updated.ai_note
    assert "Output test" in updated.ai_draft


def test_process_no_edits_when_ai_returns_text(db, tmp_git_repo):
    svc, ticket = _setup(db, tmp_git_repo)
    worker = CodeWorker(svc, FakeAIClient(response="Non so come fare."), ProjectRepository(db))

    worker.process(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.IN_ATTESA
    assert "non ha prodotto modifiche" in updated.ai_note.lower()


def test_dirty_repo_is_protected(db, tmp_git_repo):
    svc, ticket = _setup(db, tmp_git_repo)
    (tmp_git_repo / "wip.txt").write_text("lavoro in corso\n", encoding="utf-8")
    worker = CodeWorker(svc, FakeAIClient(response=FILE_BLOCK), ProjectRepository(db))

    worker.process(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.IN_LAVORAZIONE  # non procede
    assert "committate" in updated.ai_note.lower()


def test_finalize_commits_on_branch(db, tmp_git_repo):
    svc, ticket = _setup(db, tmp_git_repo)
    worker = CodeWorker(svc, FakeAIClient(response=FILE_BLOCK), ProjectRepository(db))

    worker.process(ticket.id)
    svc.change_status(ticket.id, TicketStatus.APPROVATO)
    worker.finalize(ticket.id)

    updated = svc.get(ticket.id)
    assert updated.status == TicketStatus.CONCLUSO
    assert "Commit" in updated.ai_note

    repo = GitRepo(tmp_git_repo)
    assert not repo.has_changes()  # tutto committato
    assert (tmp_git_repo / "hello.py").exists()
