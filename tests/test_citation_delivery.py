from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from commands.discovery import Discovery
from models.paper import Paper
from views.paper_actions import CiteSelect


@pytest.mark.asyncio
async def test_export_citation_attaches_file_when_too_long(monkeypatch):
    paper = Paper(
        arxiv_id="2401.12345",
        title="Test Paper",
        authors=["Alice"],
        arxiv_url="https://arxiv.org/abs/2401.12345",
    )

    monkeypatch.setattr("commands.discovery.get_paper_by_id", AsyncMock(return_value=paper))
    monkeypatch.setattr("commands.discovery.to_plain_citation", lambda _: "x" * 3000)

    interaction = SimpleNamespace(
        user=SimpleNamespace(id=1),
        response=SimpleNamespace(defer=AsyncMock(), is_done=lambda: True),
        followup=SimpleNamespace(send=AsyncMock()),
    )

    cog = Discovery(bot=SimpleNamespace())
    await Discovery.export_citation.callback(cog, interaction, "2401.12345", "plain")

    interaction.response.defer.assert_awaited_once()
    assert interaction.followup.send.await_count == 1
    _, kwargs = interaction.followup.send.await_args
    assert kwargs["ephemeral"] is True
    assert kwargs.get("file") is not None


@pytest.mark.asyncio
async def test_cite_select_attaches_file_when_too_long(monkeypatch):
    paper = Paper(
        arxiv_id="2401.12345",
        title="Test Paper",
        authors=["Alice"],
        arxiv_url="https://arxiv.org/abs/2401.12345",
    )

    monkeypatch.setattr("views.paper_actions.to_plain_citation", lambda _: "x" * 3000)

    select = CiteSelect(paper)
    select._values = ["plain"]

    interaction = SimpleNamespace(
        response=SimpleNamespace(send_message=AsyncMock()),
    )

    await select.callback(interaction)

    assert interaction.response.send_message.await_count == 1
    _, kwargs = interaction.response.send_message.await_args
    assert kwargs["ephemeral"] is True
    assert kwargs.get("file") is not None
