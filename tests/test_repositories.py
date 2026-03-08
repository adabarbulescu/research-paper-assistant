"""Tests for library, metadata, and collection repositories."""

from __future__ import annotations

import pytest

from models.paper import Paper


# ── library_repository ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_paper(db, sample_paper: Paper):
    from repositories.library_repository import save_paper, paper_exists

    saved = await save_paper("user1", "guild1", sample_paper)
    assert saved is True

    exists = await paper_exists("user1", "guild1", sample_paper.arxiv_id)
    assert exists is True


@pytest.mark.asyncio
async def test_save_paper_duplicate(db, sample_paper: Paper):
    from repositories.library_repository import save_paper

    await save_paper("user1", "guild1", sample_paper)
    duplicate = await save_paper("user1", "guild1", sample_paper)
    assert duplicate is False


@pytest.mark.asyncio
async def test_save_paper_different_guild(db, sample_paper: Paper):
    from repositories.library_repository import save_paper, paper_exists

    await save_paper("user1", "guild1", sample_paper)
    saved_other = await save_paper("user1", "guild2", sample_paper)
    assert saved_other is True

    assert await paper_exists("user1", "guild1", sample_paper.arxiv_id) is True
    assert await paper_exists("user1", "guild2", sample_paper.arxiv_id) is True
    assert await paper_exists("user1", "guild3", sample_paper.arxiv_id) is False


@pytest.mark.asyncio
async def test_get_saved_papers(db, sample_paper: Paper, sample_paper_b: Paper):
    from repositories.library_repository import save_paper, get_saved_papers

    await save_paper("user1", "guild1", sample_paper)
    await save_paper("user1", "guild1", sample_paper_b)

    entries = await get_saved_papers("user1", "guild1")
    assert len(entries) == 2
    ids = {e["paper"].arxiv_id for e in entries}
    assert ids == {sample_paper.arxiv_id, sample_paper_b.arxiv_id}


@pytest.mark.asyncio
async def test_get_saved_papers_guild_isolation(db, sample_paper: Paper):
    from repositories.library_repository import save_paper, get_saved_papers

    await save_paper("user1", "guild1", sample_paper)

    assert len(await get_saved_papers("user1", "guild1")) == 1
    assert len(await get_saved_papers("user1", "guild2")) == 0


@pytest.mark.asyncio
async def test_remove_paper(db, sample_paper: Paper):
    from repositories.library_repository import save_paper, remove_paper, paper_exists

    await save_paper("user1", "guild1", sample_paper)
    removed = await remove_paper("user1", "guild1", sample_paper.arxiv_id)
    assert removed is True
    assert await paper_exists("user1", "guild1", sample_paper.arxiv_id) is False


@pytest.mark.asyncio
async def test_remove_paper_not_found(db):
    from repositories.library_repository import remove_paper

    removed = await remove_paper("user1", "guild1", "nonexistent")
    assert removed is False


@pytest.mark.asyncio
async def test_remove_paper_cleans_collection_papers(db, sample_paper: Paper):
    """Removing a paper should also delete it from any collections."""
    from repositories.library_repository import save_paper, remove_paper
    from repositories.collection_repository import (
        create_collection,
        add_to_collection,
        get_collection_papers,
    )

    await save_paper("user1", "guild1", sample_paper)
    await create_collection("user1", "guild1", "refs")
    await add_to_collection("user1", "guild1", "refs", sample_paper.arxiv_id)

    papers = await get_collection_papers("user1", "guild1", "refs")
    assert len(papers) == 1

    await remove_paper("user1", "guild1", sample_paper.arxiv_id)

    # get_collection_papers JOINs saved_papers so it'll be empty after removal.
    # Verify the orphan row in collection_papers is actually gone via raw query.
    from database.connection import get_connection

    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM collection_papers WHERE user_id = ? AND guild_id = ? AND paper_id = ?",
            ("user1", "guild1", sample_paper.arxiv_id),
        )
        row = await cursor.fetchone()
        assert row[0] == 0
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_all_papers(db, sample_paper: Paper, sample_paper_b: Paper):
    from repositories.library_repository import save_paper, get_all_papers

    await save_paper("user1", "guild1", sample_paper)
    await save_paper("user1", "guild1", sample_paper_b)

    papers = await get_all_papers("user1", "guild1")
    assert len(papers) == 2
    assert all(isinstance(p, Paper) for p in papers)


@pytest.mark.asyncio
async def test_get_paper_ids(db, sample_paper: Paper, sample_paper_b: Paper):
    from repositories.library_repository import save_paper, get_paper_ids

    await save_paper("user1", "guild1", sample_paper)
    await save_paper("user1", "guild1", sample_paper_b)

    ids = await get_paper_ids("user1", "guild1")
    assert set(ids) == {sample_paper.arxiv_id, sample_paper_b.arxiv_id}


@pytest.mark.asyncio
async def test_get_library_stats(db, sample_paper: Paper, sample_paper_b: Paper):
    from repositories.library_repository import save_paper, get_library_stats

    await save_paper("user1", "guild1", sample_paper)
    await save_paper("user1", "guild1", sample_paper_b)

    stats = await get_library_stats("user1", "guild1")
    assert stats["total"] == 2
    assert stats["status_counts"].get("to-read", 0) == 2
    assert stats["collections_count"] == 0
    assert isinstance(stats["top_categories"], list)


@pytest.mark.asyncio
async def test_get_library_stats_empty(db):
    from repositories.library_repository import get_library_stats

    stats = await get_library_stats("user1", "guild1")
    assert stats["total"] == 0


# ── metadata_repository ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_status(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.metadata_repository import set_status, get_papers_by_status

    await save_paper("user1", "guild1", sample_paper)

    result = await set_status("user1", "guild1", sample_paper.arxiv_id, "reading")
    assert result == "updated"

    papers = await get_papers_by_status("user1", "guild1", "reading")
    assert len(papers) == 1
    assert papers[0]["paper"].arxiv_id == sample_paper.arxiv_id


@pytest.mark.asyncio
async def test_set_status_not_found(db):
    from repositories.metadata_repository import set_status

    result = await set_status("user1", "guild1", "nonexistent", "done")
    assert result == "not_found"


@pytest.mark.asyncio
async def test_set_status_invalid(db):
    from repositories.metadata_repository import set_status

    result = await set_status("user1", "guild1", "anything", "invalid-status")
    assert result == "invalid"


@pytest.mark.asyncio
async def test_set_and_get_note(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.metadata_repository import set_note, get_note

    await save_paper("user1", "guild1", sample_paper)

    updated = await set_note("user1", "guild1", sample_paper.arxiv_id, "Great paper!")
    assert updated is True

    note = await get_note("user1", "guild1", sample_paper.arxiv_id)
    assert note == "Great paper!"


@pytest.mark.asyncio
async def test_get_note_not_found(db):
    from repositories.metadata_repository import get_note

    note = await get_note("user1", "guild1", "nonexistent")
    assert note is None


@pytest.mark.asyncio
async def test_get_note_empty(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.metadata_repository import get_note

    await save_paper("user1", "guild1", sample_paper)

    note = await get_note("user1", "guild1", sample_paper.arxiv_id)
    assert note == ""


# ── collection_repository ───────────────────────────────────────

@pytest.mark.asyncio
async def test_create_collection(db):
    from repositories.collection_repository import create_collection, get_collections

    created = await create_collection("user1", "guild1", "thesis")
    assert created is True

    collections = await get_collections("user1", "guild1")
    assert len(collections) == 1
    assert collections[0]["name"] == "thesis"


@pytest.mark.asyncio
async def test_create_collection_duplicate(db):
    from repositories.collection_repository import create_collection

    await create_collection("user1", "guild1", "thesis")
    dup = await create_collection("user1", "guild1", "thesis")
    assert dup is False


@pytest.mark.asyncio
async def test_create_collection_blank_name(db):
    from repositories.collection_repository import create_collection, get_collections

    assert await create_collection("user1", "guild1", "   ") is False
    assert await create_collection("user1", "guild1", "") is False
    assert len(await get_collections("user1", "guild1")) == 0


@pytest.mark.asyncio
async def test_collection_guild_isolation(db):
    from repositories.collection_repository import create_collection, get_collections

    await create_collection("user1", "guild1", "thesis")
    await create_collection("user1", "guild2", "thesis")

    assert len(await get_collections("user1", "guild1")) == 1
    assert len(await get_collections("user1", "guild2")) == 1


@pytest.mark.asyncio
async def test_add_to_collection(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.collection_repository import (
        create_collection, add_to_collection, get_collection_papers,
    )

    await save_paper("user1", "guild1", sample_paper)
    await create_collection("user1", "guild1", "ml-papers")

    result = await add_to_collection("user1", "guild1", "ml-papers", sample_paper.arxiv_id)
    assert result == "added"

    papers = await get_collection_papers("user1", "guild1", "ml-papers")
    assert papers is not None
    assert len(papers) == 1
    assert papers[0]["paper_id"] == sample_paper.arxiv_id


@pytest.mark.asyncio
async def test_add_to_collection_not_saved(db):
    from repositories.collection_repository import create_collection, add_to_collection

    await create_collection("user1", "guild1", "ml-papers")
    result = await add_to_collection("user1", "guild1", "ml-papers", "nonexistent")
    assert result == "not_saved"


@pytest.mark.asyncio
async def test_add_to_collection_not_found(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.collection_repository import add_to_collection

    await save_paper("user1", "guild1", sample_paper)
    result = await add_to_collection("user1", "guild1", "doesnt-exist", sample_paper.arxiv_id)
    assert result == "not_found"


@pytest.mark.asyncio
async def test_add_to_collection_duplicate(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.collection_repository import create_collection, add_to_collection

    await save_paper("user1", "guild1", sample_paper)
    await create_collection("user1", "guild1", "ml-papers")

    await add_to_collection("user1", "guild1", "ml-papers", sample_paper.arxiv_id)
    dup = await add_to_collection("user1", "guild1", "ml-papers", sample_paper.arxiv_id)
    assert dup == "duplicate"


@pytest.mark.asyncio
async def test_remove_from_collection(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.collection_repository import (
        create_collection, add_to_collection, remove_from_collection, get_collection_papers,
    )

    await save_paper("user1", "guild1", sample_paper)
    await create_collection("user1", "guild1", "ml-papers")
    await add_to_collection("user1", "guild1", "ml-papers", sample_paper.arxiv_id)

    result = await remove_from_collection("user1", "guild1", "ml-papers", sample_paper.arxiv_id)
    assert result == "removed"

    papers = await get_collection_papers("user1", "guild1", "ml-papers")
    assert papers == []


@pytest.mark.asyncio
async def test_remove_from_collection_not_found(db):
    from repositories.collection_repository import remove_from_collection

    result = await remove_from_collection("user1", "guild1", "doesnt-exist", "xxx")
    assert result == "not_found"


@pytest.mark.asyncio
async def test_delete_collection(db, sample_paper: Paper):
    from repositories.library_repository import save_paper
    from repositories.collection_repository import (
        create_collection, add_to_collection, delete_collection, get_collections,
    )

    await save_paper("user1", "guild1", sample_paper)
    await create_collection("user1", "guild1", "ml-papers")
    await add_to_collection("user1", "guild1", "ml-papers", sample_paper.arxiv_id)

    deleted = await delete_collection("user1", "guild1", "ml-papers")
    assert deleted is True
    assert len(await get_collections("user1", "guild1")) == 0


@pytest.mark.asyncio
async def test_get_collection_names(db):
    from repositories.collection_repository import create_collection, get_collection_names

    await create_collection("user1", "guild1", "alpha")
    await create_collection("user1", "guild1", "beta")

    names = await get_collection_names("user1", "guild1")
    assert sorted(names) == ["alpha", "beta"]


@pytest.mark.asyncio
async def test_get_collection_papers_nonexistent(db):
    from repositories.collection_repository import get_collection_papers

    result = await get_collection_papers("user1", "guild1", "nope")
    assert result is None
