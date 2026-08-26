"""Integration Gauntlet tests for Sentinel Mode, Guaranteed Organic Soil Floor, and Bootstrap Presets."""

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.testclient import TestClient

from credence.feeds.sentinel import partition_ingestion_burst
from credence.feeds.worker import bootstrap_preset_feeds
from credence.models import FeedSubscription
from credence.server.app import create_app


def test_guaranteed_organic_soil_floor_partitioning() -> None:
    """Assert partition_ingestion_burst guarantees at least 50% capacity for organic soil."""
    sentinel_items = [f"sentinel_article_{i}" for i in range(10)]
    organic_items = [f"organic_citation_{i}" for i in range(10)]

    # Total burst = 6 -> Max 3 sentinels (50%), at least 3 organic
    burst_6 = partition_ingestion_burst(sentinel_items, organic_items, total_burst=6, max_sentinel_ratio=0.50)
    assert len(burst_6) == 6
    assert sum(1 for item in burst_6 if "sentinel" in item) == 3
    assert sum(1 for item in burst_6 if "organic" in item) == 3

    # Total burst = 10 -> Max 5 sentinels, 5 organic
    burst_10 = partition_ingestion_burst(sentinel_items, organic_items, total_burst=10, max_sentinel_ratio=0.50)
    assert len(burst_10) == 10
    assert sum(1 for item in burst_10 if "sentinel" in item) == 5
    assert sum(1 for item in burst_10 if "organic" in item) == 5

    # Starved organic queue (0 organic candidates) -> Falls back to sentinels up to burst
    burst_starved = partition_ingestion_burst(sentinel_items, [], total_burst=4, max_sentinel_ratio=0.50)
    assert len(burst_starved) == 4
    assert all("sentinel" in item for item in burst_starved)


@pytest.mark.asyncio
async def test_inmaricopa_preset_sentinel_bootstrap(db_session: AsyncSession) -> None:
    """Assert bootstrap_preset_feeds configures inmaricopa.com as an active sentinel preset."""
    added = await bootstrap_preset_feeds(db_session, category="regional-civic")
    assert added >= 1

    stmt = select(FeedSubscription).where(FeedSubscription.feed_url == "https://inmaricopa.com/feed/")
    inmaricopa_sub = (await db_session.exec(stmt)).first()

    assert inmaricopa_sub is not None
    assert inmaricopa_sub.is_sentinel is True
    assert inmaricopa_sub.sentinel_interval_seconds == 300
    assert inmaricopa_sub.priority_tier == 1


@pytest.mark.asyncio
async def test_sentinel_rest_api(db_session: AsyncSession) -> None:
    """Test Starlette REST API endpoints for Sentinel Mode."""
    app = create_app()
    client = TestClient(app)

    # 1. GET /api/feeds/sentinels
    resp_list = client.get("/api/feeds/sentinels")
    assert resp_list.status_code == 200
    assert "sentinels" in resp_list.json()

    # 2. POST /api/feeds/sentinel with invalid credentials -> 401 Unauthorized
    resp_unauth = client.post(
        "/api/feeds/sentinel",
        json={"target": "https://inmaricopa.com/feed/"},
        headers={"Authorization": "Bearer invalid_secret_token"},
    )
    assert resp_unauth.status_code == 401

    # 3. POST /api/feeds/sentinel valid configuration -> 200 OK
    resp_ok = client.post(
        "/api/feeds/sentinel",
        json={"target": "https://inmaricopa.com/feed/", "enabled": True, "interval_seconds": 180},
    )
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["is_sentinel"] is True
    assert data["interval_seconds"] == 180
