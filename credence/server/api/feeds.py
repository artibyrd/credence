"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any

from sqlmodel import col, func, select
from starlette.responses import JSONResponse

from credence.db import get_async_session, init_db
from credence.models import FeedItem, FeedSubscription

logger = logging.getLogger("credence.server.api")


async def api_sifter_status(request: Any) -> Any:
    """REST API: Get current sifter daemon status and telemetry."""

    from credence.feeds.sifter import get_sifter_status

    await init_db()
    async with get_async_session() as session:
        status = await get_sifter_status(session)
        return JSONResponse(status)
    return JSONResponse({"status": "unavailable"}, status_code=500)


async def api_sifter_cycle(request: Any) -> Any:
    """REST API: Trigger an immediate sifting cycle."""

    from credence.feeds.sifter import run_sifting_cycle

    await init_db()
    async with get_async_session() as session:
        summary = await run_sifting_cycle(session)
        return JSONResponse(
            {
                "status": "completed",
                "summary": {
                    "total_feeds_polled": summary.total_feeds_polled,
                    "feeds_unmodified_304": summary.feeds_unmodified_304,
                    "new_items_discovered": summary.new_items_discovered,
                    "items_adopted_from_mesh": summary.items_adopted_from_mesh,
                    "items_evaluated_locally": summary.items_evaluated_locally,
                    "tokens_saved_total": summary.tokens_saved_total,
                },
            }
        )
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_feeds_stream(request: Any) -> Any:
    """REST API: Stream recent feed items."""

    limit = min(int(request.query_params.get("limit", 30)), 100)
    await init_db()
    async with get_async_session() as session:
        stmt = (
            select(FeedItem, FeedSubscription)
            .join(FeedSubscription, col(FeedItem.feed_id) == col(FeedSubscription.id), isouter=True)
            .order_by(col(FeedItem.discovered_at).desc())
            .limit(limit)
        )
        results = (await session.exec(stmt)).all()
        items = []
        for item, sub in results:
            items.append(
                {
                    "id": item.id,
                    "url": item.item_url,
                    "title": item.title,
                    "feed_title": sub.title if sub else "",
                    "feed_url": sub.feed_url if sub else "",
                    "subject": item.subject_id,
                    "processing_status": item.processing_status,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                    "discovered_at": item.discovered_at.isoformat() if item.discovered_at else None,
                }
            )
        return JSONResponse({"items": items, "count": len(items)})
    return JSONResponse({"items": [], "count": 0})


async def api_roots_expand(request: Any) -> Any:
    """REST API: Trigger autonomous root expansion from cited domains."""
    from dataclasses import asdict

    from credence.feeds.roots import expand_roots

    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
    max_sources = int(body.get("max_sources", request.query_params.get("max_sources", 5)))
    dry_run = bool(body.get("dry_run", request.query_params.get("dry_run", False)))

    await init_db()
    async with get_async_session() as s:
        summary = await expand_roots(s, max_new_sources=max_sources, dry_run=dry_run)
        return JSONResponse(asdict(summary))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_roots_tree(request: Any) -> Any:
    """REST API: Retrieve hierarchical root and subscription tree."""

    from credence.feeds.roots import get_root_tree

    await init_db()
    async with get_async_session() as s:
        tree = await get_root_tree(s)
        return JSONResponse(tree)
    return JSONResponse({"active_roots": [], "total_active_roots": 0})


async def api_roots_candidates(request: Any) -> Any:
    """REST API: Retrieve candidate domains cited by audited articles."""
    from dataclasses import asdict

    from credence.feeds.roots import extract_root_candidates

    limit = min(int(request.query_params.get("limit", 20)), 50)
    await init_db()
    async with get_async_session() as s:
        cands = await extract_root_candidates(s, limit=limit)
        return JSONResponse({"total": len(cands), "candidates": [asdict(c) for c in cands]})
    return JSONResponse({"total": 0, "candidates": []})


async def api_boredom_cycle(request: Any) -> Any:
    """REST API: Trigger an immediate opportunistic boredom cycle."""
    from dataclasses import asdict

    from credence.feeds.boredom import run_boredom_cycle

    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
    burst = int(body.get("burst", request.query_params.get("burst", 3)))
    ratio = float(body.get("ratio", body.get("boredom_ratio", request.query_params.get("ratio", 0.60))))
    expand_roots_enabled = bool(body.get("expand_roots", request.query_params.get("expand_roots", True)))

    await init_db()
    async with get_async_session() as s:
        summary = await run_boredom_cycle(
            s,
            audit_burst=burst,
            boredom_ratio=ratio,
            expand_roots_enabled=expand_roots_enabled,
        )
        res = asdict(summary)
        res["timestamp"] = summary.timestamp.isoformat()
        return JSONResponse(res)
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_boredom_status(request: Any) -> Any:
    """REST API: Get real-time boredom engine and token headroom telemetry."""
    from sqlmodel import col, select
    from starlette.responses import JSONResponse

    from credence.pipeline.governor import get_token_headroom_status

    await init_db()
    async with get_async_session() as s:
        headroom = await get_token_headroom_status(s)
        stmt_pending = select(func.count(col(FeedItem.id))).where(FeedItem.processing_status == "pending")
        pending_count = (await s.exec(stmt_pending)).first() or 0
        stmt_audited = select(func.count(col(FeedItem.id))).where(FeedItem.processing_status == "audited")
        audited_count = (await s.exec(stmt_audited)).first() or 0
        stmt_adopted = select(func.count(col(FeedItem.id))).where(FeedItem.processing_status == "mesh_adopted")
        adopted_count = (await s.exec(stmt_adopted)).first() or 0
        stmt_roots = select(func.count(col(FeedSubscription.id))).where(col(FeedSubscription.is_active).is_(True))
        roots_count = (await s.exec(stmt_roots)).first() or 0

        return JSONResponse(
            {
                "status": "idle" if pending_count == 0 else "opportunistic_ready",
                "token_headroom": {
                    "daily_pct": headroom.daily_headroom_pct,
                    "hourly_pct": headroom.hourly_headroom_pct,
                    "daily_spend_usd": headroom.daily_spend_usd,
                    "circuit_breaker_tripped": headroom.circuit_breaker_tripped,
                },
                "queue": {
                    "pending_items": pending_count,
                    "audited_items": audited_count,
                    "mesh_adopted_items": adopted_count,
                    "active_roots_count": roots_count,
                },
                "boredom_trigger_eligible": (
                    not headroom.circuit_breaker_tripped and headroom.daily_headroom_pct >= 30.0
                ),
            }
        )
    return JSONResponse({"status": "unavailable"}, status_code=500)
