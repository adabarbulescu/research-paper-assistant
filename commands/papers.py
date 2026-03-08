import discord
from discord import app_commands
from discord.ext import commands

from config import logger
from services.arxiv import get_first_arxiv_result, search_arxiv
from utils.embeds import build_search_embed, build_summary_embed


async def send_error_response(
    interaction: discord.Interaction,
    message: str,
) -> None:
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
    @app_commands.describe(query="Topic or keywords to search for")
    async def paper_search(self, interaction: discord.Interaction, query: str) -> None:
        logger.info("/paper_search called with query=%r", query)

        try:
            await interaction.response.defer(thinking=True)

            papers = await search_arxiv(query)

            if not papers:
                await interaction.followup.send("No papers found.")
                return

            embed = build_search_embed(query=query, papers=papers)
            await interaction.followup.send(embed=embed)

        except Exception:
            logger.exception("Unhandled error in /paper_search")
            await send_error_response(
                interaction,
                "Error while searching arXiv. Please try again.",
            )

    @app_commands.command(
        name="paper_summary",
        description="Get a summary for the first matching arXiv paper",
    )
    @app_commands.describe(query="Topic or keywords to summarize")
    async def paper_summary(self, interaction: discord.Interaction, query: str) -> None:
        logger.info("/paper_summary called with query=%r", query)

        try:
            await interaction.response.defer(thinking=True)

            paper = await get_first_arxiv_result(query)

            if not paper:
                await interaction.followup.send(f'No papers found for "{query}".')
                return

            embed = build_summary_embed(paper)
            await interaction.followup.send(embed=embed)

        except Exception:
            logger.exception("Unhandled error in /paper_summary")
            await send_error_response(
                interaction,
                "Error while fetching paper summary. Please try again.",
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Papers(bot))
