"""Hermetic Unit Tests for Feed Sifter Sharding & Morning Digest Generation."""

from datetime import datetime, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.digest import generate_morning_digest
from credence.feeds.worker import (
    PRESET_FEED_CATALOGS,
    bootstrap_preset_feeds,
    compute_feed_affinity,
)
from credence.models import Audit, Snapshot, Violation


def test_rendezvous_hashing_affinity():
    """Verify deterministic Rendezvous Hashing (HRW) partition scores."""
    pubkey_node1 = "ed25519:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    pubkey_node2 = "ed25519:9999991234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    feed_url = "https://www.propublica.org/feeds/propublica/main"

    score1 = compute_feed_affinity(pubkey_node1, feed_url)
    score2 = compute_feed_affinity(pubkey_node2, feed_url)

    assert 0.0 <= score1 <= 1.0
    assert 0.0 <= score2 <= 1.0
    # Must be deterministic
    assert score1 == compute_feed_affinity(pubkey_node1, feed_url)
    # Different node pubkeys produce different affinity weights
    assert score1 != score2


@pytest.mark.asyncio
async def test_bootstrap_preset_feeds(db_session: AsyncSession):
    """Verify categorized feed preset bootstrapping."""
    # Bootstrap investigative tech
    added_tech = await bootstrap_preset_feeds(db_session, category="investigative-tech")
    assert added_tech == len(PRESET_FEED_CATALOGS["investigative-tech"])

    # Verify idempotency
    added_again = await bootstrap_preset_feeds(db_session, category="investigative-tech")
    assert added_again == 0


@pytest.mark.asyncio
async def test_morning_digest_generation(db_session: AsyncSession):
    """Verify Morning Digest aggregates and categorizes clean vs flagged items."""
    now = datetime.now(timezone.utc)

    # Insert mock snapshots
    snap_clean = Snapshot(
        url="https://example.org/clean-investigation",
        content_sha256="sha256:clean1",
        simhash_64="0x1111",
        title="Clean Investigative Report",
    )
    snap_deceptive = Snapshot(
        url="https://example.org/fake-miracle-cure",
        content_sha256="sha256:fake1",
        simhash_64="0x2222",
        title="Fake Miracle Cure Article",
    )
    db_session.add(snap_clean)
    db_session.add(snap_deceptive)
    await db_session.commit()
    await db_session.refresh(snap_clean)
    await db_session.refresh(snap_deceptive)

    # Insert mock audits
    audit_clean = Audit(
        snapshot_id=snap_clean.id,  # type: ignore[arg-type]
        content_sha256=snap_clean.content_sha256,
        audited_at=now,
        suspicion_score=4.2,
        classification="CLEAN",
        is_satire=False,
    )
    audit_deceptive = Audit(
        snapshot_id=snap_deceptive.id,  # type: ignore[arg-type]
        content_sha256=snap_deceptive.content_sha256,
        audited_at=now,
        suspicion_score=88.5,
        classification="DECEPTIVE",
        is_satire=False,
    )
    db_session.add(audit_clean)
    db_session.add(audit_deceptive)
    await db_session.commit()
    await db_session.refresh(audit_deceptive)

    # Insert violation for deceptive article
    violation = Violation(
        audit_id=audit_deceptive.id,  # type: ignore[arg-type]
        rule_id="SPJ-1.1",
        rule_uri="ethics:accuracy/unverified_allegation@v1",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="accuracy",
        severity=5,
        confidence=1.0,
        quote_or_element="Doctors hate this one secret cure",
        reasoning="Medical misinformation",
    )
    db_session.add(violation)
    await db_session.commit()

    # Generate digest
    digest = await generate_morning_digest(db_session, timeframe_hours=24)
    assert digest.total_articles_evaluated >= 2
    assert digest.clean_articles_count >= 1
    assert digest.flagged_articles_count >= 1

    md_output = digest.to_markdown()
    assert "# 🌅 Credence Morning Epistemic Digest" in md_output
    assert "Clean Investigative Report" in md_output or "clean-investigation" in md_output
    assert "SPJ-1.1" in md_output


@pytest.mark.asyncio
async def test_sifter_cycle_and_telemetry(db_session: AsyncSession):
    """Verify autonomous sifting cycle and database telemetry tracking."""
    from unittest.mock import AsyncMock, patch

    from credence.feeds.parser import ParsedFeed
    from credence.feeds.sifter import get_sifter_status, run_sifting_cycle

    # Mock feed parser to return hermetic offline entries
    mock_feed = ParsedFeed(
        title="ProPublica Main",
        is_modified=True,
        entries=[],
    )

    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock, return_value=mock_feed):
        # Bootstrap presets
        await bootstrap_preset_feeds(db_session)

        # Execute sifter cycle with auto_audit=False (dry_run)
        summary = await run_sifting_cycle(db_session, auto_audit=False)
        assert summary.total_feeds_polled >= 1

        # Check sifter status telemetry
        telemetry = await get_sifter_status(db_session)
        assert telemetry["status"] == "online"
        assert telemetry["active_feed_subscriptions"] >= 1
