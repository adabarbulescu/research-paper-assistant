from __future__ import annotations

import re

import aiohttp
import xml.etree.ElementTree as ET

from models.paper import Paper

ARXIV_API_URL = "https://export.arxiv.org/api/query"

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

SORT_BY_OPTIONS = {"relevance", "submittedDate", "lastUpdatedDate"}
SORT_ORDER_OPTIONS = {"descending", "ascending"}

# Matches the numeric arXiv ID from a full URL or bare ID
_ID_PATTERN = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?$")


def _clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def _extract_arxiv_id(id_url: str) -> str:
    match = _ID_PATTERN.search(id_url)
    return match.group(1) if match else id_url


def build_query(
    query: str,
    category: str | None = None,
) -> str:
    parts: list[str] = []

    if query:
        parts.append(f"all:{query}")

    if category:
        parts.append(f"cat:{category}")

    return " AND ".join(parts) if parts else "all:*"


def build_quick_summary(abstract: str) -> str:
    if not abstract:
        return "No abstract available."

    sentences = [s.strip() for s in abstract.replace("\n", " ").split(".") if s.strip()]

    if not sentences:
        return abstract[:500]

    summary = ". ".join(sentences[:2]).strip()
    if not summary.endswith("."):
        summary += "."

    return summary[:500]


def _parse_entry(entry: ET.Element) -> Paper:
    title = _clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
    summary = _clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
    updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
    id_url = entry.findtext("atom:id", default="", namespaces=ATOM_NS)

    authors = [
        name
        for author in entry.findall("atom:author", ATOM_NS)
        if (name := author.findtext("atom:name", default="", namespaces=ATOM_NS))
    ]

    categories = [
        term
        for cat in entry.findall("atom:category", ATOM_NS)
        if (term := cat.attrib.get("term"))
    ]

    # Extract PDF link from <link> elements
    pdf_url = ""
    for link in entry.findall("atom:link", ATOM_NS):
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href", "")
            break

    # Extract DOI if present
    doi = entry.findtext("arxiv:doi", default="", namespaces=ATOM_NS)

    arxiv_id = _extract_arxiv_id(id_url)

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        summary=summary,
        published=published,
        updated=updated,
        categories=categories,
        arxiv_url=id_url,
        pdf_url=pdf_url,
        doi=doi,
    )


async def search_arxiv(
    query: str,
    category: str | None = None,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    max_results: int = 5,
) -> list[Paper]:
    search_query = build_query(query, category)

    params: dict[str, str | int] = {
        "search_query": search_query,
        "start": 0,
        "max_results": min(max_results, 25),
    }

    if sort_by in SORT_BY_OPTIONS and sort_by != "relevance":
        params["sortBy"] = sort_by
    if sort_order in SORT_ORDER_OPTIONS and sort_order != "descending":
        params["sortOrder"] = sort_order

    async with aiohttp.ClientSession() as session:
        async with session.get(ARXIV_API_URL, params=params) as response:
            response.raise_for_status()
            data = await response.text()

    root = ET.fromstring(data)
    entries = root.findall("atom:entry", ATOM_NS)

    return [_parse_entry(entry) for entry in entries]


async def get_first_arxiv_result(
    query: str,
    category: str | None = None,
) -> Paper | None:
    results = await search_arxiv(query, category=category, max_results=1)
    return results[0] if results else None