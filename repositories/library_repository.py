from __future__ import annotations

from datetime import datetime, timezone

from aiosqlite import IntegrityError

from database.connection import get_connection
from models.paper import Paper


async def save_paper(user_id: str, paper: Paper) -> bool:
    """Save a paper to the user's library. Returns True if saved, False if duplicate."""
    conn = await get_connection()
    try:
        await conn.execute(
            """
            INSERT INTO saved_papers
                (user_id, paper_id, title, authors, published, categories,
                 arxiv_url, pdf_url, doi, saved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                paper.arxiv_id,
                paper.title,
                ", ".join(paper.authors),
                paper.published,
                ", ".join(paper.categories),
                paper.arxiv_url,
                paper.pdf_url,
                paper.doi,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        await conn.commit()
        return True
    except IntegrityError:
        return False
    finally:
        await conn.close()


async def paper_exists(user_id: str, paper_id: str) -> bool:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT 1 FROM saved_papers WHERE user_id = ? AND paper_id = ?",
            (user_id, paper_id),
        )
        row = await cursor.fetchone()
        return row is not None
    finally:
        await conn.close()


async def get_saved_papers(user_id: str) -> list[dict]:
    """Return saved papers with metadata. Each dict has 'paper' (Paper) and 'saved_at' (str)."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT paper_id, title, authors, published, categories,
                   arxiv_url, pdf_url, doi, saved_at
            FROM saved_papers
            WHERE user_id = ?
            ORDER BY saved_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "paper": Paper(
                    arxiv_id=row["paper_id"],
                    title=row["title"],
                    authors=[a.strip() for a in (row["authors"] or "").split(",") if a.strip()],
                    published=row["published"] or "",
                    categories=[c.strip() for c in (row["categories"] or "").split(",") if c.strip()],
                    arxiv_url=row["arxiv_url"],
                    pdf_url=row["pdf_url"] or "",
                    doi=row["doi"] or "",
                ),
                "saved_at": row["saved_at"],
            }
            for row in rows
        ]
    finally:
        await conn.close()


async def remove_paper(user_id: str, paper_id: str) -> bool:
    """Remove a paper from the user's library. Returns True if removed."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "DELETE FROM saved_papers WHERE user_id = ? AND paper_id = ?",
            (user_id, paper_id),
        )
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()
