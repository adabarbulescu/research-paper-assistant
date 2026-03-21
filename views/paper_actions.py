from __future__ import annotations

import io

import discord

from config import logger
from models.paper import Paper
from repositories.library_repository import get_all_papers, save_paper
from utils.citations import to_bibtex, to_markdown_citation, to_plain_citation
from utils.embeds import build_related_embed
from services.similarity import find_related


class SaveButton(discord.ui.Button):
    def __init__(self, paper: Paper) -> None:
        super().__init__(
            style=discord.ButtonStyle.green,
            label="Save to Library",
            emoji="\U0001F4BE",
        )
        self.paper = paper

    async def callback(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id or "")

        try:
            saved = await save_paper(user_id, guild_id, self.paper)
        except Exception:
            logger.exception("DB error saving paper %s", self.paper.arxiv_id)
            await interaction.response.send_message(
                "Something went wrong while saving. Please try again.",
                ephemeral=True,
            )
            return

        if saved:
            self.label = "Saved"
            self.disabled = True
            self.emoji = "\u2705"
            await interaction.response.edit_message(view=self.view)
        else:
            self.label = "Already Saved"
            self.disabled = True
            self.emoji = "\U0001F4D6"
            await interaction.response.edit_message(view=self.view)


class CiteSelect(discord.ui.Select):
    def __init__(self, paper: Paper) -> None:
        self.paper = paper
        options = [
            discord.SelectOption(label="BibTeX", value="bibtex", description="LaTeX bibliography entry"),
            discord.SelectOption(label="Plain text", value="plain", description="Simple text citation"),
            discord.SelectOption(label="Markdown", value="markdown", description="Markdown formatted citation"),
        ]
        super().__init__(placeholder="Choose citation format\u2026", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        fmt = self.values[0]
        formatters = {
            "bibtex": to_bibtex,
            "plain": to_plain_citation,
            "markdown": to_markdown_citation,
        }
        citation = formatters[fmt](self.paper)
        lang = "bibtex" if fmt == "bibtex" else "md" if fmt == "markdown" else ""
        payload = f"```{lang}\n{citation}\n```"

        if len(payload) < 2000:
            await interaction.response.send_message(payload, ephemeral=True)
            return

        ext = {"bibtex": "bib", "markdown": "md", "plain": "txt"}[fmt]
        file = discord.File(
            io.BytesIO(citation.encode()),
            filename=f"{self.paper.arxiv_id}.{ext}",
        )
        await interaction.response.send_message(
            "Citation was too long for an inline message, attached as a file.",
            file=file,
            ephemeral=True,
        )


class RelatedButton(discord.ui.Button):
    def __init__(self, paper: Paper) -> None:
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label="Related Papers",
            emoji="\U0001F517",
        )
        self.paper = paper

    async def callback(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id or "")

        try:
            all_papers = await get_all_papers(user_id, guild_id)

            candidates = [p for p in all_papers if p.arxiv_id != self.paper.arxiv_id]
            if not candidates:
                await interaction.response.send_message(
                    "Save at least 2 papers to find related ones!",
                    ephemeral=True,
                )
                return

            related = find_related(self.paper, candidates, top_k=5)

            if not related:
                await interaction.response.send_message(
                    "No similar papers found in your library yet.",
                    ephemeral=True,
                )
                return

            embed = build_related_embed(self.paper, related)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception:
            logger.exception("Error finding related papers for %s", self.paper.arxiv_id)
            await interaction.response.send_message(
                "Something went wrong finding related papers.",
                ephemeral=True,
            )


class PaperDetailView(discord.ui.View):
    def __init__(self, paper: Paper, timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.add_item(SaveButton(paper))
        self.add_item(RelatedButton(paper))
        self.add_item(CiteSelect(paper))

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True

        msg = getattr(self, "message", None)
        if msg is not None:
            try:
                await msg.edit(view=self)
            except discord.HTTPException:
                pass
