"""Hermetic Unit Tests for 4-Tier P2P Discovery Fallback Client & Offline Resilience."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlmodel import select

from credence.config import settings
from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity
from credence.mesh.discovery import BootstrapDiscovery
from credence.mesh.seed import SeedNodeEntry, generate_seed_file
from credence.models import PeerMetric


@pytest.mark.asyncio
async def test_tier1_local_sqlite_cache_discovery(tmp_path):
    """Verify that cached high-quality peers in SQLite are discovered in Tier 1."""
    await init_db()
    async with get_async_session() as session:
        # Clear existing
        records = (await session.exec(select(PeerMetric))).all()
        for r in records:
            await session.delete(r)
        await session.commit()

        # Insert healthy peer
        record = PeerMetric(
            node_pubkey="a" * 64,
            node_alias="cached-peer-1",
            ws_url="ws://127.0.0.1:8765",
            quality_score=0.92,
            is_seed_candidate=True,
        )
        session.add(record)
        await session.commit()

    discovery = BootstrapDiscovery(enable_local_beacon=False)
    peers = await discovery.discover_peers()
    assert "ws://127.0.0.1:8765" in peers


@pytest.mark.asyncio
async def test_tier3_signed_seed_file_discovery(tmp_path):
    """Verify that a valid local or remote signed seed file provides peers in Tier 3."""
    identity = load_or_create_node_identity(key_path=tmp_path / "root.key")
    nodes = [
        SeedNodeEntry(
            node_pubkey="b" * 64,
            node_alias="seed-peer-nexus",
            ws_url="wss://seeds.credence.nexus:8765",
            quality_score=0.96,
            uptime_pct=99.9,
        )
    ]
    manifest = generate_seed_file(nodes=nodes, identity=identity)
    seed_file_path = tmp_path / "seeds.json"
    seed_file_path.write_text(json.dumps(manifest.model_dump(mode="json")), encoding="utf-8")

    discovery = BootstrapDiscovery(
        seed_url=str(seed_file_path),
        enable_local_beacon=False,
    )
    peers = await discovery.discover_peers()
    assert "wss://seeds.credence.nexus:8765" in peers


@pytest.mark.asyncio
async def test_offline_failure_http_404_resilience():
    """Verify that when remote seed URL returns HTTP 404, discovery gracefully falls back to static seeds."""
    settings.PEER_SEEDS = "ws://fallback-node-404:8765"

    mock_response = httpx.Response(
        status_code=404, request=httpx.Request("GET", "https://seeds.credence.nexus/peers.json")
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        discovery = BootstrapDiscovery(
            seed_url="https://seeds.credence.nexus/peers.json",
            enable_local_beacon=False,
            timeout_sec=0.1,
        )
        peers = await discovery.discover_peers()
        assert "ws://fallback-node-404:8765" in peers


@pytest.mark.asyncio
async def test_offline_failure_http_500_resilience():
    """Verify that when remote seed URL returns HTTP 500, discovery gracefully falls back to static seeds."""
    settings.PEER_SEEDS = "ws://fallback-node-500:8765"

    mock_response = httpx.Response(
        status_code=500, request=httpx.Request("GET", "https://seeds.credence.nexus/peers.json")
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        discovery = BootstrapDiscovery(
            seed_url="https://seeds.credence.nexus/peers.json",
            enable_local_beacon=False,
            timeout_sec=0.1,
        )
        peers = await discovery.discover_peers()
        assert "ws://fallback-node-500:8765" in peers


@pytest.mark.asyncio
async def test_offline_failure_network_timeout_resilience():
    """Verify that network timeout / connection refused errors gracefully fall back without unhandled exceptions."""
    settings.PEER_SEEDS = "ws://fallback-node-timeout:8765"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectTimeout("Connection timed out to seeds.credence.nexus")

        discovery = BootstrapDiscovery(
            seed_url="https://seeds.credence.nexus/peers.json",
            enable_local_beacon=False,
            timeout_sec=0.1,
        )
        peers = await discovery.discover_peers()
        assert "ws://fallback-node-timeout:8765" in peers


@pytest.mark.asyncio
async def test_offline_failure_tampered_seed_signature_rejection(tmp_path):
    """Verify that forged/tampered remote seed files are rejected and discovery falls back to static seeds."""
    settings.PEER_SEEDS = "ws://fallback-node-tamper:8765"

    identity = load_or_create_node_identity(key_path=tmp_path / "root.key")
    nodes = [
        SeedNodeEntry(
            node_pubkey="c" * 64,
            node_alias="malicious-poisoned-seed",
            ws_url="ws://attacker.com:8765",
            quality_score=0.99,
            uptime_pct=100.0,
        )
    ]
    manifest = generate_seed_file(nodes=nodes, identity=identity)
    tampered_data = manifest.model_dump(mode="json")
    tampered_data["seed_nodes"][0]["ws_url"] = "ws://sybil-cartel-hijack.com:8765"  # Modify without resigning

    mock_response = httpx.Response(
        status_code=200,
        text=json.dumps(tampered_data),
        request=httpx.Request("GET", "https://seeds.credence.nexus/peers.json"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        discovery = BootstrapDiscovery(
            seed_url="https://seeds.credence.nexus/peers.json",
            enable_local_beacon=False,
            timeout_sec=0.1,
        )
        peers = await discovery.discover_peers()
        # Attacker's URL must NOT be present
        assert "ws://sybil-cartel-hijack.com:8765" not in peers
        # Fallback seed MUST be present
        assert "ws://fallback-node-tamper:8765" in peers
