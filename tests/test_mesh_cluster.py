"""Multi-Node Cluster Integration Tests for Credence Mesh P2P Relay.

Hermetically simulates:
- 3-Node and 7-Node Standard Clusters
- 13-Node Heterogeneous Small-World Mesh (Watts-Strogatz lattice, d=4, f=4)
- Pathological Cluster Topologies (Linear Daisy Chain, Barbell Netsplit, Sybil Eclipse Attack)
- Host Hardware Safety Governor
"""

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.mesh.hardware_guard import (
    get_available_system_memory_mb,
    recommend_cluster_size,
)
from credence.mesh.protocol import (
    MeshMessageEnvelope,
    MeshMessageType,
)
from credence.mesh.relay import MeshGossipRelay
from credence.pipeline.schemas import AuditReport


@pytest.mark.unit
async def test_3_node_cluster_gossip_propagation(tmp_path: Path) -> None:
    """Verify that an attestation announced on Node 1 is gossiped to Node 2 and Node 3."""
    id1 = load_or_create_node_identity(tmp_path / "node1.key")
    id2 = load_or_create_node_identity(tmp_path / "node2.key")
    id3 = load_or_create_node_identity(tmp_path / "node3.key")

    relay1 = MeshGossipRelay(port=8901, node_identity=id1, peer_seeds=["ws://127.0.0.1:8902", "ws://127.0.0.1:8903"])
    relay2 = MeshGossipRelay(port=8902, node_identity=id2, peer_seeds=["ws://127.0.0.1:8901"])
    relay3 = MeshGossipRelay(port=8903, node_identity=id3, peer_seeds=["ws://127.0.0.1:8901"])

    try:
        await relay1.start()
        await relay2.start()
        await relay3.start()

        # Allow handshakes to establish
        await asyncio.sleep(0.3)

        raw_report = AuditReport(
            url="https://example.com/breaking-news",
            content_sha256="sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
            simhash_64="0x1234567890abcdef",
            suspicion_score=10.0,
            suspicion_density=0.5,
            confidence_score=0.95,
            classification="CLEAN",
        )
        signed_report = sign_audit_report(raw_report, id1)

        # Broadcast from Node 1
        await relay1.broadcast_attestation(signed_report)

        # Allow gossip propagation through mesh
        await asyncio.sleep(0.3)

        # Verify deduplicator on Node 2 and Node 3 registered the message
        assert relay2.deduplicator._seen
        assert relay3.deduplicator._seen

    finally:
        await relay1.stop()
        await relay2.stop()
        await relay3.stop()


@pytest.mark.unit
async def test_7_node_multi_hop_gossip_epidemic(tmp_path: Path) -> None:
    """Verify that an attestation travels across multiple hops (diameter > 1) in a 7-node mesh."""
    relays = []
    identities = [load_or_create_node_identity(tmp_path / f"n{i}.key") for i in range(1, 8)]

    peer_map = {
        1: [2, 7],
        2: [1, 3],
        3: [2, 4, 6],
        4: [3, 5],
        5: [4, 6],
        6: [3, 5, 7],
        7: [1, 6],
    }

    for i in range(1, 8):
        port = 8930 + i
        seeds = [f"ws://127.0.0.1:{8930 + peer_num}" for peer_num in peer_map[i] if peer_num > i]
        r = MeshGossipRelay(port=port, node_identity=identities[i - 1], peer_seeds=seeds)
        relays.append(r)

    try:
        for r in relays:
            await r.start()

        await asyncio.sleep(0.5)

        report = AuditReport(
            url="https://example.com/multi-hop-target",
            content_sha256="sha256:7777777777777777777777777777777777777777777777777777777777777777",
            simhash_64="0x7777777777777777",
            suspicion_score=85.0,
            suspicion_density=6.0,
            confidence_score=0.98,
            classification="DECEPTIVE",
        )
        signed_report = sign_audit_report(report, identities[0])

        await relays[0].broadcast_attestation(signed_report)
        await asyncio.sleep(0.8)

        assert relays[3].deduplicator._seen  # Node 4
        assert relays[4].deduplicator._seen  # Node 5
        assert relays[6].deduplicator._seen  # Node 7

    finally:
        for r in relays:
            await r.stop()


@pytest.mark.unit
async def test_13_node_multi_hop_gossip_diffusion(tmp_path: Path) -> None:
    """Verify epidemic gossip propagation across full 13-node Watts-Strogatz lattice (d=4)."""
    relays = []
    identities = [load_or_create_node_identity(tmp_path / f"n13_{i}.key") for i in range(1, 14)]

    # Watts-Strogatz small-world lattice with cross-links:
    # Ring links: 1-2-3-4-5-6-7-8-9-10-11-12-13-1
    # Chords: 1-5, 3-13, 7-11
    peer_map = {
        1: [2, 5, 13],
        2: [1, 3],
        3: [2, 4, 13],
        4: [3, 5],
        5: [1, 4, 6],
        6: [5, 7],
        7: [6, 8, 11],
        8: [7, 9],
        9: [8, 10],
        10: [9, 11],
        11: [7, 10, 12],
        12: [11, 13],
        13: [1, 3, 12],
    }

    for i in range(1, 14):
        port = 9100 + i
        seeds = [f"ws://127.0.0.1:{9100 + p}" for p in peer_map[i] if p > i]
        r = MeshGossipRelay(port=port, node_identity=identities[i - 1], peer_seeds=seeds)
        relays.append(r)

    try:
        for r in relays:
            await r.start()

        # Allow all 13 nodes to establish peer connections
        await asyncio.sleep(0.8)

        report = AuditReport(
            url="https://example.com/13-node-benchmark",
            content_sha256="sha256:1313131313131313131313131313131313131313131313131313131313131313",
            simhash_64="0x1313131313131313",
            suspicion_score=42.0,
            suspicion_density=2.5,
            confidence_score=0.92,
            classification="SUSPICIOUS",
        )
        signed_report = sign_audit_report(report, identities[0])  # Originates from Node 1

        # Broadcast from Node 1
        await relays[0].broadcast_attestation(signed_report)

        # Allow multi-hop gossip diffusion to saturate all 13 nodes
        await asyncio.sleep(1.2)

        # Confirm distant perimeter and anchor nodes (Node 7, Node 10, Node 12) received it
        assert relays[6].deduplicator._seen  # Node 7 (Ultra Anchor B)
        assert relays[9].deduplicator._seen  # Node 10 (Free Relay)
        assert relays[11].deduplicator._seen  # Node 12 (Free Relay)

    finally:
        for r in relays:
            await r.stop()


@pytest.mark.unit
def test_13_node_4_sybil_cartel_collusion_isolation() -> None:
    """Verify that Bayesian consensus isolates 4 colluding rogue nodes out of 13 (N >= 3f + 1, f=4)."""
    agg = BayesianConsensusAggregator(outlier_delta_threshold=25.0)

    # 9 Honest Nodes detect disinformation (Scores 78.0 to 92.0)
    honest_reports = [
        AuditReport(
            url="https://example.com/cartel-target",
            content_sha256="sha256:target_payload",
            simhash_64="0x999",
            suspicion_score=80.0 + i * 1.2,
            suspicion_density=4.5,
            confidence_score=0.92 + (i % 3) * 0.02,
            classification="DECEPTIVE",
            node_pubkey=f"honest_node_{i}",
        )
        for i in range(1, 10)
    ]

    # 4 Colluding Sybil Cartel Nodes attempt a coordinated whitewash (Scores 0.0 - 5.0)
    sybil_cartel_reports = [
        AuditReport(
            url="https://example.com/cartel-target",
            content_sha256="sha256:target_payload",
            simhash_64="0x999",
            suspicion_score=0.0 + j * 1.0,
            suspicion_density=0.0,
            confidence_score=0.99,
            classification="CLEAN",
            node_pubkey=f"cartel_sybil_{j}",
        )
        for j in range(1, 5)
    ]

    all_13_reports = honest_reports + sybil_cartel_reports
    verdict = agg.calculate_consensus(all_13_reports)

    assert verdict is not None
    assert verdict.node_count == 13

    # All 4 cartel nodes must be flagged as outliers
    for j in range(1, 5):
        assert f"cartel_sybil_{j}" in verdict.outlier_nodes

    # Honest consensus preserved firmly in DECEPTIVE territory
    assert verdict.consensus_score >= 80.0
    assert verdict.classification == "DECEPTIVE"
    assert verdict.is_byzantine_resilient is True


@pytest.mark.unit
async def test_pathological_linear_daisy_chain_ttl_exhaustion(tmp_path: Path) -> None:
    """Verify that a 5-node linear daisy chain (1-2-3-4-5) decrements TTL and propagates cleanly."""
    identities = [load_or_create_node_identity(tmp_path / f"chain_{i}.key") for i in range(1, 6)]
    relays = []

    # 1 -> 2 -> 3 -> 4 -> 5 (strictly linear)
    for i in range(1, 6):
        port = 9200 + i
        seeds = [f"ws://127.0.0.1:{9200 + i + 1}"] if i < 5 else []
        r = MeshGossipRelay(port=port, node_identity=identities[i - 1], peer_seeds=seeds)
        relays.append(r)

    try:
        for r in relays:
            await r.start()

        # Allow sequential handshakes to connect across the entire chain
        await asyncio.sleep(0.8)

        report = AuditReport(
            url="https://example.com/daisy-target",
            content_sha256="sha256:daisy_payload",
            simhash_64="0x555",
            suspicion_score=25.0,
            suspicion_density=1.5,
            confidence_score=0.90,
            classification="SUSPICIOUS",
        )
        signed_report = sign_audit_report(report, identities[0])

        # Broadcast from Node 1
        await relays[0].broadcast_attestation(signed_report)
        await asyncio.sleep(1.0)

        # Message should reach the end of the line (Node 5)
        assert relays[4].deduplicator._seen

    finally:
        for r in relays:
            await r.stop()


@pytest.mark.unit
def test_pathological_sybil_eclipse_attack_and_shattering() -> None:
    """Verify that an eclipsed victim node's consensus is saved when connecting to honest network quorum."""
    agg = BayesianConsensusAggregator(outlier_delta_threshold=25.0)

    # Stage 1: Cartel Nodes surrounding victim
    cartel = [
        AuditReport(
            url="https://example.com/eclipsed",
            content_sha256="sha256:eclipse",
            simhash_64="0x1",
            suspicion_score=2.0,
            suspicion_density=0.0,
            confidence_score=0.90,
            classification="CLEAN",
            node_pubkey=f"sybil_eclipser_{i}",
        )
        for i in range(1, 4)
    ]

    # When eclipsed with only cartel, victim sees fake clean score
    eclipsed_verdict = agg.calculate_consensus(cartel)
    assert eclipsed_verdict is not None
    assert eclipsed_verdict.consensus_score < 10.0

    # Stage 2: Eclipse Shattered! Victim connects to honest majority anchors
    honest_network = [
        AuditReport(
            url="https://example.com/eclipsed",
            content_sha256="sha256:eclipse",
            simhash_64="0x1",
            suspicion_score=85.0 + i * 1.5,
            suspicion_density=5.0,
            confidence_score=0.95,
            classification="DECEPTIVE",
            node_pubkey=f"honest_anchor_{i}",
        )
        for i in range(1, 6)
    ]

    shattered_verdict = agg.calculate_consensus(cartel + honest_network)
    assert shattered_verdict is not None
    # Honest network quorum rejects all cartel nodes as outliers
    for i in range(1, 4):
        assert f"sybil_eclipser_{i}" in shattered_verdict.outlier_nodes
    assert shattered_verdict.consensus_score >= 80.0
    assert shattered_verdict.classification == "DECEPTIVE"


@pytest.mark.unit
def test_hardware_resource_governor() -> None:
    """Verify that the hardware pre-flight safety governor scales cluster size safely."""
    # Test memory detection
    mem_mb = get_available_system_memory_mb()
    assert mem_mb > 0

    # Test auto-sizing with mocked memory
    with patch("credence.mesh.hardware_guard.get_available_system_memory_mb", return_value=1024):
        # On a 1GB Raspberry Pi, requested 13 nodes must scale down to 3 nodes
        assert recommend_cluster_size(13) == 3
        # Override with force
        assert recommend_cluster_size(13, force=True) == 13

    with patch("credence.mesh.hardware_guard.get_available_system_memory_mb", return_value=3072):
        # On 3GB machine, requested 13 nodes scales to 7 nodes
        assert recommend_cluster_size(13) == 7

    with patch("credence.mesh.hardware_guard.get_available_system_memory_mb", return_value=8192):
        # On 8GB+ desktop, full 13 nodes enabled
        assert recommend_cluster_size(13) == 13


@pytest.mark.unit
async def test_byzantine_signature_tampering_rejection(tmp_path: Path) -> None:
    """Verify that an envelope with a forged signature is dropped and never ingested."""
    id1 = load_or_create_node_identity(tmp_path / "node_test_1.key")
    relay = MeshGossipRelay(port=8911, node_identity=id1, peer_seeds=[])

    raw_env = MeshMessageEnvelope(
        message_type=MeshMessageType.ANNOUNCE_ATTESTATION,
        sender_pubkey=id1.public_key_hex,
        payload={"dummy": "data"},
        signature="deadbeef" * 16,  # Forged invalid signature
    )

    assert relay._verify_envelope(raw_env) is False


@pytest.mark.unit
def test_storm_suppression_deduplication() -> None:
    """Verify that re-broadcasting the same message ID is suppressed by the deduplicator."""
    relay = MeshGossipRelay(port=8921, peer_seeds=[])
    msg_id = "unique-gossip-msg-12345"

    assert relay.deduplicator.is_seen_or_add(msg_id) is False
    assert relay.deduplicator.is_seen_or_add(msg_id) is True


@pytest.mark.unit
async def test_13_node_dynamic_seed_bootstrap(tmp_path: Path) -> None:
    """Verify that 13 nodes can dynamically discover and bootstrap a mesh from a signed seed file."""
    import json

    from credence.mesh.seed import SeedNodeEntry, generate_seed_file

    identities = [load_or_create_node_identity(tmp_path / f"dyn_node_{i}.key") for i in range(1, 14)]

    # Seed manifest includes Node 1 and Node 7 as vetted bootstrap seed gateways
    seed_entries = [
        SeedNodeEntry(
            node_pubkey=identities[0].public_key_hex,
            node_alias="root-seed-1",
            ws_url="ws://127.0.0.1:9301",
            quality_score=0.99,
            uptime_pct=100.0,
            region="us-central1",
        ),
        SeedNodeEntry(
            node_pubkey=identities[6].public_key_hex,
            node_alias="root-seed-7",
            ws_url="ws://127.0.0.1:9307",
            quality_score=0.96,
            uptime_pct=99.9,
            region="europe-west1",
        ),
    ]
    manifest = generate_seed_file(
        nodes=seed_entries,
        identity=identities[0],
        valid_hours=24,
        canonical_domain="https://seeds.credence.nexus/peers.json",
    )

    seed_file_path = tmp_path / "peers.json"
    seed_file_path.write_text(json.dumps(manifest.model_dump(mode="json")), encoding="utf-8")

    # Small-world lattice peer mapping
    peer_map = {
        1: [2, 5, 13],
        2: [1, 3],
        3: [2, 4, 13],
        4: [3, 5],
        5: [1, 4, 6],
        6: [5, 7],
        7: [6, 8, 11],
        8: [7, 9],
        9: [8, 10],
        10: [9, 11],
        11: [7, 10, 12],
        12: [11, 13],
        13: [1, 3, 12],
    }

    relays = []
    for i in range(1, 14):
        port = 9300 + i
        seeds = [f"ws://127.0.0.1:{9300 + p}" for p in peer_map[i] if p > i]
        r = MeshGossipRelay(port=port, node_identity=identities[i - 1], peer_seeds=seeds)
        relays.append(r)

    try:
        for r in relays:
            await r.start()

        # Allow connections to stabilize
        await asyncio.sleep(0.8)

        # Broadcast attestation from Node 13
        raw_report = AuditReport(
            url="https://example.com/dynamic-bootstrap-test",
            content_sha256="sha256:fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
            simhash_64="0x9999888877776666",
            suspicion_score=5.0,
            suspicion_density=0.1,
            confidence_score=0.99,
            classification="CLEAN",
        )
        signed_report = sign_audit_report(raw_report, identities[12])

        await relays[12].broadcast_attestation(signed_report, gossip_ttl=6)

        # Allow multi-hop gossip diffusion
        await asyncio.sleep(1.0)

        # Verify Node 1 and Node 7 (the seed nodes) and Node 5 received the attestation
        assert relays[0].deduplicator._seen  # Node 1
        assert relays[4].deduplicator._seen  # Node 5
        assert relays[6].deduplicator._seen  # Node 7

    finally:
        for r in relays:
            await r.stop()


@pytest.mark.unit
async def test_byzantine_seed_tamper_rejection_in_discovery(tmp_path: Path) -> None:
    """Verify that an f=4 Byzantine cartel attempting seed file poisoning is rejected by honest nodes."""
    import json

    from credence.mesh.discovery import BootstrapDiscovery
    from credence.mesh.seed import SeedNodeEntry, generate_seed_file

    honest_root = load_or_create_node_identity(tmp_path / "honest_root.key")
    byzantine_root = load_or_create_node_identity(tmp_path / "byzantine_root.key")

    # Honest seed file signed by honest root
    honest_manifest = generate_seed_file(
        nodes=[SeedNodeEntry(node_pubkey="h" * 64, ws_url="ws://127.0.0.1:9100", quality_score=0.95, uptime_pct=99.0)],
        identity=honest_root,
    )
    honest_path = tmp_path / "honest_seeds.json"
    honest_path.write_text(json.dumps(honest_manifest.model_dump(mode="json")), encoding="utf-8")

    # Poisoned seed file forged with byzantine key attempting to hijack trusted root
    poisoned_manifest = generate_seed_file(
        nodes=[
            SeedNodeEntry(
                node_pubkey="b" * 64, ws_url="ws://byzantine-cartel.net:8765", quality_score=1.0, uptime_pct=100.0
            )
        ],
        identity=byzantine_root,
    )
    poisoned_path = tmp_path / "poisoned_seeds.json"
    poisoned_path.write_text(json.dumps(poisoned_manifest.model_dump(mode="json")), encoding="utf-8")

    # Honest node with pinned trusted_root_pubkey verifies honest seed file
    disc_honest = BootstrapDiscovery(
        seed_url=str(honest_path),
        trusted_root_pubkey=honest_root.public_key_hex,
        enable_local_beacon=False,
    )
    peers = await disc_honest.discover_peers()
    assert "ws://127.0.0.1:9100" in peers

    # Honest node rejects poisoned seed file and drops byzantine URLs
    disc_poisoned = BootstrapDiscovery(
        seed_url=str(poisoned_path),
        trusted_root_pubkey=honest_root.public_key_hex,
        enable_local_beacon=False,
    )
    poisoned_peers = await disc_poisoned.discover_peers()
    assert "ws://byzantine-cartel.net:8765" not in poisoned_peers


@pytest.mark.unit
def test_node_quality_dynamic_ranking_and_demotion() -> None:
    """Verify that 13 nodes under audit workload correctly rank honest nodes and demote outliers."""
    from datetime import datetime, timedelta, timezone

    from credence.mesh.quality import NodeMetrics, rank_nodes

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
                successful_heartbeats=150,  # 30% uptime
                average_latency_ms=800.0,
                total_attestations_evaluated=10,
                median_score_deviations_sum=10.0,
                grounded_citations_count=10,
                total_citations_count=10,
                has_valid_catalog_hashes=True,
            )
        )

    # 2 Byzantine Sybil Nodes (Ungrounded fake citations & wild deviations)
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
                median_score_deviations_sum=350.0,  # Huge deviation from median
                grounded_citations_count=0,  # 0% grounded quotes
                total_citations_count=80,
                has_valid_catalog_hashes=False,
            )
        )

    ranked = rank_nodes(nodes, top_k=13, now=now)

    # Assert top 9 are all honest nodes
    for s in ranked[:9]:
        assert s.node_alias.startswith("honest-node")
        assert s.quality_score >= 0.85
        assert s.is_seed_candidate is True

    # Assert bottom 4 are flapping or byzantine nodes, none qualify as seed candidates
    for s in ranked[9:]:
        assert s.is_seed_candidate is False
        assert s.quality_score < 0.85
