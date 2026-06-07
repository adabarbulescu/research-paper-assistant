import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Show all available commands and features"
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="📚 Research Paper Assistant Help",
            description="Here are all the commands you can use to discover, organize, and cite arXiv papers directly in Discord.",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🔍 Search & Discovery",
            value=(
                "`/paper_search` - Search arXiv papers\n"
                "`/paper_summary` - Get detailed summary of top matching paper\n"
                "`/related_papers` - Find similar papers in your library"
            ),
            inline=False
        )

        embed.add_field(
            name="📂 Library Management",
            value=(
                "`/my_library` - View your saved papers\n"
                "`/library_by_status` - Filter papers by reading status\n"
                "`/library_stats` - View your library statistics\n"
                "`/set_status` - Set reading status (`to-read`, `reading`, `done`)\n"
                "`/remove_paper` - Remove a paper from your library"
            ),
            inline=False
        )

        embed.add_field(
            name="📝 Notes",
            value=(
                "`/add_note` - Add or update a note on a paper\n"
                "`/view_note` - Read your note for a paper\n"
                "`/edit_note` - Replace your note entirely"
            ),
            inline=False
        )

        embed.add_field(
            name="📑 Collections",
            value=(
                "`/create_collection` - Create a new collection\n"
                "`/my_collections` - View your collections\n"
                "`/add_to_collection` - Add paper to a collection\n"
                "`/view_collection` - View papers in a collection\n"
                "`/remove_from_collection` - Remove paper from a collection\n"
                "`/delete_collection` - Delete a collection"
            ),
            inline=False
        )

        embed.add_field(
            name="🎓 Citations",
            value=(
                "`/export_citation` - Generate citation (bibtex, plain, markdown)\n"
                "`/export_collection` - Export citations for entire collection"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Utility",
            value="`/ping` - Check bot latency and status",
            inline=False
        )

        embed.set_footer(text="Organize your research seamlessly within Discord!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
