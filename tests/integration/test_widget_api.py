import xml.etree.ElementTree as ET

import pytest
from httpx import ASGITransport, AsyncClient

from credence.db import init_db
from credence.server.app import create_app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_api_badge_data_404_on_unknown():
    await init_db()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/badge/sha256:nonexistent99999")
        assert resp.status_code == 404
        data = resp.json()
        assert data["status"] == "UNAUDITED"


async def test_api_history_404_on_unknown():
    await init_db()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/history/https://nonexistent-url.xyz")
        assert resp.status_code == 404


async def test_api_badge_svg_endpoint():
    """Verify /api/badge/{badge_id} returns valid SVG with Cache-Control headers."""
    await init_db()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Default pill style
        resp = await client.get("/api/badge/verified_auditor?node=anchor-node-01&style=pill")
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers["content-type"]
        assert "public, max-age=300" in resp.headers.get("cache-control", "")
        tree = ET.fromstring(resp.content.decode("utf-8"))
        assert tree.tag.endswith("svg")
        assert "anchor-node-01" in resp.text
        assert "Verified Auditor" in resp.text

        # Shield style
        resp_shield = await client.get("/api/badge/root_seed_candidate?node=seed-01&style=shield")
        assert resp_shield.status_code == 200
        tree_shield = ET.fromstring(resp_shield.content.decode("utf-8"))
        assert tree_shield.tag.endswith("svg")


async def test_api_publisher_badge_svg_endpoint():
    """Verify /api/badge/publisher/{domain} returns valid publisher SVG badge."""
    await init_db()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/badge/publisher/reuters.com?style=shield")
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers["content-type"]
        tree = ET.fromstring(resp.content.decode("utf-8"))
        assert tree.tag.endswith("svg")
        assert "reuters.com" in resp.text
