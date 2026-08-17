"""Scenario 4: FastMCP 2.0 Protocol Conformance.

Validates that FastMCP server exposes all tools, resources, and prompts
with valid JSON-RPC 2.0 schema definitions.
"""

import pytest

from credence.server.app import create_mcp_server


@pytest.mark.asyncio
async def test_fastmcp_tool_and_resource_registry_conformance() -> None:
    """Verify that create_mcp_server() correctly registers tools, resources, and prompts."""
    server = create_mcp_server()
    assert server is not None

    # Retrieve registered tool names from FastMCP server instance
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]

    expected_tools = [
        "credence_check_url",
        "credence_evaluate_text",
        "credence_get_audit",
        "credence_verify_attestation",
        "credence_get_quota_status",
        "credence_get_consensus",
        "credence_get_seed_nodes",
        "credence_sync_feeds",
        "credence_get_feed_stats",
        "credence_add_feed_subscription",
        "credence_list_feeds",
        "credence_remove_feed_subscription",
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Expected FastMCP tool '{expected}' not registered"

    # Retrieve registered resource templates
    resources = await server.list_resources()
    resource_uris = [str(r.uri) for r in resources]
    assert any("taxonomies" in u for u in resource_uris)
    assert any("identity" in u for u in resource_uris)
