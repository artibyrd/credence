"""Hermetic Unit Tests for 5-Factor Epistemic Node Quality Engine (Q_i)."""

from datetime import datetime, timedelta, timezone

from credence.mesh.quality import (
    NodeMetrics,
    calculate_node_quality,
    rank_nodes,
)


def test_honest_high_uptime_node_quality():
    """Verify that a reliable, grounded, concordant node achieves Q_i >= 0.85 and is marked as seed candidate."""
    now = datetime.now(timezone.utc)
    metrics = NodeMetrics(
        node_pubkey="a" * 64,
        node_alias="honest-validator-1",
        ws_url="ws://10.0.0.1:8765",
        first_seen=now - timedelta(days=120),  # Long-lived identity (>90 days)
        last_seen=now,
        total_heartbeats_sent=1000,
        successful_heartbeats=998,
        average_latency_ms=35.0,
        total_attestations_evaluated=50,
        median_score_deviations_sum=1.5,  # Avg dev: 0.03 points -> C_i ~ 0.999
        grounded_citations_count=120,
        total_citations_count=120,  # 100% grounded -> G_i = 1.0
        has_valid_catalog_hashes=True,  # T_i = 1.0
    )

    score = calculate_node_quality(metrics, now=now)
    assert score.quality_score >= 0.90
    assert score.uptime_factor >= 0.95
    assert score.concordance_factor >= 0.95
    assert score.grounding_factor == 1.0
    assert score.taxonomy_factor == 1.0
    assert score.longevity_factor == 1.0
    assert score.is_seed_candidate is True


def test_flapping_unreliable_node_demotion():
    """Verify that a node with high packet loss and flapping connection is penalized and not a seed candidate."""
    now = datetime.now(timezone.utc)
    metrics = NodeMetrics(
        node_pubkey="b" * 64,
        node_alias="flapping-node-2",
        ws_url="ws://10.0.0.2:8765",
        first_seen=now - timedelta(days=30),
        total_heartbeats_sent=1000,
        successful_heartbeats=400,  # 40% uptime
        average_latency_ms=650.0,
        total_attestations_evaluated=10,
        median_score_deviations_sum=5.0,
        grounded_citations_count=10,
        total_citations_count=10,
        has_valid_catalog_hashes=True,
    )

    score = calculate_node_quality(metrics, now=now)
    assert score.uptime_factor < 0.50
    assert score.quality_score < 0.85
    assert score.is_seed_candidate is False


def test_byzantine_ungrounded_hallucinating_node_demotion():
    """Verify that a node submitting fake/ungrounded citations suffers severe grounding penalties."""
    now = datetime.now(timezone.utc)
    metrics = NodeMetrics(
        node_pubkey="c" * 64,
        node_alias="byzantine-hallucinator-3",
        ws_url="ws://10.0.0.3:8765",
        first_seen=now - timedelta(days=100),
        total_heartbeats_sent=1000,
        successful_heartbeats=1000,
        average_latency_ms=20.0,
        total_attestations_evaluated=30,
        median_score_deviations_sum=150.0,  # Avg dev: 5.0 points
        grounded_citations_count=0,  # 0% grounded citations!
        total_citations_count=50,
        has_valid_catalog_hashes=True,
    )

    score = calculate_node_quality(metrics, now=now)
    assert score.grounding_factor == 0.0
    assert score.quality_score < 0.75
    assert score.is_seed_candidate is False


def test_outdated_taxonomy_version_penalty():
    """Verify that running outdated taxonomy catalog versions incurs a penalty."""
    now = datetime.now(timezone.utc)
    metrics = NodeMetrics(
        node_pubkey="d" * 64,
        node_alias="outdated-catalog-node",
        ws_url="ws://10.0.0.4:8765",
        first_seen=now - timedelta(days=90),
        total_heartbeats_sent=500,
        successful_heartbeats=500,
        has_valid_catalog_hashes=False,  # Outdated or modified catalogs
    )

    score = calculate_node_quality(metrics, now=now)
    assert score.taxonomy_factor == 0.0
    assert score.is_seed_candidate is False


def test_sybil_ephemeral_key_damping():
    """Verify that brand new burner keys (<1 hour old) are damped compared to established nodes."""
    now = datetime.now(timezone.utc)
    fresh_metrics = NodeMetrics(
        node_pubkey="e" * 64,
        node_alias="fresh-burner-key",
        ws_url="ws://10.0.0.5:8765",
        first_seen=now - timedelta(minutes=5),  # 5 minutes old
        total_heartbeats_sent=10,
        successful_heartbeats=10,
    )

    score = calculate_node_quality(fresh_metrics, now=now)
    assert score.longevity_factor < 0.01  # Very low longevity score


def test_rank_nodes_sorting():
    """Verify that rank_nodes properly sorts seed candidates descending by composite score."""
    now = datetime.now(timezone.utc)
    nodes = [
        NodeMetrics(
            node_pubkey="1" * 64,
            node_alias="mediocre-peer",
            ws_url="ws://10.0.0.1:8765",
            first_seen=now - timedelta(days=10),
            total_heartbeats_sent=100,
            successful_heartbeats=70,
        ),
        NodeMetrics(
            node_pubkey="2" * 64,
            node_alias="top-seed",
            ws_url="ws://10.0.0.2:8765",
            first_seen=now - timedelta(days=100),
            total_heartbeats_sent=1000,
            successful_heartbeats=1000,
            average_latency_ms=15.0,
            total_attestations_evaluated=100,
            median_score_deviations_sum=0.5,
            grounded_citations_count=200,
            total_citations_count=200,
        ),
        NodeMetrics(
            node_pubkey="3" * 64,
            node_alias="bad-peer",
            ws_url="ws://10.0.0.3:8765",
            first_seen=now - timedelta(days=5),
            total_heartbeats_sent=100,
            successful_heartbeats=20,
            grounded_citations_count=0,
            total_citations_count=10,
        ),
    ]

    ranked = rank_nodes(nodes, top_k=10, now=now)
    assert len(ranked) == 3
    assert ranked[0].node_alias == "top-seed"
    assert ranked[0].is_seed_candidate is True
    assert ranked[1].node_alias == "mediocre-peer"
    assert ranked[2].node_alias == "bad-peer"
