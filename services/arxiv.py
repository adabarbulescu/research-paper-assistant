import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import quote


ARXIV_API_URL = "http://export.arxiv.org/api/query"


async def search_arxiv(query: str, max_results: int = 5):
    search_query = quote(query)
    url = f"{ARXIV_API_URL}?search_query=all:{search_query}&start=0&max_results={max_results}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            text = await response.text()

    root = ET.fromstring(text)

    ns = {
        "atom": "http://www.w3.org/2005/Atom"
    }

    results = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns)
        summary = entry.find("atom:summary", ns)
        published = entry.find("atom:published", ns)
        link = entry.find("atom:id", ns)

        authors = entry.findall("atom:author", ns)
        author_names = []
        for author in authors:
            name = author.find("atom:name", ns)
            if name is not None and name.text:
                author_names.append(name.text.strip())

        results.append({
            "title": title.text.strip().replace("\n", " ") if title is not None and title.text else "No title",
            "summary": summary.text.strip().replace("\n", " ") if summary is not None and summary.text else "No summary",
            "published": published.text.strip() if published is not None and published.text else "Unknown date",
            "link": link.text.strip() if link is not None and link.text else "",
            "authors": author_names
        })

    return results