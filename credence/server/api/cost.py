"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any

from starlette.responses import JSONResponse

from credence.db import get_async_session, init_db
from credence.server.middleware.security import _check_admin_auth

logger = logging.getLogger("credence.server.api")


async def api_cost_telemetry(request: Any) -> Any:
    """REST API: Query real-time token spend, headroom, and live cost telemetry."""

    from credence.cache.distributed import get_state_store
    from credence.pipeline.governor import get_token_headroom_status

    await init_db()
    async with get_async_session() as s:
        headroom = await get_token_headroom_status(s)
        state = await get_state_store().get_runtime_cost_settings()
        data = headroom.model_dump(mode="json")
        data["emergency_brake_pulled"] = state.emergency_brake_pulled
        data["brake_reason"] = state.brake_reason
        data["runtime_daily_budget_usd"] = state.daily_budget_usd
        data["runtime_max_tokens_per_hour"] = state.max_tokens_per_hour
        data["runtime_active_profile"] = state.active_profile_override
        return JSONResponse(data)
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_cost_recommendations(request: Any) -> Any:
    """REST API: Query autonomous Cost Profile Optimizer upgrade/downgrade recommendation."""

    from credence.pipeline.cost_optimizer import evaluate_cost_profile_recommendation
    from credence.pipeline.governor import get_token_headroom_status

    await init_db()
    async with get_async_session() as s:
        headroom = await get_token_headroom_status(s)
        rec = evaluate_cost_profile_recommendation(
            avg_daily_spend_usd=headroom.daily_spend_usd,
            trips_last_72h=1 if headroom.circuit_breaker_tripped else 0,
            hours_throttled_last_72h=2.0 if headroom.throttle_active else 0.0,
        )
        return JSONResponse(rec.model_dump(mode="json"))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_cost_budget(request: Any) -> Any:
    """REST API: Update live runtime budget and token ceilings."""

    from credence.cache.distributed import get_state_store

    if not bool(_check_admin_auth(request)):
        return JSONResponse({"error": "Unauthorized: Administrator Bearer token required"}, status_code=401)

    try:
        body = await request.json() if request.method == "POST" else {}
    except Exception:
        body = {}

    daily_budget = body.get("daily_budget_usd", request.query_params.get("daily_budget_usd"))
    max_tokens = body.get("max_tokens_per_hour", request.query_params.get("max_tokens_per_hour"))
    profile = body.get("profile", request.query_params.get("profile"))

    state_store = get_state_store()
    await state_store.set_runtime_budget_override(
        daily_budget_usd=float(daily_budget) if daily_budget is not None else None,
        max_tokens_per_hour=int(max_tokens) if max_tokens is not None else None,
        active_profile=str(profile) if profile is not None else None,
    )
    return JSONResponse({"status": "success", "message": "Runtime cost settings updated"})


async def api_cost_emergency_stop(request: Any) -> Any:
    """REST API: Pull 1-Click Emergency Brake into QUOTA_PRESERVED offline mode."""

    from credence.cache.distributed import get_state_store

    if not bool(_check_admin_auth(request)):
        return JSONResponse({"error": "Unauthorized: Administrator Bearer token required"}, status_code=401)

    try:
        body = await request.json() if request.method == "POST" else {}
    except Exception:
        body = {}

    reason = body.get("reason", "Operator Emergency Stop")
    state_store = get_state_store()
    await state_store.pull_emergency_brake(reason=reason)
    return JSONResponse({"status": "tripped", "circuit_breaker_tripped": True, "reason": reason})


async def api_cost_resume(request: Any) -> Any:
    """REST API: Release Emergency Brake and resume AI operations."""

    from credence.cache.distributed import get_state_store

    if not bool(_check_admin_auth(request)):
        return JSONResponse({"error": "Unauthorized: Administrator Bearer token required"}, status_code=401)

    state_store = get_state_store()
    await state_store.release_emergency_brake()
    return JSONResponse({"status": "resumed", "circuit_breaker_tripped": False})
