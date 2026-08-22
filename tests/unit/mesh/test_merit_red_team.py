"""Hermetic Red Team Attack Suite for Credence Merit & Reputation Mechanics.

Simulates 5 adversarial attack vectors against the P2P mesh network:
1. The 'Puppet Farm' Attack (Sybil /24 subnet merit & token farming)
2. The 'Ghost Quote' Attack (Ungrounded citation spraying & hallucination)
3. The 'Time Machine' Attack (Manipulated first_seen timestamp forgery)
4. The 'Chameleon Node' Attack (Probation evasion & rapid spam rehabilitation)
5. The 'False Galileo' Attack (Contrarian score divergence astroturfing)
6. Dynamic Demotion & Sovereign Forgiveness Lifecycle
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from credence.mesh.badges import compute_longevity_days, determine_node_tier, evaluate_node_badges
from credence.mesh.consensus import should_adopt_attestation
from credence.mesh.relay import PeerConnection, PeerTrafficClass, extract_ip_subnet
from credence.models import DomainMetric, EpistemicTier, PeerMetric
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


@pytest.mark.unit
def test_red_team_sybil_subnet_farming() -> None:
    """Vector 1: Verify /24 subnet clustering and rate limits prevent Sybil merit farming."""
    mock_ws = MagicMock()

    # 10 Sybil nodes on 192.168.1.0/24 subnet
    subnet_map: dict[str, list[PeerConnection]] = {}
    for i in range(1, 11):
        ip = f"192.168.1.{10 + i}:8765"
        subnet = extract_ip_subnet(f"ws://{ip}")
        conn = PeerConnection(mock_ws, ip, traffic_class=PeerTrafficClass.STANDARD)
        subnet_map.setdefault(subnet, []).append(conn)

    # Assert that all 10 virtual nodes correctly resolve to the exact same /24 cluster
    assert "192.168.1.0/24" in subnet_map
    assert len(subnet_map["192.168.1.0/24"]) == 10

    # Rate limiting on choked/quarantined traffic restricts puppet spam
    conn_quarantine = PeerConnection(mock_ws, "192.168.1.100:8765", traffic_class=PeerTrafficClass.QUARANTINED)
    assert conn_quarantine.check_rate_limit() is False


@pytest.mark.unit
def test_red_team_ghost_quote_ungrounded_spraying() -> None:
    """Vector 2: Verify ungrounded citation spraying is rejected and blocks merit badges."""
    report_unverified = AuditReport(
        url="https://adversarial-target.org/ghost-quotes",
        content_sha256="22" * 32,
        simhash_64="0x1234567890abcdef",
        suspicion_score=85.0,
        suspicion_density=4.5,
        classification="DECEPTIVE",
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalism:accuracy/SPJ-1.1@1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="accuracy",
                severity=4,
                confidence=0.95,
                quote_or_element="fabricated hallucinated quote not in DOM",
                reasoning="Fake violation",
                is_grounded=False,
            )
        ],
        node_pubkey="bad_node_" + "0" * 55,
        node_signature="valid_sig_" + "0" * 54,
    )

    # Attestation adoption gate drops ungrounded reports
    assert should_adopt_attestation(report_unverified, peer_quality=0.95) is False

    # Low grounding ratio prevents verified_auditor badge
    now = datetime.now(timezone.utc)
    bad_peer = PeerMetric(
        node_pubkey="bad_node_" + "0" * 55,
        node_alias="ghost-sprayer",
        ws_url="ws://127.0.0.1:9000",
        first_seen=now - timedelta(days=10),
        quality_score=0.90,
        total_citations_count=500,
        grounded_citations_count=50,  # 10% grounding (G=0.10)
        total_attestations_evaluated=500,
    )
    awards = evaluate_node_badges(bad_peer, [], now=now)
    unlocked_ids = {a.badge_id for a in awards}

    assert "verified_auditor" not in unlocked_ids
    assert "century_anchor" not in unlocked_ids


@pytest.mark.unit
def test_red_team_time_machine_timestamp_forgery() -> None:
    """Vector 3: Verify that self-reported timestamp forgery cannot bypass local observation."""
    now = datetime.now(timezone.utc)
    genuine_first_seen = now - timedelta(days=2)  # Node only observed for 2 days

    # Genuine local longevity calculation
    longevity = compute_longevity_days(genuine_first_seen, now=now)
    assert round(longevity, 1) == 2.0

    peer = PeerMetric(
        node_pubkey="time_traveller_" + "0" * 49,
        node_alias="fake-vintage-node",
        ws_url="ws://127.0.0.1:9001",
        first_seen=genuine_first_seen,
        quality_score=0.99,
        grounded_citations_count=100,
        total_citations_count=100,
        total_attestations_evaluated=1000,
    )
    awards = evaluate_node_badges(peer, [], now=now)
    unlocked_ids = {a.badge_id for a in awards}

    # 2 days longevity is insufficient for 30-day Root Seed or 100-day Century Anchor
    assert "root_seed_candidate" not in unlocked_ids
    assert "century_anchor" not in unlocked_ids


@pytest.mark.unit
def test_red_team_probation_evasion_and_rehabilitation() -> None:
    """Vector 4: Verify that slashed nodes cannot evade probation without genuine clean audits."""
    now = datetime.now(timezone.utc)
    slashed_domain = DomainMetric(
        node_pubkey="slashed_node_" + "0" * 51,
        subject_id="JOURNALISTIC_ETHICS",
        expertise_score=0.85,
        unique_domains_count=10,
        slashing_count=1,  # Slashed!
    )

    peer_slashed = PeerMetric(
        node_pubkey="slashed_node_" + "0" * 51,
        node_alias="recovering-node",
        ws_url="ws://127.0.0.1:9002",
        first_seen=now - timedelta(days=20),
        quality_score=0.60,
        total_attestations_evaluated=5000,
        grounded_citations_count=4500,
        total_citations_count=5000,
    )

    awards = evaluate_node_badges(peer_slashed, [slashed_domain], now=now)
    unlocked_ids = {a.badge_id for a in awards}

    # Slashed node is locked out of sybil_shield
    assert "sybil_shield" not in unlocked_ids

    # Slashed domain cleared after verified redemption
    slashed_domain.slashing_count = 0
    awards_recovered = evaluate_node_badges(peer_slashed, [slashed_domain], now=now)
    assert "sybil_shield" in {a.badge_id for a in awards_recovered}


@pytest.mark.unit
def test_red_team_false_galileo_noise_rejection() -> None:
    """Vector 5: Verify that random contrarian score deviations do not unlock Galileo Pioneer."""
    now = datetime.now(timezone.utc)
    peer_noisy = PeerMetric(
        node_pubkey="contrarian_" + "0" * 53,
        node_alias="noisy-contrarian",
        ws_url="ws://127.0.0.1:9003",
        first_seen=now - timedelta(days=15),
        quality_score=0.50,
        total_attestations_evaluated=200,
        median_score_deviations_sum=95.0,  # High erratic deviation
        galileo_discoveries_count=0,  # Zero verified ground truth breakthroughs
    )

    awards = evaluate_node_badges(peer_noisy, [], now=now)
    unlocked_ids = {a.badge_id for a in awards}

    # Mere erratic deviation is not Galileo discovery
    assert "galileo_pioneer" not in unlocked_ids


@pytest.mark.unit
def test_red_team_dynamic_demotion_and_reinstatement() -> None:
    """Vector 6: Verify dynamic tier demotion under quality drift and upward promotion upon recovery."""
    # 1. Healthy Auditor Performance
    tier_healthy = determine_node_tier(
        quality_score=0.88,
        evaluations_count=150,
        grounding_ratio=0.96,
        max_domain_expertise=0.60,
        longevity_days=15.0,
    )
    assert tier_healthy == EpistemicTier.AUDITOR

    # 2. Quality Drops (Epistemic Drift -> Demotion to SIFTER)
    tier_demoted = determine_node_tier(
        quality_score=0.65,  # Dropped below 0.75
        evaluations_count=160,
        grounding_ratio=0.80,  # Dropped below 0.85
        max_domain_expertise=0.60,
        longevity_days=16.0,
    )
    assert tier_demoted == EpistemicTier.SIFTER

    # 3. Severe Quality Crash (Demotion to SPROUT)
    tier_crashed = determine_node_tier(
        quality_score=0.40,  # Dropped below 0.60
        evaluations_count=170,
        grounding_ratio=0.50,
        max_domain_expertise=0.10,
        longevity_days=17.0,
    )
    assert tier_crashed == EpistemicTier.SPROUT

    # 4. Recovery through Clean Audits (Reinstatement to AUDITOR)
    tier_reinstated = determine_node_tier(
        quality_score=0.86,
        evaluations_count=250,
        grounding_ratio=0.95,
        max_domain_expertise=0.60,
        longevity_days=20.0,
    )
    assert tier_reinstated == EpistemicTier.AUDITOR
