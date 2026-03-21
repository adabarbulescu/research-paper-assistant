from __future__ import annotations

import io
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from config import logger
from models.paper import Paper
from repositories.collection_repository import (
    add_to_collection,
    create_collection,
    delete_collection,
    get_collection_names,
    get_collection_papers,
    get_collections,
    remove_from_collection,
)
from repositories.library_repository import get_paper_ids
from utils.citations import to_bibtex, to_markdown_citation, to_plain_citation
from utils.embeds import build_collection_embed, build_collections_list_embed
from utils.serialization import decode_str_list
from views.confirm import ConfirmView
from views.pagination import PaginatedCollectionsView, COLLECTIONS_PER_PAGE


CitationFormat = Literal["bibtex", "plain", "markdown"]


def _gid(interaction: discord.Interaction) -> str:
    return str(interaction.guild_id or "")


async def _send_error(interaction: discord.Interaction, message: str) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


def _row_to_paper(row: dict) -> Paper:
    raw_authors = row.get("authors", "")
    authors = (
        raw_authors
        if isinstance(raw_authors, list)
        else decode_str_list(raw_authors)
    )
    raw_categories = row.get("categories", "")
    categories = (
        raw_categories
        if isinstance(raw_categories, list)
        else decode_str_list(raw_categories)
    )

    return Paper(
        arxiv_id=row["paper_id"],
        title=row.get("title", ""),
        authors=authors,
        summary=row.get("summary", "") or "",
        published=row.get("published", "") or "",
        categories=categories,
        arxiv_url=row.get("arxiv_url", ""),
        pdf_url=row.get("pdf_url", "") or "",
        doi=row.get("doi", "") or "",
    )


class Collections(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── Autocomplete helpers ─────────────────────────────────────

    async def _collection_ac(
        self, interaction: discord.Interaction, current: str,
    ) -> list[app_commands.Choice[str]]:
        try:
            names = await get_collection_names(str(interaction.user.id), _gid(interaction))
            filtered = [n for n in names if current.lower() in n.lower()]
            return [app_commands.Choice(name=n, value=n) for n in filtered[:25]]
        except Exception:
            return []

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
        name="create_collection",
        description="Create a new paper collection",
    )
    @app_commands.describe(name="Collection name (e.g. thesis-sources, read-later)")
    async def create_collection_cmd(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        logger.info("/create_collection user=%s name=%r", interaction.user.id, name)

        try:
            cleaned = name.strip()
            if not cleaned:
                await interaction.response.send_message(
                    "Collection name cannot be blank.", ephemeral=True,
                )
                return

            created = await create_collection(
                str(interaction.user.id), _gid(interaction), cleaned,
            )

            if created:
                await interaction.response.send_message(
                    f"\U0001F4C1 Collection **{cleaned}** created!",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"You already have a collection named **{cleaned}**.",
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /create_collection")
            await _send_error(interaction, "Error creating collection. Please try again.")

    @app_commands.command(
        name="my_collections",
        description="View all your collections",
    )
    async def my_collections(self, interaction: discord.Interaction) -> None:
        logger.info("/my_collections user=%s", interaction.user.id)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            collections = await get_collections(str(interaction.user.id), _gid(interaction))

            if not collections:
                await interaction.followup.send(
                    "\U0001F4C1 You have no collections yet. "
                    "Use `/create_collection` to get started!",
                    ephemeral=True,
                )
                return

            if len(collections) <= COLLECTIONS_PER_PAGE:
                embed = build_collections_list_embed(collections)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                view = PaginatedCollectionsView(collections)
                embed = view.build_embed()
                msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                view.message = msg

        except Exception:
            logger.exception("Unhandled error in /my_collections")
            await _send_error(interaction, "Error loading collections. Please try again.")

    @app_commands.command(
        name="add_to_collection",
        description="Add a saved paper to a collection",
    )
    @app_commands.describe(
        arxiv_id="arXiv ID of the paper (e.g. 2512.22190)",
        collection="Name of the collection",
    )
    async def add_to_collection_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
        collection: str,
    ) -> None:
        logger.info(
            "/add_to_collection user=%s arxiv_id=%r collection=%r",
            interaction.user.id, arxiv_id, collection,
        )

        try:
            uid = str(interaction.user.id)
            gid = _gid(interaction)

            result = await add_to_collection(
                uid, gid, collection.strip(), arxiv_id.strip(),
            )

            messages = {
                "added": f"\u2705 Added `{arxiv_id.strip()}` to **{collection.strip()}**.",
                "duplicate": f"Paper `{arxiv_id.strip()}` is already in **{collection.strip()}**.",
                "not_found": f"Collection **{collection.strip()}** doesn't exist. Create it first with `/create_collection`.",
                "not_saved": f"Paper `{arxiv_id.strip()}` is not in your library. Save it first!",
            }
            await interaction.response.send_message(
                messages.get(result, "Something went wrong."),
                ephemeral=True,
            )

        except Exception:
            logger.exception("Unhandled error in /add_to_collection")
            await _send_error(interaction, "Error adding paper to collection. Please try again.")

    @add_to_collection_cmd.autocomplete("arxiv_id")
    async def _atc_paper_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    @add_to_collection_cmd.autocomplete("collection")
    async def _atc_coll_ac(self, interaction: discord.Interaction, current: str):
        return await self._collection_ac(interaction, current)

    @app_commands.command(
        name="view_collection",
        description="View papers in a collection",
    )
    @app_commands.describe(name="Name of the collection to view")
    async def view_collection(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        logger.info("/view_collection user=%s name=%r", interaction.user.id, name)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            papers = await get_collection_papers(
                str(interaction.user.id), _gid(interaction), name.strip(),
            )

            if papers is None:
                await interaction.followup.send(
                    f"Collection **{name.strip()}** doesn't exist.",
                    ephemeral=True,
                )
                return

            if not papers:
                await interaction.followup.send(
                    f"\U0001F4C1 **{name.strip()}** is empty. "
                    "Use `/add_to_collection` to add papers!",
                    ephemeral=True,
                )
                return

            embed = build_collection_embed(name.strip(), papers)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception:
            logger.exception("Unhandled error in /view_collection")
            await _send_error(interaction, "Error loading collection. Please try again.")

    @view_collection.autocomplete("name")
    async def _vc_ac(self, interaction: discord.Interaction, current: str):
        return await self._collection_ac(interaction, current)

    @app_commands.command(
        name="remove_from_collection",
        description="Remove a paper from a collection",
    )
    @app_commands.describe(
        arxiv_id="arXiv ID of the paper to remove",
        collection="Name of the collection",
    )
    async def remove_from_collection_cmd(
        self,
        interaction: discord.Interaction,
        arxiv_id: str,
        collection: str,
    ) -> None:
        logger.info(
            "/remove_from_collection user=%s arxiv_id=%r collection=%r",
            interaction.user.id, arxiv_id, collection,
        )

        try:
            result = await remove_from_collection(
                str(interaction.user.id), _gid(interaction),
                collection.strip(), arxiv_id.strip(),
            )

            messages = {
                "removed": f"\u2705 Removed `{arxiv_id.strip()}` from **{collection.strip()}**.",
                "not_in_collection": f"Paper `{arxiv_id.strip()}` is not in **{collection.strip()}**.",
                "not_found": f"Collection **{collection.strip()}** doesn't exist.",
            }
            await interaction.response.send_message(
                messages.get(result, "Something went wrong."),
                ephemeral=True,
            )

        except Exception:
            logger.exception("Unhandled error in /remove_from_collection")
            await _send_error(interaction, "Error removing paper from collection. Please try again.")

    @remove_from_collection_cmd.autocomplete("arxiv_id")
    async def _rfc_paper_ac(self, interaction: discord.Interaction, current: str):
        return await self._paper_id_ac(interaction, current)

    @remove_from_collection_cmd.autocomplete("collection")
    async def _rfc_coll_ac(self, interaction: discord.Interaction, current: str):
        return await self._collection_ac(interaction, current)

    @app_commands.command(
        name="delete_collection",
        description="Delete a collection (papers stay in your library)",
    )
    @app_commands.describe(name="Name of the collection to delete")
    async def delete_collection_cmd(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        logger.info("/delete_collection user=%s name=%r", interaction.user.id, name)

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            uid = str(interaction.user.id)
            gid = _gid(interaction)
            cname = name.strip()

            view = ConfirmView()
            msg = await interaction.followup.send(
                f"\u26a0\ufe0f Delete collection **{cname}**? Papers will remain in your library.",
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

            deleted = await delete_collection(uid, gid, cname)
            text = (
                f"\u2705 Deleted collection **{cname}**."
                if deleted
                else f"Collection **{cname}** doesn't exist."
            )
            await view.interact.response.edit_message(content=text, view=None)

        except Exception:
            logger.exception("Unhandled error in /delete_collection")
            await _send_error(interaction, "Error deleting collection. Please try again.")

    @delete_collection_cmd.autocomplete("name")
    async def _dc_ac(self, interaction: discord.Interaction, current: str):
        return await self._collection_ac(interaction, current)

    @app_commands.command(
        name="export_collection",
        description="Export citations for all papers in a collection",
    )
    @app_commands.describe(
        name="Name of the collection",
        format="Citation format",
    )
    async def export_collection_cmd(
        self,
        interaction: discord.Interaction,
        name: str,
        format: CitationFormat = "bibtex",
    ) -> None:
        logger.info(
            "/export_collection user=%s name=%r format=%s",
            interaction.user.id, name, format,
        )

        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            papers_raw = await get_collection_papers(
                str(interaction.user.id), _gid(interaction), name.strip(),
            )

            if papers_raw is None:
                await interaction.followup.send(
                    f"Collection **{name.strip()}** doesn't exist.",
                    ephemeral=True,
                )
                return

            if not papers_raw:
                await interaction.followup.send(
                    f"**{name.strip()}** is empty \u2014 nothing to export.",
                    ephemeral=True,
                )
                return

            formatters = {
                "bibtex": to_bibtex,
                "plain": to_plain_citation,
                "markdown": to_markdown_citation,
            }
            formatter = formatters[format]
            citations = [formatter(_row_to_paper(row)) for row in papers_raw]
            combined = "\n\n".join(citations)

            heading = f"**{len(citations)}** citations from **{name.strip()}**"
            lang = "bibtex" if format == "bibtex" else "md" if format == "markdown" else ""
            # heading + ```lang\n...\n``` + newline
            overhead = len(heading) + len(lang) + 8
            if len(combined) + overhead < 2000:
                await interaction.followup.send(
                    f"{heading}\n```{lang}\n{combined}\n```",
                    ephemeral=True,
                )
            else:
                ext = {"bibtex": "bib", "markdown": "md", "plain": "txt"}[format]
                file = discord.File(
                    io.BytesIO(combined.encode()),
                    filename=f"{name.strip()}.{ext}",
                )
                await interaction.followup.send(
                    f"\U0001F4C4 **{len(citations)}** citations exported from **{name.strip()}**:",
                    file=file,
                    ephemeral=True,
                )

        except Exception:
            logger.exception("Unhandled error in /export_collection")
            await _send_error(interaction, "Error exporting citations. Please try again.")

    @export_collection_cmd.autocomplete("name")
    async def _ec_ac(self, interaction: discord.Interaction, current: str):
        return await self._collection_ac(interaction, current)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Collections(bot))
