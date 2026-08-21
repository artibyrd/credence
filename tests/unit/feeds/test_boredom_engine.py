"""Hermetic Unit Tests for Curiosity Loop (Epistemic Boredom Engine)."""

from pathlib import Path

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfile, settings
from credence.db import get_engine, init_db
from credence.feeds.boredom import run_boredom_cycle
from credence.models import Audit, FeedItem, FeedSubscription, Snapshot


@pytest.fixture
def temp_boredom_env(tmp_path: Path, monkeypatch):
    """Provide isolated environment for Boredom Engine tests."""
    db_path = tmp_path / "boredom_test.db"
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "NODE_KEY_PATH", tmp_path / "node.key")
    monkeypatch.setattr(settings, "CREDENCE_PROFILE", CostProfile.OFFLINE)
    return tmp_path


@pytest.mark.unit
@pytest.mark.asyncio
async def test_boredom_cycle_mesh_effort_avoidance(temp_boredom_env: Path):
    """Verify that boredom cycle adopts existing content via mesh effort avoidance with 0 tokens."""
    db_path = temp_boredom_env / "boredom_test.db"
    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    await init_db(engine)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Create subscription
        sub = FeedSubscription(
            feed_url="https://example.com/rss.xml",
            title="Example Feed",
            priority_tier=1,
            is_active=True,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        sub_id = sub.id

        # Existing audit for a URL
        snap = Snapshot(
            url="https://example.com/cached_article",
            content_sha256="sha256:8888888888888888888888888888888888888888888888888888888888888888",
            simhash_64="0x8888888888888888",
            title="Cached Article",
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=6.0,
            classification="CLEAN",
        )
        session.add(audit)

        # Pending feed item with identical URL
        item = FeedItem(
            feed_id=sub_id,
            item_url="https://example.com/cached_article",
            title="Cached Article",
            processing_status="pending",
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        item_id = item.id

        # Run boredom cycle with expand_roots_enabled=False
        summary = await run_boredom_cycle(
            session=session,
            audit_burst=3,
            expand_roots_enabled=False,
        )

        assert summary.mesh_attestations_adopted == 1
        assert summary.pending_items_audited == 0
        assert summary.tokens_saved_mesh >= 0

        # Verify FeedItem status updated
        stmt_check = select(FeedItem).where(FeedItem.id == item_id)
        updated_item = (await session.exec(stmt_check)).first()
        assert updated_item is not None
        assert updated_item.processing_status == "mesh_adopted"
