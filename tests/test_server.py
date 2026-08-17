"""Unit tests for the Credence FastMCP Server."""

import json
from typing import Any

import pytest

from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.pipeline.schemas import AuditReport
from credence.server.app import create_mcp_server


@pytest.mark.unit
async def test_fastmcp_server_initialization() -> None:
    """Verify FastMCP server initializes with expected name, tools, resources, and prompts."""
    server = create_mcp_server()
    assert server.name == "credence"

    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "credence_check_url" in tool_names
    assert "credence_evaluate_text" in tool_names
    assert "credence_get_audit" in tool_names
    assert "credence_verify_attestation" in tool_names
    assert "credence_get_quota_status" in tool_names
    assert "credence_get_consensus" in tool_names
    assert "credence_get_seed_nodes" in tool_names

    resources = await server.list_resources()
    resource_uris = [r.uri for r in resources]
    assert "credence://taxonomies" in resource_uris
    assert "credence://node/identity" in resource_uris
    assert "credence://mesh/seeds" in resource_uris

    prompts = await server.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "audit_article_prompt" in prompt_names
    assert "fallacy_review_prompt" in prompt_names
    assert "dark_pattern_review_prompt" in prompt_names


@pytest.mark.unit
async def test_fastmcp_evaluate_text_tool() -> None:
    """Verify credence_evaluate_text tool directly audits raw text without network requests."""
    server = create_mcp_server()

    raw_text = (
        "Either you are 100% on our side, or you are an enemy of the people! Those ignorant cowards hate progress."
    )
    res: Any = await server.call_tool(
        "credence_evaluate_text",
        {"text": raw_text, "title": "Test Fallacy Snippet"},
    )
    assert res is not None
    text_content = res.content[0].text
    data = json.loads(text_content)
    assert data["suspicion_score"] > 0.0
    assert len(data["violations"]) >= 2
    assert any(v["rule_id"] == "FALLACY-2.2" for v in data["violations"])
    assert data["node_signature"] is not None


@pytest.mark.unit
async def test_fastmcp_verify_attestation_tool() -> None:
    """Verify credence_verify_attestation tool validates authentic and tampered attestations."""
    server = create_mcp_server()
    identity = load_or_create_node_identity()

    report = AuditReport(
        url="https://example.com/test",
        content_sha256="sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        simhash_64="0x1234567890abcdef",
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=1.0,
        classification="CLEAN",
    )
    signed_report = sign_audit_report(report, identity)

    # Valid check
    valid_res: Any = await server.call_tool(
        "credence_verify_attestation",
        {"signed_attestation_json": signed_report.model_dump_json()},
    )
    valid_data = json.loads(valid_res.content[0].text)
    assert valid_data["is_valid"] is True

    # Tampered check
    tampered_data = signed_report.model_dump(mode="json")
    tampered_data["suspicion_score"] = 99.9  # Tamper score
    invalid_res: Any = await server.call_tool(
        "credence_verify_attestation",
        {"signed_attestation_json": json.dumps(tampered_data)},
    )
    invalid_data = json.loads(invalid_res.content[0].text)
    assert invalid_data["is_valid"] is False


@pytest.mark.unit
async def test_fastmcp_quota_and_resources() -> None:
    """Verify quota status tool and dynamic resources."""
    server = create_mcp_server()

    # Quota tool
    quota_res: Any = await server.call_tool("credence_get_quota_status", {})
    quota_data = json.loads(quota_res.content[0].text)
    assert "hourly_headroom_pct" in quota_data
    assert "daily_spend_usd" in quota_data

    # Taxonomies resource
    tax_res: Any = await server.read_resource("credence://taxonomies")
    tax_data = json.loads(tax_res[0].content)
    assert len(tax_data) >= 3

    # Node Identity resource
    id_res: Any = await server.read_resource("credence://node/identity")
    id_data = json.loads(id_res[0].content)
    assert "public_key_hex" in id_data
