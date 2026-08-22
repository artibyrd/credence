"""Hermetic unit tests for Web Epistemic Analytics and Intelligence.

Covers:
- Domain Credence Index (DCI) calculation & trust banding
- Domain Leaderboards (Honor Roll vs Wall of Shame vs Astroturf)
- Top 10 Violated Rules aggregation across snapshot violations
- Global Epistemic Weather macro barometer
- Community Verification Bounties
- Publisher Trust SVG Badge Generation
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import Audit, FeedSubscription, Snapshot, Violation
from credence.subjects.analytics import (
    generate_publisher_svg_badge,
    get_community_bounties,
    get_domain_leaderboard,
    get_global_epistemic_weather,
    get_top_violated_rules,
)


@pytest.mark.asyncio
async def test_domain_epistemic_index_and_leaderboards(db_session: AsyncSession) -> None:
    """Verify DEI calculations, Honor Roll (best), and Wall of Shame (worst)."""
    now = datetime.now(timezone.utc)

    # 1. Clean snapshots for reuters.com (low suspicion)
    s1 = Snapshot(
        url="https://reuters.com/news/article1",
        title="Reuters News Article",
        byline="Jane Doe, Senior Reporter",
        content_sha256="11" * 32,
        simhash_64=12345,
        captured_at=now,
    )
    db_session.add(s1)
    await db_session.flush()

    a1 = Audit(
        snapshot_id=s1.id,
        evaluator_version="0.1.0",
        content_sha256="11" * 32,
        suspicion_score=5.0,
        classification="CLEAN",
        evaluation_method="llm_agent",
        created_at=now,
    )
    db_session.add(a1)

    # 2. Deceptive snapshots for shady-news.biz (high suspicion + violations)
    s2 = Snapshot(
        url="https://shady-news.biz/clickbait",
        title="Sensationalist Clickbait",
        content_sha256="22" * 32,
        simhash_64=67890,
        captured_at=now,
    )
    db_session.add(s2)
    await db_session.flush()

    a2 = Audit(
        snapshot_id=s2.id,
        evaluator_version="0.1.0",
        content_sha256="22" * 32,
        suspicion_score=85.0,
        classification="DECEPTIVE",
        evaluation_method="llm_agent",
        created_at=now,
    )
    db_session.add(a2)
    await db_session.flush()

    v2 = Violation(
        audit_id=a2.id,
        rule_id="SPJ-1.1",
        rule_uri="journalism:accuracy/SPJ-1.1@1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="accuracy",
        severity=4,
        confidence=0.95,
        quote_or_element="Shocking cure discovered!",
        reasoning="Unverified health claim",
    )
    db_session.add(v2)
    await db_session.commit()

    # Query Honor Roll (best)
    honor_roll = await get_domain_leaderboard(db_session, category="best")
    assert len(honor_roll) >= 2
    assert honor_roll[0].domain == "reuters.com"
    assert honor_roll[0].dci_score >= 80.0
    assert honor_roll[0].trust_band in ("HIGH_INTEGRITY", "PRISTINE")

    # Query Wall of Shame (worst)
    wall_of_shame = await get_domain_leaderboard(db_session, category="worst")
    assert len(wall_of_shame) >= 2
    assert wall_of_shame[0].domain == "shady-news.biz"
    assert wall_of_shame[0].dci_score <= 50.0
    assert wall_of_shame[0].trust_band in ("LOW_INTEGRITY", "DECEPTIVE", "SUSPICIOUS")


@pytest.mark.asyncio
async def test_top_violated_rules_aggregation(db_session: AsyncSession) -> None:
    """Verify Top 10 violated rules aggregation and excerpt extraction."""
    now = datetime.now(timezone.utc)

    s = Snapshot(
        url="https://example.com/test",
        title="Test Article",
        content_sha256="33" * 32,
        simhash_64=11111,
        captured_at=now,
    )
    db_session.add(s)
    await db_session.flush()

    a = Audit(
        snapshot_id=s.id,
        evaluator_version="0.1.0",
        content_sha256="33" * 32,
        suspicion_score=60.0,
        classification="SUSPICIOUS",
        evaluation_method="llm_agent",
        created_at=now,
    )
    db_session.add(a)
    await db_session.flush()

    v1 = Violation(
        audit_id=a.id,
        rule_id="SPJ-1.1",
        rule_uri="journalism:accuracy/SPJ-1.1@1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="accuracy",
        severity=4,
        confidence=0.90,
        quote_or_element="Sample quote 1",
        reasoning="Test explanation 1",
    )
    v2 = Violation(
        audit_id=a.id,
        rule_id="SPJ-1.1",
        rule_uri="journalism:accuracy/SPJ-1.1@1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="accuracy",
        severity=4,
        confidence=0.90,
        quote_or_element="Sample quote 2",
        reasoning="Test explanation 2",
    )
    db_session.add_all([v1, v2])
    await db_session.commit()

    top_rules = await get_top_violated_rules(db_session, limit=5)
    assert len(top_rules) >= 1
    assert top_rules[0].rule_id == "SPJ-1.1"
    assert top_rules[0].total_violations == 2
    assert top_rules[0].example_quote in ("Sample quote 1", "Sample quote 2")


@pytest.mark.asyncio
async def test_global_epistemic_weather_report(db_session: AsyncSession) -> None:
    """Verify macro Epistemic Weather report generation."""
    weather = await get_global_epistemic_weather(db_session)
    assert weather.global_weather_score >= 0.0
    assert weather.global_weather_score <= 100.0
    assert weather.weather_condition is not None
    assert len(weather.categories) >= 1


@pytest.mark.asyncio
async def test_community_bounties(db_session: AsyncSession) -> None:
    """Verify open verification bounties generated from feeds."""
    now = datetime.now(timezone.utc)
    sub = FeedSubscription(
        feed_url="https://news.ycombinator.com/rss",
        title="Hacker News",
        priority_tier=2,
        subject_tag="tech.news",
        last_polled_at=now,
    )
    db_session.add(sub)
    await db_session.commit()

    bounties = await get_community_bounties(db_session, limit=10)
    assert isinstance(bounties, list)
    if bounties:
        assert bounties[0].bounty_id
        assert bounties[0].title
        assert bounties[0].urgency in ("LOW", "NORMAL", "HIGH")


def test_publisher_svg_badge_generation() -> None:
    """Verify publisher trust SVG badge generator."""
    svg = generate_publisher_svg_badge(domain="reuters.com", dci_score=98.5, status="HIGH_INTEGRITY", theme="dark")
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "reuters.com" in svg
    assert "98" in svg
    assert "HIGH_INTEGRITY" in svg
