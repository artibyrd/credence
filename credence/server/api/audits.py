"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlmodel import col, select
from starlette.responses import JSONResponse

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.evaluator import audit_url
from credence.server.middleware.security import _check_admin_auth

logger = logging.getLogger("credence.server.api")


async def _reconstitute_report_from_db(identifier: str) -> Optional[dict]:
    """Reconstitute full audit report JSON from SQLite."""
    await init_db()
    async with get_async_session() as session:
        stmt = select(Audit).where(Audit.content_sha256 == identifier).order_by(col(Audit.audited_at).desc())
        audit = (await session.exec(stmt)).first()

        if not audit:
            stmt_url = (
                select(Audit)
                .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
                .where(col(Snapshot.url) == identifier)
                .order_by(col(Audit.audited_at).desc())
            )
            audit = (await session.exec(stmt_url)).first()

        if not audit:
            return None

        snap = None
        if audit.snapshot_id:
            stmt_snap = select(Snapshot).where(Snapshot.id == audit.snapshot_id)
            snap = (await session.exec(stmt_snap)).first()

        stmt_v = select(Violation).where(Violation.audit_id == audit.id)
        violations = list((await session.exec(stmt_v)).all())

        return {
            "service": "credence",
            "url": snap.url if snap else "",
            "content_sha256": audit.content_sha256,
            "suspicion_score": audit.suspicion_score,
            "suspicion_density": audit.suspicion_density,
            "confidence_score": audit.confidence_score,
            "classification": audit.classification,
            "is_satire": audit.is_satire,
            "audited_at": str(audit.audited_at),
            "findings": [v.model_dump(mode="json") for v in violations],
        }


async def api_audit_url(request: Any) -> Any:
    """REST API: Audit a webpage URL synchronously or return cached evaluation."""
    if not bool(_check_admin_auth(request)):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        data = await request.json()
        target_url = data.get("url")
    except Exception:
        target_url = request.query_params.get("url")

    if not target_url:
        return JSONResponse({"error": "Missing 'url' parameter."}, status_code=400)

    prof_str = request.query_params.get("profile")
    prof_cfg = COST_PROFILES.get(CostProfile(prof_str.lower())) if prof_str else None

    async with get_async_session() as s:
        report = await audit_url(target_url, session=s, profile_override=prof_cfg)

    rep_dict = report.model_dump(mode="json")
    return JSONResponse(rep_dict)


async def api_reports(request: Any) -> Any:
    """REST API: Query recent audit reports with pagination."""
    limit = int(request.query_params.get("limit", "20"))
    limit = max(1, min(100, limit))

    await init_db()
    async with get_async_session() as s:
        stmt = (
            select(Audit, Snapshot)
            .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
            .order_by(col(Audit.audited_at).desc())
            .limit(limit)
        )
        res = (await s.exec(stmt)).all()

        reports = []
        for audit, snap in res:
            reports.append(
                {
                    "content_sha256": audit.content_sha256,
                    "url": snap.url,
                    "title": snap.title,
                    "suspicion_score": audit.suspicion_score,
                    "classification": audit.classification,
                    "confidence_score": audit.confidence_score,
                    "is_satire": audit.is_satire,
                    "audited_at": audit.audited_at.isoformat() if audit.audited_at else None,
                }
            )

        return JSONResponse(
            {
                "count": len(reports),
                "total": len(reports),
                "reports": reports,
            }
        )


async def api_get_report(request: Any) -> Any:
    """REST API: Get complete audit report by SHA-256 or URL identifier with immutable edge caching headers."""
    identifier = request.path_params.get("identifier", "")
    if not identifier:
        identifier = request.query_params.get("q", "")

    report_dict = await _reconstitute_report_from_db(identifier)
    if not report_dict:
        return JSONResponse({"error": f"No audit record found for identifier '{identifier}'."}, status_code=404)

    return JSONResponse(
        report_dict,
        headers={
            "Cache-Control": "public, max-age=2592000, immutable",
            "CDN-Cache-Control": "public, max-age=2592000, immutable",
            "ETag": f'W/"sha256:{identifier}"',
        },
    )
