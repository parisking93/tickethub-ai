"""Esecuzione del comando di test di un progetto dopo le modifiche."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestOutcome:
    ran: bool
    passed: bool
    output: str


def run_tests(repo_path: str | Path, command: str | None, timeout: int = 600) -> TestOutcome:
    """Esegue il comando di test nel repo. Se `command` è vuoto, non esegue nulla."""
    if not command or not command.strip():
        return TestOutcome(ran=False, passed=True, output="(nessun comando di test configurato)")

    try:
        proc = subprocess.run(
            shlex.split(command),
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return TestOutcome(ran=True, passed=False, output=f"Timeout dopo {timeout}s")
    except (OSError, ValueError) as exc:
        return TestOutcome(ran=True, passed=False, output=f"Impossibile eseguire i test: {exc}")

    output = (proc.stdout + "\n" + proc.stderr).strip()
    # Limita la dimensione salvata sul ticket.
    if len(output) > 4000:
        output = output[:4000] + "\n…(output troncato)"
    return TestOutcome(ran=True, passed=proc.returncode == 0, output=output)
