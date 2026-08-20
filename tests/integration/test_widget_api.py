import pytest
from starlette.testclient import TestClient

from credence.db import init_db
from credence.server.app import create_app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_api_badge_data_404_on_unknown():
    await init_db()
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/v1/badge/sha256:nonexistent99999")
        assert resp.status_code == 404
        data = resp.json()
        assert data["status"] == "UNAUDITED"


async def test_api_history_404_on_unknown():
    await init_db()
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/v1/history/https://nonexistent-url.xyz")
        assert resp.status_code == 404
