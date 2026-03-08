from __future__ import annotations

import discord


class ConfirmView(discord.ui.View):
    """Two-button confirmation dialog for destructive actions."""

    def __init__(self, timeout: float = 30) -> None:
        super().__init__(timeout=timeout)
        self.confirmed: bool | None = None
        self.interact: discord.Interaction | None = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.confirmed = True
        self.interact = interaction
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.confirmed = False
        self.interact = interaction
        self.stop()
