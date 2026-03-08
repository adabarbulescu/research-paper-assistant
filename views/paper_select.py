from __future__ import annotations

import discord

from models.paper import Paper
from utils.embeds import build_detail_embed
from utils.formatting import truncate


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
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PaperSelectView(discord.ui.View):
    def __init__(self, papers: list[Paper], timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.add_item(PaperSelect(papers))

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass
