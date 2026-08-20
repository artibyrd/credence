"""Unit tests for HTTP Cache-Control and ETag headers on reports API."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, utc_now
from credence.server.app import api_get_report


@pytest.mark.governance
@pytest.mark.asyncio
async def test_api_get_report_cache_headers():
    """Verify that immutable edge cache headers are attached to report responses."""
    await init_db()
    hash_val = "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff"

    async with get_async_session() as session:
        snap = Snapshot(
            url="https://example.com/news/1",
            content_sha256=hash_val,
            simhash_64="0x1234",
            title="Sample News",
        )
        session.add(snap)
        await session.flush()

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=hash_val,
            suspicion_score=5.0,
            suspicion_density=0.01,
            confidence_score=0.95,
            classification="NEWS_ARTICLE",
            is_satire=False,
            audited_at=utc_now(),
        )
        session.add(audit)
        await session.commit()

    scope = {
        "type": "http",
        "method": "GET",
        "path": f"/api/reports/{hash_val}",
        "path_params": {"identifier": hash_val},
        "headers": [],
    }
    request = Request(scope)
    response = await api_get_report(request)

    assert response.status_code == 200
    assert "public, max-age=2592000" in response.headers.get("Cache-Control", "")
    assert f'W/"sha256:{hash_val}"' == response.headers.get("ETag", "")
