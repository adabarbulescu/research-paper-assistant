import discord
from discord import app_commands

from repositories.collection_repository import get_collection_names
from repositories.library_repository import get_paper_ids


def get_guild_id(interaction: discord.Interaction) -> str:
    """Safely extract the guild ID as a string."""
    return str(interaction.guild_id or "")


async def send_error(interaction: discord.Interaction, message: str) -> None:
    """Send an ephemeral error message securely, handling deferred states."""
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def paper_id_autocomplete(
    interaction: discord.Interaction, current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete helper for saved paper IDs."""
    try:
        ids = await get_paper_ids(str(interaction.user.id), get_guild_id(interaction))
        filtered = [i for i in ids if current.lower() in i.lower()]
        return [app_commands.Choice(name=i, value=i) for i in filtered[:25]]
    except Exception:
        return []


async def collection_autocomplete(
    interaction: discord.Interaction, current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete helper for user collections."""
    try:
        names = await get_collection_names(str(interaction.user.id), get_guild_id(interaction))
        filtered = [n for n in names if current.lower() in n.lower()]
        return [app_commands.Choice(name=n, value=n) for n in filtered[:25]]
    except Exception:
        return []
