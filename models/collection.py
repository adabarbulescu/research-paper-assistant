from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Collection:
    id: int
    name: str
    created_at: str
    paper_count: int = 0
