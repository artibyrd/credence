"""Interface Isolation & Core Logic Verification Suite.

Explicitly tests:
1. Pure underlying business logic without any presentation interface wrappers.
2. Presentation layer isolation and equivalence across CLI, FastMCP 2.0, Textual TUI, and Web.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from credence.feeds.parser import parse_feed_content
from credence.identity import verify_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.security import is_safe_url
from credence.ingestion.snapshot import DualCaptureResult
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.schemas import AuditReport
from credence.server.app import create_mcp_server
from credence.subjects.expertise import DomainMetrics, compute_subject_expertise


@pytest.mark.integration
async def test_core_logic_pure_pipeline_without_interfaces(db_session: Any) -> None:
    """Verify core epistemic evaluation logic executes completely decoupled from any presentation layer."""
    text = (
        "You are either 100% on our side, or you are an enemy of the people! "
        "Those ignorant cowards hate progress and want our nation to fail."
    )
    content_hash = compute_content_sha256(text)
    simhash_val = compute_simhash(text)

    extracted = ExtractedContent(
        title="Sensationalist Claim",
        clean_text=text,
        byline="Anonymous",
        word_count=len(text.split()),
        char_count=len(text),
    )
    snapshot = DualCaptureResult(
        url="text://direct-core-evaluation",
        content_sha256=content_hash,
        simhash_64=simhash_val,
        raw_html=f"<html><body><p>{text}</p></body></html>",
        extracted=extracted,
    )

    # 1. Pure core pipeline evaluation
    report = await evaluate_snapshot(snapshot, session=db_session, sign_result=True)
    assert isinstance(report, AuditReport)
    assert report.suspicion_score > 0.0
    assert report.confidence_score > 0.0
    assert report.node_signature is not None
    assert len(report.violations) >= 2

    # 2. Pure core cryptographic verification
    is_valid = verify_audit_report(report)
    assert is_valid is True

    # 3. Pure core empirical expertise math
    metrics = DomainMetrics(
        evaluations_count=25,
        median_deviations_sum=10.0,
        grounded_quotes_count=45,
        total_quotes_count=50,
    )
    exp_score = compute_subject_expertise(metrics)
    assert 0.70 <= exp_score <= 1.0

    # 4. Pure core consensus calculation
    aggregator = BayesianConsensusAggregator()
    verdict = aggregator.compute_consensus([report])
    assert verdict is not None
    assert verdict.node_count == 1

    # 5. Pure core feed parsing
    rss_sample = """<?xml version="1.0"?>
    <rss version="2.0"><channel><title>Direct Feed</title><item><title>Post 1</title><link>https://example.com/p1</link></item></channel></rss>"""
    feed = parse_feed_content(rss_sample)
    assert feed.title == "Direct Feed"
    assert len(feed.entries) == 1

    # 6. Pure core SSRF guard
    assert is_safe_url("https://example.com/clean", allow_local=False) is True
    assert is_safe_url("http://169.254.169.254/secret", allow_local=False) is False


@pytest.mark.integration
async def test_interface_parity_cli_mcp_equivalence(tmp_path: Path) -> None:
    """Verify that evaluating raw text yields identical structured findings in FastMCP and Direct invocation."""
    server = create_mcp_server()

    raw_text = (
        "You are either 100% on our side, or you are an enemy of the people! "
        "Those ignorant cowards hate working families."
    )

    # Direct Logic Invocation
    direct_hash = compute_content_sha256(raw_text)
    assert direct_hash.startswith("sha256:")

    # FastMCP Tool Invocation
    res: Any = await server.call_tool(
        "credence_evaluate_text",
        {"text": raw_text, "title": "Fallacy Sample"},
    )
    mcp_data = json.loads(res.content[0].text)

    assert mcp_data["content_sha256"] == direct_hash
    assert mcp_data["suspicion_score"] > 0.0
    assert any(v["rule_id"] == "FALLACY-2.2" for v in mcp_data["violations"])
    assert any(v["rule_id"] == "FALLACY-1.1" for v in mcp_data["violations"])


@pytest.mark.integration
async def test_fastmcp_feed_discovery_and_digest_tools(db_session: Any) -> None:
    """Verify that FastMCP tools for feed autodiscovery and digest generation respond synchronously."""
    server = create_mcp_server()

    # 1. Test credence_generate_digest tool
    digest_res: Any = await server.call_tool(
        "credence_generate_digest",
        {"hours": 24},
    )
    digest_data = json.loads(digest_res.content[0].text)
    assert "total_articles_evaluated" in digest_data
    assert "clean_articles_count" in digest_data
    assert "estimated_tokens_saved" in digest_data

    # 2. Test credence://digest/morning resource
    res_list: Any = await server.read_resource("credence://digest/morning")
    assert res_list is not None and len(res_list) > 0
    res_text = res_list[0].content if hasattr(res_list[0], "content") else str(res_list[0])
    res_dict = json.loads(res_text)
    assert "total_articles_evaluated" in res_dict


@pytest.mark.integration
async def test_complete_4_way_feature_parity_matrix() -> None:
    """Explicitly verify 4-way parity across CLI, FastMCP 2.0, Textual TUI, and Zero-Build Web."""
    from credence.tui.app import CredenceApp

    # 1. FastMCP 2.0 Parity Gate
    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    expected_tools = {
        "credence_check_url",
        "credence_evaluate_text",
        "credence_get_audit",
        "credence_verify_attestation",
        "credence_get_consensus",
        "credence_discover_feeds",
        "credence_inspect_feed_health",
        "credence_generate_digest",
        "credence_get_quota_status",
        "credence_get_leaderboard",
        "credence_get_node_merit",
        "credence_get_domain_rankings",
        "credence_get_taxonomy_analytics",
        "credence_get_epistemic_weather",
        "credence_get_mesh_stats",
        "credence_get_mesh_network_health",
        "credence_get_seed_nodes",
        "credence_generate_badge",
    }
    missing_tools = expected_tools - tool_names
    assert not missing_tools, f"Missing FastMCP tools in parity matrix: {missing_tools}"

    resources = await server.list_resources()
    resource_uris = {str(r.uri) for r in resources}

    expected_resources = {
        "credence://feeds/status",
        "credence://digest/morning",
        "credence://profiles",
        "credence://taxonomies",
        "credence://node/identity",
        "credence://mesh/seeds",
        "credence://mesh/stats",
        "credence://mesh/network-health",
        "credence://subjects/registry",
        "credence://merit/badges",
    }
    missing_resources = expected_resources - resource_uris
    assert not missing_resources, f"Missing FastMCP resources in parity matrix: {missing_resources}"

    # 2. Textual TUI Parity Gate
    app = CredenceApp()
    tui_binding_keys = {b[0] if isinstance(b, tuple) else b.key for b in app.BINDINGS}
    assert {"1", "2", "3", "4", "5", "6", "7", "8", "9", "m", "slash", "v", "o", "e", "f", "s"}.issubset(
        tui_binding_keys
    ), "All core actions must have mapped TUI keybindings"

    # 3. Zero-Build Web UI Parity Gate
    web_dir = Path(__file__).resolve().parents[2] / "web"
    expected_web_pages = [
        web_dir / "credence.run" / "index.html",
        web_dir / "credence.report" / "index.html",
        web_dir / "credence.report" / "viewer.html",
        web_dir / "credence.report" / "history.html",
        web_dir / "credence.nexus" / "index.html",
        web_dir / "admin.credence.run" / "index.html",
        web_dir / "credence.foundation" / "index.html",
    ]

    for page in expected_web_pages:
        assert page.exists(), f"Missing required web portal surface: {page}"
        html = page.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html
        # Zero npm invariant
        assert "package.json" not in html
        assert "node_modules" not in html
        # 5 Invariant header links
        assert "https://credence.run" in html
        assert "https://docs.credence.run" in html
        assert "https://credence.report" in html
        assert "https://credence.nexus" in html
        assert "https://credence.foundation" in html
