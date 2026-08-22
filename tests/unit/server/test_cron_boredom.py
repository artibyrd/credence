from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport

from credence.feeds.boredom import BoredomCycleSummary
from credence.feeds.worker import FeedSyncSummary
from credence.server.app import create_server_app


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cron_boredom_endpoint_and_stats_parity(db_session: Any) -> None:
    """Verify /cron/boredom executes adaptive heartbeat and updates stats in-memory."""
    app = create_server_app()
    transport = ASGITransport(app=app)

    mock_sifter_res = FeedSyncSummary(new_items_discovered=2)
    mock_boredom_res = BoredomCycleSummary(
        boredom_ratio=0.6,
        pending_items_audited=3,
        mesh_attestations_adopted=0,
        headroom_daily_pct=95.0,
    )

    with (
        patch("credence.feeds.sifter.run_sifting_cycle", new_callable=AsyncMock) as mock_sifter,
        patch("credence.feeds.boredom.run_boredom_cycle", new_callable=AsyncMock) as mock_boredom,
    ):
        mock_sifter.return_value = mock_sifter_res
        mock_boredom.return_value = mock_boredom_res

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Trigger /cron/boredom
            resp = await client.post("/cron/boredom")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("completed", "skipped")
            assert "mode" in data
            assert "excitement_score" in data

            # 2. Verify /api/node/stats reports live dynamic boredom_engine
            stats_resp = await client.get("/api/node/stats")
            assert stats_resp.status_code == 200
            stats_data = stats_resp.json()
            bored = stats_data["boredom_engine"]
            assert "state" in bored
            assert "excitement_mode" in bored
            assert bored["state"] in ("HYPER_EXCITED", "ACTIVE", "MAINTENANCE", "IDLE", "QUOTA_PRESERVED")
