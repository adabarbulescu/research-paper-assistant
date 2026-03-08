from __future__ import annotations

import re

from models.paper import Paper

# Only allow ASCII letters/digits in BibTeX keys
_BIBTEX_KEY_RE = re.compile(r"[^a-zA-Z0-9]")


def _last_first(name: str) -> str:
    """Convert 'First Last' to 'Last, First'. Handles single names."""
    parts = name.strip().rsplit(" ", 1)
    if len(parts) == 2:
        return f"{parts[1]}, {parts[0]}"
    return name.strip()


def _bibtex_key(paper: Paper) -> str:
    first_author = paper.authors[0] if paper.authors else "unknown"
    surname = first_author.strip().rsplit(" ", 1)[-1]
    safe_surname = _BIBTEX_KEY_RE.sub("", surname).lower() or "unknown"
    year = paper.published[:4] if paper.published else "nd"
    return f"{safe_surname}{year}"


def _escape_bibtex(text: str) -> str:
    """Escape special LaTeX characters in BibTeX field values."""
    for char in ("&", "%", "#"):
        text = text.replace(char, f"\\{char}")
    return text


def to_bibtex(paper: Paper) -> str:
    key = _bibtex_key(paper)
    authors = " and ".join(_last_first(a) for a in paper.authors) or "Unknown"
    year = paper.published[:4] if paper.published else ""
    title = _escape_bibtex(paper.title)

    lines = [
        f"@article{{{key},",
        f"  title     = {{{title}}},",
        f"  author    = {{{authors}}},",
        f"  year      = {{{year}}},",
        f"  eprint    = {{{paper.arxiv_id}}},",
        f"  archivePrefix = {{arXiv}},",
        f"  primaryClass  = {{{paper.primary_category}}},",
        f"  url       = {{{paper.arxiv_url}}},",
    ]
    if paper.doi:
        lines.append(f"  doi       = {{{paper.doi}}},")
    lines.append("}")

    return "\n".join(lines)


def to_plain_citation(paper: Paper) -> str:
    authors = ", ".join(paper.authors) if paper.authors else "Unknown"
    year = f" ({paper.published[:4]})" if paper.published else ""
    doi_part = f" doi:{paper.doi}" if paper.doi else ""

    return f"{authors}{year}. {paper.title}. arXiv:{paper.arxiv_id}.{doi_part}"


def to_markdown_citation(paper: Paper) -> str:
    authors = ", ".join(paper.authors) if paper.authors else "Unknown"
    year = f" ({paper.published[:4]})" if paper.published else ""
    doi_part = f" doi:{paper.doi}" if paper.doi else ""

    return (
        f"{authors}{year}. **{paper.title}**. "
        f"[arXiv:{paper.arxiv_id}]({paper.arxiv_url}){doi_part}"
    )
