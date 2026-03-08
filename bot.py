import discord
from discord import app_commands
from discord.ext import commands

from config import logger, settings


EXTENSIONS = [
    "commands.papers",
]


class ResearchPaperAssistantBot(commands.Bot):
    def __init__(self, guild_id: int) -> None:
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        self.dev_guild = discord.Object(id=guild_id)

    async def setup_hook(self) -> None:
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            logger.info("Loaded extension: %s", ext)

        self.tree.copy_global_to(guild=self.dev_guild)
        await self.tree.sync(guild=self.dev_guild)
        logger.info("Synced application commands to guild %s", self.dev_guild.id)

        # Clear stale global commands so they don't ghost alongside guild ones
        self.tree.clear_commands(guild=None)
        await self.tree.sync()

    async def on_ready(self) -> None:
        if self.user:
            logger.info("Bot connected as %s", self.user)


bot = ResearchPaperAssistantBot(guild_id=settings.discord_guild_id)


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    logger.exception("Application command error: %s", error)
    if interaction.response.is_done():
        await interaction.followup.send(
            "Something went wrong while processing that command.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "Something went wrong while processing that command.",
            ephemeral=True,
        )


def main() -> None:
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()