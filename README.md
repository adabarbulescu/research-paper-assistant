# Research Paper Assistant

A Discord bot for discovering and summarizing academic papers from [arXiv](https://arxiv.org).

Built with Python and `discord.py`, it uses slash commands to search arXiv, retrieve paper metadata, and display structured results directly inside Discord.

## Features

- Search arXiv papers directly from Discord
- Display top matching results in Discord embeds
- Summarize the first matching paper for a given query
- Show key paper metadata: title, authors, publication date, categories, arXiv link, and abstract
- Use guild-specific slash command sync for fast development and testing

## Commands

| Command | Description |
|---------|-------------|
| `/ping` | Check if the bot is online |
| `/paper_search <query>` | Search arXiv and display top results |
| `/paper_summary <query>` | Get a structured summary of the first matching paper |

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/adabarbulescu/research-paper-assistant.git
cd research-paper-assistant
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then fill in the following values:

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications) |
| `DISCORD_GUILD_ID` | ID of the Discord server used for guild-specific slash command registration |

### 5. Run the bot

```bash
python bot.py
```

## Example Usage

```
/paper_search transformers
/paper_summary graph neural networks
```

## Project Structure

```
research-paper-assistant/
├── bot.py              # Entry point & bot class
├── config.py           # Settings, logging, env loading
├── requirements.txt
├── .env.example
├── commands/
│   └── papers.py       # Slash commands
├── services/
│   └── arxiv.py        # arXiv API client
└── utils/
    ├── embeds.py       # Discord embed builders
    └── formatting.py   # Text formatting helpers
```

## Tech Stack

- **Python**
- **[discord.py](https://discordpy.readthedocs.io/)** — Discord API wrapper with slash command support
- **[aiohttp](https://docs.aiohttp.org/)** — Async HTTP client for arXiv API requests
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment variable loading
- **[arXiv API](https://info.arxiv.org/help/api/)** — Academic paper metadata and abstracts
- **xml.etree.ElementTree** — XML parsing from the Python standard library

## Roadmap

Planned next improvements:

- `/citation_bibtex`
- Reading list support
- Result pagination
- Richer embeds
- Additional paper export formats
