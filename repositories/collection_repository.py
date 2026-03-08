from __future__ import annotations

from datetime import datetime, timezone

from aiosqlite import IntegrityError

from database.connection import get_connection


async def create_collection(user_id: str, guild_id: str, name: str) -> bool:
    """Create a named collection. Returns True if created, False if duplicate or blank."""
    cleaned = name.strip()
    if not cleaned:
        return False
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO collections (user_id, guild_id, name, created_at) VALUES (?, ?, ?, ?)",
            (user_id, guild_id, cleaned, datetime.now(timezone.utc).isoformat()),
        )
        await conn.commit()
        return True
    except IntegrityError:
        return False
    finally:
        await conn.close()


async def get_collections(user_id: str, guild_id: str) -> list[dict]:
    """Return all collections for a user with paper counts."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT c.id, c.name, c.created_at,
                   COUNT(cp.paper_id) AS paper_count
            FROM collections c
            LEFT JOIN collection_papers cp ON cp.collection_id = c.id
            WHERE c.user_id = ? AND c.guild_id = ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """,
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "paper_count": row["paper_count"],
            }
            for row in rows
        ]
    finally:
        await conn.close()


async def add_to_collection(
    user_id: str, guild_id: str, collection_name: str, paper_id: str
) -> str:
    """Add a paper to a collection. Returns 'added', 'duplicate', 'not_found', or 'not_saved'."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM collections WHERE user_id = ? AND guild_id = ? AND name = ?",
            (user_id, guild_id, collection_name),
        )
        row = await cursor.fetchone()
        if not row:
            return "not_found"

        paper_check = await conn.execute(
            "SELECT 1 FROM saved_papers WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (user_id, guild_id, paper_id),
        )
        if not await paper_check.fetchone():
            return "not_saved"

        try:
            await conn.execute(
                """INSERT INTO collection_papers
                       (collection_id, paper_id, user_id, guild_id, added_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (row["id"], paper_id, user_id, guild_id, datetime.now(timezone.utc).isoformat()),
            )
            await conn.commit()
            return "added"
        except IntegrityError:
            return "duplicate"
    finally:
        await conn.close()


async def get_collection_papers(
    user_id: str, guild_id: str, collection_name: str
) -> list[dict] | None:
    """Return papers in a collection. Returns None if collection doesn't exist."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM collections WHERE user_id = ? AND guild_id = ? AND name = ?",
            (user_id, guild_id, collection_name),
        )
        col_row = await cursor.fetchone()
        if not col_row:
            return None

        cursor = await conn.execute(
            """
            SELECT sp.paper_id, sp.title, sp.authors, sp.summary, sp.published,
                   sp.categories, sp.arxiv_url, sp.pdf_url, sp.doi, sp.status,
                   sp.note, cp.added_at
            FROM collection_papers cp
            JOIN saved_papers sp
                ON sp.paper_id = cp.paper_id
               AND sp.user_id = cp.user_id
               AND sp.guild_id = cp.guild_id
            WHERE cp.collection_id = ? AND cp.user_id = ?
            ORDER BY cp.added_at DESC
            """,
            (col_row["id"], user_id),
        )
        rows = await cursor.fetchall()
        return [
            {
                "paper_id": row["paper_id"],
                "title": row["title"],
                "authors": row["authors"],
                "summary": row["summary"],
                "published": row["published"],
                "categories": row["categories"],
                "arxiv_url": row["arxiv_url"],
                "pdf_url": row["pdf_url"],
                "doi": row["doi"],
                "status": row["status"],
                "note": row["note"],
                "added_at": row["added_at"],
            }
            for row in rows
        ]
    finally:
        await conn.close()


async def remove_from_collection(
    user_id: str, guild_id: str, collection_name: str, paper_id: str
) -> str:
    """Remove a paper from a collection. Returns 'removed', 'not_in_collection', or 'not_found'."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM collections WHERE user_id = ? AND guild_id = ? AND name = ?",
            (user_id, guild_id, collection_name),
        )
        row = await cursor.fetchone()
        if not row:
            return "not_found"

        cursor = await conn.execute(
            "DELETE FROM collection_papers WHERE collection_id = ? AND paper_id = ?",
            (row["id"], paper_id),
        )
        await conn.commit()
        return "removed" if cursor.rowcount > 0 else "not_in_collection"
    finally:
        await conn.close()


async def delete_collection(user_id: str, guild_id: str, collection_name: str) -> bool:
    """Delete a collection and its paper associations. Returns True if deleted."""
    conn = await get_connection()
    try:
        await conn.execute("PRAGMA foreign_keys = ON;")
        cursor = await conn.execute(
            "DELETE FROM collections WHERE user_id = ? AND guild_id = ? AND name = ?",
            (user_id, guild_id, collection_name),
        )
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()


async def get_collection_names(user_id: str, guild_id: str) -> list[str]:
    """Return all collection names for autocomplete."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT name FROM collections WHERE user_id = ? AND guild_id = ? ORDER BY name",
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        return [row["name"] for row in rows]
    finally:
        await conn.close()
