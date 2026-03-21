from __future__ import annotations

import logging

import aiosqlite

from database.connection import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_papers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    guild_id    TEXT    NOT NULL DEFAULT '',
    paper_id    TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    authors     TEXT    NOT NULL,
    summary     TEXT,
    published   TEXT,
    categories  TEXT,
    arxiv_url   TEXT    NOT NULL,
    pdf_url     TEXT,
    doi         TEXT,
    status      TEXT    NOT NULL DEFAULT 'to-read',
    note        TEXT,
    saved_at    TEXT    NOT NULL,
    UNIQUE(user_id, guild_id, paper_id)
);

CREATE TABLE IF NOT EXISTS collections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    guild_id    TEXT    NOT NULL DEFAULT '',
    name        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    UNIQUE(user_id, guild_id, name)
);

CREATE TABLE IF NOT EXISTS collection_papers (
    collection_id   INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    paper_id        TEXT    NOT NULL,
    user_id         TEXT    NOT NULL,
    guild_id        TEXT    NOT NULL DEFAULT '',
    added_at        TEXT    NOT NULL,
    UNIQUE(collection_id, paper_id)
);
"""

COLUMN_MIGRATIONS = [
    "ALTER TABLE saved_papers ADD COLUMN status TEXT NOT NULL DEFAULT 'to-read';",
    "ALTER TABLE saved_papers ADD COLUMN note TEXT;",
    "ALTER TABLE saved_papers ADD COLUMN summary TEXT;",
]

logger = logging.getLogger("research_paper_assistant")


async def _needs_guild_id_migration(conn) -> bool:
    cursor = await conn.execute("PRAGMA table_info(saved_papers)")
    columns = [row[1] for row in await cursor.fetchall()]
    return "guild_id" not in columns


async def _migrate_guild_id(conn) -> None:
    """Recreate tables with guild_id column and updated UNIQUE constraints."""
    if not await _needs_guild_id_migration(conn):
        return

    await conn.execute("PRAGMA foreign_keys = OFF;")

    await conn.executescript("""
        CREATE TABLE saved_papers_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT    NOT NULL,
            guild_id    TEXT    NOT NULL DEFAULT '',
            paper_id    TEXT    NOT NULL,
            title       TEXT    NOT NULL,
            authors     TEXT    NOT NULL,
            summary     TEXT,
            published   TEXT,
            categories  TEXT,
            arxiv_url   TEXT    NOT NULL,
            pdf_url     TEXT,
            doi         TEXT,
            status      TEXT    NOT NULL DEFAULT 'to-read',
            note        TEXT,
            saved_at    TEXT    NOT NULL,
            UNIQUE(user_id, guild_id, paper_id)
        );
        INSERT INTO saved_papers_new
            (id, user_id, guild_id, paper_id, title, authors, summary,
             published, categories, arxiv_url, pdf_url, doi, status, note, saved_at)
        SELECT id, user_id, '', paper_id, title, authors, summary,
               published, categories, arxiv_url, pdf_url, doi, status, note, saved_at
        FROM saved_papers;
        DROP TABLE saved_papers;
        ALTER TABLE saved_papers_new RENAME TO saved_papers;

        CREATE TABLE collections_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT    NOT NULL,
            guild_id    TEXT    NOT NULL DEFAULT '',
            name        TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            UNIQUE(user_id, guild_id, name)
        );
        INSERT INTO collections_new (id, user_id, guild_id, name, created_at)
        SELECT id, user_id, '', name, created_at FROM collections;
        DROP TABLE collections;
        ALTER TABLE collections_new RENAME TO collections;

        CREATE TABLE collection_papers_new (
            collection_id   INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            paper_id        TEXT    NOT NULL,
            user_id         TEXT    NOT NULL,
            guild_id        TEXT    NOT NULL DEFAULT '',
            added_at        TEXT    NOT NULL,
            UNIQUE(collection_id, paper_id)
        );
        INSERT INTO collection_papers_new (collection_id, paper_id, user_id, guild_id, added_at)
        SELECT collection_id, paper_id, user_id, '', added_at FROM collection_papers;
        DROP TABLE collection_papers;
        ALTER TABLE collection_papers_new RENAME TO collection_papers;
    """)

    await conn.execute("PRAGMA foreign_keys = ON;")


async def init_db() -> None:
    conn = await get_connection()
    try:
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.executescript(SCHEMA)
        for migration in COLUMN_MIGRATIONS:
            try:
                await conn.execute(migration)
            except aiosqlite.OperationalError as exc:
                if "duplicate column name" in str(exc).lower():
                    continue
                logger.exception("Schema migration failed: %s", migration)
                raise
        await _migrate_guild_id(conn)
        await conn.commit()
    finally:
        await conn.close()
