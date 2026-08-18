"""Live Multi-Domain End-to-End Integration Test Suite for Credence.

NOTE: This suite tests real production endpoints across:
1. https://credence.run (Landing Hub & Installer)
2. https://mcp.credence.run/sse (FastMCP 2.0 Server-Sent Events)
3. https://seeds.credence.nexus/peers.json (Signed Bootstrap Seed Directory)
4. https://taxonomies.credence.foundation (Static JSON Catalogs & Root Key)
5. https://credence.report (Public Audit Viewer & Social Card Cards)

In accordance with Invariant 4, this suite is strictly segregated under the `e2e` mark
and only executes when CREDENCE_LIVE_TESTS=1 is explicitly set.
"""

from __future__ import annotations

import os
import subprocess

import httpx
import pytest

from credence.mesh.seed import BootstrapSeedFile, verify_seed_file

LIVE_TESTS_ENABLED = os.environ.get("CREDENCE_LIVE_TESTS") == "1"
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not LIVE_TESTS_ENABLED,
        reason="Live domain tests require CREDENCE_LIVE_TESTS=1 and active internet connectivity.",
    ),
]

DOMAIN_RUN = os.environ.get("CREDENCE_TEST_DOMAIN_RUN", "https://credence.run")
DOMAIN_MCP = os.environ.get("CREDENCE_TEST_DOMAIN_MCP", "https://mcp.credence.run")
DOMAIN_NEXUS = os.environ.get("CREDENCE_TEST_DOMAIN_NEXUS", "https://seeds.credence.nexus")
DOMAIN_FOUNDATION = os.environ.get("CREDENCE_TEST_DOMAIN_FOUNDATION", "https://taxonomies.credence.foundation")
DOMAIN_REPORT = os.environ.get("CREDENCE_TEST_DOMAIN_REPORT", "https://credence.report")


@pytest.mark.asyncio
async def test_live_mcp_sse_handshake() -> None:
    """Verify live FastMCP SSE endpoint connects and streams endpoint session event."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        async with client.stream("GET", f"{DOMAIN_MCP}/sse") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            first_chunk = ""
            async for chunk in response.aiter_text():
                first_chunk += chunk
                if "session_id" in first_chunk or "endpoint" in first_chunk:
                    break
            assert "session_id" in first_chunk or "endpoint" in first_chunk


@pytest.mark.asyncio
async def test_live_seed_file_verification() -> None:
    """Fetch live signed seed manifest and cryptographically verify RFC 8785 signature."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(f"{DOMAIN_NEXUS}/peers.json")
        assert response.status_code == 200

        data = response.json()
        manifest = BootstrapSeedFile.model_validate(data)

        # Verify RFC 8785 deterministic Ed25519 signature
        is_valid = verify_seed_file(manifest)
        assert is_valid is True
        assert len(manifest.seed_nodes) >= 1


@pytest.mark.asyncio
async def test_live_foundation_catalogs_and_root_key() -> None:
    """Verify static taxonomy catalogs and root public key on live foundation domain."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # 1. Fetch root public key
        key_resp = await client.get(f"{DOMAIN_FOUNDATION}/keys/root.pub")
        assert key_resp.status_code == 200
        root_pubkey = key_resp.text.strip()
        assert len(root_pubkey) == 64  # 32-byte Ed25519 hex

        # 2. Fetch SPJ Ethics catalog
        cat_resp = await client.get(f"{DOMAIN_FOUNDATION}/v1/spj_ethics.json")
        assert cat_resp.status_code == 200
        cat_data = cat_resp.json()
        assert cat_data["catalog_id"] == "spj_ethics"
        assert len(cat_data["clusters"]) >= 1


@pytest.mark.asyncio
async def test_live_report_viewer_render() -> None:
    """Verify public report domain serves HTML with OpenGraph tags."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(f"{DOMAIN_REPORT}/viewer.html")
        assert response.status_code == 200
        html = response.text
        assert '<meta property="og:site_name"' in html
        assert "Credence" in html


@pytest.mark.asyncio
async def test_live_install_script_syntax() -> None:
    """Fetch live installer and verify valid POSIX shell syntax."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(f"{DOMAIN_RUN}/install.sh")
        assert response.status_code == 200
        script_text = response.text
        assert "#!/usr/bin/env sh" in script_text

        # Verify shell syntax via sh -n
        proc = subprocess.run(["sh", "-n"], input=script_text.encode("utf-8"), capture_output=True)
        assert proc.returncode == 0
