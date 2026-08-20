"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging
from typing import Optional

from mcp.server.mcpserver import MCPServer

from credence.config import CostProfile
from credence.db import get_async_session, init_db
from credence.pipeline.governor import get_token_headroom_status

logger = logging.getLogger("credence.server.mcp")


def _register_cost_tools_and_resources(server: MCPServer) -> None:
    """Register Cost Governance, Token Telemetry, and Autonomous Optimizer tools and resources."""

    @server.tool(
        name="credence_get_cost_telemetry",
        description="Retrieve real-time token spend, thinking token counts, hourly/daily headroom, USD spend, and Emergency Brake status.",
    )
    async def get_cost_telemetry_tool() -> str:
        from credence.cache.distributed import get_state_store

        await init_db()
        async with get_async_session() as session:
            headroom = await get_token_headroom_status(session)
            state = await get_state_store().get_runtime_cost_settings()
            data = headroom.model_dump(mode="json")
            data["emergency_brake_pulled"] = state.emergency_brake_pulled
            data["brake_reason"] = state.brake_reason
            data["runtime_daily_budget_usd"] = state.daily_budget_usd
            data["runtime_max_tokens_per_hour"] = state.max_tokens_per_hour
            data["runtime_active_profile"] = state.active_profile_override
            return json.dumps(data, indent=2)
        return "{}"

    @server.tool(
        name="credence_get_cost_recommendations",
        description="Query the Autonomous Cost Profile Optimizer for trend-based upgrade/downgrade recommendations based on rolling usage.",
    )
    async def get_cost_recommendations_tool() -> str:
        from credence.pipeline.cost_optimizer import evaluate_cost_profile_recommendation

        await init_db()
        async with get_async_session() as session:
            headroom = await get_token_headroom_status(session)
            rec = evaluate_cost_profile_recommendation(
                avg_daily_spend_usd=headroom.daily_spend_usd,
                trips_last_72h=1 if headroom.circuit_breaker_tripped else 0,
                hours_throttled_last_72h=2.0 if headroom.throttle_active else 0.0,
            )
            return json.dumps(rec.model_dump(mode="json"), indent=2)
        return "{}"

    @server.tool(
        name="credence_set_budget",
        description="Dynamically adjust live daily USD budget and hourly token ceiling across all container replicas without restarting.",
    )
    async def set_budget_tool(
        daily_budget_usd: Optional[float] = None,
        max_tokens_per_hour: Optional[int] = None,
        profile: Optional[str] = None,
    ) -> str:
        from credence.cache.distributed import get_state_store

        state_store = get_state_store()
        await state_store.set_runtime_budget_override(
            daily_budget_usd=daily_budget_usd,
            max_tokens_per_hour=max_tokens_per_hour,
            active_profile=profile,
        )
        return json.dumps({"status": "success", "message": "Runtime budget settings updated successfully."})

    @server.tool(
        name="credence_trigger_emergency_brake",
        description="Instantly pull the Emergency Brake, downshifting 100% of audits into offline heuristic mode ($0 spend).",
    )
    async def trigger_emergency_brake_tool(reason: str = "Agentic Cost Guard") -> str:
        from credence.cache.distributed import get_state_store

        state_store = get_state_store()
        await state_store.pull_emergency_brake(reason=reason)
        return json.dumps({"status": "tripped", "circuit_breaker_tripped": True, "reason": reason})

    @server.tool(
        name="credence_apply_cost_recommendation",
        description="Apply the recommended cost profile from the Autonomous Cost Optimizer.",
    )
    async def apply_cost_recommendation_tool(target_profile: str) -> str:
        from credence.cache.distributed import get_state_store

        if target_profile not in CostProfile.__members__.values():
            return json.dumps({"error": f"Invalid target profile '{target_profile}'."})

        state_store = get_state_store()
        await state_store.set_runtime_budget_override(active_profile=target_profile)
        return json.dumps({"status": "success", "active_profile": target_profile})

    @server.resource("credence://cost/telemetry")
    async def get_cost_telemetry_resource() -> str:
        return await get_cost_telemetry_tool()

    @server.resource("credence://cost/recommendations")
    async def get_cost_recommendations_resource() -> str:
        return await get_cost_recommendations_tool()

    @server.resource("credence://cost/dashboard")
    async def get_cost_dashboard_resource() -> str:
        return await get_cost_telemetry_tool()
