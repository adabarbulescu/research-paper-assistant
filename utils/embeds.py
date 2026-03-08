import discord

from services.arxiv import build_quick_summary
from utils.formatting import (
    format_authors,
    format_categories,
    format_published_date,
    truncate,
)


def build_search_embed(query: str, papers: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title=f"arXiv results for: {truncate(query, 256)}",
        description=f"Top {min(len(papers), 5)} results",
        color=discord.Color.blue(),
    )

    for index, paper in enumerate(papers[:5], start=1):
        title = truncate(paper.get("title", "Untitled"), 256)
        link = paper.get("link", "")
        authors = format_authors(paper.get("authors", []), limit=3)
        published = format_published_date(paper.get("published"))

        value = (
            f"**Authors:** {authors}\n"
            f"**Published:** {published}\n"
            f"[Read on arXiv]({link})"
        )

        embed.add_field(
            name=f"{index}. {title}",
            value=truncate(value, 1024),
            inline=False,
        )

    embed.set_footer(text="Research Paper Assistant • arXiv search")
    return embed


def build_summary_embed(paper: dict) -> discord.Embed:
    title = truncate(paper.get("title", "Untitled"), 256)
    link = paper.get("link", "")
    authors = format_authors(paper.get("authors", []), limit=5)
    published = format_published_date(paper.get("published"))
    categories = format_categories(paper.get("categories", []), limit=5)
    abstract = paper.get("summary", "") or "No abstract available."
    quick_summary = build_quick_summary(abstract)

    embed = discord.Embed(
        title=title,
        url=link,
        description="Structured paper overview",
        color=discord.Color.green(),
    )

    embed.add_field(name="Authors", value=truncate(authors, 1024), inline=False)
    embed.add_field(name="Published", value=truncate(published, 1024), inline=True)
    embed.add_field(name="Categories", value=truncate(categories, 1024), inline=True)
    embed.add_field(
        name="Quick Summary",
        value=truncate(quick_summary, 1024),
        inline=False,
    )
    embed.add_field(
        name="Abstract",
        value=truncate(abstract, 1024),
        inline=False,
    )

    embed.set_footer(text="Research Paper Assistant • arXiv summary")
    return embed
