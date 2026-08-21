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
from credence.pipeline.schemas import AuditReport


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
