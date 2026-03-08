from __future__ import annotations

from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from config import logger
from repositories.library_repository import (
    get_library_stats,
    get_paper_ids,
    get_saved_papers,
    remove_paper,
)
from repositories.metadata_repository import (
    get_note,
    get_papers_by_status,
    set_note,
    set_status,
)
from utils.embeds import build_library_embed, build_stats_embed
from views.confirm import ConfirmView
from views.pagination import ITEMS_PER_PAGE, PaginatedLibraryView


ReadingStatus = Literal["to-read", "reading", "done"]

STATUS_EMOJI = {"to-read": "\U0001F4D6", "reading": "\U0001F4D6", "done": "\u2705"}


def _gid(interaction: discord.Interaction) -> str:
    return str(interaction.guild_id or "")


async def _send_error(interaction: discord.Interaction, message: str) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class Library(commands.Cog):
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

    # ── Core Library ─────────────────────────────────────────────

    @app_commands.command(
        name="my_library",
        description="View your saved papers",
    )
    async def my_library(self, interaction: discord.Interaction) -> None:
        logger.info("/my_library user=%s guild=%s", interaction.user.id, interaction.guild_id)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            entries = await get_saved_papers(str(interaction.user.id), _gid(interaction))

            if not entries:
                await interaction.followup.send(
                    "\U0001F4DA Your library is empty. "
                    "Use `/paper_search` to find papers, then save them!",
                    ephemeral=True,
                )
                return

            if len(entries) <= ITEMS_PER_PAGE:
                embed = build_library_embed(entries)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                view = PaginatedLibraryView(entries)
                embed = view.build_embed()
                msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                view.message = msg

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
        logger.info("/remove_paper user=%s paper_id=%r", interaction.user.id, paper_id)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            uid = str(interaction.user.id)
            gid = _gid(interaction)
            pid = paper_id.strip()

            view = ConfirmView()
            msg = await interaction.followup.send(
                f"\u26a0\ufe0f Remove `{pid}` from your library?",
                view=view,
                ephemeral=True,
            )

            timed_out = await view.wait()
            if timed_out or view.confirmed is None:
                await msg.edit(content="Timed out.", view=None)
                return

            if not view.confirmed:
                await view.interact.response.edit_message(content="Cancelled.", view=None)
                return

            removed = await remove_paper(uid, gid, pid)
            text = (
                f"\u2705 Removed `{pid}` from your library."
                if removed
                else f"Paper `{pid}` is not in your library."
            )
            await view.interact.response.edit_message(content=text, view=None)

        except Exception:
            logger.exception("Unhandled error in /remove_paper")
            await _send_error(
                interaction,
                "Error while removing paper. Please try again.",
            )

    @remove_paper_cmd.autocomplete("paper_id")
    async def _remove_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    # ── Reading Status ───────────────────────────────────────────

    @app_commands.command(
        name="set_status",
        description="Set reading status for a saved paper",
    )
    @app_commands.describe(
        arxiv_id="arXiv ID of the paper",
        status="Reading status",
    )
    async def set_status_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
        status: ReadingStatus,
    ) -> None:
        logger.info(
            "/set_status user=%s arxiv_id=%r status=%s",
            interaction.user.id, arxiv_id, status,
        )

        try:
            result = await set_status(
                str(interaction.user.id), _gid(interaction), arxiv_id.strip(), status,
            )

            if result == "updated":
                emoji = STATUS_EMOJI.get(status, "")
                await interaction.response.send_message(
                    f"{emoji} `{arxiv_id.strip()}` marked as **{status}**.",
                    ephemeral=True,
                )
            elif result == "not_found":
                await interaction.response.send_message(
                    f"Paper `{arxiv_id.strip()}` is not in your library.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"Invalid status `{status}`.",
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /set_status")
            await _send_error(interaction, "Error setting status. Please try again.")

    @set_status_cmd.autocomplete("arxiv_id")
    async def _status_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    @app_commands.command(
        name="library_by_status",
        description="View saved papers filtered by reading status",
    )
    @app_commands.describe(status="Filter by reading status")
    async def library_by_status(
        self,
        interaction: discord.Interaction,
        status: ReadingStatus,
    ) -> None:
        logger.info("/library_by_status user=%s status=%s", interaction.user.id, status)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            entries = await get_papers_by_status(
                str(interaction.user.id), _gid(interaction), status,
            )

            if not entries:
                emoji = STATUS_EMOJI.get(status, "")
                await interaction.followup.send(
                    f"{emoji} No papers with status **{status}**.",
                    ephemeral=True,
                )
                return

            title = f"\U0001F4DA  Library \u2014 {status}"
            if len(entries) <= ITEMS_PER_PAGE:
                embed = build_library_embed(entries, title=title)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                view = PaginatedLibraryView(entries, title=title)
                embed = view.build_embed()
                msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                view.message = msg

        except Exception:
            logger.exception("Unhandled error in /library_by_status")
            await _send_error(interaction, "Error loading papers. Please try again.")

    # ── Stats ────────────────────────────────────────────────────

    @app_commands.command(
        name="library_stats",
        description="View statistics about your library",
    )
    async def library_stats(self, interaction: discord.Interaction) -> None:
        logger.info("/library_stats user=%s", interaction.user.id)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            stats = await get_library_stats(
                str(interaction.user.id), _gid(interaction),
            )

            if stats["total"] == 0:
                await interaction.followup.send(
                    "\U0001F4DA Your library is empty. Save some papers first!",
                    ephemeral=True,
                )
                return

            embed = build_stats_embed(stats)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception:
            logger.exception("Unhandled error in /library_stats")
            await _send_error(interaction, "Error loading stats. Please try again.")

    # ── Notes ────────────────────────────────────────────────────

    @app_commands.command(
        name="add_note",
        description="Add or update a note on a saved paper",
    )
    @app_commands.describe(
        arxiv_id="arXiv ID of the paper",
        note="Your note (max 500 characters)",
    )
    async def add_note_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
        note: app_commands.Range[str, 1, 500],
    ) -> None:
        logger.info("/add_note user=%s arxiv_id=%r", interaction.user.id, arxiv_id)

        try:
            updated = await set_note(
                str(interaction.user.id), _gid(interaction), arxiv_id.strip(), note,
            )

            if updated:
                await interaction.response.send_message(
                    f"\U0001F4DD Note saved for `{arxiv_id.strip()}`.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"Paper `{arxiv_id.strip()}` is not in your library.",
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /add_note")
            await _send_error(interaction, "Error saving note. Please try again.")

    @add_note_cmd.autocomplete("arxiv_id")
    async def _add_note_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    @app_commands.command(
        name="view_note",
        description="View your note on a saved paper",
    )
    @app_commands.describe(arxiv_id="arXiv ID of the paper")
    async def view_note_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
    ) -> None:
        logger.info("/view_note user=%s arxiv_id=%r", interaction.user.id, arxiv_id)

        try:
            note = await get_note(
                str(interaction.user.id), _gid(interaction), arxiv_id.strip(),
            )

            if note is None:
                await interaction.response.send_message(
                    f"Paper `{arxiv_id.strip()}` is not in your library.",
                    ephemeral=True,
                )
            elif not note:
                await interaction.response.send_message(
                    f"No note on `{arxiv_id.strip()}`. Use `/add_note` to add one.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"\U0001F4DD **Note on** `{arxiv_id.strip()}`\n>>> {note}",
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /view_note")
            await _send_error(interaction, "Error loading note. Please try again.")

    @view_note_cmd.autocomplete("arxiv_id")
    async def _view_note_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    @app_commands.command(
        name="edit_note",
        description="Replace your note on a saved paper",
    )
    @app_commands.describe(
        arxiv_id="arXiv ID of the paper",
        note="New note text (max 500 characters)",
    )
    async def edit_note_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
        note: app_commands.Range[str, 1, 500],
    ) -> None:
        logger.info("/edit_note user=%s arxiv_id=%r", interaction.user.id, arxiv_id)

        try:
            updated = await set_note(
                str(interaction.user.id), _gid(interaction), arxiv_id.strip(), note,
            )

            if updated:
                await interaction.response.send_message(
                    f"\U0001F4DD Note updated for `{arxiv_id.strip()}`.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"Paper `{arxiv_id.strip()}` is not in your library.",
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /edit_note")
            await _send_error(interaction, "Error updating note. Please try again.")

    @edit_note_cmd.autocomplete("arxiv_id")
    async def _edit_note_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Library(bot))
