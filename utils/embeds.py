from __future__ import annotations

import discord

from models.paper import Paper
from services.arxiv import build_quick_summary
from utils.formatting import format_authors, format_categories, format_saved_date, truncate
from utils.serialization import decode_str_list


def build_search_embed(query: str, papers: list[Paper]) -> discord.Embed:
    embed = discord.Embed(
        title=f"\U0001F50D  {truncate(query, 240)}",
        description=f"Showing **{len(papers)}** result{'s' if len(papers) != 1 else ''} from arXiv",
        color=0x3498DB,
    )

    for idx, paper in enumerate(papers, start=1):
        authors = format_authors(paper.authors, limit=2)
        cats = format_categories(paper.categories, limit=2)

        value_lines = [
            f"{authors}  \u2022  {paper.published_date}  \u2022  `{cats}`",
            truncate(paper.summary, 120),
            f"[\U0001F4C4 arXiv]({paper.arxiv_url})",
        ]
        if paper.pdf_url:
            value_lines[-1] += f"  \u2022  [\U0001F4E5 PDF]({paper.pdf_url})"

        field_name = f"`{idx}` {truncate(paper.title, 200)}"
        field_value = truncate("\n".join(value_lines), 1024)

        if len(embed) + len(field_name) + len(field_value) > 5900:
            embed.set_footer(
                text=f"Showing {idx - 1} of {len(papers)} results (embed size limit reached)"
            )
            return embed

        embed.add_field(name=field_name, value=field_value, inline=False)

    embed.set_footer(text="Select a paper below for the full details")
    return embed


def build_detail_embed(paper: Paper) -> discord.Embed:
    authors = format_authors(paper.authors, limit=8)
    cats = format_categories(paper.categories, limit=6)
    abstract = paper.summary or "No abstract available."
    quick_summary = build_quick_summary(abstract)

    embed = discord.Embed(
        title=truncate(paper.title, 256),
        url=paper.arxiv_url,
        color=0x2ECC71,
    )

    embed.add_field(name="Authors", value=truncate(authors, 1024), inline=False)
    embed.add_field(name="Published", value=paper.published_date, inline=True)
    embed.add_field(name="Categories", value=truncate(cats, 1024), inline=True)

    if paper.doi:
        embed.add_field(
            name="DOI",
            value=f"[{paper.doi}](https://doi.org/{paper.doi})",
            inline=True,
        )

    embed.add_field(
        name="\U0001F4DD Quick Summary",
        value=truncate(quick_summary, 1024),
        inline=False,
    )
    embed.add_field(
        name="Abstract",
        value=truncate(abstract, 1024),
        inline=False,
    )

    links = f"[\U0001F4C4 arXiv]({paper.arxiv_url})"
    if paper.pdf_url:
        links += f"  \u2022  [\U0001F4E5 PDF]({paper.pdf_url})"
    embed.add_field(name="Links", value=links, inline=False)

    embed.set_footer(text=f"arXiv:{paper.arxiv_id}")
    return embed


def build_library_embed(
    entries: list[dict],
    title: str = "\U0001F4DA  My Library",
    page: int | None = None,
    total_pages: int | None = None,
    total_count: int | None = None,
    start_index: int = 0,
) -> discord.Embed:
    display_count = total_count if total_count is not None else len(entries)
    embed = discord.Embed(
        title=title,
        description=f"**{display_count}** paper{'s' if display_count != 1 else ''}",
        color=0x9B59B6,
    )

    status_emoji = {"to-read": "\U0001F4D6", "reading": "\U0001F440", "done": "\u2705"}

    for idx, entry in enumerate(entries, start=start_index + 1):
        paper = entry["paper"]
        saved_at = format_saved_date(entry.get("saved_at", ""))
        authors = format_authors(paper.authors, limit=2)
        cats = format_categories(paper.categories, limit=2)
        status = entry.get("status", "to-read")
        s_emoji = status_emoji.get(status, "")
        note = entry.get("note")

        value_lines = [
            f"{s_emoji} **{status}**  \u2022  {authors}  \u2022  {paper.published_date}  \u2022  `{cats}`",
            f"Saved {saved_at}  \u2022  `{paper.arxiv_id}`",
        ]
        if note:
            value_lines.append(f"\U0001F4DD {truncate(note, 100)}")
        value_lines.append(f"[\U0001F4C4 arXiv]({paper.arxiv_url})")
        if paper.pdf_url:
            value_lines[-1] += f"  \u2022  [\U0001F4E5 PDF]({paper.pdf_url})"

        embed.add_field(
            name=f"`{idx}` {truncate(paper.title, 200)}",
            value=truncate("\n".join(value_lines), 1024),
            inline=False,
        )

    if page is not None and total_pages is not None:
        embed.set_footer(text=f"Page {page}/{total_pages}  \u2022  {display_count} papers total")
    else:
        embed.set_footer(text="Remove with /remove_paper <arxiv_id>  (e.g. /remove_paper 2512.22190)")

    return embed


def build_stats_embed(stats: dict) -> discord.Embed:
    embed = discord.Embed(title="\U0001F4CA  Library Stats", color=0x3498DB)

    embed.add_field(name="\U0001F4DA Total Papers", value=str(stats["total"]), inline=True)
    embed.add_field(name="\U0001F4C1 Collections", value=str(stats["collections_count"]), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    status_emoji = {"to-read": "\U0001F4D6", "reading": "\U0001F440", "done": "\u2705"}
    status_lines = []
    for s in ("to-read", "reading", "done"):
        count = stats["status_counts"].get(s, 0)
        status_lines.append(f"{status_emoji.get(s, '')} **{s}**: {count}")
    embed.add_field(name="\U0001F4CB By Status", value="\n".join(status_lines), inline=False)

    if stats["top_categories"]:
        cat_lines = [f"`{cat}` \u2014 {count}" for cat, count in stats["top_categories"]]
        embed.add_field(name="\U0001F3F7\uFE0F Top Categories", value="\n".join(cat_lines), inline=False)

    return embed


def build_collections_list_embed(
    collections: list[dict],
    *,
    page: int = 1,
    total_pages: int = 1,
    total_count: int | None = None,
) -> discord.Embed:
    count = total_count if total_count is not None else len(collections)
    embed = discord.Embed(
        title="\U0001F4C1  My Collections",
        description=f"You have **{count}** collection{'s' if count != 1 else ''}",
        color=0xE67E22,
    )

    for coll in collections:
        paper_count = coll["paper_count"]
        created = format_saved_date(coll.get("created_at", ""))
        embed.add_field(
            name=f"\U0001F4C2 {coll['name']}",
            value=f"**{paper_count}** paper{'s' if paper_count != 1 else ''}  \u2022  Created {created}",
            inline=False,
        )

    footer = "Use /view_collection <name> to see papers inside"
    if total_pages > 1:
        footer = f"Page {page}/{total_pages}  \u2022  " + footer
    embed.set_footer(text=footer)
    return embed


def build_collection_embed(collection_name: str, papers: list[dict]) -> discord.Embed:
    count = len(papers)
    embed = discord.Embed(
        title=f"\U0001F4C2  {collection_name}",
        description=f"**{count}** paper{'s' if count != 1 else ''}",
        color=0xE67E22,
    )

    status_emoji = {"to-read": "\U0001F4D6", "reading": "\U0001F440", "done": "\u2705"}

    for idx, row in enumerate(papers[:15], start=1):
        raw_authors = row.get("authors", "")
        authors_list = (
            raw_authors
            if isinstance(raw_authors, list)
            else decode_str_list(raw_authors)
        )
        authors = format_authors(authors_list, limit=2)
        status = row.get("status", "to-read")
        s_emoji = status_emoji.get(status, "")
        published = (row.get("published") or "")[:10] or "Unknown"

        value_lines = [
            f"{s_emoji} **{status}**  \u2022  {authors}  \u2022  {published}",
            f"`{row['paper_id']}`  \u2022  [\U0001F4C4 arXiv]({row['arxiv_url']})",
        ]
        if row.get("pdf_url"):
            value_lines[-1] += f"  \u2022  [\U0001F4E5 PDF]({row['pdf_url']})"

        embed.add_field(
            name=f"`{idx}` {truncate(row.get('title', 'Untitled'), 200)}",
            value="\n".join(value_lines),
            inline=False,
        )

    if count > 15:
        embed.set_footer(text=f"Showing 15 of {count} papers")
    else:
        embed.set_footer(text="Use /remove_from_collection to remove papers")

    return embed


def build_related_embed(target: Paper, related: list[tuple[Paper, float]]) -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F517  Related Papers",
        description=f"Papers in your library similar to:\n**{truncate(target.title, 200)}**",
        color=0x1ABC9C,
    )

    for idx, (paper, score) in enumerate(related[:5], start=1):
        pct = int(score * 100)
        authors = format_authors(paper.authors, limit=2)
        cats = format_categories(paper.categories, limit=2)

        value_lines = [
            f"\U0001F4CA **{pct}%** match  \u2022  {authors}  \u2022  {paper.published_date}",
            f"`{cats}`  \u2022  `{paper.arxiv_id}`",
            f"[\U0001F4C4 arXiv]({paper.arxiv_url})",
        ]
        if paper.pdf_url:
            value_lines[-1] += f"  \u2022  [\U0001F4E5 PDF]({paper.pdf_url})"

        embed.add_field(
            name=f"`{idx}` {truncate(paper.title, 200)}",
            value="\n".join(value_lines),
            inline=False,
        )

    embed.set_footer(text="Similarity based on title, abstract, and categories (TF-IDF)")
    return embed
