"""Unit tests for Mesh Effort Avoidance, Zero-Token Adoption, and Feed Worker."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.dedup import (
    adopt_peer_attestation,
    check_mesh_effort_avoidance,
)
from credence.feeds.parser import FeedEntry, ParsedFeed
from credence.feeds.worker import sync_single_feed
from credence.models import (
    FeedItem,
    FeedSubscription,
    PeerMetric,
)


@pytest.mark.asyncio
async def test_zero_token_mesh_adoption_workflow(db_session: AsyncSession):
    """Verify adopting a gossiped peer attestation at $0.00 token cost."""
    url = "https://apiculture-review.org/bee-suits-2026"
    peer_pubkey = "trusted_beekeeper_peer_pubkey_abc"
    peer_signature = "sig_beekeeper_123"
    content_hash = "sha256_bee_suit_12345"

    # 1. Register peer with high reputation in PeerMetric
    peer_metric = PeerMetric(
        node_pubkey=peer_pubkey,
        quality_score=0.96,
        ws_url="wss://relay.credence.nexus:8765",
    )
    db_session.add(peer_metric)
    await db_session.commit()

    # 2. Peer publishes signed attestation
    adopted_audit = await adopt_peer_attestation(
        session=db_session,
        item_url=url,
        title="Best Apiary Suits Review",
        peer_pubkey=peer_pubkey,
        peer_signature=peer_signature,
        suspicion_score=12.5,
        classification="CLEAN",
        is_satire=False,
        content_sha256=content_hash,
        simhash_64="aabbccdd11223344",
    )
    assert adopted_audit.id is not None
    assert adopted_audit.node_pubkey == peer_pubkey

    # 3. Another component checks effort avoidance for this URL / hash
    result = await check_mesh_effort_avoidance(
        session=db_session,
        item_url=url,
        content_sha256=content_hash,
        min_peer_quality=0.85,
    )
    # Since it's in local snapshot/audit DB, should return local_cached or mesh_adopted
    assert result.status in ("local_cached", "mesh_adopted")
    assert result.suspicion_score == 12.5


@pytest.mark.asyncio
async def test_feed_worker_sync_single_feed_mock(db_session: AsyncSession):
    """Verify feed worker processes discovered entries and triggers effort avoidance."""
    # Register subscription
    sub = FeedSubscription(
        feed_url="https://mocknews.org/feed.xml",
        title="Mock News",
        priority_tier=2,
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    mock_parsed = ParsedFeed(
        title="Mock News Channel",
        feed_format="rss",
        etag="etag_v1",
        last_modified="Mon, 17 Aug 2026 12:00:00 GMT",
        is_modified=True,
        entries=[
            FeedEntry(
                url="https://mocknews.org/articles/1",
                title="Beekeeping Guide to Protective Apiary Suits",
                summary="Review of breathable veil designs and sting resistance.",
            ),
            FeedEntry(
                url="https://mocknews.org/articles/2",
                title="Canine Behavioral Leash Training Essentials",
                summary="How to train puppies safely without trachea pressure.",
            ),
        ],
    )

    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_parsed

        summary = await sync_single_feed(
            session=db_session,
            subscription=sub,
            dry_run=False,
            evaluate_novel=False,
        )

        assert summary.total_feeds_polled == 1
        assert summary.new_items_discovered == 2
        assert sub.etag == "etag_v1"

        # Check records in FeedItem
        stmt_items = select(FeedItem).where(FeedItem.feed_id == sub.id)
        items = (await db_session.exec(stmt_items)).all()
        assert len(items) == 2

        item_subjects = {i.subject_id for i in items}
        assert any("apiculture" in s for s in item_subjects)
        assert any("veterinary.canine" in s for s in item_subjects)
