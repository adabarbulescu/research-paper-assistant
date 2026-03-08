def truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def format_authors(authors: list[str], limit: int = 3) -> str:
    if not authors:
        return "Unknown"

    selected = authors[:limit]
    result = ", ".join(selected)

    if len(authors) > limit:
        result += ", et al."

    return result


def format_published_date(published: str | None) -> str:
    if not published:
        return "Unknown"
    return published[:10]


def format_categories(categories: list[str], limit: int = 5) -> str:
    if not categories:
        return "N/A"
    return ", ".join(categories[:limit])
