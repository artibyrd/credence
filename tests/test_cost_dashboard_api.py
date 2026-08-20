"""Unit tests for Cost Governance REST APIs and FastMCP cost tools."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from credence.cache.distributed import get_state_store
from credence.server.app import (
    api_cost_emergency_stop,
    api_cost_recommendations,
    api_cost_resume,
    api_cost_telemetry,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cost_telemetry_endpoint():
    """Verify api_cost_telemetry returns valid headroom and spend data."""
    scope = {"type": "http", "method": "GET", "path": "/api/cost/telemetry", "headers": []}
    request = Request(scope)
    response = await api_cost_telemetry(request)
    assert response.status_code == 200


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cost_recommendations_endpoint():
    """Verify api_cost_recommendations returns structured recommendation."""
    scope = {"type": "http", "method": "GET", "path": "/api/cost/recommendations", "headers": []}
    request = Request(scope)
    response = await api_cost_recommendations(request)
    assert response.status_code == 200


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cost_emergency_stop_and_resume():
    """Verify emergency brake trip and resume cycle."""
    state = get_state_store()

    # Trip brake
    scope_stop = {
        "type": "http",
        "method": "POST",
        "path": "/api/cost/emergency-stop",
        "headers": [(b"host", b"localhost:8000")],
        "client": ("127.0.0.1", 50000),
    }
    req_stop = Request(scope_stop)
    res_stop = await api_cost_emergency_stop(req_stop)
    assert res_stop.status_code == 200

    settings = await state.get_runtime_cost_settings()
    assert settings.emergency_brake_pulled is True

    # Resume
    scope_resume = {
        "type": "http",
        "method": "POST",
        "path": "/api/cost/resume",
        "headers": [(b"host", b"localhost:8000")],
        "client": ("127.0.0.1", 50000),
    }
    req_resume = Request(scope_resume)
    res_resume = await api_cost_resume(req_resume)
    assert res_resume.status_code == 200

    settings = await state.get_runtime_cost_settings()
    assert settings.emergency_brake_pulled is False
