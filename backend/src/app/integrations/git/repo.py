"""Operazioni git su un repository locale, via CLI `git` (nessuna dipendenza extra)."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


class GitRepo:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not (self.path / ".git").exists():
            raise GitError(f"{self.path} non è un repository git.")

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(self.path),
            capture_output=True,
            text=True,
        )
        if check and proc.returncode != 0:
            raise GitError(f"git {' '.join(args)} fallito: {proc.stderr.strip()}")
        return proc

    # --- Stato ---

    def current_branch(self) -> str:
        return self._run("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    def is_clean(self) -> bool:
        return self._run("status", "--porcelain").stdout.strip() == ""

    def branch_exists(self, name: str) -> bool:
        proc = self._run("rev-parse", "--verify", "--quiet", f"refs/heads/{name}", check=False)
        return proc.returncode == 0

    def diff(self, staged: bool = False) -> str:
        args = ["diff", "--staged"] if staged else ["diff"]
        return self._run(*args).stdout

    def list_files(self, limit: int = 400) -> list[str]:
        """File tracciati dal repo (rispetta .gitignore)."""
        files = self._run("ls-files").stdout.splitlines()
        return files[:limit]

    # --- Branch / checkout ---

    def checkout(self, branch: str) -> None:
        self._run("checkout", branch)

    def create_branch(self, name: str, base: str) -> None:
        """Crea `name` a partire da `base` e ci si posiziona sopra."""
        self._run("checkout", base)
        self._run("checkout", "-b", name)

    def checkout_or_create(self, name: str, base: str) -> None:
        if self.branch_exists(name):
            self.checkout(name)
        else:
            self.create_branch(name, base)

    # --- Commit ---

    def add_all(self) -> None:
        self._run("add", "-A")

    def has_changes(self) -> bool:
        """True se ci sono modifiche (staged o meno) rispetto a HEAD."""
        return self._run("status", "--porcelain").stdout.strip() != ""

    def commit_all(self, message: str, author: str | None = None) -> str:
        """Aggiunge tutto e committa; ritorna l'hash. Solleva se non c'è nulla da committare."""
        self.add_all()
        if self._run("diff", "--staged", "--name-only").stdout.strip() == "":
            raise GitError("Nessuna modifica da committare.")
        args = ["commit", "-m", message]
        if author:
            args = ["commit", "-m", message, "--author", author]
        self._run(*args)
        return self._run("rev-parse", "HEAD").stdout.strip()
