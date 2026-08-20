"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any

from starlette.responses import JSONResponse

from credence.db import get_async_session, init_db

logger = logging.getLogger("credence.server.api")


async def api_rankings_domains(request: Any) -> Any:
    """REST API: Query Domain Credence Index (DCI) rankings."""
    from dataclasses import asdict

    from credence.subjects.analytics import get_domain_leaderboard

    cat = request.query_params.get("category", "best")
    try:
        limit = min(int(request.query_params.get("limit", 50)), 100)
    except ValueError:
        limit = 50

    await init_db()
    async with get_async_session() as s:
        ranks = await get_domain_leaderboard(s, category=cat, limit=limit)
        return JSONResponse({"category": cat, "total": len(ranks), "rankings": [asdict(r) for r in ranks]})
    return JSONResponse({"rankings": []})


async def api_domain_reputation(request: Any) -> Any:
    """REST API: Get domain-level reputation metrics and BuzzFeed Doctrine standing."""

    from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

    domain = request.path_params.get("domain", "")
    if not domain:
        return JSONResponse({"error": "Domain required"}, status_code=400)
    await init_db()
    async with get_async_session() as session:
        record = await get_or_create_domain_reputation(session, normalize_domain(domain))
        return JSONResponse(record.model_dump(mode="json"))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_domain_quarantine(request: Any) -> Any:
    """REST API: List all currently quarantined or suspicious domains with exponential backoff."""

    from credence.feeds.reputation import get_domain_quarantine_list

    await init_db()
    async with get_async_session() as session:
        quarantined = await get_domain_quarantine_list(session)
        return JSONResponse({"total_quarantined": len(quarantined), "quarantined_domains": quarantined})
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_domain_appeal(request: Any) -> Any:
    """REST API: File an expedited BuzzFeed News Doctrine redemption appeal."""

    from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

    domain = request.path_params.get("domain", "")
    if not domain:
        return JSONResponse({"error": "Domain required"}, status_code=400)
    await init_db()
    async with get_async_session() as session:
        record = await get_or_create_domain_reputation(session, normalize_domain(domain))
        return JSONResponse(
            {
                "domain": record.domain,
                "status": record.status,
                "reputation_score": record.reputation_score,
                "appeal_status": "QUEUED_FOR_EXPEDITED_AUDIT",
                "doctrine": "The BuzzFeed News Doctrine (Asymmetric Epistemic Recovery)",
            }
        )
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)
