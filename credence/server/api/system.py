"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any

from starlette.responses import JSONResponse

from credence.db import get_async_session, init_db
from credence.server.middleware.telemetry import global_telemetry

logger = logging.getLogger("credence.server.api")


async def api_health(request: Any) -> Any:
    """REST API: Health check endpoint with Interface Telemetry Loopback (ITLP-v1)."""

    from credence import __version__

    telemetry_data = global_telemetry.get_snapshot()
    return JSONResponse(
        {
            "status": telemetry_data["status"],
            "service": "credence",
            "version": __version__,
            "telemetry": telemetry_data,
        }
    )


async def api_germinate(request: Any) -> Any:
    """REST API: Trigger rapid node germination and Miracle-Gro burst."""

    from credence.germinate import germinate_node

    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}

    burst = int(body.get("burst", request.query_params.get("burst", 3)))
    sync_mesh = bool(body.get("sync_mesh", request.query_params.get("sync_mesh", True)))
    profile = body.get("profile", request.query_params.get("profile", None))

    await init_db()
    async with get_async_session() as session:
        summary = await germinate_node(
            session=session,
            burst_items=burst,
            sync_mesh=sync_mesh,
            profile_override=profile,
            verbose=True,
        )
        return JSONResponse(summary.model_dump(mode="json"))
