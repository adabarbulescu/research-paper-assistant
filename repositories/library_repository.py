from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from aiosqlite import IntegrityError

from database.connection import get_connection
from models.paper import Paper
from utils.serialization import decode_str_list, encode_str_list


async def save_paper(user_id: str, guild_id: str, paper: Paper) -> bool:
    """Save a paper to the user's library. Returns True if saved, False if duplicate."""
    conn = await get_connection()
    try:
        await conn.execute(
            """
            INSERT INTO saved_papers
                (user_id, guild_id, paper_id, title, authors, summary, published, categories,
                 arxiv_url, pdf_url, doi, saved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                guild_id,
                paper.arxiv_id,
                paper.title,
                encode_str_list(paper.authors),
                paper.summary,
                paper.published,
                encode_str_list(paper.categories),
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


async def paper_exists(user_id: str, guild_id: str, paper_id: str) -> bool:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT 1 FROM saved_papers WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (user_id, guild_id, paper_id),
        )
        row = await cursor.fetchone()
        return row is not None
    finally:
        await conn.close()


async def get_saved_papers(user_id: str, guild_id: str) -> list[dict]:
    """Return saved papers with metadata. Each dict has 'paper' (Paper) and 'saved_at' (str)."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT paper_id, title, authors, summary, published, categories,
                   arxiv_url, pdf_url, doi, status, note, saved_at
            FROM saved_papers
            WHERE user_id = ? AND guild_id = ?
            ORDER BY saved_at DESC
            """,
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        return [
            {
                "paper": Paper(
                    arxiv_id=row["paper_id"],
                    title=row["title"],
                    authors=decode_str_list(row["authors"]),
                    summary=row["summary"] or "",
                    published=row["published"] or "",
                    categories=decode_str_list(row["categories"]),
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


async def remove_paper(user_id: str, guild_id: str, paper_id: str) -> bool:
    """Remove a paper from the user's library and any collection references."""
    conn = await get_connection()
    try:
        await conn.execute(
            "DELETE FROM collection_papers WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (user_id, guild_id, paper_id),
        )
        cursor = await conn.execute(
            "DELETE FROM saved_papers WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            (user_id, guild_id, paper_id),
        )
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()


async def get_all_papers(user_id: str, guild_id: str) -> list[Paper]:
    """Return all saved papers as Paper objects (with summaries for similarity)."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT paper_id, title, authors, summary, published, categories,
                   arxiv_url, pdf_url, doi
            FROM saved_papers
            WHERE user_id = ? AND guild_id = ?
            """,
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        return [
            Paper(
                arxiv_id=row["paper_id"],
                title=row["title"],
                authors=decode_str_list(row["authors"]),
                summary=row["summary"] or "",
                published=row["published"] or "",
                categories=decode_str_list(row["categories"]),
                arxiv_url=row["arxiv_url"],
                pdf_url=row["pdf_url"] or "",
                doi=row["doi"] or "",
            )
            for row in rows
        ]
    finally:
        await conn.close()


async def get_paper_ids(user_id: str, guild_id: str) -> list[str]:
    """Return all saved paper IDs for autocomplete."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT paper_id FROM saved_papers WHERE user_id = ? AND guild_id = ? ORDER BY saved_at DESC",
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        return [row["paper_id"] for row in rows]
    finally:
        await conn.close()


async def get_library_stats(user_id: str, guild_id: str) -> dict:
    """Return library statistics: total, status counts, collection count, top categories."""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) as total FROM saved_papers WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        total = (await cursor.fetchone())["total"]

        cursor = await conn.execute(
            "SELECT status, COUNT(*) as count FROM saved_papers WHERE user_id = ? AND guild_id = ? GROUP BY status",
            (user_id, guild_id),
        )
        status_counts = {row["status"]: row["count"] for row in await cursor.fetchall()}

        cursor = await conn.execute(
            "SELECT COUNT(*) as total FROM collections WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        collections_count = (await cursor.fetchone())["total"]

        cursor = await conn.execute(
            "SELECT categories FROM saved_papers WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        cat_counter: Counter[str] = Counter()
        for row in rows:
            for cat in decode_str_list(row["categories"]):
                cat_counter[cat] += 1

        return {
            "total": total,
            "status_counts": status_counts,
            "collections_count": collections_count,
            "top_categories": cat_counter.most_common(5),
        }
    finally:
        await conn.close()
