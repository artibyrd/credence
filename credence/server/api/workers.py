"""Volunteer Worker Leaderboard, Contributor Dossiers & Vector SVG Badges.

Governed by Invariant 1 (500 LOC Ceiling Law), inv-dense-workstation-viewport,
and inv-unified-merit-and-attestation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import desc, select
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from credence.db import get_async_session
from credence.mesh.worker_badges import generate_worker_profile_badge_svg
from credence.models import Audit, Snapshot, WorkerRecord, utc_now


def compute_token_savings(tokens_count: int) -> float:
    """Calculate estimated dollar savings for the network based on tokens donated."""
    # Blended baseline of $0.34 per 1M tokens (Gemini Flash reference)
    return round((tokens_count / 1_000_000.0) * 0.34, 4)


def compute_worker_quality_score(
    total_completed: int,
    bounties_cleared: int,
    grounded_violations: int,
    first_seen: datetime,
) -> float:
    """Compute 5-factor quality score Q_w for a volunteer worker."""
    now = utc_now()
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    longevity_days = max(0.1, (now - first_seen).total_seconds() / 86400.0)

    # Volume factor
    vol_factor = min(1.0, bounties_cleared / 50.0)
    # Grounding factor (assume high if positive violations)
    ground_factor = 1.0 if grounded_violations >= 0 else 0.5
    # Longevity factor
    long_factor = min(1.0, longevity_days / 14.0)

    score = 0.50 + (0.25 * vol_factor) + (0.15 * ground_factor) + (0.10 * long_factor)
    return round(min(1.0, max(0.1, score)), 2)


async def api_workers_leaderboard(request: Request) -> JSONResponse:
    """GET /api/workers/leaderboard: Retrieve ranked list of volunteer compute contributors."""
    params = request.query_params
    search = params.get("search", "").strip().lower()
    family_filter = params.get("family", "").strip().lower()
    limit = min(100, max(1, int(params.get("limit", 50))))
    offset = max(0, int(params.get("offset", 0)))

    async with get_async_session() as session:
        statement = select(WorkerRecord).order_by(
            desc(WorkerRecord.tokens_donated), desc(WorkerRecord.bounties_cleared)
        )
        result = await session.exec(statement)
        workers = result.all()

        filtered = []
        for w in workers:
            if search and (search not in w.worker_alias.lower() and search not in w.worker_pubkey.lower()):
                continue
            if family_filter and family_filter != "all" and family_filter not in w.model_family.lower():
                continue

            badges_list = json.loads(w.badges_unlocked_json or "[]")
            q_score = compute_worker_quality_score(
                w.total_completed, w.bounties_cleared, w.grounded_violations_count, w.first_seen
            )
            filtered.append(
                {
                    "worker_pubkey": w.worker_pubkey,
                    "worker_alias": w.worker_alias,
                    "model_family": w.model_family,
                    "model_slug": w.model_slug,
                    "total_completed": w.total_completed,
                    "bounties_cleared": w.bounties_cleared,
                    "tokens_donated": w.tokens_donated,
                    "tokens_saved_usd": compute_token_savings(w.tokens_donated),
                    "quality_score": q_score,
                    "badges_count": len(badges_list),
                    "badges": badges_list,
                    "last_seen": w.last_seen.isoformat(),
                    "first_seen": w.first_seen.isoformat(),
                }
            )

        paginated = filtered[offset : offset + limit]
        return JSONResponse(
            {
                "total_workers": len(filtered),
                "limit": limit,
                "offset": offset,
                "workers": paginated,
            }
        )


async def api_worker_dossier(request: Request) -> JSONResponse:
    """GET /api/worker/{pubkey}: Retrieve complete contributor dossier and audit history."""
    pubkey = request.path_params.get("pubkey", "").strip()
    if not pubkey:
        return JSONResponse({"error": "Missing worker pubkey"}, status_code=400)

    async with get_async_session() as session:
        statement = select(WorkerRecord).where(WorkerRecord.worker_pubkey == pubkey)
        result = await session.exec(statement)
        worker = result.first()

        if not worker:
            return JSONResponse({"error": "Worker not found"}, status_code=404)

        badges_list = json.loads(worker.badges_unlocked_json or "[]")
        q_score = compute_worker_quality_score(
            worker.total_completed, worker.bounties_cleared, worker.grounded_violations_count, worker.first_seen
        )

        # Retrieve recent audits completed by this worker
        audit_stmt = (
            select(Audit).where(Audit.node_pubkey == worker.worker_pubkey).order_by(desc(Audit.audited_at)).limit(10)
        )
        audit_res = await session.exec(audit_stmt)
        recent_audits = []
        for a in audit_res.all():
            snap_stmt = select(Snapshot).where(Snapshot.id == a.snapshot_id)
            snap = (await session.exec(snap_stmt)).first()
            recent_audits.append(
                {
                    "url": snap.url if snap else "unknown",
                    "content_sha256": a.content_sha256,
                    "suspicion_score": a.suspicion_score,
                    "classification": a.classification,
                    "audited_at": a.audited_at.isoformat(),
                    "node_signature": a.node_signature,
                }
            )

        return JSONResponse(
            {
                "worker_pubkey": worker.worker_pubkey,
                "worker_alias": worker.worker_alias,
                "model_family": worker.model_family,
                "model_slug": worker.model_slug,
                "total_completed": worker.total_completed,
                "bounties_cleared": worker.bounties_cleared,
                "tokens_donated": worker.tokens_donated,
                "tokens_saved_usd": compute_token_savings(worker.tokens_donated),
                "quality_score": q_score,
                "badges": badges_list,
                "first_seen": worker.first_seen.isoformat(),
                "last_seen": worker.last_seen.isoformat(),
                "recent_audits": recent_audits,
                "embed_badge_url": f"/api/badge/worker/{worker.worker_pubkey}.svg",
            }
        )


async def api_worker_badge_svg(request: Request) -> Response:
    """GET /api/badge/worker/{pubkey}: Return dynamic vector SVG badge for worker."""
    pubkey = request.path_params.get("pubkey", "").replace(".svg", "").strip()
    style = request.query_params.get("style", "shield")
    theme = request.query_params.get("theme", "dark")

    async with get_async_session() as session:
        statement = select(WorkerRecord).where(WorkerRecord.worker_pubkey == pubkey)
        result = await session.exec(statement)
        worker = result.first()

        if not worker:
            worker = WorkerRecord(
                worker_pubkey=pubkey,
                worker_alias=f"worker-{pubkey[:8]}",
                total_completed=0,
                bounties_cleared=0,
            )

        svg = generate_worker_profile_badge_svg(worker, style=style, theme=theme)
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=60, s-maxage=60"},
        )
