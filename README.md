# Research Paper Assistant

Research Paper Assistant is an async Discord bot for discovering, organizing, and citing arXiv papers without leaving Discord.

Built to make lightweight literature discovery and organization available directly inside a Discord server.

It supports paper search, personal libraries, collections, reading-status tracking, notes, related-paper discovery, and citation export through slash commands and interactive Discord UI components.

## Features

- Search arXiv papers directly from Discord
- View paper details, summaries, and citation formats
- Save papers to a per-user, per-guild SQLite library
- Organize saved papers into collections
- Track reading status (`to-read`, `reading`, `done`) and personal notes
- Export citations for individual papers or entire collections
- Find related papers from saved library items using lightweight similarity ranking

## Tech Stack

- Python
- `discord.py`
- `aiohttp`
- `aiosqlite`
- SQLite
- arXiv API
- `pytest` + `pytest-asyncio`

## Quick Start

```bash
git clone git@github.com:adabarbulescu/research-paper-assistant.git
cd research-paper-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

Windows PowerShell activation:

```powershell
venv\Scripts\Activate.ps1
```

## Environment Variables

- `DISCORD_TOKEN` - required
- `DISCORD_GUILD_ID` - required
- `DATABASE_PATH` - optional, defaults to `library.db`
- `CLEAR_GLOBAL_COMMANDS` - optional, defaults to `false` (set `true` only if you intentionally want to clear global slash commands on startup)

## Example Commands

```text
/paper_search transformers
/paper_summary graph neural networks
/export_citation arxiv_id:2401.12345 format:bibtex
/set_status arxiv_id:2401.12345 status:reading
/create_collection name:thesis-sources
/add_to_collection arxiv_id:2401.12345 collection:thesis-sources
/export_collection name:thesis-sources format:markdown
```

## Testing

```bash
python -m pytest tests/ -v
```

## CI

GitHub Actions runs the test suite automatically on every push and pull request.

- `.github/workflows/ci.yml`

## Docker

Build and run:

```bash
docker build -t research-paper-assistant .
docker run --env-file .env -e DATABASE_PATH=/data/library.db -v rpa_data:/data research-paper-assistant
```

Run with Compose:

```bash
docker compose up --build -d
```

## Project Structure

```text
commands/      slash command cogs
database/      SQLite connection and migrations
models/        shared dataclasses
repositories/  data access layer
services/      arXiv client and similarity logic
utils/         formatting, citations, and embeds
views/         interactive Discord UI components
tests/         pytest suite
```
