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


def test_svg_badge_generation_strict_xml_and_styles() -> None:
    """Verify strict XML ElementTree parseability, visual styles, and metadata across styles."""
    import xml.etree.ElementTree as ET

    # Test glass style (Doc header style)
    svg_glass = generate_svg_badge(
        badge_id="verified_auditor",
        node_alias="anchor-us-central1",
        score_or_val="100.0 Clean",
        style="glass",
        theme="dark",
    )
    root_glass = ET.fromstring(svg_glass)
    assert root_glass.tag == "{http://www.w3.org/2000/svg}svg" or root_glass.tag.endswith("svg")
    assert "anchor-us-central1" in svg_glass
    assert "100.0 Clean" in svg_glass
    assert int(root_glass.attrib["height"]) == 28

    # Test pill style
    svg_pill = generate_svg_badge(
        badge_id="root_seed_candidate",
        node_alias="anchor-us-central1",
        score_or_val="0.985",
        style="pill",
        theme="dark",
    )
    root_pill = ET.fromstring(svg_pill)
    assert root_pill.tag == "{http://www.w3.org/2000/svg}svg" or root_pill.tag.endswith("svg")
    assert "anchor-us-central1" in svg_pill
    assert "0.985" in svg_pill
    assert int(root_pill.attrib["height"]) == 28
    assert int(root_pill.attrib["width"]) > 100

    # Test shield style
    svg_shield = generate_svg_badge(
        badge_id="verified_auditor",
        node_alias="sifter-node-09",
        score_or_val="99.4%",
        style="shield",
        theme="midnight",
    )
    root_shield = ET.fromstring(svg_shield)
    assert root_shield.tag == "{http://www.w3.org/2000/svg}svg" or root_shield.tag.endswith("svg")
    assert "sifter-node-09" in svg_shield
    assert "99.4%" in svg_shield
    assert int(root_shield.attrib["height"]) == 28


def test_svg_badge_8_registry_matrix() -> None:
    """Verify all 8 official badges and fallbacks generate valid, well-formed XML across styles."""
    import xml.etree.ElementTree as ET

    for badge_id, badge_info in BADGE_REGISTRY.items():
        for style in ["glass", "pill", "shield"]:
            for theme in ["dark", "midnight", "light"]:
                svg = generate_svg_badge(
                    badge_id=badge_id,
                    node_alias=f"node-{badge_id}",
                    score_or_val="VERIFIED",
                    style=style,
                    theme=theme,
                )
                tree = ET.fromstring(svg)
                assert tree.tag.endswith("svg")
                assert badge_info.name in svg or badge_id.replace("_", " ").title() in svg

    # Test unknown fallback badge_id
    fallback_svg = generate_svg_badge(badge_id="custom_pioneer_tier", node_alias="custom-node", score_or_val="TIER 1")
    fallback_tree = ET.fromstring(fallback_svg)
    assert fallback_tree.tag.endswith("svg")
    assert "Custom Pioneer Tier" in fallback_svg


def test_svg_badge_xml_escaping_and_fuzzing() -> None:
    """Verify robust XML sanitization against special characters and injection payloads."""
    import xml.etree.ElementTree as ET

    malicious_aliases = [
        "Node & Co. <script>alert('pwn')</script>",
        'Quote "Test" & Ampersand',
        "Special < > & ' \" Chars",
        "Emoji 🚀 & Symbols <>",
    ]
    for alias in malicious_aliases:
        svg = generate_svg_badge(
            badge_id="sybil_shield",
            node_alias=alias,
            score_or_val="G=1.00 & 100%",
            style="pill",
        )
        # ElementTree will raise ParseError if XML escaping is broken
        tree = ET.fromstring(svg)
        assert tree.tag.endswith("svg")


def test_svg_badge_dynamic_width_boundaries() -> None:
    """Verify text width calculation for extreme short and long strings without crashing or clipping."""
    import xml.etree.ElementTree as ET

    # Extreme short
    svg_short = generate_svg_badge(badge_id="sprout_node", node_alias="N", score_or_val="1")
    tree_short = ET.fromstring(svg_short)
    w_short = int(tree_short.attrib["width"])
    assert w_short > 50

    # Extreme long
    long_alias = "extremely-long-sovereign-decentralized-validator-node-cluster-alias-primary"
    long_val = "UNLOCKED_WITH_100_PERCENT_GROUNDING_AND_ZERO_FAILURES"
    svg_long = generate_svg_badge(badge_id="root_seed_candidate", node_alias=long_alias, score_or_val=long_val)
    tree_long = ET.fromstring(svg_long)
    w_long = int(tree_long.attrib["width"])
    assert w_long > 400


def test_publisher_svg_badge_generation() -> None:
    """Verify publisher trust badges produce well-formed XML and reflect DCI scores and bands."""
    import xml.etree.ElementTree as ET

    from credence.subjects.weather import generate_publisher_svg_badge

    for score, expected_band in [(95.0, "PRISTINE"), (75.0, "CLEAN"), (40.0, "SUSPICIOUS")]:
        for style in ["pill", "shield"]:
            svg = generate_publisher_svg_badge(
                domain="reuters.com",
                dci_score=score,
                status=expected_band,
                style=style,
            )
            tree = ET.fromstring(svg)
            assert tree.tag.endswith("svg")
            assert "reuters.com" in svg
            assert expected_band in svg


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
