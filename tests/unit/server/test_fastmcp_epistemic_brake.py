"""Unit tests for FastMCP Epistemic Brake and in-chat verification tools."""

import json

import pytest
from mcp.server.mcpserver import MCPServer
from sqlmodel import delete

from credence.db import get_async_session, init_db
from credence.models import Audit, AuditJob, Snapshot, Violation
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
        await session.commit()


@pytest.mark.asyncio
async def test_fastmcp_verify_and_anchor_grounding_rejection():
    """Test that credence_verify_and_anchor rejects ungrounded quotes (G < 1.00)."""
    server = MCPServer(name="test_mcp")
    _register_eval_tools(server)

    verify_fn = server._tool_manager._tools["credence_verify_and_anchor"].fn

    # Source text does NOT contain the quote
    source = "Clean factual reporting about a new solar energy facility."
    violations = [
        {
            "rule_id": "SPJ-1.1",
            "quote_or_element": "Fabricated allegation of embezzlement",
            "severity": 4,
            "reasoning": "Ungrounded claim",
        }
    ]

    res_str = await verify_fn(
        url="https://example.com/solar",
        normalized_text=source,
        suspicion_score=75.0,
        classification="DECEPTIVE",
        violations=violations,
    )
    res = json.loads(res_str)
    assert res["status"] == "rejected"
    assert "Grounding precision G < 1.00" in res["error"]


@pytest.mark.asyncio
async def test_fastmcp_verify_and_anchor_success():
    """Test that credence_verify_and_anchor persists verified and signed audit."""
    server = MCPServer(name="test_mcp")
    _register_eval_tools(server)

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

    res_str = await verify_fn(
        url="https://example.com/moon-cheese",
        normalized_text=source,
        suspicion_score=80.0,
        classification="DECEPTIVE",
        violations=violations,
        model_name="anthropic/claude-3-7-sonnet",
    )
    res = json.loads(res_str)
    assert res["status"] == "anchored"
    assert res["violations_anchored"] == 1
    assert res["node_pubkey"] is not None
    assert res["node_signature"] is not None

    # Check persistence in database
    async with get_async_session() as s:
        from sqlmodel import select

        audits = (await s.exec(select(Audit))).all()
        assert len(audits) == 1
        assert audits[0].node_signature == res["node_signature"]
