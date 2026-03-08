from __future__ import annotations

import discord

from config import logger
from models.paper import Paper
from repositories.library_repository import save_paper
from utils.citations import to_bibtex, to_markdown_citation, to_plain_citation
from utils.embeds import build_detail_embed
from utils.formatting import truncate


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

        try:
            saved = await save_paper(user_id, self.paper)
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
        await interaction.response.send_message(
            f"```{lang}\n{citation}\n```",
            ephemeral=True,
        )


class PaperDetailView(discord.ui.View):
    def __init__(self, paper: Paper, timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.add_item(SaveButton(paper))
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


class PaperSelect(discord.ui.Select):
    def __init__(self, papers: list[Paper]) -> None:
        self.papers = {paper.arxiv_id: paper for paper in papers}

        options = [
            discord.SelectOption(
                label=truncate(paper.title, 100),
                value=paper.arxiv_id,
                description=truncate(
                    f"{paper.published_date} • {paper.authors[0] if paper.authors else 'Unknown'}",
                    100,
                ),
            )
            for paper in papers
        ]

        super().__init__(
            placeholder="Select a paper for details\u2026",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        arxiv_id = self.values[0]
        paper = self.papers.get(arxiv_id)

        if not paper:
            await interaction.response.send_message(
                "Paper not found.", ephemeral=True
            )
            return

        embed = build_detail_embed(paper)
        view = PaperDetailView(paper)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class PaperSelectView(discord.ui.View):
    def __init__(self, papers: list[Paper], timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.add_item(PaperSelect(papers))

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = True

        msg = getattr(self, "message", None)
        if msg is not None:
            try:
                await msg.edit(view=self)
            except discord.HTTPException:
                pass
