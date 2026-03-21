from __future__ import annotations

import io
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from config import logger
from repositories.library_repository import get_all_papers, get_paper_ids
from services.arxiv import get_paper_by_id
from services.similarity import find_related
from utils.citations import to_bibtex, to_markdown_citation, to_plain_citation
from utils.embeds import build_related_embed


CitationFormat = Literal["bibtex", "plain", "markdown"]


def _gid(interaction: discord.Interaction) -> str:
    return str(interaction.guild_id or "")


async def _send_error(interaction: discord.Interaction, message: str) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def _send_citation(
    interaction: discord.Interaction,
    *,
    paper_id: str,
    fmt: CitationFormat,
    citation: str,
) -> None:
    heading = f"**{fmt.title()} citation for** `{paper_id}`"
    lang = "bibtex" if fmt == "bibtex" else "md" if fmt == "markdown" else ""
    payload = f"{heading}\n```{lang}\n{citation}\n```"

    if len(payload) < 2000:
        await interaction.followup.send(payload, ephemeral=True)
        return

    ext = {"bibtex": "bib", "markdown": "md", "plain": "txt"}[fmt]
    file = discord.File(
        io.BytesIO(citation.encode()),
        filename=f"{paper_id}.{ext}",
    )
    await interaction.followup.send(
        f"{heading}\nCitation was too long for an inline message, attached as a file.",
        file=file,
        ephemeral=True,
    )


class Discovery(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── Autocomplete helper ──────────────────────────────────────

    async def _paper_id_ac(
        self, interaction: discord.Interaction, current: str,
    ) -> list[app_commands.Choice[str]]:
        try:
            ids = await get_paper_ids(str(interaction.user.id), _gid(interaction))
            filtered = [i for i in ids if current.lower() in i.lower()]
            return [app_commands.Choice(name=i, value=i) for i in filtered[:25]]
        except Exception:
            return []

    # ── Commands ─────────────────────────────────────────────────

    @app_commands.command(
        name="related_papers",
        description="Find similar papers in your library",
    )
    @app_commands.describe(arxiv_id="arXiv ID of the paper to find related papers for")
    async def related_papers_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
    ) -> None:
        logger.info("/related_papers user=%s arxiv_id=%r", interaction.user.id, arxiv_id)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            uid = str(interaction.user.id)
            gid = _gid(interaction)

            all_papers = await get_all_papers(uid, gid)

            target = next((p for p in all_papers if p.arxiv_id == arxiv_id.strip()), None)
            if not target:
                await interaction.followup.send(
                    f"Paper `{arxiv_id.strip()}` is not in your library.",
                    ephemeral=True,
                )
                return

            candidates = [p for p in all_papers if p.arxiv_id != target.arxiv_id]
            if not candidates:
                await interaction.followup.send(
                    "You need at least 2 papers in your library to find related papers.",
                    ephemeral=True,
                )
                return

            related = find_related(target, candidates, top_k=5)

            if not related:
                await interaction.followup.send(
                    "No similar papers found in your library. Try saving more papers!",
                    ephemeral=True,
                )
                return

            embed = build_related_embed(target, related)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception:
            logger.exception("Unhandled error in /related_papers")
            await _send_error(interaction, "Error finding related papers. Please try again.")

    @related_papers_cmd.autocomplete("arxiv_id")
    async def _related_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    @app_commands.command(
        name="export_citation",
        description="Generate a citation for an arXiv paper",
    )
    @app_commands.describe(
        arxiv_id="arXiv ID of the paper (e.g. 2512.22190)",
        format="Citation format",
    )
    async def export_citation(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
        format: CitationFormat = "bibtex",
    ) -> None:
        logger.info(
            "/export_citation arxiv_id=%r format=%s user=%s",
            arxiv_id, format, interaction.user.id,
        )

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            paper = await get_paper_by_id(arxiv_id.strip())

            if not paper:
                await interaction.followup.send(
                    f"Could not find paper `{arxiv_id}` on arXiv. Check the ID and try again.",
                    ephemeral=True,
                )
                return

            formatters = {
                "bibtex": to_bibtex,
                "plain": to_plain_citation,
                "markdown": to_markdown_citation,
            }
            citation = formatters[format](paper)
            await _send_citation(
                interaction,
                paper_id=paper.arxiv_id,
                fmt=format,
                citation=citation,
            )

        except Exception:
            logger.exception("Unhandled error in /export_citation")
            await _send_error(
                interaction,
                "Error generating citation. Please try again.",
            )

    @export_citation.autocomplete("arxiv_id")
    async def _cite_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Discovery(bot))
