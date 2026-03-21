# Research Paper Assistant

![CI](https://github.com/adabarbulescu/research-paper-assistant/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000)
![Docker](https://img.shields.io/badge/docker-ready-blue)

An async Discord bot for discovering, organizing, and citing arXiv papers without leaving Discord — built for researchers and students who do their work where the conversation already is.

Supports paper search, personal libraries, collections, reading-status tracking, notes, related-paper discovery, and citation export through slash commands and interactive Discord UI components.

## Features

- Search arXiv papers directly from Discord
- View paper details, summaries, and citation formats
- Save papers to a per-user, per-guild SQLite library
- Organize saved papers into collections
- Track reading status (`to-read`, `reading`, `done`) and personal notes
- Export citations for individual papers or entire collections
- Find related papers from saved library items using lightweight similarity ranking
- Supported citation formats: `bibtex`, `plain`, `markdown`

## Tech Stack

- Python 3.11+
- `discord.py`
- `aiohttp` + `aiosqlite`
- `python-dotenv`
- `defusedxml`
- SQLite
- arXiv API
- `pytest` + `pytest-asyncio`

## Prerequisites

- Python 3.11+
- A Discord application with a bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- Bot invited to your server with the `applications.commands` and `bot` scopes, and `Send Messages` + `Read Message History` permissions
- Message Content Intent enabled in the Developer Portal

## Quick Start
```bash
git clone git@github.com:adabarbulescu/research-paper-assistant.git
cd research-paper-assistant
python -m venv venv
source venv/bin/activate  # Windows PowerShell: venv\Scripts\Activate.ps1  |  CMD: venv\Scripts\activate.bat
pip install -r requirements.txt
cp .env.example .env
# fill in DISCORD_TOKEN and DISCORD_GUILD_ID in .env
python bot.py
```

## Environment Variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `DISCORD_TOKEN` | yes | — | Bot token from Developer Portal |
| `DISCORD_GUILD_ID` | yes | — | ID of your Discord server |
| `DATABASE_PATH` | no | `library.db` | Path to SQLite database file |
| `CLEAR_GLOBAL_COMMANDS` | no | `false` | Set `true` only to intentionally wipe global slash commands on startup |

## Commands

### Search & Discovery
| Command | Description |
|---|---|
| `/paper_search <query>` | Search arXiv papers. Optional: `category` (e.g. `cs.AI`), `sort_by` (`relevance`, `submittedDate`, `lastUpdatedDate`), `sort_order` (`descending`, `ascending`), `max_results` (1–10, default 5) |
| `/paper_summary <query>` | Detailed summary of the top matching paper. Optional: `category` |
| `/related_papers <arxiv_id>` | Find similar papers in your library |

### Library
| Command | Description |
|---|---|
| `/my_library` | View your saved papers |
| `/library_by_status <status>` | Filter saved papers by reading status (`to-read`, `reading`, `done`) |
| `/library_stats` | View statistics about your library |
| `/set_status <arxiv_id> <status>` | Set reading status for a saved paper |
| `/remove_paper <paper_id>` | Remove a paper from your library |

### Notes
| Command | Description |
|---|---|
| `/add_note <arxiv_id> <note>` | Add or update a note on a saved paper (max 500 chars) |
| `/view_note <arxiv_id>` | View your note on a saved paper |
| `/edit_note <arxiv_id> <note>` | Replace your note on a saved paper |

### Collections
| Command | Description |
|---|---|
| `/create_collection <name>` | Create a new paper collection |
| `/my_collections` | View all your collections |
| `/add_to_collection <arxiv_id> <collection>` | Add a saved paper to a collection |
| `/view_collection <name>` | View papers in a collection |
| `/remove_from_collection <arxiv_id> <collection>` | Remove a paper from a collection |
| `/delete_collection <name>` | Delete a collection (papers stay in your library) |

### Citations
| Command | Description |
|---|---|
| `/export_citation <arxiv_id>` | Generate a citation for a paper. Optional: `format` (`bibtex`, `plain`, `markdown`; default `bibtex`) |
| `/export_collection <name>` | Export citations for all papers in a collection. Optional: `format` |

### Utility
| Command | Description |
|---|---|
| `/ping` | Check if the bot is working |

## Example Commands
```text
/paper_search transformers category:cs.AI max_results:10
/paper_summary attention mechanisms category:cs.LG
/export_citation arxiv_id:2401.12345 format:bibtex
/set_status arxiv_id:2401.12345 status:reading
/add_note arxiv_id:2401.12345 note:Great intro to sparse attention
/create_collection name:thesis-sources
/add_to_collection arxiv_id:2401.12345 collection:thesis-sources
/export_collection name:thesis-sources format:markdown
```

## Testing
```bash
python -m pytest tests/ -v
```

CI also runs [Ruff](https://docs.astral.sh/ruff/) (linting) and [Bandit](https://bandit.readthedocs.io/) (security scanning) — run `ruff check .` and `bandit -c bandit.yaml -r .` locally before pushing.

## CI

GitHub Actions runs the test suite on every push and pull request — see `.github/workflows/ci.yml`.

## Docker
```bash
# Build and run
docker build -t research-paper-assistant .
docker run --env-file .env -e DATABASE_PATH=/data/library.db -v rpa_data:/data research-paper-assistant

# Or with Compose
docker compose up --build -d
```