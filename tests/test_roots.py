"""Hermetic Unit Tests for Epistemic Root Expansion Engine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.discovery import DiscoveredFeedCandidate
from credence.feeds.parser import FeedEntry, ParsedFeed
from credence.feeds.roots import (
    _is_candidate_eligible,
    _normalize_domain,
    expand_roots,
    extract_root_candidates,
    get_root_tree,
)
from credence.models import AuditRecord, FeedItemRecord, FeedSubscriptionRecord, SnapshotRecord, utc_now


@pytest.mark.unit
def test_candidate_domain_filtering_and_normalization():
    """Verify domain normalization, social filtering, and SSRF rejection."""
    assert _normalize_domain("https://www.reuters.com/world/news") == "reuters.com"
    assert _normalize_domain("nature.com/articles/123") == "nature.com"
    assert _normalize_domain("http://sub.domain.org/path") == "sub.domain.org"

    # Social and CDN domains must be excluded
    assert not _is_candidate_eligible("twitter.com")
    assert not _is_candidate_eligible("x.com")
    assert not _is_candidate_eligible("t.co")
    assert not _is_candidate_eligible("bit.ly")
    assert not _is_candidate_eligible("cdn.ampproject.org")

    # SSRF / internal hostnames must be excluded
    assert not _is_candidate_eligible("169.254.169.254")
    assert not _is_candidate_eligible("localhost")
    assert not _is_candidate_eligible("metadata.google.internal")

    # Legitimate domains are eligible
    assert _is_candidate_eligible("reuters.com")
    assert _is_candidate_eligible("nature.com")
    assert _is_candidate_eligible("inmaricopa.com")


@pytest.mark.unit
async def test_extract_root_candidates_from_clean_snapshots(db_session: AsyncSession, tmp_path: Path):
    """Verify candidate root domains are extracted from clean parent article citations."""
    dom_file = tmp_path / "article_clean.html"
    dom_file.write_text(
        """
        <html><body>
          <h1>Groundbreaking Solar Efficiency Breakthrough</h1>
          <p>Researchers published findings in <a href="https://nature.com/articles/solar-2026">Nature</a>.</p>
          <p>Confirmation reported by <a href="https://reuters.com/business/energy/solar">Reuters Energy</a>.</p>
          <p>Discussion on <a href="https://twitter.com/science/status/123">Twitter</a>.</p>
          <p>Metadata probe at <a href="http://169.254.169.254/latest/meta-data/">Cloud Metadata</a>.</p>
        </body></html>
        """,
        encoding="utf-8",
    )

    snap = SnapshotRecord(
        url="https://sciencedaily.com/releases/2026/solar-breakthrough",
        content_sha256="sha256:1111222233334444555566667777888899990000aaaaabbbbbcccccdddddeeeee",
        simhash_64="0x1234567890abcdef",
        dom_file_path=str(dom_file),
        title="Solar Breakthrough 2026",
    )
    db_session.add(snap)
    await db_session.commit()
    await db_session.refresh(snap)

    audit = AuditRecord(
        snapshot_id=snap.id,
        content_sha256=snap.content_sha256,
        suspicion_score=10.0,
        classification="CLEAN",
        confidence_score=0.98,
        audited_at=utc_now(),
    )
    db_session.add(audit)
    await db_session.commit()

    # Extract candidates
    candidates = await extract_root_candidates(db_session, min_parent_score=75.0, limit=10, allow_local=False)
    domains = [c.domain for c in candidates]

    # Valid research/news domains are present
    assert "nature.com" in domains
    assert "reuters.com" in domains

    # Social and SSRF links must be filtered out
    assert "twitter.com" not in domains
    assert "169.254.169.254" not in domains


@pytest.mark.unit
async def test_expand_roots_registers_new_subscriptions(db_session: AsyncSession, tmp_path: Path):
    """Verify autonomous root expansion discovers endpoints and registers subscriptions."""
    dom_file = tmp_path / "investigative.html"
    dom_file.write_text(
        """
        <html><body>
          <p>Primary court filings reviewed by <a href="https://courtwatch.org/cases/2026">Court Watch</a>.</p>
        </body></html>
        """,
        encoding="utf-8",
    )

    snap = SnapshotRecord(
        url="https://propublica.org/article/judicial-ethics",
        content_sha256="sha256:2222333344445555666677778888999900001111bbbbbcccccdddddeeeeefffff",
        simhash_64="0xabcdef1234567890",
        dom_file_path=str(dom_file),
        title="Judicial Ethics Review",
    )
    db_session.add(snap)
    await db_session.commit()
    await db_session.refresh(snap)

    audit = AuditRecord(
        snapshot_id=snap.id,
        content_sha256=snap.content_sha256,
        suspicion_score=8.0,
        classification="CLEAN",
        confidence_score=0.99,
        audited_at=utc_now(),
    )
    db_session.add(audit)
    await db_session.commit()

    mock_discovered = [
        DiscoveredFeedCandidate(
            feed_url="https://courtwatch.org/feed.xml",
            title="Court Watch Docket Feed",
            feed_type="rss",
            source_url="https://courtwatch.org",
            base_domain="courtwatch.org",
            is_verified=True,
        )
    ]

    mock_parsed = ParsedFeed(
        feed_format="rss",
        title="Court Watch Docket Feed",
        is_modified=True,
        etag="W/'abc123'",
        last_modified="Mon, 18 Aug 2026 12:00:00 GMT",
        entries=[
            FeedEntry(
                url="https://courtwatch.org/cases/2026/brief-01",
                title="Federal Appeals Court Brief Filed",
                summary="Appellate review of administrative jurisdiction.",
                published_at=utc_now(),
            )
        ],
    )

    with (
        patch("credence.feeds.roots.discover_feed_endpoints", new=AsyncMock(return_value=mock_discovered)),
        patch("credence.feeds.roots.fetch_and_parse_feed", new=AsyncMock(return_value=mock_parsed)),
    ):
        summary = await expand_roots(session=db_session, max_new_sources=1, min_citation_count=1, dry_run=False)

        assert summary.new_feeds_subscribed == 1
        assert summary.initial_items_harvested == 1

        # Verify in database
        stmt_sub = select(FeedSubscriptionRecord).where(
            FeedSubscriptionRecord.feed_url == "https://courtwatch.org/feed.xml"
        )
        sub = (await db_session.exec(stmt_sub)).first()
        assert sub is not None
        assert sub.title == "Court Watch Docket Feed"
        assert sub.is_active is True

        stmt_item = select(FeedItemRecord).where(
            FeedItemRecord.item_url == "https://courtwatch.org/cases/2026/brief-01"
        )
        item = (await db_session.exec(stmt_item)).first()
        assert item is not None
        assert item.processing_status == "pending"


@pytest.mark.unit
async def test_get_root_tree_structure(db_session: AsyncSession):
    """Verify hierarchical root tree generation."""
    sub = FeedSubscriptionRecord(
        feed_url="https://testscience.org/feed",
        title="Test Science News",
        priority_tier=1,
        is_active=True,
    )
    db_session.add(sub)
    await db_session.commit()

    tree = await get_root_tree(db_session)
    assert tree["total_active_roots"] >= 1
    assert any(r["feed_url"] == "https://testscience.org/feed" for r in tree["active_roots"])
    assert "pending_citation_candidates" in tree
