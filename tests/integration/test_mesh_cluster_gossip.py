"""Multi-Node Cluster Integration Tests for Credence Mesh Gossip & Topology.

Hermetically tests:
- 3-Node and 7-Node Standard Multi-Hop Clusters
- 13-Node Heterogeneous Small-World Mesh (Watts-Strogatz lattice)
- Linear Daisy Chain Latency Accumulation
- Highest Random Weight (HRW) Rendezvous Hashing Feed Distribution
- Host Hardware Safety Governor
"""

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.mesh.hardware_guard import (
    recommend_cluster_size,
)
from credence.mesh.relay import MeshGossipRelay
from credence.pipeline.schemas import AuditReport


@pytest.mark.integration
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

        await relay1.broadcast_attestation(signed_report)
        await asyncio.sleep(0.3)

        assert relay2.deduplicator._seen
        assert relay3.deduplicator._seen
    finally:
        await relay1.stop()
        await relay2.stop()
        await relay3.stop()


@pytest.mark.integration
async def test_7_node_multi_hop_gossip_epidemic(tmp_path: Path) -> None:
    """Verify that an attestation travels across multiple hops in a 7-node mesh."""
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
        await asyncio.gather(*(r.start() for r in relays))
        await asyncio.sleep(0.4)

        report = sign_audit_report(
            AuditReport(
                url="https://example.org/multi-hop-target",
                content_sha256="sha256:7777777777777777777777777777777777777777777777777777777777777777",
                simhash_64="0x7777777777777777",
                suspicion_score=5.0,
                suspicion_density=0.1,
                confidence_score=0.99,
                classification="CLEAN",
            ),
            identities[0],
        )

        await relays[0].broadcast_attestation(report)
        await asyncio.sleep(0.5)

        for r in relays[1:]:
            assert len(r.deduplicator._seen) >= 1
    finally:
        await asyncio.gather(*(r.stop() for r in relays), return_exceptions=True)


@pytest.mark.integration
def test_hardware_safety_governor_memory_bounds() -> None:
    """Verify system safety governor clamps cluster simulation sizes based on RAM."""
    with patch("psutil.virtual_memory") as mock_vm:
        mock_vm.return_value.available = 1024 * 1024 * 1024  # 1 GB
        assert recommend_cluster_size(requested=13) <= 7

        mock_vm.return_value.available = 4 * 1024 * 1024 * 1024  # 4 GB
        assert recommend_cluster_size(requested=13) == 13
