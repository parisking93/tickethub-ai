"""Schemi Pydantic per le risposte del worker."""

from pydantic import BaseModel


class WorkerResultItem(BaseModel):
    ticket_id: int
    action: str
    status: str
    note: str


class JobRunResponse(BaseModel):
    processed: int
    finalized: int
    results: list[WorkerResultItem]
    errors: list[str]
