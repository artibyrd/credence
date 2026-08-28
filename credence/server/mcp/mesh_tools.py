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

    @server.tool(
        name="credence_submit_mesh_attestation",
        description="Submit a cryptographically signed AuditReport to a remote Credence mesh node.",
    )
    async def submit_mesh_attestation(report_json: str, node_url: Optional[str] = None) -> str:
        import httpx

        from credence.config import settings

        endpoint = node_url or settings.CREDENCE_SENTINEL_NODE_URL or "http://127.0.0.1:8000"
        submit_url = f"{endpoint.rstrip('/')}/api/mesh/submit-attestation"

        try:
            payload = json.loads(report_json) if isinstance(report_json, str) else report_json
        except Exception as e:
            return json.dumps({"error": f"Invalid JSON payload: {e}"})

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(submit_url, json=payload)
            return json.dumps(
                {
                    "status_code": resp.status_code,
                    "response": resp.json()
                    if resp.headers.get("content-type", "").startswith("application/json")
                    else resp.text,
                },
                indent=2,
            )

    @server.tool(
        name="credence_submit_mesh_batch",
        description="Submit a batch of cryptographically signed AuditReports to a remote Credence mesh node.",
    )
    async def submit_mesh_batch(batch_json: str, node_url: Optional[str] = None) -> str:
        import httpx

        from credence.config import settings

        endpoint = node_url or settings.CREDENCE_SENTINEL_NODE_URL or "http://127.0.0.1:8000"
        submit_url = f"{endpoint.rstrip('/')}/api/mesh/submit-batch"

        try:
            payload = json.loads(batch_json) if isinstance(batch_json, str) else batch_json
        except Exception as e:
            return json.dumps({"error": f"Invalid JSON batch payload: {e}"})

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(submit_url, json=payload)
            return json.dumps(
                {
                    "status_code": resp.status_code,
                    "response": resp.json()
                    if resp.headers.get("content-type", "").startswith("application/json")
                    else resp.text,
                },
                indent=2,
            )
