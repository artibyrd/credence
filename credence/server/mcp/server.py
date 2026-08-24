"""FastMCP 2.0 Server Factory for Credence."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from credence import __version__
from credence.server.mcp.admin_tools import _register_admin_tools
from credence.server.mcp.consensus_tools import _register_consensus_tools
from credence.server.mcp.cost_tools import _register_cost_tools_and_resources
from credence.server.mcp.eval_tools import _register_eval_tools
from credence.server.mcp.feed_tools import _register_feed_management_tools, _register_feed_sync_tools
from credence.server.mcp.governance_tools import _register_governance_tools
from credence.server.mcp.merit_tools import _register_merit_and_analytics_resources, _register_merit_and_analytics_tools
from credence.server.mcp.mesh_tools import _register_mesh_tools
from credence.server.mcp.prompts import _register_prompts
from credence.server.mcp.query_tools import _register_query_tools
from credence.server.mcp.resources import _register_subject_resources, _register_taxonomy_resources


def create_mcp_server() -> MCPServer:
    """Instantiate and configure the Credence FastMCP server."""
    server = MCPServer(
        name="credence",
        instructions="Autonomous Epistemic Evaluation Engine, FastMCP Server, and Trust Network.",
        version=__version__,
    )
    _register_eval_tools(server)
    _register_query_tools(server)
    _register_consensus_tools(server)
    _register_mesh_tools(server)
    _register_feed_sync_tools(server)
    _register_feed_management_tools(server)
    _register_merit_and_analytics_tools(server)
    _register_cost_tools_and_resources(server)
    _register_admin_tools(server)
    _register_governance_tools(server)
    _register_taxonomy_resources(server)
    _register_subject_resources(server)
    _register_merit_and_analytics_resources(server)
    _register_prompts(server)
    return server
