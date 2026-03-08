from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    summary: str = ""
    published: str = ""
    updated: str = ""
    categories: list[str] = field(default_factory=list)
    arxiv_url: str = ""
    pdf_url: str = ""
    doi: str = ""

    @property
    def published_date(self) -> str:
        return self.published[:10] if self.published else "Unknown"

    @property
    def primary_category(self) -> str:
        return self.categories[0] if self.categories else "N/A"
