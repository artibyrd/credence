"""Unit tests for FastMCP 2.0 Governance & Standards RFC Tools and Resources (Phase 2).

Tests:
- credence_list_rfcs
- credence_get_rfc
- credence_validate_standard
- credence_benchmark_standard
- credence://governance/rfcs
- credence://governance/rfcs/{rfc_id}
"""

import json

import pytest

from credence.server.mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_mcp_governance_tools_and_resources() -> None:
    """Verify FastMCP 2.0 governance tools and resources execute and return valid JSON."""
    server = create_mcp_server()

    # 1. Test credence_list_rfcs tool
    list_tool = server._tool_manager.get_tool("credence_list_rfcs")
    assert list_tool is not None
    result_str = await list_tool.fn()
    rfcs = json.loads(result_str)
    assert isinstance(rfcs, list)
    assert len(rfcs) >= 3

    # 2. Test credence_get_rfc tool
    get_tool = server._tool_manager.get_tool("credence_get_rfc")
    assert get_tool is not None
    rfc_res = await get_tool.fn(rfc_id="RFC-001")
    rfc_data = json.loads(rfc_res)
    assert rfc_data["rfc_id"] == "RFC-001"
    assert rfc_data["stage"] == "RATIFIED"

    # 3. Test credence_validate_standard tool
    valid_yaml = """
catalog_id: "mcp_test_cat"
domain: "TEST"
name: "MCP Test Catalog"
version: "1.0.0"
description: "Test description"
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "T-1.1"
        name: "Test Rule"
        severity: 3
        description: "Test rule description"
        detection_signals:
          - "Signal 1"
          - "Signal 2"
        evidence_guidelines: "Must quote evidence."
"""
    val_tool = server._tool_manager.get_tool("credence_validate_standard")
    assert val_tool is not None
    val_res = await val_tool.fn(yaml_content=valid_yaml)
    val_data = json.loads(val_res)
    assert val_data["valid"] is True
    assert val_data["rules_count"] == 1
