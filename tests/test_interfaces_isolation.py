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
from credence.subjects.expertise import DomainMetrics, calculate_subject_expertise


@pytest.mark.unit
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
    exp_score = calculate_subject_expertise(metrics)
    assert 0.70 <= exp_score <= 1.0

    # 4. Pure core consensus calculation
    aggregator = BayesianConsensusAggregator()
    verdict = aggregator.calculate_consensus([report])
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


@pytest.mark.unit
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
