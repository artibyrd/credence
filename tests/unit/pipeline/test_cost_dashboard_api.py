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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_verify_and_config_endpoints():
    """Verify /api/auth/verify and /api/auth/config handlers."""
    from credence.server.api.system import api_auth_config, api_auth_verify

    # Test auth config
    scope_cfg = {"type": "http", "method": "GET", "path": "/api/auth/config", "headers": []}
    res_cfg = await api_auth_config(Request(scope_cfg))
    assert res_cfg.status_code == 200

    # Test unauthorized verify
    scope_unauth = {
        "type": "http",
        "method": "GET",
        "path": "/api/auth/verify",
        "headers": [(b"host", b"testserver")],
        "client": ("192.168.1.100", 50000),
    }
    res_unauth = await api_auth_verify(Request(scope_unauth))
    assert res_unauth.status_code == 401

    # Test authorized verify with dev key
    scope_auth = {
        "type": "http",
        "method": "GET",
        "path": "/api/auth/verify",
        "headers": [(b"authorization", b"Bearer dev_admin_key"), (b"host", b"testserver")],
    }
    res_auth = await api_auth_verify(Request(scope_auth))
    assert res_auth.status_code == 200


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unauthorized_gated_endpoints_return_401():
    """Verify mutating endpoints return 401 when called by unauthorized remote clients."""
    from credence.server.api.cost import api_cost_budget
    from credence.server.api.feeds import api_boredom_cycle, api_roots_expand, api_sifter_cycle
    from credence.server.api.system import api_germinate

    unauth_scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/test",
        "headers": [(b"host", b"public.example.com")],
        "client": ("203.0.113.42", 50000),
    }

    # Test cost budget 401
    res_budget = await api_cost_budget(Request(unauth_scope))
    assert res_budget.status_code == 401

    # Test germinate 401
    res_germ = await api_germinate(Request(unauth_scope))
    assert res_germ.status_code == 401

    # Test sifter cycle 401
    res_sift = await api_sifter_cycle(Request(unauth_scope))
    assert res_sift.status_code == 401

    # Test roots expand 401
    res_roots = await api_roots_expand(Request(unauth_scope))
    assert res_roots.status_code == 401

    # Test boredom cycle 401
    res_bored = await api_boredom_cycle(Request(unauth_scope))
    assert res_bored.status_code == 401
