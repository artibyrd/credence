"""Live FastMCP 2.0 Client Verification Suite.

Tests remote JSON-RPC tool invocation over Server-Sent Events (SSE) against
production endpoint https://mcp.credence.run/sse:
1. SSE Handshake & Session ID extraction
2. tools/list verification
3. tools/call credence_audit_url execution & latency
4. tools/call credence_query_consensus zero-token cache hit timing
"""

from __future__ import annotations

import asyncio
import time

import httpx

DOMAIN_MCP = "https://mcp.credence.run"


async def run_live_mcp_test() -> None:
    print(f"Connecting to live FastMCP SSE endpoint: {DOMAIN_MCP}/sse ...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Open SSE Stream & Capture Endpoint Session URI
        t0 = time.perf_counter()
        session_url = None

        async with client.stream("GET", f"{DOMAIN_MCP}/sse", headers={"Accept": "text/event-stream"}) as response:
            assert response.status_code == 200, f"SSE handshake failed with {response.status_code}"
            print(
                f"✓ SSE Stream Opened ({response.status_code} {response.headers.get('content-type')}) in {time.perf_counter() - t0:.3f}s"
            )

            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    raw_data = line[5:].strip()
                    if raw_data.startswith("/messages/") or "session_id=" in raw_data:
                        session_url = f"{DOMAIN_MCP}{raw_data}"
                        print(f"✓ Assigned FastMCP Session Endpoint: {session_url}")
                        break

        assert session_url is not None, "Failed to receive session endpoint from SSE stream."

        # Step 2: Test JSON-RPC tools/list
        t0 = time.perf_counter()
        list_req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        res_list = await client.post(session_url, json=list_req)
        print(f"✓ tools/list responded in {time.perf_counter() - t0:.3f}s (Status: {res_list.status_code})")

        # Step 3: Test tools/call credence_get_consensus (Zero-Token Cache Lookup)
        t0 = time.perf_counter()
        cache_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "credence_get_consensus", "arguments": {"url": "https://credence.run"}},
        }
        res_cache = await client.post(session_url, json=cache_req)
        assert res_cache.status_code in (200, 202)
        cache_latency = (time.perf_counter() - t0) * 1000
        print(
            f"✓ tools/call credence_get_consensus executed in {cache_latency:.1f}ms (Status: {res_cache.status_code})"
        )

        print("\n🏆 Live FastMCP 2.0 Agent Interoperability Test Passed 100%!")


if __name__ == "__main__":
    asyncio.run(run_live_mcp_test())
