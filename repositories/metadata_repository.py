from __future__ import annotations

from database.connection import get_connection
from models.paper import Paper
from models.saved_paper import VALID_STATUSES


async def set_status(user_id: str, guild_id: str, paper_id: str, status: str) -> str:
    """Set reading status. Returns 'updated', 'not_found', or 'invalid'."""
    if status not in VALID_STATUSES:
        return "invalid"
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "UPDATE saved_papers SET status = ? WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (status, user_id, guild_id, paper_id),
        )
        await conn.commit()
        return "updated" if cursor.rowcount > 0 else "not_found"
    finally:
        await conn.close()


async def get_papers_by_status(user_id: str, guild_id: str, status: str) -> list[dict]:
    """Return saved papers filtered by status."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT paper_id, title, authors, summary, published, categories,
                   arxiv_url, pdf_url, doi, status, note, saved_at
            FROM saved_papers
            WHERE user_id = ? AND guild_id = ? AND status = ?
            ORDER BY saved_at DESC
            """,
            (user_id, guild_id, status),
        )
        rows = await cursor.fetchall()
        return [
            {
                "paper": Paper(
                    arxiv_id=row["paper_id"],
                    title=row["title"],
                    authors=[a.strip() for a in (row["authors"] or "").split(",") if a.strip()],
                    summary=row["summary"] or "",
                    published=row["published"] or "",
                    categories=[c.strip() for c in (row["categories"] or "").split(",") if c.strip()],
                    arxiv_url=row["arxiv_url"],
                    pdf_url=row["pdf_url"] or "",
                    doi=row["doi"] or "",
                ),
                "saved_at": row["saved_at"],
                "status": row["status"],
                "note": row["note"],
            }
            for row in rows
        ]
    finally:
        await conn.close()


async def set_note(user_id: str, guild_id: str, paper_id: str, note: str) -> bool:
    """Set or update a note on a saved paper. Returns True if paper exists."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "UPDATE saved_papers SET note = ? WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (note.strip(), user_id, guild_id, paper_id),
        )
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()


async def get_note(user_id: str, guild_id: str, paper_id: str) -> str | None:
    """Get the note for a saved paper. Returns None if paper not found."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT note FROM saved_papers WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (user_id, guild_id, paper_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return row["note"] or ""
    finally:
        await conn.close()
