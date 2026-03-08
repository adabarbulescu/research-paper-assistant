import aiohttp
import xml.etree.ElementTree as ET

ARXIV_API_URL = "https://export.arxiv.org/api/query"

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_quick_summary(abstract: str) -> str:

    if not abstract:
        return "No abstract available."

    sentences = [s.strip() for s in abstract.replace("\n", " ").split(".") if s.strip()]

    if not sentences:
        return _shorten(abstract, 500)

    first = sentences[0]
    second = sentences[1] if len(sentences) > 1 else ""

    summary_parts = [first]
    if second:
        summary_parts.append(second)

    summary = ". ".join(summary_parts).strip()
    if not summary.endswith("."):
        summary += "."

    return _shorten(summary, 500)


async def search_arxiv(query: str, max_results: int = 5):
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(ARXIV_API_URL, params=params) as response:
            response.raise_for_status()
            data = await response.text()

    root = ET.fromstring(data)
    entries = root.findall("atom:entry", ATOM_NS)

    results = []

    for entry in entries:
        title = _clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
        summary = _clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        paper_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)

        authors = []
        for author in entry.findall("atom:author", ATOM_NS):
            name = author.findtext("atom:name", default="", namespaces=ATOM_NS)
            if name:
                authors.append(name)

        categories = []
        for category in entry.findall("atom:category", ATOM_NS):
            term = category.attrib.get("term")
            if term:
                categories.append(term)

        results.append(
            {
                "title": title,
                "authors": authors,
                "published": published,
                "link": paper_id,
                "summary": summary,
                "categories": categories,
            }
        )

    return results


async def get_first_arxiv_result(query: str):
    results = await search_arxiv(query, max_results=1)
    return results[0] if results else None