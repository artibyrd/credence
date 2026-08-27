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


def _format_clean_title(raw_title: Optional[str], url: Optional[str]) -> str:
    """Extract and format a human-readable title, stripping Mesh Submission prefixes and converting slugs."""
    if raw_title and not raw_title.startswith("Mesh Submission:") and not raw_title.startswith("http"):
        return raw_title
    target = (raw_title.replace("Mesh Submission:", "").strip() if raw_title else "") or (url or "")
    from urllib.parse import unquote, urlparse

    try:
        slug = urlparse(target).path.rstrip("/").split("/")[-1]
        if "." in slug:
            slug = slug.rsplit(".", 1)[0]
        if slug and len(slug) > 2:
            return unquote(slug).replace("-", " ").replace("_", " ").strip().title()
    except Exception:
        pass
    return raw_title or "Audited Article"


GENESIS_SEED_SUBSTRINGS = {
    "copper-sky-land-sale-is-no-scandal",
    "a-new-option-for-pigmentation",
    "what-landlords-discover",
    "bicyclist-dead-after-sr-347",
    "history-when-john-wayne-parkway-overpass",
    "clean-grid-transition",
    "supreme-court-digital-privacy",
    "exoplanet-atmosphere",
    "groundwater-contamination-records",
    "rail-expansion",
    "tandem-silicon-solar",
    "golden-retriever-elected-mayor",
    "nasa-giant-squeegee",
    "zoning-sludge-crisis",
    "breakthrough-battery-claim",
    "senate-tax-debate",
    "scan-now",
    "claim-token-2026",
}


def _derive_source_type(
    eval_method: Optional[str],
    node_pubkey: Optional[str] = None,
    snap_url: Optional[str] = None,
) -> str:
    """Determine standardized human-readable source category."""
    if eval_method:
        em = eval_method.lower()
        if "sifter" in em or "sentinel" in em or "rss" in em:
            return "Sentinel Feed"
        if "genesis" in em:
            return "Genesis Seeder"
        if "cli" in em or "manual" in em:
            return "CLI / Manual"

    if node_pubkey:
        np_lower = node_pubkey.lower()
        if "genesis" in np_lower or np_lower.startswith("9580dc91") or np_lower == "genesis-root-seed":
            return "Genesis Seeder"

    if snap_url and any(sub in snap_url.lower() for sub in GENESIS_SEED_SUBSTRINGS):
        return "Genesis Seeder"

    return "P2P Mesh"


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

        raw_title = snap.title if snap else ""
        clean_title = _format_clean_title(raw_title, snap.url if snap else "")
        source_type = _derive_source_type(audit.evaluation_method, audit.node_pubkey)

        return {
            "service": "credence",
            "url": snap.url if snap else "",
            "title": clean_title,
            "source": source_type,
            "byline": snap.byline if (snap and snap.byline) else "",
            "site_name": snap.site_name if (snap and snap.site_name) else "",
            "content_sha256": audit.content_sha256,
            "suspicion_score": audit.suspicion_score,
            "suspicion_density": audit.suspicion_density,
            "confidence_score": audit.confidence_score,
            "classification": audit.classification,
            "is_satire": audit.is_satire,
            "audited_at": str(audit.audited_at),
            "findings": [v.model_dump(mode="json") for v in violations],
            "violations": [v.model_dump(mode="json") for v in violations],
            "quota_preserved": audit.quota_preserved,
            "evaluation_method": audit.evaluation_method,
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

    domain = request.query_params.get("domain", "").strip()

    await init_db()
    async with get_async_session() as s:
        stmt = select(Audit, Snapshot).join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id), isouter=True)
        if domain:
            stmt = stmt.where(col(Snapshot.url).like(f"%{domain}%"))
        stmt = stmt.order_by(col(Audit.audited_at).desc())
        res = (await s.exec(stmt)).all()

        seen_urls = set()
        reports = []
        for audit, snap in res:
            target_url = snap.url if snap and snap.url else audit.content_sha256
            if target_url in seen_urls:
                continue
            seen_urls.add(target_url)

            raw_title = snap.title if snap else ""
            clean_title = _format_clean_title(raw_title, snap.url if snap else "")
            source_type = _derive_source_type(audit.evaluation_method, audit.node_pubkey)

            reports.append(
                {
                    "id": str(audit.id),
                    "url": snap.url if snap else "",
                    "title": clean_title,
                    "source": source_type,
                    "byline": snap.byline if (snap and snap.byline) else "",
                    "site_name": snap.site_name if (snap and snap.site_name) else "",
                    "content_sha256": audit.content_sha256,
                    "suspicion_score": audit.suspicion_score,
                    "suspicion_density": audit.suspicion_density,
                    "confidence_score": audit.confidence_score,
                    "classification": audit.classification,
                    "is_satire": audit.is_satire,
                    "audited_at": str(audit.audited_at),
                    "quota_preserved": audit.quota_preserved,
                    "evaluation_method": audit.evaluation_method,
                }
            )
            if len(reports) >= limit:
                break

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
