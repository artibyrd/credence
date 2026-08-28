"""Unit tests for Sentinel Mode anti-abuse defenses, SSRF gateways, and capacity boundaries."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.reputation import get_or_create_domain_reputation
from credence.feeds.sentinel import (
    MAX_ACTIVE_SENTINELS,
    MIN_SENTINEL_INTERVAL_SECONDS,
    compute_sentinel_poll_due,
    list_sentinel_sources,
    set_feed_sentinel_mode,
)
from credence.models import FeedSubscription


@pytest.mark.asyncio
async def test_sentinel_ssrf_rejection(db_session: AsyncSession) -> None:
    """Assert loopback, metadata IPs, and private addresses are rejected under inv-untrusted-ingestion."""
    # 1. Cloud metadata service
    with pytest.raises(ValueError, match="violates untrusted ingestion boundaries"):
        await set_feed_sentinel_mode(db_session, "http://169.254.169.254/latest/meta-data")

    # 2. Localhost / Loopback
    with pytest.raises(ValueError, match="violates untrusted ingestion boundaries"):
        await set_feed_sentinel_mode(db_session, "http://127.0.0.1:8080/feed.xml")

    with pytest.raises(ValueError, match="violates untrusted ingestion boundaries"):
        await set_feed_sentinel_mode(db_session, "http://localhost/rss")

    # 3. Private Class A/B/C subnets
    with pytest.raises(ValueError, match="violates untrusted ingestion boundaries"):
        await set_feed_sentinel_mode(db_session, "http://10.0.1.50/feed")

    with pytest.raises(ValueError, match="violates untrusted ingestion boundaries"):
        await set_feed_sentinel_mode(db_session, "http://192.168.1.1/feed")


@pytest.mark.asyncio
async def test_sentinel_capacity_ceiling(db_session: AsyncSession) -> None:
    """Assert node refuses to activate more than 10 active Sentinel feeds simultaneously."""
    # Register 10 distinct sentinel feeds
    for i in range(MAX_ACTIVE_SENTINELS):
        domain = f"sentinel-source-{i}.org"
        url = f"https://{domain}/feed.xml"
        sub = FeedSubscription(
            feed_url=url,
            title=f"Source {i}",
            priority_tier=1,
            is_active=True,
            is_sentinel=True,
            sentinel_interval_seconds=300,
        )
        db_session.add(sub)
    await db_session.commit()

    # Attempt to activate an 11th sentinel feed
    with pytest.raises(ValueError, match="Sentinel capacity ceiling reached"):
        await set_feed_sentinel_mode(db_session, "https://overflow-source.org/feed.xml")


@pytest.mark.asyncio
async def test_sentinel_minimum_interval_guard(db_session: AsyncSession) -> None:
    """Assert intervals below 60s are clamped to the minimum safety cadence."""
    res = await set_feed_sentinel_mode(
        db_session,
        "https://example-news-outlet.org/rss",
        enabled=True,
        interval_seconds=10,  # Below 60s
    )
    assert res["interval_seconds"] == MIN_SENTINEL_INTERVAL_SECONDS
    assert res["is_sentinel"] is True


@pytest.mark.asyncio
async def test_sentinel_quarantine_integrity(db_session: AsyncSession) -> None:
    """Assert enabling Sentinel Mode on a quarantined domain preserves its quarantine status."""
    domain = "untrusted-adversary.com"
    rep = await get_or_create_domain_reputation(db_session, domain)
    rep.status = "QUARANTINED_PROBATION"
    rep.reputation_score = 12.5
    db_session.add(rep)
    await db_session.commit()

    # Enable sentinel mode on the quarantined domain
    res = await set_feed_sentinel_mode(db_session, f"https://{domain}/feed.xml", enabled=True)
    assert res["is_sentinel"] is True
    assert res["quarantine_status"] == "QUARANTINED_PROBATION"

    # Verify domain reputation record still retains QUARANTINED_PROBATION
    rep_refreshed = await get_or_create_domain_reputation(db_session, domain)
    assert rep_refreshed.status == "QUARANTINED_PROBATION"
    assert rep_refreshed.is_sentinel is True


@pytest.mark.asyncio
async def test_sentinel_enable_disable_lifecycle(db_session: AsyncSession) -> None:
    """Test full enable, list, set-interval, and disable lifecycle for Sentinel Mode."""
    feed_url = "https://inmaricopa.com/feed/"

    # 1. Enable Sentinel
    res_en = await set_feed_sentinel_mode(db_session, feed_url, enabled=True, interval_seconds=300)
    assert res_en["status"] == "enabled"
    assert res_en["domain"] == "inmaricopa.com"
    assert res_en["is_sentinel"] is True

    # 2. List Sentinels
    sentinels = await list_sentinel_sources(db_session)
    assert any(s["domain"] == "inmaricopa.com" and s["is_sentinel"] for s in sentinels)

    # 3. Disable Sentinel
    res_dis = await set_feed_sentinel_mode(db_session, feed_url, enabled=False)
    assert res_dis["status"] == "disabled"
    assert res_dis["is_sentinel"] is False


def test_compute_sentinel_poll_due() -> None:
    """Test sentinel poll due calculation with UTC datetime awareness."""
    now = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    # Never polled before -> Due immediately
    sub_new = FeedSubscription(
        feed_url="https://target.com/feed",
        is_active=True,
        is_sentinel=True,
        sentinel_interval_seconds=300,
        last_polled_at=None,
    )
    assert compute_sentinel_poll_due(sub_new, now) is True

    # Polled 100 seconds ago (interval 300s) -> Not due
    sub_recent = FeedSubscription(
        feed_url="https://target.com/feed",
        is_active=True,
        is_sentinel=True,
        sentinel_interval_seconds=300,
        last_polled_at=now - timedelta(seconds=100),
    )
    assert compute_sentinel_poll_due(sub_recent, now) is False

    # Polled 350 seconds ago (interval 300s) -> Due
    sub_due = FeedSubscription(
        feed_url="https://target.com/feed",
        is_active=True,
        is_sentinel=True,
        sentinel_interval_seconds=300,
        last_polled_at=now - timedelta(seconds=350),
    )
    assert compute_sentinel_poll_due(sub_due, now) is True

    # Inactive feed -> Never due
    sub_inactive = FeedSubscription(
        feed_url="https://target.com/feed",
        is_active=False,
        is_sentinel=True,
        sentinel_interval_seconds=300,
    )
    assert compute_sentinel_poll_due(sub_inactive, now) is False
