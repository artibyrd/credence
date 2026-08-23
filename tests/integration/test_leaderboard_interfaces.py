"""Hermetic tests for 4-interface feature parity on Leaderboards & Merit.

Covers:
- FastMCP 2.0 tools & resources
- REST API endpoints & SVG badge responses
- CLI subcommands & Rich output formatting
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from starlette.testclient import TestClient

from credence.cli.main import (
    cli_badge_export,
    cli_leaderboard,
    cli_merit,
    cli_rankings,
)
from credence.server.app import create_mcp_server, create_server_app


def _extract_mcp_text(res: Any) -> str:
    if hasattr(res, "content") and isinstance(res.content, list) and len(res.content) > 0:
        return str(res.content[0].text)
    if isinstance(res, list) and len(res) > 0:
        if hasattr(res[0], "text"):
            return str(res[0].text)
        return str(res[0])
    return str(res)


@pytest.mark.asyncio
async def test_fastmcp_merit_and_leaderboard_tools() -> None:
    """Verify FastMCP tools execute and return valid JSON structures."""
    server = create_mcp_server()

    # 1. Test credence_get_leaderboard
    res_lb = await server.call_tool("credence_get_leaderboard", {"category": "quality", "limit": 10})
    assert res_lb is not None
    data_lb = json.loads(_extract_mcp_text(res_lb))
    assert isinstance(data_lb, list)

    # 2. Test credence_get_node_merit
    res_merit = await server.call_tool("credence_get_node_merit", {})
    assert res_merit is not None
    data_merit = json.loads(_extract_mcp_text(res_merit))
    assert "node_alias" in data_merit
    assert "tier" in data_merit
    assert "quality_score" in data_merit

    # 3. Test credence_get_domain_rankings
    res_dom = await server.call_tool("credence_get_domain_rankings", {"category": "best", "limit": 10})
    assert res_dom is not None
    data_dom = json.loads(_extract_mcp_text(res_dom))
    assert isinstance(data_dom, list)

    # 4. Test credence_get_taxonomy_analytics
    res_tax = await server.call_tool("credence_get_taxonomy_analytics", {"limit": 5})
    assert res_tax is not None
    data_tax = json.loads(_extract_mcp_text(res_tax))
    assert isinstance(data_tax, list)

    # 5. Test credence_get_epistemic_weather
    res_w = await server.call_tool("credence_get_epistemic_weather", {})
    assert res_w is not None
    data_w = json.loads(_extract_mcp_text(res_w))
    assert "global_weather_score" in data_w
    assert "weather_condition" in data_w

    # 6. Test credence_get_bounties
    res_b = await server.call_tool("credence_get_bounties", {"limit": 5})
    assert res_b is not None
    data_b = json.loads(_extract_mcp_text(res_b))
    assert isinstance(data_b, list)

    # 7. Test credence_generate_badge tool across 3 modalities
    res_badge_node = await server.call_tool(
        "credence_generate_badge", {"modality": "node", "identifier": "sprout_node", "format": "svg"}
    )
    assert "<svg" in _extract_mcp_text(res_badge_node)

    res_badge_pub = await server.call_tool(
        "credence_generate_badge", {"modality": "publisher", "identifier": "reuters.com", "format": "component"}
    )
    assert "<credence-badge" in _extract_mcp_text(res_badge_pub)

    res_badge_attest = await server.call_tool(
        "credence_generate_badge",
        {"modality": "attestation", "identifier": "https://example.com/test", "format": "json"},
    )
    data_attest = json.loads(_extract_mcp_text(res_badge_attest))
    assert data_attest["modality"] == "attestation"
    assert "<svg" in data_attest["svg"]


def test_rest_api_leaderboards_and_badges() -> None:
    """Verify REST API endpoints and SVG badge content-types."""
    app = create_server_app()
    client = TestClient(app)

    # 1. GET /api/leaderboard
    resp_lb = client.get("/api/leaderboard?category=quality&limit=5")
    assert resp_lb.status_code == 200
    assert "leaderboard" in resp_lb.json()

    # 2. GET /api/merit
    resp_merit = client.get("/api/merit")
    assert resp_merit.status_code == 200
    assert "tier" in resp_merit.json()

    # 3. GET /api/badge/root_seed_candidate.svg
    resp_badge = client.get("/api/badge/root_seed_candidate.svg?node=test-node")
    assert resp_badge.status_code == 200
    assert "image/svg+xml" in resp_badge.headers["content-type"]
    assert "<svg" in resp_badge.text

    # 4. GET /api/badge/publisher/reuters.com.svg
    resp_pub = client.get("/api/badge/publisher/reuters.com.svg")
    assert resp_pub.status_code == 200
    assert "image/svg+xml" in resp_pub.headers["content-type"]
    assert "<svg" in resp_pub.text

    # 5. GET /api/badge/attestation/https://example.com/article.svg
    resp_attest = client.get("/api/badge/attestation/https://example.com/article.svg")
    assert resp_attest.status_code == 200
    assert "image/svg+xml" in resp_attest.headers["content-type"]
    assert "<svg" in resp_attest.text

    # 6. GET /api/rankings/domains
    resp_dom = client.get("/api/rankings/domains?category=best")
    assert resp_dom.status_code == 200
    assert "rankings" in resp_dom.json()

    # 7. GET /api/weather
    resp_w = client.get("/api/weather")
    assert resp_w.status_code == 200
    assert "global_weather_score" in resp_w.json()


@pytest.mark.asyncio
async def test_cli_commands_execution(tmp_path) -> None:
    """Verify CLI subcommands execute without exceptions across formats."""
    # Test leaderboard human & json
    await cli_leaderboard(category="quality", limit=5, format_type="human")
    await cli_leaderboard(category="philanthropy", limit=5, format_type="json")
    await cli_leaderboard(category="galileo", limit=5, format_type="tsv")

    # Test merit show & export
    svg_out = str(tmp_path / "test_badge.svg")
    await cli_merit(export_svg=svg_out)
    assert (tmp_path / "test_badge.svg").exists()
    await cli_merit(mesh=True)

    # Test standalone badge export across modalities
    badge_out = str(tmp_path / "root_seed.svg")
    cli_badge_export(badge_id="root_seed_candidate", output_path=badge_out, node="node-1", modality="node")
    assert (tmp_path / "root_seed.svg").exists()

    pub_badge_out = str(tmp_path / "reuters_badge.svg")
    cli_badge_export(badge_id="reuters.com", output_path=pub_badge_out, modality="publisher")
    assert (tmp_path / "reuters_badge.svg").exists()

    attest_badge_out = str(tmp_path / "attest_badge.html")
    cli_badge_export(
        badge_id="https://example.com/article",
        output_path=attest_badge_out,
        modality="attestation",
        format_type="component",
    )
    assert (tmp_path / "attest_badge.html").exists()

    # Test rankings
    await cli_rankings(ranking_type="domains", category="best", limit=5, format_type="human")
    await cli_rankings(ranking_type="rules", limit=5, format_type="human")
    await cli_rankings(ranking_type="weather", format_type="human")
    await cli_rankings(ranking_type="bounties", limit=5, format_type="human")
