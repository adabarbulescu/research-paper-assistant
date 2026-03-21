"""Shared fixtures for the test suite."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from unittest.mock import patch

import aiosqlite
import pytest

from models.paper import Paper


# ── Event loop ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory database ──────────────────────────────────────────

@pytest.fixture()
async def db():
    """Yield a patched in-memory database that init_db has already set up."""
    base_tmp = Path.cwd() / ".tmp" / "pytest-db"
    base_tmp.mkdir(parents=True, exist_ok=True)
    db_path = base_tmp / f"test-{uuid.uuid4().hex}.db"

    async def _get_connection() -> aiosqlite.Connection:
        conn = await aiosqlite.connect(str(db_path))
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    with patch("database.connection.get_connection", _get_connection), \
         patch("repositories.library_repository.get_connection", _get_connection), \
         patch("repositories.metadata_repository.get_connection", _get_connection), \
         patch("repositories.collection_repository.get_connection", _get_connection):

        # Run schema creation
        conn = await _get_connection()
        from database.migrations import SCHEMA
        await conn.executescript(SCHEMA)
        await conn.commit()
        await conn.close()

        yield _get_connection

    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass


# ── Sample papers ────────────────────────────────────────────────

@pytest.fixture()
def sample_paper() -> Paper:
    return Paper(
        arxiv_id="2401.12345",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        summary="We propose a new simple network architecture, the Transformer.",
        published="2017-06-12T17:57:34Z",
        categories=["cs.CL", "cs.AI"],
        arxiv_url="https://arxiv.org/abs/2401.12345",
        pdf_url="https://arxiv.org/pdf/2401.12345",
        doi="10.1234/test",
    )


@pytest.fixture()
def sample_paper_b() -> Paper:
    return Paper(
        arxiv_id="2402.67890",
        title="BERT: Pre-training of Deep Bidirectional Transformers",
        authors=["Jacob Devlin", "Ming-Wei Chang"],
        summary="We introduce BERT, a new language representation model.",
        published="2018-10-11T00:00:00Z",
        categories=["cs.CL"],
        arxiv_url="https://arxiv.org/abs/2402.67890",
        pdf_url="https://arxiv.org/pdf/2402.67890",
        doi="",
    )


@pytest.fixture()
def sample_paper_c() -> Paper:
    return Paper(
        arxiv_id="2403.11111",
        title="Graph Neural Networks: A Review of Methods and Applications",
        authors=["Jie Zhou", "Ganqu Cui"],
        summary="Graph neural networks have been applied to various domains.",
        published="2019-01-15T00:00:00Z",
        categories=["cs.LG", "cs.AI"],
        arxiv_url="https://arxiv.org/abs/2403.11111",
        pdf_url="",
        doi="",
    )
