from __future__ import annotations

import os
from pathlib import Path

import aiosqlite

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "library.db"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


async def get_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(str(DATABASE_PATH))
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA foreign_keys=ON;")
    return conn
