from __future__ import annotations

import aiosqlite

DATABASE_PATH = "library.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_papers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    paper_id    TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    authors     TEXT    NOT NULL,
    published   TEXT,
    categories  TEXT,
    arxiv_url   TEXT    NOT NULL,
    pdf_url     TEXT,
    doi         TEXT,
    saved_at    TEXT    NOT NULL,
    UNIQUE(user_id, paper_id)
);
"""


async def get_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DATABASE_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL;")
    return conn


async def init_db() -> None:
    conn = await get_connection()
    try:
        await conn.executescript(SCHEMA)
        await conn.commit()
    finally:
        await conn.close()
