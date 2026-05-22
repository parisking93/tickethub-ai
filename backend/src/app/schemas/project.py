"""Schemi Pydantic per i progetti git."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    repo_path: str = Field(min_length=1, max_length=1024)
    default_branch: str = "main"
    test_command: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    default_branch: str | None = None
    test_command: str | None = None
    active: bool | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    repo_path: str
    default_branch: str
    test_command: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
