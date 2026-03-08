from __future__ import annotations

import discord

from utils.embeds import build_collections_list_embed, build_library_embed

ITEMS_PER_PAGE = 5


class PaginatedLibraryView(discord.ui.View):
    """Paginated view for library listings with Prev/Next buttons."""

    def __init__(
        self,
        entries: list[dict],
        title: str = "\U0001f4da  My Library",
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.entries = entries
        self.title = title
        self.page = 0
        self.total_pages = max(1, -(-len(entries) // ITEMS_PER_PAGE))
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= self.total_pages - 1

    def build_embed(self) -> discord.Embed:
        start = self.page * ITEMS_PER_PAGE
        page_entries = self.entries[start : start + ITEMS_PER_PAGE]
        return build_library_embed(
            page_entries,
            title=self.title,
            page=self.page + 1,
            total_pages=self.total_pages,
            total_count=len(self.entries),
            start_index=start,
        )

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.secondary)
    async def next_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page = min(self.total_pages - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        msg = getattr(self, "message", None)
        if msg is not None:
            try:
                await msg.edit(view=self)
            except discord.HTTPException:
                pass


COLLECTIONS_PER_PAGE = 10


class PaginatedCollectionsView(discord.ui.View):
    """Paginated view for collection listings with Prev/Next buttons."""

    def __init__(self, collections: list[dict], timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.collections = collections
        self.page = 0
        self.total_pages = max(1, -(-len(collections) // COLLECTIONS_PER_PAGE))
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= self.total_pages - 1

    def build_embed(self) -> discord.Embed:
        start = self.page * COLLECTIONS_PER_PAGE
        page_entries = self.collections[start : start + COLLECTIONS_PER_PAGE]
        return build_collections_list_embed(
            page_entries,
            page=self.page + 1,
            total_pages=self.total_pages,
            total_count=len(self.collections),
        )

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.secondary)
    async def next_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page = min(self.total_pages - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        msg = getattr(self, "message", None)
        if msg is not None:
            try:
                await msg.edit(view=self)
            except discord.HTTPException:
                pass