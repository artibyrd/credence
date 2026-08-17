"""Offline Mock End-to-End Integration Test Suite for Credence.

Hermetically simulates all 4 canonical domain endpoints offline using httpx MockTransport:
1. FastMCP SSE stream endpoint
2. Signed bootstrap seed manifest verification (RFC 8785 Ed25519)
3. Taxonomy catalog registry lookup
4. Report viewer HTML rendering and OpenGraph verification
5. Install script POSIX compliance validation
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import httpx
import pytest

from credence.identity import load_or_create_node_identity
from credence.mesh.seed import BootstrapSeedFile, SeedNodeEntry, generate_seed_file, verify_seed_file
from credence.taxonomy_loader import registry


def _create_mock_handler(identity, seed_json: str):
    """Create simulated ASGI/HTTP handler responding for all 4 domains."""
    registry.load_all()
    spj_cat = registry.get_catalog("spj_ethics")
    spj_json = json.dumps(spj_cat.model_dump(mode="json")) if spj_cat else "{}"

    web_root = Path("web")
    run_html = (
        (web_root / "credence.run" / "index.html").read_text(encoding="utf-8")
        if (web_root / "credence.run" / "index.html").exists()
        else "<html>Credence Run</html>"
    )
    install_sh = (
        (web_root / "credence.run" / "install.sh").read_text(encoding="utf-8")
        if (web_root / "credence.run" / "install.sh").exists()
        else "#!/usr/bin/env sh\necho ok\n"
    )
    report_html = (
        (web_root / "credence.report" / "viewer.html").read_text(encoding="utf-8")
        if (web_root / "credence.report" / "viewer.html").exists()
        else "<html>Credence Report</html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "mcp.credence.run/sse" in url:
            return httpx.Response(
                200, headers={"Content-Type": "text/event-stream"}, content=b"event: endpoint\ndata: /messages\n\n"
            )
        elif "seeds.credence.nexus/peers.json" in url:
            return httpx.Response(200, headers={"Content-Type": "application/json"}, text=seed_json)
        elif "taxonomies.credence.foundation/keys/root.pub" in url:
            return httpx.Response(200, text=identity.public_key_hex)
        elif "taxonomies.credence.foundation/v1/spj_ethics.json" in url:
            return httpx.Response(200, headers={"Content-Type": "application/json"}, text=spj_json)
        elif "credence.report/viewer.html" in url:
            return httpx.Response(200, headers={"Content-Type": "text/html"}, text=report_html)
        elif "credence.run/install.sh" in url:
            return httpx.Response(200, headers={"Content-Type": "text/plain"}, text=install_sh)
        elif "credence.run" in url:
            return httpx.Response(200, headers={"Content-Type": "text/html"}, text=run_html)
        return httpx.Response(404, text="Not Found")

    return handler


@pytest.mark.asyncio
async def test_mock_e2e_multi_domain_workflow() -> None:
    """Hermetically verify complete 4-domain integration flow against mock HTTP transport."""
    identity = load_or_create_node_identity()
    nodes = [
        SeedNodeEntry(
            node_pubkey=identity.public_key_hex,
            node_alias="anchor-mock-1",
            ws_url="wss://relay.credence.nexus:8765",
            quality_score=0.99,
            uptime_pct=99.9,
            region="us-central1",
        )
    ]
    manifest = generate_seed_file(nodes, identity=identity, valid_hours=24)
    seed_json = json.dumps(manifest.model_dump(mode="json"))

    mock_transport = httpx.MockTransport(_create_mock_handler(identity, seed_json))

    async with httpx.AsyncClient(transport=mock_transport) as client:
        # 1. Test FastMCP SSE Endpoint
        sse_resp = await client.get("https://mcp.credence.run/sse")
        assert sse_resp.status_code == 200
        assert "text/event-stream" in sse_resp.headers.get("content-type", "")

        # 2. Test Signed Seed Manifest & Verify RFC 8785 Signature
        seed_resp = await client.get("https://seeds.credence.nexus/peers.json")
        assert seed_resp.status_code == 200
        fetched_manifest = BootstrapSeedFile.model_validate(seed_resp.json())
        assert verify_seed_file(fetched_manifest) is True
        assert fetched_manifest.seed_nodes[0].node_alias == "anchor-mock-1"

        # 3. Test Foundation Root Key & Catalog
        pubkey_resp = await client.get("https://taxonomies.credence.foundation/keys/root.pub")
        assert pubkey_resp.status_code == 200
        assert pubkey_resp.text.strip() == identity.public_key_hex

        cat_resp = await client.get("https://taxonomies.credence.foundation/v1/spj_ethics.json")
        assert cat_resp.status_code == 200
        assert cat_resp.json()["catalog_id"] == "spj_ethics"

        # 4. Test Report Viewer & OpenGraph Tags
        report_resp = await client.get("https://credence.report/viewer.html")
        assert report_resp.status_code == 200
        assert '<meta property="og:site_name"' in report_resp.text
        assert "Credence" in report_resp.text

        # 5. Test Install Script Syntax
        install_resp = await client.get("https://credence.run/install.sh")
        assert install_resp.status_code == 200
        sh_syntax = subprocess.run(["sh", "-n"], input=install_resp.text.encode("utf-8"), capture_output=True)
        assert sh_syntax.returncode == 0
