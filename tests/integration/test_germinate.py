"""Hermetic test suite for node germination and Miracle-Gro ignition lifecycle."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.parser import ParsedFeed
from credence.germinate import (
    GerminationSummary,
    germinate_node,
    run_germination_sifting_burst,
)
from credence.models import Audit, FeedSubscription


@pytest.mark.asyncio
async def test_germinate_node_fresh_db(db_session: AsyncSession) -> None:
    """Verify end-to-end node germination on a fresh database with mock evaluator."""
    # Mock feed parser to return empty entries to avoid real network calls
    mock_feed = ParsedFeed(title="Mock Stream", is_modified=True, entries=[])

    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock, return_value=mock_feed):
        summary: GerminationSummary = await germinate_node(
            session=db_session,
            burst_items=2,
            sync_mesh=True,
            verbose=False,
        )

        assert summary.status == "germinated"
        assert len(summary.identity_pubkey) == 64
        assert summary.peer_attestations_adopted >= 3
        assert summary.tokens_saved_mesh >= 7500
        assert summary.feeds_sowed >= 20
        assert summary.total_reports_ready >= 3
        assert summary.duration_seconds >= 0.0

        # Verify records persisted in SQLite
        stmt_audits = select(func.count(col(Audit.id)))
        audit_count = (await db_session.exec(stmt_audits)).first() or 0
        assert audit_count >= 3

        stmt_subs = select(func.count(col(FeedSubscription.id)))
        subs_count = (await db_session.exec(stmt_subs)).first() or 0
        assert subs_count >= 20


@pytest.mark.asyncio
async def test_germinate_idempotency(db_session: AsyncSession) -> None:
    """Verify running germination multiple times is idempotent and does not duplicate records."""
    mock_feed = ParsedFeed(title="Mock Stream", is_modified=True, entries=[])

    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock, return_value=mock_feed):
        # First germination pass
        await germinate_node(session=db_session, burst_items=0, sync_mesh=True, verbose=False)

        stmt_audits = select(func.count(col(Audit.id)))
        count1 = (await db_session.exec(stmt_audits)).first() or 0

        # Second germination pass
        summary2 = await germinate_node(session=db_session, burst_items=0, sync_mesh=True, verbose=False)

        count2 = (await db_session.exec(stmt_audits)).first() or 0

        assert count1 == count2
        assert summary2.peer_attestations_adopted == 0  # No duplicate adoptions


@pytest.mark.asyncio
async def test_germinate_no_mesh_offline(db_session: AsyncSession) -> None:
    """Verify 100% offline air-gapped germination when sync_mesh is False."""
    summary = await germinate_node(session=db_session, burst_items=0, sync_mesh=False, verbose=False)

    assert summary.peer_attestations_adopted == 0
    assert summary.tokens_saved_mesh == 0
    assert summary.feeds_sowed >= 20


@pytest.mark.asyncio
async def test_germinate_governor_headroom_guard(db_session: AsyncSession) -> None:
    """Verify that when governor headroom is exhausted (<30%), sifting burst safely defers audits."""
    from credence.pipeline.governor import TokenHeadroomStatus

    mock_headroom = TokenHeadroomStatus(
        circuit_breaker_tripped=True,
    )
    with patch("credence.germinate.get_token_headroom_status", new_callable=AsyncMock, return_value=mock_headroom):
        burst_count = await run_germination_sifting_burst(session=db_session, burst_limit=5)
        assert burst_count == 0


@pytest.mark.asyncio
async def test_germinate_rest_endpoint(db_session: Any) -> None:
    """Verify Starlette POST /api/germinate endpoint returns valid GerminationSummary JSON."""
    import httpx
    from httpx import ASGITransport

    from credence.server.app import create_server_app

    mock_feed = ParsedFeed(title="Mock Stream", is_modified=True, entries=[])

    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock, return_value=mock_feed):
        app = create_server_app()
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/germinate", json={"burst": 0, "sync_mesh": True})
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "germinated"
            assert "identity_pubkey" in data
            assert "peer_attestations_adopted" in data
            assert "total_reports_ready" in data
