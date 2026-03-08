from __future__ import annotations

import discord

from models.paper import Paper
from services.arxiv import build_quick_summary
from utils.formatting import format_authors, format_categories, truncate


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

        embed.add_field(
            name=f"`{idx}` {truncate(paper.title, 200)}",
            value=truncate("\n".join(value_lines), 1024),
            inline=False,
        )

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
