"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging
from typing import Optional

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("credence.server.mcp")


def _register_mesh_tools(server: MCPServer) -> None:
    """Register P2P mesh discovery tools."""

    @server.tool(
        name="credence_get_seed_nodes",
        description="Retrieve verified active P2P bootstrap seed nodes from seeds.credence.nexus or fallback sources.",
    )
    async def get_seed_nodes(seed_url: Optional[str] = None) -> str:
        from credence.mesh.discovery import BootstrapDiscovery

        discovery = BootstrapDiscovery(seed_url=seed_url)
        peer_urls = await discovery.discover_peers()
        return json.dumps(
            {
                "canonical_seed_url": discovery.seed_url,
                "discovered_peers_count": len(peer_urls),
                "peer_urls": peer_urls,
            },
            indent=2,
        )
