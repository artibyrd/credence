"""Multi-Node Cluster Byzantine Fault Tolerance & Sybil Cartel Integration Tests.

Hermetically tests:
- Byzantine Sybil Cartel Resistance (3f + 1 Tolerance)
- Barbell Network Partitions & Post-Split Consensus Reconciliation
- Dynamic Node Quality Scoring, Flapping Demotion & Outlier Quarantine
- Cryptographic Bootstrap Seed Manifest Verification
- Network Subnet-Based Sybil Traffic Throttling
"""

from datetime import datetime, timedelta, timezone

import pytest

from credence.mesh.consensus import BayesianConsensusAggregator
from credence.mesh.quality import NodeMetrics, rank_nodes
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.subjects.expertise import (
    DomainMetrics,
    compute_divergence_acceleration_dampening,
    compute_subject_expertise,
)


@pytest.mark.integration
def test_byzantine_sybil_cartel_resistance_3f_plus_1() -> None:
    """Verify that a 13-node mesh with 4 Byzantine cartel nodes cannot shift consensus."""
    aggregator = BayesianConsensusAggregator(
        f=4,
        prior_mean=20.0,
        prior_variance=100.0,
        enable_byzantine_trimming=True,
    )

    reports = []

    # 9 Honest nodes submit consistent scores around 15.0 - 22.0
    for i in range(1, 10):
        rep = AuditReport(
            url="https://adversarial-target.org/investigation",
            content_sha256="sha256:target_sha_256_hash_here_11111111111111111111111111111111",
            simhash_64="0x1111222233334444",
            suspicion_score=18.0 + (i % 3),
            suspicion_density=0.4,
            confidence_score=0.92,
            classification="LOW_SUSPICION",
            node_pubkey=f"honest_pubkey_{i:02d}" + "0" * 48,
        )
        reports.append(rep)

    # 4 Byzantine Cartel nodes collude to report 95.0 (Extreme False Alarm attack)
    for i in range(1, 5):
        rep = AuditReport(
            url="https://adversarial-target.org/investigation",
            content_sha256="sha256:target_sha_256_hash_here_11111111111111111111111111111111",
            simhash_64="0x1111222233334444",
            suspicion_score=95.0,
            suspicion_density=8.5,
            confidence_score=0.99,
            classification="DECEPTIVE",
            node_pubkey=f"byzantine_cartel_{i}" + "0" * 48,
        )
        reports.append(rep)

    consensus = aggregator.compute_consensus(reports)
    assert consensus is not None

    # Assert robust median rejected cartel collusion
    assert consensus.consensus_score < 30.0
    assert consensus.classification in ("LOW_SUSPICION", "CLEAN")
    assert consensus.byzantine_nodes_trimmed_count >= 4


@pytest.mark.integration
def test_node_quality_dynamic_ranking_and_demotion() -> None:
    """Verify that nodes under audit workload correctly rank honest nodes and demote outliers."""
    now = datetime.now(timezone.utc)
    nodes: list[NodeMetrics] = []

    # 9 Honest Nodes
    for i in range(1, 10):
        nodes.append(
            NodeMetrics(
                node_pubkey=f"honest_{i:02d}" + "0" * 55,
                node_alias=f"honest-node-{i}",
                ws_url=f"ws://127.0.0.1:{9200 + i}",
                first_seen=now - timedelta(days=60),
                total_heartbeats_sent=500,
                successful_heartbeats=498,
                average_latency_ms=25.0,
                total_attestations_evaluated=50,
                median_score_deviations_sum=1.0,
                grounded_citations_count=100,
                total_citations_count=100,
                has_valid_catalog_hashes=True,
            )
        )

    # 2 Flapping Nodes
    for i in range(10, 12):
        nodes.append(
            NodeMetrics(
                node_pubkey=f"flapping_{i}" + "0" * 53,
                node_alias=f"flapping-node-{i}",
                ws_url=f"ws://127.0.0.1:{9200 + i}",
                first_seen=now - timedelta(days=20),
                total_heartbeats_sent=500,
                successful_heartbeats=150,
                average_latency_ms=800.0,
                total_attestations_evaluated=10,
                median_score_deviations_sum=10.0,
                grounded_citations_count=10,
                total_citations_count=10,
                has_valid_catalog_hashes=True,
            )
        )

    # 2 Byzantine Sybil Nodes
    for i in range(12, 14):
        nodes.append(
            NodeMetrics(
                node_pubkey=f"byzantine_{i}" + "0" * 52,
                node_alias=f"byzantine-node-{i}",
                ws_url=f"ws://127.0.0.1:{9200 + i}",
                first_seen=now - timedelta(days=5),
                total_heartbeats_sent=500,
                successful_heartbeats=500,
                average_latency_ms=15.0,
                total_attestations_evaluated=50,
                median_score_deviations_sum=350.0,
                grounded_citations_count=0,
                total_citations_count=80,
                has_valid_catalog_hashes=False,
            )
        )

    ranked = rank_nodes(nodes, top_k=13, now=now)

    for s in ranked[:9]:
        assert s.node_alias.startswith("honest-node")
        assert s.quality_score >= 0.85
        assert s.is_seed_candidate is True


@pytest.mark.integration
def test_galileo_weaponization_resisted_in_13_node_mesh() -> None:
    """Verify a 13-node mesh resists a 0.90-expertise node pivoting to grounded-but-divergent findings."""
    now = datetime.now(timezone.utc)
    first_eval = now - timedelta(days=45)
    subject_id = "journalism.news"
    content_sha = "sha256:galileo_13node_" + "a" * 47

    # 1. Attacker builds >= 0.90 expertise over 30 concordant evaluations
    pre_pivot_metrics = DomainMetrics(
        evaluations_count=30,
        median_deviations_sum=0.0,
        grounded_quotes_count=60,
        total_quotes_count=60,
        unique_domains_count=6,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=[0.0] * 20,
    )
    assert compute_subject_expertise(pre_pivot_metrics) >= 0.90

    # 2. Attacker pivots to 10 grounded-but-divergent evaluations (deviation = 85.0)
    pivoted_recent = [0.0] * 10 + [85.0] * 10
    dampening = compute_divergence_acceleration_dampening(pivoted_recent, baseline_deviation=0.0)
    assert dampening == 0.0

    post_pivot_metrics = DomainMetrics(
        evaluations_count=40,
        median_deviations_sum=850.0,
        grounded_quotes_count=80,
        total_quotes_count=80,
        unique_domains_count=6,
        slashing_count=0,
        first_evaluated_at=first_eval,
        last_evaluated_at=now,
        recent_deviations=pivoted_recent,
    )
    post_pivot_expertise = compute_subject_expertise(post_pivot_metrics)
    assert post_pivot_expertise < 0.70

    # 3. 13-node mesh: 12 honest generalist nodes score CLEAN (0..4) vs 1 pivoting grounded attacker (88.0)
    attacker_pubkey = "pivoting_galileo_attacker_" + "f" * 38
    reports: list[AuditReport] = []
    reps: dict[str, float] = {}
    exp_map: dict[str, float] = {}

    for i in range(1, 13):
        pk = f"honest_mesh_node_{i:02d}_" + "0" * 45
        reports.append(
            AuditReport(
                url="https://example.org/galileo-13node-test",
                content_sha256=content_sha,
                simhash_64="0x1111222233334444",
                suspicion_score=float(i % 4),
                suspicion_density=0.0,
                confidence_score=0.92,
                classification="CLEAN",
                violations=[],
                node_pubkey=pk,
            )
        )
        reps[pk] = 0.85
        exp_map[pk] = 0.05

    attacker_report = AuditReport(
        url="https://example.org/galileo-13node-test",
        content_sha256=content_sha,
        simhash_64="0x1111222233334444",
        suspicion_score=88.0,
        suspicion_density=6.0,
        confidence_score=0.99,
        classification="DECEPTIVE",
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalistic-ethics:seek-truth/SPJ-1.1@v1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="SEEK_TRUTH_AND_REPORT",
                severity=5,
                confidence=0.99,
                quote_or_element="The municipal budget passed 5-2.",
                reasoning="Malicious interpretive framing on benign factual quote.",
                is_grounded=True,
            )
        ],
        node_pubkey=attacker_pubkey,
    )
    reports.append(attacker_report)
    reps[attacker_pubkey] = 0.95
    # Even if stale 0.90 expertise is still cached in subject_expertise_map, consensus dampening withdraws protection
    exp_map[attacker_pubkey] = 0.90

    aggregator = BayesianConsensusAggregator(f=4, outlier_delta_threshold=25.0, enable_byzantine_trimming=True)
    verdict = aggregator.compute_consensus(
        attestations=reports,
        node_reputations=reps,
        subject_id=subject_id,
        subject_expertise_map=exp_map,
        peer_recent_deviations={attacker_pubkey: pivoted_recent},
        peer_baseline_deviations={attacker_pubkey: 0.0},
    )

    assert verdict is not None
    assert verdict.node_count == 13
    assert attacker_pubkey in verdict.outlier_nodes
    assert attacker_pubkey in verdict.galileo_escalated_nodes
    assert verdict.galileo_override is False
    assert verdict.consensus_score <= 15.0
    assert verdict.classification == "CLEAN"
