# Research Paper Assistant

A Discord bot for discovering and summarizing academic papers from [arXiv](https://arxiv.org).

Built with Python and `discord.py`, it uses slash commands to search arXiv with filters, display structured results in embeds, let users inspect individual papers through an interactive dropdown, and save papers to a personal SQLite library.

## Features

- Search arXiv with optional filters: category, sort order, and result count
- Display results in compact, scannable embeds with authors, date, categories, and links
- Select a paper from a dropdown menu to view full details (abstract, DOI, PDF link)
- Save papers to a per-user SQLite library with one click
- View and manage your saved library
- Summarize the top matching paper for a given query
- Guild-specific slash command sync for instant updates during development

## Commands

| Command | Description |
|---------|-------------|
| `/ping` | Check if the bot is online |
| `/paper_search <query>` | Search arXiv with optional filters and interactive result selection |
| `/paper_summary <query>` | Get a detailed summary of the top matching paper |
| `/my_library` | View all papers you've saved |
| `/remove_paper <arxiv_id>` | Remove a paper from your library |

### `/paper_search` options

| Option | Description | Default |
|--------|-------------|---------|
| `query` | Topic or keywords to search for | *(required)* |
| `category` | arXiv category filter (e.g. `cs.AI`, `math.CO`) | None |
| `sort_by` | `relevance`, `submittedDate`, or `lastUpdatedDate` | `relevance` |
| `sort_order` | `descending` or `ascending` | `descending` |
| `max_results` | Number of results, 1–25 | `5` |

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
/paper_search query:attention category:cs.AI sort_by:submittedDate max_results:10
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
│   └── papers.py       # Slash commands (Cog)
├── database/
│   └── connection.py   # SQLite connection & schema init
├── repositories/
│   └── library_repository.py  # Library CRUD operations
├── models/
│   └── paper.py        # Paper dataclass
├── services/
│   └── arxiv.py        # arXiv API client & XML parsing
├── views/
│   └── paper_select.py # Interactive dropdown & save button
└── utils/
    ├── embeds.py       # Discord embed builders
    └── formatting.py   # Text formatting helpers
```

## Tech Stack

- **Python**
- **[discord.py](https://discordpy.readthedocs.io/)** — Discord API wrapper with slash command support
- **[aiohttp](https://docs.aiohttp.org/)** — Async HTTP client for arXiv API requests
- **[aiosqlite](https://github.com/omnilib/aiosqlite)** — Async SQLite for per-user paper library
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment variable loading
- **[arXiv API](https://info.arxiv.org/help/api/)** — Academic paper metadata and abstracts
- **xml.etree.ElementTree** — XML parsing from the Python standard library

## Roadmap

Planned next improvements:

- `/citation_bibtex`
- Result pagination
- Additional paper export formats
