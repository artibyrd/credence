"""Hermetic unit tests for Epistemic Merit and Leaderboard functionality.

Covers:
- 8 badge evaluation criteria
- 5 epistemic tier transitions
- Shields.io compatible dynamic SVG badge generation
- Multi-category leaderboards (quality, subjects, philanthropy, galileo, teams)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.mesh.merit import (
    BADGE_REGISTRY,
    EpistemicTier,
    determine_node_tier,
    evaluate_node_badges,
    generate_svg_badge,
    get_leaderboard,
)
from credence.models import DomainMetric, PeerMetric


def test_badge_registry_completeness() -> None:
    """Verify all 8 expected merit badges exist in BADGE_REGISTRY."""
    expected_ids = {
        "sprout_node",
        "sifter_pioneer",
        "verified_auditor",
        "domain_specialist",
        "philanthropic_relay",
        "root_seed_candidate",
        "galileo_pioneer",
        "sybil_shield",
    }
    assert set(BADGE_REGISTRY.keys()) == expected_ids
    for b in BADGE_REGISTRY.values():
        assert b.badge_id
        assert b.name
        assert b.icon
        assert b.description
        assert isinstance(b.tier, EpistemicTier)


def test_badge_evaluation_logic() -> None:
    """Verify criteria for unlocking each badge."""
    now = datetime.now(timezone.utc)
    peer = PeerMetric(
        node_pubkey="99" * 32,
        node_alias="test-node",
        ws_url="ws://127.0.0.1:8765",
        first_seen=now - timedelta(days=60),
        total_heartbeats_sent=500,
        successful_heartbeats=498,
        total_attestations_evaluated=150,
        grounded_citations_count=150,
        total_citations_count=150,
        has_valid_catalog_hashes=True,
        quality_score=0.95,
        is_seed_candidate=True,
        tokens_seeded_count=1_500_000,
        galileo_discoveries_count=2,
        ip_subnet="192.168.1.0/24",
    )

    domain_records = [
        DomainMetric(
            node_pubkey="99" * 32,
            subject_id=f"subject.{i}",
            evaluations_count=20,
            grounded_quotes_count=20,
            total_quotes_count=20,
            unique_domains_count=6,
            expertise_score=0.85,
        )
        for i in range(5)
    ]

    unlocked = evaluate_node_badges(
        peer_record=peer,
        domain_records=domain_records,
        feed_items_count=10,
        now=now,
    )

    badge_ids = {b.badge_id for b in unlocked}
    assert "sprout_node" in badge_ids
    assert "sifter_pioneer" in badge_ids
    assert "verified_auditor" in badge_ids
    assert "philanthropic_relay" in badge_ids
    assert "root_seed_candidate" in badge_ids
    assert "galileo_pioneer" in badge_ids
    assert "domain_specialist" in badge_ids


def test_epistemic_tier_progression() -> None:
    """Verify tier progression from SPROUT -> SIFTER -> AUDITOR -> SPECIALIST -> ROOT_ANCHOR."""
    # 1. Sprout (0 audits)
    assert (
        determine_node_tier(
            quality_score=0.5, evaluations_count=0, grounding_ratio=0.0, max_domain_expertise=0.0, longevity_days=1.0
        )
        == EpistemicTier.SPROUT
    )

    # 2. Sifter (10 audits, quality > 0.60)
    assert (
        determine_node_tier(
            quality_score=0.65, evaluations_count=15, grounding_ratio=0.70, max_domain_expertise=0.0, longevity_days=2.0
        )
        == EpistemicTier.SIFTER
    )

    # 3. Auditor (50 audits, quality > 0.75, grounding > 0.85)
    assert (
        determine_node_tier(
            quality_score=0.80,
            evaluations_count=60,
            grounding_ratio=0.90,
            max_domain_expertise=0.50,
            longevity_days=10.0,
        )
        == EpistemicTier.AUDITOR
    )

    # 4. Specialist (max domain expertise >= 0.80)
    assert (
        determine_node_tier(
            quality_score=0.80,
            evaluations_count=60,
            grounding_ratio=0.90,
            max_domain_expertise=0.85,
            longevity_days=15.0,
        )
        == EpistemicTier.SPECIALIST
    )

    # 5. Root Anchor (quality >= 0.85, longevity >= 30d, grounding >= 0.80)
    assert (
        determine_node_tier(
            quality_score=0.95,
            evaluations_count=120,
            grounding_ratio=0.95,
            max_domain_expertise=0.90,
            longevity_days=45.0,
        )
        == EpistemicTier.ROOT_ANCHOR
    )


def test_svg_badge_generation() -> None:
    """Verify Shields.io compatible SVG generation."""
    svg = generate_svg_badge(
        badge_id="root_seed_candidate",
        node_alias="anchor-us-central1",
        score_or_val="0.985",
        theme="dark",
    )
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "anchor-us-central1" in svg
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    # Light theme
    svg_light = generate_svg_badge(
        badge_id="sprout_node",
        node_alias="my-node",
        score_or_val="ACTIVE",
        theme="light",
    )
    assert svg_light.startswith("<svg")
    assert "my-node" in svg_light


@pytest.mark.asyncio
async def test_leaderboard_multi_categories_and_teams(db_session: AsyncSession) -> None:
    """Verify leaderboards support quality, philanthropy, galileo, and team filtering."""
    now = datetime.now(timezone.utc)
    # Node 1: Team Alpha, high quality, low tokens
    n1 = PeerMetric(
        node_pubkey="11" * 32,
        node_alias="alpha-node",
        team_tag="alpha-team",
        ws_url="ws://127.0.0.1:8765",
        first_seen=now - timedelta(days=10),
        total_heartbeats_sent=200,
        successful_heartbeats=198,
        total_attestations_evaluated=50,
        grounded_citations_count=50,
        total_citations_count=50,
        has_valid_catalog_hashes=True,
        traffic_class="FAST_LANE",
        tokens_seeded_count=1000,
        galileo_discoveries_count=0,
    )
    # Node 2: Team Beta, lower quality, very high tokens (philanthropy champion)
    n2 = PeerMetric(
        node_pubkey="22" * 32,
        node_alias="beta-node",
        team_tag="beta-team",
        ws_url="ws://127.0.0.1:8766",
        first_seen=now - timedelta(days=5),
        total_heartbeats_sent=100,
        successful_heartbeats=90,
        total_attestations_evaluated=20,
        grounded_citations_count=18,
        total_citations_count=20,
        has_valid_catalog_hashes=True,
        traffic_class="STANDARD",
        tokens_seeded_count=50000,
        galileo_discoveries_count=3,
    )
    db_session.add_all([n1, n2])
    await db_session.commit()

    # Quality category: n1 wins
    lb_q = await get_leaderboard(db_session, category="quality")
    assert lb_q[0].node_alias == "alpha-node"

    # Philanthropy category: n2 wins
    lb_p = await get_leaderboard(db_session, category="philanthropy")
    assert lb_p[0].node_alias == "beta-node"
    assert lb_p[0].score == 50000

    # Galileo category: n2 wins
    lb_g = await get_leaderboard(db_session, category="galileo")
    assert lb_g[0].node_alias == "beta-node"
    assert lb_g[0].score == 3

    # Team filtering: alpha-team only returns alpha-node
    lb_team = await get_leaderboard(db_session, category="quality", team_filter="alpha-team")
    assert len(lb_team) == 1
    assert lb_team[0].node_alias == "alpha-node"
