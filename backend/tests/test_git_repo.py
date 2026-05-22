"""Test del layer git (operazioni su repository) e della naming dei branch."""

import pytest

from app.integrations.git.branches import branch_name, slugify
from app.integrations.git.repo import GitError, GitRepo
from app.models.ticket import TicketType


def test_slugify():
    assert slugify("Login non funziona!") == "login-non-funziona"
    assert slugify("Àccénti & spazi") == "accenti-spazi"
    assert slugify("") == "ticket"


def test_branch_name():
    assert branch_name(TicketType.FIX, 12, "Bug login") == "fix/12/bug-login"
    assert branch_name(TicketType.FEATURE, 7, "Export CSV") == "feature/7/export-csv"
    with pytest.raises(ValueError):
        branch_name(TicketType.EMAIL, 1, "x")


def test_not_a_repo(tmp_path):
    with pytest.raises(GitError):
        GitRepo(tmp_path)


def test_branch_lifecycle_and_commit(tmp_git_repo):
    repo = GitRepo(tmp_git_repo)
    assert repo.current_branch() == "main"
    assert repo.is_clean()

    repo.create_branch("fix/1/test", "main")
    assert repo.current_branch() == "fix/1/test"
    assert repo.branch_exists("fix/1/test")

    (tmp_git_repo / "nuovo.txt").write_text("contenuto\n", encoding="utf-8")
    assert repo.has_changes()
    assert not repo.is_clean()
    assert "nuovo.txt" in repo.diff() or "nuovo.txt" in repo._run("status", "--porcelain").stdout

    commit_hash = repo.commit_all("aggiunto nuovo.txt")
    assert len(commit_hash) >= 7
    assert not repo.has_changes()


def test_checkout_or_create_idempotent(tmp_git_repo):
    repo = GitRepo(tmp_git_repo)
    repo.checkout_or_create("feature/2/x", "main")
    repo.checkout("main")
    repo.checkout_or_create("feature/2/x", "main")  # esiste già: solo checkout
    assert repo.current_branch() == "feature/2/x"


def test_commit_without_changes_raises(tmp_git_repo):
    repo = GitRepo(tmp_git_repo)
    with pytest.raises(GitError):
        repo.commit_all("niente da committare")
