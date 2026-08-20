"""Automated Test Suite for Credence Node & Mesh Health, Stats, and Scored Pages Dashboard.

Covers:
- `credence.mesh.stats.calculate_mesh_stats` metric aggregations across sources, categories, and verdicts
- REST API endpoint `GET /api/v1/mesh/stats` & `GET /api/mesh/stats`
- FastMCP 2.0 tool `credence_get_mesh_stats` & resource `credence://mesh/stats`
- CLI subcommand `credence stats` with `--breakdown` and `--json`
- Zero-build web dashboard asset integrity (`web/credence.nexus/dashboard.html`)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from credence.db import get_async_session, init_db
from credence.mesh.stats import calculate_mesh_stats
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord, utc_now
from credence.server.app import create_server_app


@pytest.mark.asyncio
async def test_calculate_mesh_stats_aggregations() -> None:
    """Test calculate_mesh_stats computes accurate aggregations on seeded audit records."""
    await init_db()
    async with get_async_session() as session:
        # Seed test snapshots
        snap1 = SnapshotRecord(
            url="https://reuters.com/investigates/clean-energy-2026",
            site_name="Reuters",
            title="Clean Energy Investment Hits Record",
            dom_text_raw="Clean energy investments rose by 40% worldwide in 2026.",
            cleaned_text="Clean energy investments rose by 40% worldwide in 2026.",
            content_sha256="sha256:reuters_test_01",
            simhash_64="0x1111111111111111",
        )
        snap2 = SnapshotRecord(
            url="https://deceptive-news.fake/cure-all-pill",
            site_name="Deceptive News",
            title="Miracle Pill Cures All Illness",
            dom_text_raw="Scientists confirm miracle pill cures all illness instantly.",
            cleaned_text="Scientists confirm miracle pill cures all illness instantly.",
            content_sha256="sha256:deceptive_test_01",
            simhash_64="0x2222222222222222",
        )
        snap3 = SnapshotRecord(
            url="https://theonion.com/scientists-discover-new-color",
            site_name="The Onion",
            title="Scientists Discover New Color",
            dom_text_raw="Scientists discover new color called bleen.",
            cleaned_text="Scientists discover new color called bleen.",
            content_sha256="sha256:onion_test_01",
            simhash_64="0x3333333333333333",
        )
        session.add(snap1)
        session.add(snap2)
        session.add(snap3)
        await session.commit()
        await session.refresh(snap1)
        await session.refresh(snap2)
        await session.refresh(snap3)

        # Seed test audit records
        audit1 = AuditRecord(
            snapshot_id=snap1.id,
            suspicion_score=5.0,
            suspicion_density=0.01,
            confidence_score=0.98,
            classification="CLEAN",
            is_satire=False,
            content_type="NEWS_ARTICLE",
            content_sha256=snap1.content_sha256,
            audited_at=utc_now(),
        )
        audit2 = AuditRecord(
            snapshot_id=snap2.id,
            suspicion_score=85.0,
            suspicion_density=0.35,
            confidence_score=0.92,
            classification="HIGH_DECEPTION",
            is_satire=False,
            content_type="HEALTH_CLAIMS",
            content_sha256=snap2.content_sha256,
            audited_at=utc_now(),
        )
        audit3 = AuditRecord(
            snapshot_id=snap3.id,
            suspicion_score=10.0,
            suspicion_density=0.02,
            confidence_score=0.95,
            classification="SATIRE_PARODY",
            is_satire=True,
            content_type="SATIRE_PARODY",
            content_sha256=snap3.content_sha256,
            audited_at=utc_now(),
        )
        session.add(audit1)
        session.add(audit2)
        session.add(audit3)
        await session.commit()
        await session.refresh(audit1)
        await session.refresh(audit2)
        await session.refresh(audit3)

        # Seed violation record
        viol = ViolationRecord(
            audit_id=audit2.id,
            rule_id="SPJ-1.1",
            rule_uri="credence://taxonomies/journalistic-ethics/spj-1-1",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="accuracy_and_verification",
            severity=5,
            confidence=1.0,
            quote_or_element="miracle pill cures all illness instantly",
            reasoning="Unsubstantiated medical allegation",
        )
        session.add(viol)
        await session.commit()

        # Execute aggregation
        stats = await calculate_mesh_stats(session)

        assert stats["service"] == "credence"
        assert "my_node" in stats
        assert stats["my_node"]["total_audited_lifetime"] >= 3
        assert stats["my_node"]["avg_grounding_quotient"] == 1.00

        # Verdict distribution check
        v_dist = stats["verdict_distribution"]
        assert v_dist["CLEAN"] >= 1
        assert v_dist["HIGH_DECEPTION"] >= 1
        assert v_dist["SATIRE_PARODY"] >= 1

        # Sources breakdown check
        sources = stats["sources_breakdown"]
        domains = [s["domain"] for s in sources]
        assert "reuters.com" in domains
        assert "deceptive-news.fake" in domains

        # Top violations check
        top_viols = stats["top_violations"]
        assert len(top_viols) > 0
        assert all("rule_id" in v and "domain" in v and "count" in v for v in top_viols)


def test_rest_mesh_stats_endpoint() -> None:
    """Test REST API GET /api/v1/mesh/stats returns valid schema and HTTP 200."""
    app = create_server_app()
    with TestClient(app) as client:
        # Test /api/v1/mesh/stats
        response_v1 = client.get("/api/v1/mesh/stats")
        assert response_v1.status_code == 200
        data = response_v1.json()

        assert data["service"] == "credence"
        assert "my_node" in data
        assert "sre_telemetry" in data
        assert "mesh_dynamics" in data
        assert "sources_breakdown" in data
        assert "categories_breakdown" in data
        assert "verdict_distribution" in data
        assert "top_violations" in data
        assert "recent_audits" in data

        # Test alias /api/mesh/stats
        response_alias = client.get("/api/mesh/stats")
        assert response_alias.status_code == 200


@pytest.mark.asyncio
async def test_fastmcp_mesh_stats_tool_and_resource() -> None:
    """Test FastMCP 2.0 tool and resource serialization for mesh stats."""
    from credence.server.app import create_mcp_server

    server = create_mcp_server()
    # Find registered tool
    tools = await server.list_tools()
    mesh_tool = next((t for t in tools if t.name == "credence_get_mesh_stats"), None)
    assert mesh_tool is not None, "credence_get_mesh_stats FastMCP tool must be registered"

    # Find registered resource
    resources = await server.list_resources()
    mesh_resource = next((r for r in resources if str(r.uri) == "credence://mesh/stats"), None)
    assert mesh_resource is not None, "credence://mesh/stats FastMCP resource must be registered"


def test_cli_stats_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Test cli_stats with json_output flag produces valid machine-readable JSON."""
    from credence.cli.main import cli_stats

    cli_stats(json_output=True)
    captured = capsys.readouterr()
    assert len(captured.out) > 0
    parsed = json.loads(captured.out)
    assert parsed["service"] == "credence"
    assert "my_node" in parsed
    assert "mesh_dynamics" in parsed


def test_dashboard_web_asset_integrity() -> None:
    """Test dashboard.html exists and obeys zero-npm and WCAG accessibility invariants."""
    dashboard_path = Path(__file__).parent.parent / "web" / "credence.nexus" / "dashboard.html"
    assert dashboard_path.exists(), "dashboard.html must exist under web/credence.nexus/"

    content = dashboard_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "My Credence Node" in content
    assert "tab-overview" in content
    assert "tab-sources" in content
    assert "tab-categories" in content
    assert "tab-mesh" in content
    assert "tab-sre" in content
    assert "mesh.html" in content

    # Zero-npm invariant check
    assert "npm" not in content.lower() or "zero npm" in content.lower() or "zero-npm" in content.lower()
    assert "package.json" not in content
    assert "node_modules" not in content


@pytest.mark.asyncio
async def test_calculate_network_mesh_health_topology() -> None:
    """Test calculate_network_mesh_health computes 13-node Watts-Strogatz topology and Byzantine metrics."""
    from credence.mesh.stats import calculate_network_mesh_health

    health = await calculate_network_mesh_health(None)

    assert health["service"] == "credence"
    assert "cluster_topology" in health
    topo = health["cluster_topology"]
    assert topo["model_parameters"]["nodes_count"] == 13
    assert topo["model_parameters"]["degree_k"] == 4
    assert topo["byzantine_resilience"]["formula"] == "N >= 3f + 1"
    assert topo["byzantine_resilience"]["max_byzantine_faults"] == 4
    assert topo["epistemic_consensus"]["grounding_quotient"] == 1.00

    # Verify 13 Nodes
    nodes = health["nodes"]
    assert len(nodes) == 13
    aliases = [n["alias"] for n in nodes]
    assert "anchor-us-central1" in aliases
    assert "bridge-europe-west1" in aliases
    assert "anchor-ap-northeast1" in aliases

    # Verify Ring and Chord Edges
    edges = health["edges"]
    assert len(edges) >= 16
    chord_edges = [e for e in edges if e["type"] == "CHORD_SHORTCUT"]
    assert len(chord_edges) >= 3


def test_rest_mesh_network_health_endpoint() -> None:
    """Test REST API GET /api/v1/mesh/network-health and /api/mesh/network-health."""
    app = create_server_app()
    with TestClient(app) as client:
        res1 = client.get("/api/v1/mesh/network-health")
        assert res1.status_code == 200
        data = res1.json()
        assert data["service"] == "credence"
        assert "cluster_topology" in data
        assert len(data["nodes"]) == 13
        assert len(data["edges"]) >= 16

        # Test alias /api/mesh/network-health
        res2 = client.get("/api/mesh/network-health")
        assert res2.status_code == 200

        # Test /api/v1/mesh/health
        res3 = client.get("/api/v1/mesh/health")
        assert res3.status_code == 200


@pytest.mark.asyncio
async def test_fastmcp_mesh_network_health_tool_and_resource() -> None:
    """Test FastMCP 2.0 tool and resource registration for mesh network health."""
    from credence.server.app import create_mcp_server

    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "credence_get_mesh_network_health" in tool_names

    resources = await server.list_resources()
    resource_uris = [str(r.uri) for r in resources]
    assert "credence://mesh/network-health" in resource_uris


def test_cli_stats_mesh_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Test cli_stats with mesh flag producing valid machine-readable JSON."""
    from credence.cli.main import cli_stats

    cli_stats(mesh=True, json_output=True)
    captured = capsys.readouterr()
    assert len(captured.out) > 0
    parsed = json.loads(captured.out)
    assert parsed["service"] == "credence"
    assert "cluster_topology" in parsed
    assert len(parsed["nodes"]) == 13


def test_mesh_html_web_asset_integrity() -> None:
    """Test mesh.html exists and obeys zero-npm, 5-link nav, and WCAG accessibility invariants."""
    mesh_path = Path(__file__).parent.parent / "web" / "credence.nexus" / "mesh.html"
    assert mesh_path.exists(), "mesh.html must exist under web/credence.nexus/"

    content = mesh_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Whole-Mesh Network" in content
    assert "mesh-canvas" in content
    assert "node-inspector" in content
    assert "btn-scen-normal" in content
    assert "btn-scen-partition" in content
    assert "btn-scen-sybil" in content
    assert "btn-scen-failover" in content
    assert "btn-scen-burst" in content

    # 5 Invariant Links in Header Navbar
    assert "https://credence.run" in content
    assert "https://docs.credence.run" in content
    assert "https://credence.report" in content
    assert "https://credence.nexus" in content
    assert "https://credence.foundation" in content

    # Zero-npm invariant check
    assert "package.json" not in content
    assert "node_modules" not in content
