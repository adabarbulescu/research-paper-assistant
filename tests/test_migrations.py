from __future__ import annotations

from unittest.mock import AsyncMock

import aiosqlite
import pytest

from database import migrations


class FakeConn:
    def __init__(self, execute_side_effects: list[Exception | None]) -> None:
        self._effects = execute_side_effects
        self._idx = 0
        self.executescript = AsyncMock()
        self.commit = AsyncMock()
        self.close = AsyncMock()

    async def execute(self, _sql: str):
        if self._idx < len(self._effects):
            effect = self._effects[self._idx]
            self._idx += 1
            if effect is not None:
                raise effect
        return AsyncMock()


@pytest.mark.asyncio
async def test_init_db_ignores_duplicate_column_operational_error(monkeypatch):
    # 1) PRAGMA foreign_keys=ON
    # 2) migration 1 -> duplicate column
    # 3) migration 2 -> success
    # 4) migration 3 -> success
    fake_conn = FakeConn(
        execute_side_effects=[
            None,
            aiosqlite.OperationalError("duplicate column name: status"),
            None,
            None,
        ]
    )

    monkeypatch.setattr(migrations, "get_connection", AsyncMock(return_value=fake_conn))
    monkeypatch.setattr(migrations, "_migrate_guild_id", AsyncMock())

    await migrations.init_db()

    assert fake_conn.executescript.await_count == 1
    assert fake_conn.commit.await_count == 1
    assert fake_conn.close.await_count == 1


@pytest.mark.asyncio
async def test_init_db_reraises_unexpected_operational_error(monkeypatch):
    fake_conn = FakeConn(
        execute_side_effects=[
            None,
            aiosqlite.OperationalError("database is locked"),
        ]
    )

    monkeypatch.setattr(migrations, "get_connection", AsyncMock(return_value=fake_conn))
    monkeypatch.setattr(migrations, "_migrate_guild_id", AsyncMock())

    with pytest.raises(aiosqlite.OperationalError):
        await migrations.init_db()

    assert fake_conn.close.await_count == 1
