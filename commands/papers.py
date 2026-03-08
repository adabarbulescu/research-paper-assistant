from __future__ import annotations

from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from config import logger
from repositories.library_repository import get_saved_papers, remove_paper
from services.arxiv import get_first_arxiv_result, search_arxiv
from utils.embeds import build_detail_embed, build_library_embed, build_search_embed
from views.paper_select import PaperSelectView


SortBy = Literal["relevance", "submittedDate", "lastUpdatedDate"]
SortOrder = Literal["descending", "ascending"]


async def _send_error(interaction: discord.Interaction, message: str) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class Papers(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Check if the bot is working",
    )
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Pong!")

    @app_commands.command(
        name="paper_search",
        description="Search for papers on arXiv",
    )
    @app_commands.describe(
        query="Topic or keywords to search for",
        category="arXiv category filter (e.g. cs.AI, math.CO, physics.gen-ph)",
        sort_by="How to sort results",
        sort_order="Sort direction",
        max_results="Number of results (1-25, default 5)",
    )
    async def paper_search(
        self,
        interaction: discord.Interaction,
        query: str,
        category: str | None = None,
        sort_by: SortBy = "relevance",
        sort_order: SortOrder = "descending",
        max_results: app_commands.Range[int, 1, 25] = 5,
    ) -> None:
        logger.info(
            "/paper_search query=%r category=%r sort=%s/%s max=%d",
            query, category, sort_by, sort_order, max_results,
        )

        try:
            await interaction.response.defer(thinking=True)

            papers = await search_arxiv(
                query,
                category=category,
                sort_by=sort_by,
                sort_order=sort_order,
                max_results=max_results,
            )

            if not papers:
                await interaction.followup.send("No papers found for that query.")
                return

            embed = build_search_embed(query=query, papers=papers)
            view = PaperSelectView(papers)
            message = await interaction.followup.send(embed=embed, view=view)
            view.message = message

        except Exception:
            logger.exception("Unhandled error in /paper_search")
            await _send_error(
                interaction,
                "Error while searching arXiv. Please try again.",
            )

    @app_commands.command(
        name="paper_summary",
        description="Get a detailed summary for the top matching arXiv paper",
    )
    @app_commands.describe(
        query="Topic or keywords to summarize",
        category="arXiv category filter (e.g. cs.AI, math.CO)",
    )
    async def paper_summary(
        self,
        interaction: discord.Interaction,
        query: str,
        category: str | None = None,
    ) -> None:
        logger.info("/paper_summary query=%r category=%r", query, category)

        try:
            await interaction.response.defer(thinking=True)

            paper = await get_first_arxiv_result(query, category=category)

            if not paper:
                await interaction.followup.send(f'No papers found for "{query}".')
                return

            embed = build_detail_embed(paper)
            await interaction.followup.send(embed=embed)

        except Exception:
            logger.exception("Unhandled error in /paper_summary")
            await _send_error(
                interaction,
                "Error while fetching paper summary. Please try again.",
            )

    @app_commands.command(
        name="my_library",
        description="View your saved papers",
    )
    async def my_library(self, interaction: discord.Interaction) -> None:
        logger.info("/my_library called by user=%s", interaction.user.id)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            entries = await get_saved_papers(str(interaction.user.id))

            if not entries:
                await interaction.followup.send(
                    "\U0001F4DA Your library is empty. "
                    "Use `/paper_search` to find papers, then save them!",
                    ephemeral=True,
                )
                return

            embed = build_library_embed(entries)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception:
            logger.exception("Unhandled error in /my_library")
            await _send_error(
                interaction,
                "Error while loading your library. Please try again.",
            )

    @app_commands.command(
        name="remove_paper",
        description="Remove a paper from your library by its arXiv ID",
    )
    @app_commands.describe(paper_id="arXiv ID of the paper to remove (e.g. 2512.22190)")
    async def remove_paper_cmd(
        self,
        interaction: discord.Interaction,
        paper_id: str,
    ) -> None:
        logger.info("/remove_paper called by user=%s paper_id=%r", interaction.user.id, paper_id)

        try:
            removed = await remove_paper(str(interaction.user.id), paper_id.strip())

            if removed:
                await interaction.response.send_message(
                    f"\u2705 Removed `{paper_id}` from your library.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"Paper `{paper_id}` is not in your library.",
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /remove_paper")
            await _send_error(
                interaction,
                "Error while removing paper. Please try again.",
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Papers(bot))
