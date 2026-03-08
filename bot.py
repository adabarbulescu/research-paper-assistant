import os
import traceback

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from services.arxiv import search_arxiv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("DISCORD_GUILD_ID")))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        bot.tree.clear_commands(guild=GUILD_ID)
        bot.tree.copy_global_to(guild=GUILD_ID)
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Bot connected as {bot.user}")
        print(f"Synced {len(synced)} command(s) to guild.")
    except Exception:
        traceback.print_exc()


@bot.tree.command(name="ping", description="Check if the bot is working")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.tree.command(name="paper_search", description="Search for papers on arXiv")
@app_commands.describe(query="Topic or keywords to search for")
async def paper_search(interaction: discord.Interaction, query: str):
    print(f"paper_search called with query: {query}")

    try:
        await interaction.response.defer(thinking=True)

        papers = await search_arxiv(query)

        if not papers:
            await interaction.followup.send("No papers found.")
            return

        embed = discord.Embed(
            title=f"arXiv results for: {query}",
            description=f"Top {min(len(papers), 5)} results",
            color=discord.Color.blue()
        )

        for i, paper in enumerate(papers[:5], start=1):
            title = paper["title"]
            link = paper["link"]
            authors = ", ".join(paper["authors"][:3])
            if len(paper["authors"]) > 3:
                authors += ", et al."

            value = (
                f"**Authors:** {authors or 'Unknown'}\n"
                f"**Published:** {paper['published'][:10]}\n"
                f"[Read on arXiv]({link})"
            )

            embed.add_field(
                name=f"{i}. {title}",
                value=value,
                inline=False
            )

        embed.set_footer(text="Research Paper Assistant • arXiv search")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print("ERROR in /paper_search:")
        traceback.print_exc()

        if interaction.response.is_done():
            await interaction.followup.send(f"Error while searching arXiv: {e}")
        else:
            await interaction.response.send_message(f"Error while searching arXiv: {e}", ephemeral=True)


bot.run(TOKEN)