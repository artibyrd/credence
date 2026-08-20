"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any

from starlette.responses import JSONResponse

from credence.db import get_async_session, init_db
from credence.server.middleware.telemetry import global_telemetry

logger = logging.getLogger("credence.server.api")


async def api_mesh_stats(request: Any) -> Any:
    """REST API: Retrieve comprehensive Node & P2P Mesh health, SRE vitals, and scored pages analytics."""

    from credence.mesh.stats import compute_mesh_stats

    await init_db()
    snapshot = global_telemetry.get_snapshot()
    async with get_async_session() as s:
        stats = await compute_mesh_stats(s, telemetry_snapshot=snapshot)
        return JSONResponse(stats)
    return JSONResponse({})


async def api_mesh_network_health(request: Any) -> Any:
    """REST API: Retrieve Whole-Mesh Network Health, 13-node Watts-Strogatz topology, and Byzantine quorum metrics."""

    from credence.mesh.stats import compute_network_mesh_health

    await init_db()
    async with get_async_session() as s:
        health = await compute_network_mesh_health(s)
        return JSONResponse(health)
    health = await compute_network_mesh_health(None)
    return JSONResponse(health)
