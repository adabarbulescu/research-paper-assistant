from __future__ import annotations

from dataclasses import dataclass

from models.paper import Paper

VALID_STATUSES = {"to-read", "reading", "done"}


@dataclass(frozen=True)
class SavedPaper:
    paper: Paper
    saved_at: str
    status: str = "to-read"
    note: str = ""
