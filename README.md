# Research Paper Assistant

Research Paper Assistant is an asynchronous Discord bot for discovering, organizing, and citing academic papers from [arXiv](https://arxiv.org) without leaving Discord. It combines `discord.py` slash commands and interactive views with an `aiohttp` arXiv client, `aiosqlite` persistence, and a lightweight TF-IDF similarity engine to support search, summaries, personal libraries, collections, reading-status tracking, notes, and citation export.


## Why This Project

This project was built to make academic paper discovery and lightweight literature management available directly inside a Discord server. Instead of switching between arXiv, citation tools, and separate note-taking apps, users can search papers, inspect metadata, save papers, organize them into collections, track reading progress, and export citations from one interface.

From a portfolio perspective, the project demonstrates async Python, external API integration, database-backed state, interactive Discord UI components, repository-style data access, and automated tests.

## Technical Highlights

- Async architecture built with `discord.py`, `aiohttp`, and `aiosqlite`
- Slash commands with interactive dropdowns, buttons, confirmation dialogs, and pagination
- SQLite-backed per-user, per-guild paper library with foreign key enforcement
- arXiv Atom feed parsing with `xml.etree.ElementTree`
- Lightweight TF-IDF cosine similarity engine implemented with the Python standard library
- Citation export in BibTeX, plain text, and Markdown
- Test coverage for repositories, formatting utilities, citations, arXiv ID parsing, and similarity ranking

## Features

### Search and Discovery

- Search arXiv with optional category and sort filters
- Browse results in compact Discord embeds
- Open a full paper detail view from a dropdown
- Generate quick summaries from paper abstracts
- Export citations for any arXiv paper
- Find related papers from the user's saved library

### Personal Library

- Save papers directly from the detail view
- View saved papers in a paginated library
- Remove papers by arXiv ID
- Track reading status with `to-read`, `reading`, and `done`
- Add, view, and edit personal notes
- View library statistics including totals and top categories

### Collections

- Create named collections
- Add and remove saved papers from collections
- View collections with pagination
- View papers inside a specific collection
- Export citations from a collection inline or as a file
- Delete collections without deleting the saved papers themselves

## Example Commands

```text
/paper_search transformers
/paper_search query:attention category:cs.AI sort_by:submittedDate max_results:10
/paper_summary graph neural networks
/export_citation arxiv_id:2401.12345 format:bibtex
/set_status arxiv_id:2401.12345 status:reading
/add_note arxiv_id:2401.12345 note:Useful baseline for the methods section
/create_collection name:thesis-sources
/add_to_collection arxiv_id:2401.12345 collection:thesis-sources
/export_collection name:thesis-sources format:markdown
```

## Architecture

The project is structured as a small layered application rather than a single-script bot:

```text
Discord slash commands
  -> views and embed builders
  -> services
  -> repositories
  -> SQLite
```

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| Commands | `commands/` | Slash command definitions (4 Cogs) |
| Views | `views/` | Dropdowns, buttons, pagination, confirmation dialogs |
| Services | `services/` | arXiv API access and similarity logic |
| Repositories | `repositories/` | Database operations |
| Database | `database/` | SQLite connection, schema, and migrations |
| Models | `models/` | Shared dataclasses |
| Utils | `utils/` | Formatting, citation, and embed helpers |

## Tech Stack

| Technology | Role |
|------------|------|
| [Python](https://www.python.org/) | Language |
| [discord.py](https://discordpy.readthedocs.io/) | Discord API wrapper with slash command support |
| [aiohttp](https://docs.aiohttp.org/) | Async HTTP client for arXiv API requests |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | Async SQLite for per-user paper library |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable loading |
| [arXiv API](https://info.arxiv.org/help/api/) | Academic paper metadata and abstracts |
| xml.etree.ElementTree | XML parsing (standard library) |

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

On Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` from `.env.example`:

macOS / Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then set:

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications) |
| `DISCORD_GUILD_ID` | Server ID used for development command sync |

### 5. Run the bot

```bash
python bot.py
```

## Testing

Run the test suite with:

```bash
python -m pytest tests/ -v
```

Current test coverage includes:

- 31 repository tests (library, metadata, collections, guild isolation)
- 33 utility, citation, arXiv parsing, and similarity tests
- **64 tests** total

## Project Structure

```text
research-paper-assistant/
+-- bot.py                       # Entry point and bot class
+-- config.py                    # Settings, logging, env loading
+-- requirements.txt
+-- pyproject.toml               # Pytest configuration
+-- .env.example
+-- commands/
|   +-- papers.py               # Search and summary commands (Cog)
|   +-- library.py              # Library management, status, and notes (Cog)
|   +-- collections.py          # Collection CRUD commands (Cog)
|   +-- discovery.py            # Related papers and citation export (Cog)
+-- database/
|   +-- connection.py           # SQLite connection helper
|   +-- migrations.py           # Schema definitions and migrations
+-- repositories/
|   +-- library_repository.py   # Paper CRUD (save, remove, list)
|   +-- metadata_repository.py  # Status and notes operations
|   +-- collection_repository.py # Collection CRUD
+-- models/
|   +-- paper.py                # Paper dataclass
|   +-- collection.py           # Collection dataclass
|   +-- saved_paper.py          # SavedPaper dataclass and status constants
+-- services/
|   +-- arxiv.py                # arXiv API client and XML parsing
|   +-- similarity.py           # TF-IDF cosine similarity engine
+-- views/
|   +-- paper_select.py         # Search result dropdown
|   +-- paper_actions.py        # Save, cite, and related buttons
|   +-- pagination.py           # Paginated library and collection views
|   +-- confirm.py              # Confirmation dialog view
+-- utils/
|   +-- citations.py            # BibTeX, plain, and Markdown formatters
|   +-- embeds.py               # Discord embed builders
|   +-- formatting.py           # Text formatting helpers
+-- tests/
    +-- conftest.py             # Shared fixtures and in-memory DB setup
    +-- test_repositories.py    # Repository layer tests
    +-- test_utils.py           # Formatting, citation, and similarity tests
```

## Future Improvements

- Add CI so tests run automatically on every push
- Add Docker support for easier deployment
- Expand automated coverage for Discord interaction flows
- Improve recommendations with richer metadata or embedding-based approaches

