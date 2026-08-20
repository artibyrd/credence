"""Hermetic Unit Tests for the Autonomous Boredom Engine & Opportunistic Ingestion Loop."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfile
from credence.feeds.boredom import BoredomDaemon, run_boredom_cycle
from credence.models import FeedItemRecord, FeedSubscriptionRecord, TokenUsageRecord, utc_now
from credence.pipeline.schemas import AuditReport


@pytest.mark.unit
async def test_boredom_cycle_digests_pending_items(db_session: AsyncSession):
    """Verify opportunistic boredom cycle prioritizes and audits pending feed items."""
    sub = FeedSubscriptionRecord(
        feed_url="https://wire.example.com/rss",
        title="Wire News",
        priority_tier=1,
        is_active=True,
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    item1 = FeedItemRecord(
        item_url="https://wire.example.com/article-01",
        feed_id=sub.id,
        title="Novel Breaking Verification",
        processing_status="pending",
        discovered_at=utc_now(),
    )
    item2 = FeedItemRecord(
        item_url="https://wire.example.com/article-02",
        feed_id=sub.id,
        title="Second Breaking Item",
        processing_status="pending",
        discovered_at=utc_now(),
    )
    db_session.add_all([item1, item2])
    await db_session.commit()

    mock_report = AuditReport(
        url="https://wire.example.com/article-01",
        content_sha256="sha256:3333444455556666777788889999000011112222ccccdddddeeeeefffff00000",
        simhash_64="0x9876543210fedcba",
        suspicion_score=5.0,
        suspicion_density=0.05,
        classification="CLEAN",
        confidence_score=0.97,
    )

    with (
        patch("credence.pipeline.evaluator.audit_url", new=AsyncMock(return_value=mock_report)),
        patch(
            "credence.feeds.boredom.expand_roots",
            new=AsyncMock(return_value=AsyncMock(new_feeds_subscribed=0, initial_items_harvested=0, details=[])),
        ),
    ):
        summary = await run_boredom_cycle(
            session=db_session,
            audit_burst=2,
            expand_roots_enabled=False,
        )

        assert summary.pending_items_scanned >= 2
        assert summary.pending_items_audited == 2

        # Verify items in database updated to "audited"
        stmt_item = select(FeedItemRecord).where(FeedItemRecord.item_url == "https://wire.example.com/article-01")
        updated = (await db_session.exec(stmt_item)).first()
        assert updated is not None
        assert updated.processing_status == "audited"


@pytest.mark.unit
async def test_boredom_cycle_respects_token_governor_budget(db_session: AsyncSession):
    """Verify boredom cycle defers live audits when daily headroom drops below 30%."""
    from credence.config import COST_PROFILES

    # Insert high token spend to trip headroom limit
    record = TokenUsageRecord(
        timestamp=utc_now(),
        model_name="gemini-3.7-flash",
        prompt_tokens=850_000,
        completion_tokens=100_000,
        total_tokens=950_000,
        estimated_cost_usd=0.45,
    )
    db_session.add(record)

    sub = FeedSubscriptionRecord(feed_url="https://sample.com/rss", title="Sample", priority_tier=2)
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    item = FeedItemRecord(
        item_url="https://sample.com/item-busy",
        feed_id=sub.id,
        title="Item While Constrained",
        processing_status="pending",
    )
    db_session.add(item)
    await db_session.commit()

    custom_profile = COST_PROFILES[CostProfile.FREE]

    with patch("credence.pipeline.evaluator.audit_url") as mock_audit:
        summary = await run_boredom_cycle(
            session=db_session,
            audit_burst=1,
            expand_roots_enabled=False,
            profile_override=custom_profile,
        )

        assert summary.circuit_breaker_tripped is True or summary.headroom_daily_pct < 30.0
        assert summary.items_deferred_budget >= 1
        assert summary.pending_items_audited == 0
        # audit_url must not have been called
        mock_audit.assert_not_called()


@pytest.mark.unit
async def test_boredom_daemon_single_cycle():
    """Verify BoredomDaemon executes a clean single cycle with once=True."""
    from credence.feeds.boredom import BoredomCycleSummary

    daemon = BoredomDaemon(idle_interval_seconds=1, audit_burst=1, expand_roots_enabled=False)

    with patch(
        "credence.feeds.boredom.run_boredom_cycle",
        new=AsyncMock(return_value=BoredomCycleSummary()),
    ):
        await daemon.start(once=True)
        assert daemon._running is True
