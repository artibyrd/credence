"""Unit tests for FastMCP Epistemic Brake, cache-first fastpath, and verify_and_anchor trust boundaries."""

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.mcpserver import MCPServer
from sqlmodel import delete, select

from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.mcp.eval_tools import _register_eval_tools


@pytest.fixture(autouse=True)
async def clear_db():
    """Ensure clean database before each MCP test."""
    await init_db()
    async with get_async_session() as session:
        await session.exec(delete(AuditJob))
        await session.exec(delete(Violation))
        await session.exec(delete(Audit))
        await session.exec(delete(Snapshot))
        await session.exec(delete(WorkerRecord))
        await session.commit()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastmcp_verify_and_anchor_rejects_ungrounded_and_empty_quotes():
    """Verify G < 1.00 rejection for hallucinated AND empty quote_or_element."""
    server = MCPServer(name="test_mcp")
    _register_eval_tools(server, transport_mode="stdio")
    verify_fn = server._tool_manager._tools["credence_verify_and_anchor"].fn

    source = "Clean factual reporting about a new solar energy facility."

    res_ungrounded = json.loads(
        await verify_fn(
            url="text://inline",
            normalized_text=source,
            suspicion_score=75.0,
            classification="DECEPTIVE",
            violations=[{"rule_id": "SPJ-1.1", "quote_or_element": "Fabricated embezzlement", "severity": 4}],
        )
    )
    assert res_ungrounded["status"] == "rejected"
    assert "Grounding precision G < 1.00" in res_ungrounded["error"]

    res_empty = json.loads(
        await verify_fn(
            url="text://inline",
            normalized_text=source,
            suspicion_score=75.0,
            classification="DECEPTIVE",
            violations=[{"rule_id": "SPJ-1.1", "quote_or_element": "", "severity": 4}],
        )
    )
    assert res_empty["status"] == "rejected"
    assert "Empty quote_or_element" in res_empty["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastmcp_verify_and_anchor_stdio_inline_and_snapshot_trust_boundary():
    """In stdio mode, local node signs text://inline or URLs with a matching server Snapshot only."""
    server = MCPServer(name="test_mcp")
    _register_eval_tools(server, transport_mode="stdio")
    verify_fn = server._tool_manager._tools["credence_verify_and_anchor"].fn

    source = "The spokesperson claimed that the moon was made of green cheese yesterday."
    violations = [
        {
            "rule_id": "SPJ-1.1",
            "quote_or_element": "the moon was made of green cheese",
            "severity": 4,
            "reasoning": "Absurd unverified claim",
        }
    ]

    # 1. http(s):// without a real server-captured Snapshot must be rejected
    res_no_snap = json.loads(
        await verify_fn(
            url="https://example.com/moon-cheese",
            normalized_text=source,
            suspicion_score=80.0,
            classification="DECEPTIVE",
            violations=violations,
        )
    )
    assert res_no_snap["status"] == "rejected"
    assert "No server-captured Snapshot" in res_no_snap["error"]

    # 2. Inline prose anchored strictly as text://inline succeeds in stdio mode
    res_inline = json.loads(
        await verify_fn(
            url="text://inline",
            normalized_text=source,
            suspicion_score=80.0,
            classification="DECEPTIVE",
            violations=violations,
            model_name="anthropic/claude-3-7-sonnet",
        )
    )
    assert res_inline["status"] == "anchored"
    assert res_inline["violations_anchored"] == 1
    assert res_inline["node_pubkey"] is not None
    assert res_inline["node_signature"] is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastmcp_verify_and_anchor_remote_http_requires_caller_signature(tmp_path: Path):
    """Decision 1: Remote HTTP/SSE rejects unsigned calls and verifies caller Ed25519 signature against real Snapshot."""
    server = MCPServer(name="test_mcp_http")
    _register_eval_tools(server, transport_mode="http")
    verify_fn = server._tool_manager._tools["credence_verify_and_anchor"].fn

    url = "https://example.com/verified-snap"
    source = "The spokesperson claimed that the moon was made of green cheese yesterday."
    sha = compute_content_sha256(source)
    simhash = compute_simhash(source)

    # Seed a server-captured Snapshot
    async with get_async_session() as s:
        s.add(
            Snapshot(
                url=url,
                content_sha256=sha,
                simhash_64=simhash,
                clean_text_length=len(source),
                word_count=len(source.split()),
            )
        )
        await s.commit()

    violations_in = [
        {
            "rule_id": "SPJ-1.1",
            "rule_uri": "general:SPJ-1.1@v1.0.0",
            "domain": "GENERAL",
            "cluster_id": "GENERAL",
            "quote_or_element": "the moon was made of green cheese",
            "severity": 4,
            "confidence": 0.95,
            "reasoning": "Absurd unverified claim",
        }
    ]

    # 1. Unsigned remote call MUST be rejected (coordinator key must never sign untrusted submissions)
    res_unsigned = json.loads(
        await verify_fn(
            url=url,
            normalized_text=source,
            suspicion_score=80.0,
            classification="DECEPTIVE",
            violations=violations_in,
        )
    )
    assert res_unsigned["status"] == "rejected"
    assert "coordinator sovereign key signing is disabled" in res_unsigned["error"]

    # 2. Signed remote call with caller's own Ed25519 identity succeeds and persists under caller's pubkey
    caller_ident = load_or_create_node_identity(tmp_path / "remote_caller.key")
    density = round((1 / len(source.split())) * 1000, 2)
    report = AuditReport(
        url=url,
        content_sha256=sha,
        simhash_64=simhash,
        suspicion_score=80.0,
        suspicion_density=density,
        confidence_score=0.95,
        classification="DECEPTIVE",
        is_satire=False,
        content_type="NEWS_ARTICLE",
        violations=[SpecialistViolationFinding.model_validate(violations_in[0])],
        evaluation_method="fastmcp_in_chat_verified",
        evaluation_model="anthropic/claude-3-7-sonnet",
    )
    signed = sign_audit_report(report, caller_ident)

    res_signed = json.loads(
        await verify_fn(
            url=url,
            normalized_text=source,
            suspicion_score=80.0,
            classification="DECEPTIVE",
            violations=violations_in,
            model_name="anthropic/claude-3-7-sonnet",
            worker_pubkey=signed.node_pubkey,
            worker_signature=signed.node_signature,
            audited_at=signed.audited_at.isoformat(),
        )
    )
    assert res_signed["status"] == "anchored"
    assert res_signed["node_pubkey"] == caller_ident.public_key_hex
    assert res_signed["node_signature"] == signed.node_signature

    async with get_async_session() as s:
        audits = (await s.exec(select(Audit))).all()
        assert len(audits) == 1
        assert audits[0].node_pubkey == caller_ident.public_key_hex


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastmcp_check_url_stdio_does_not_stall_and_hits_cache():
    """Verify credence_check_url returns immediately on cached Snapshots and never hangs 25s in stdio mode."""
    server = MCPServer(name="test_mcp_stdio")
    _register_eval_tools(server, transport_mode="stdio")
    check_fn = server._tool_manager._tools["credence_check_url"].fn

    url = "https://example.com/cached-news"
    fake_report = AuditReport(
        url=url,
        content_sha256="sha256:" + "1" * 64,
        simhash_64="0x1234",
        suspicion_score=12.0,
        suspicion_density=0.0,
        confidence_score=0.9,
        classification="CLEAN",
    )

    t0 = time.monotonic()
    with patch("credence.pipeline.evaluator.audit_url", new_callable=AsyncMock, return_value=fake_report):
        res = json.loads(await check_fn(url=url, force=False))
    elapsed = time.monotonic() - t0
    assert elapsed < 3.0, f"stdio check_url unexpectedly stalled for {elapsed:.2f}s"
    assert res["classification"] == "CLEAN"
