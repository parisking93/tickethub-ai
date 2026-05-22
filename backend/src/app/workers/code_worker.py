"""CodeWorker: lavora i ticket di codice (fix/feature) su un repository git.

- process(): assicura il repo pulito, crea/seleziona il branch `fix|feature/<id>/<slug>`,
  chiede all'AI le modifiche, le applica, esegue i test, salva diff + esito nel ticket
  e lo porta a `in_attesa` (senza committare).
- finalize(): su approvazione, committa le modifiche sul branch e chiude (`concluso`).

Il commit avviene solo all'approvazione: prima le modifiche restano nel working tree
del branch, ispezionabili dal diff salvato in `ticket.ai_draft`.
"""

from __future__ import annotations

from pathlib import Path

from app.integrations.ai.base import AIClient, AIError
from app.integrations.git.branches import branch_name
from app.integrations.git.repo import GitError, GitRepo
from app.models.ticket import Ticket, TicketStatus
from app.repositories.project_repository import ProjectRepository
from app.services.ticket_service import TicketService
from app.workers import prompts
from app.workers.codegen import CodegenError, apply_edits, parse_file_edits
from app.workers.test_runner import run_tests


class CodeWorker:
    def __init__(
        self,
        tickets: TicketService,
        ai: AIClient,
        projects: ProjectRepository,
    ) -> None:
        self._tickets = tickets
        self._ai = ai
        self._projects = projects

    def process(self, ticket_id: int) -> None:
        ticket = self._tickets.get(ticket_id)
        if ticket.status in (TicketStatus.CREATO, TicketStatus.RIFIUTATO):
            self._tickets.change_status(ticket_id, TicketStatus.IN_LAVORAZIONE)

        repo, error = self._open_repo(ticket)
        if repo is None:
            self._tickets.set_ai_fields(ticket_id, ai_note=error)
            return

        branch = branch_name(ticket.type, ticket.id, ticket.title)
        try:
            if not repo.is_clean():
                self._tickets.set_ai_fields(
                    ticket_id,
                    ai_note="Repository con modifiche non committate: pulisci/stasha prima.",
                )
                return
            repo.checkout_or_create(branch, self._project(ticket).default_branch)

            tracked = repo.list_files()
            file_tree = "\n".join(tracked)
            files_content = self._read_files(repo.path, tracked)
            ai_output = self._ai.complete(
                prompts.CODEGEN_SYSTEM,
                prompts.build_codegen_prompt(ticket, file_tree, files_content),
            )
            edits = parse_file_edits(ai_output)
            if not edits:
                self._tickets.set_ai_fields(
                    ticket_id,
                    ai_draft=ai_output,
                    branch_name=branch,
                    ai_note="L'AI non ha prodotto modifiche di file. Rivedi e ridai indicazioni.",
                )
                self._tickets.change_status(ticket_id, TicketStatus.IN_ATTESA)
                return

            written = apply_edits(repo.path, edits)
            test_outcome = run_tests(repo.path, self._project(ticket).test_command)
            # Stage delle modifiche (così il diff include anche i file NUOVI) senza committare.
            repo.add_all()
            diff = repo.diff(staged=True)
        except AIError as exc:
            self._tickets.set_ai_fields(ticket_id, ai_note=f"Errore AI: {exc}")
            return
        except (GitError, CodegenError) as exc:
            self._tickets.set_ai_fields(ticket_id, ai_note=f"Errore git/codegen: {exc}")
            return

        test_line = (
            "test non eseguiti"
            if not test_outcome.ran
            else ("test OK" if test_outcome.passed else "TEST FALLITI")
        )
        note = f"Branch {branch} · {len(written)} file modificati · {test_line}. Rivedi e approva."
        draft = diff
        if test_outcome.ran:
            draft = f"{diff}\n\n--- Output test ---\n{test_outcome.output}"

        self._tickets.set_ai_fields(
            ticket_id, ai_draft=draft, ai_note=note, branch_name=branch
        )
        self._tickets.change_status(ticket_id, TicketStatus.IN_ATTESA)

    def finalize(self, ticket_id: int) -> None:
        ticket = self._tickets.get(ticket_id)
        repo, error = self._open_repo(ticket)
        if repo is None:
            self._tickets.set_ai_fields(ticket_id, ai_note=error)
            return

        branch = ticket.branch_name or branch_name(ticket.type, ticket.id, ticket.title)
        try:
            repo.checkout_or_create(branch, self._project(ticket).default_branch)
            if not repo.has_changes():
                self._tickets.set_ai_fields(
                    ticket_id, ai_note="Nessuna modifica da committare sul branch."
                )
                return
            commit_hash = repo.commit_all(f"{ticket.type.value}: {ticket.title} (#{ticket.id})")
        except GitError as exc:
            self._tickets.set_ai_fields(ticket_id, ai_note=f"Commit fallito: {exc}")
            return

        self._tickets.set_ai_fields(
            ticket_id, ai_note=f"Commit {commit_hash[:8]} sul branch {branch}."
        )
        self._tickets.change_status(ticket_id, TicketStatus.CONCLUSO)

    # --- helper ---

    @staticmethod
    def _read_files(
        repo_path: Path,
        paths: list[str],
        max_files: int = 25,
        max_per_file: int = 4000,
        total_budget: int = 24000,
    ) -> dict[str, str]:
        """Legge il contenuto dei file tracciati (solo testo) entro un budget.

        Serve a dare contesto all'AI così da preservare il codice esistente.
        Salta file binari o troppo grandi.
        """
        contents: dict[str, str] = {}
        used = 0
        for rel in paths[:max_files]:
            target = repo_path / rel
            try:
                text = target.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue  # binario o illeggibile
            if len(text) > max_per_file:
                text = text[:max_per_file] + "\n…(troncato)"
            if used + len(text) > total_budget:
                break
            contents[rel] = text
            used += len(text)
        return contents

    def _project(self, ticket: Ticket):
        return self._projects.get(ticket.project_id) if ticket.project_id else None

    def _open_repo(self, ticket: Ticket) -> tuple[GitRepo | None, str]:
        project = self._project(ticket)
        if project is None:
            return None, "Nessun progetto git associato al ticket."
        try:
            return GitRepo(project.repo_path), ""
        except GitError as exc:
            return None, f"Repository non valido: {exc}"
