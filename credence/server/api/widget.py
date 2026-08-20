"""REST API Handlers for Embeddable Credence Badge and Content History.

Provides:
- GET /api/v1/badge/{identifier:path}: Returns JSON attestation receipt & badge metadata.
- GET /api/v1/history/{identifier:path}: Returns snapshot revisions and score trajectory.
- GET /api/widget.js: Returns the standalone zero-npm web component script.
"""

from __future__ import annotations

import json
import logging

from sqlmodel import col, select
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, Violation
from credence.storage.revisions import get_url_revision_history

logger = logging.getLogger("credence.server.api.widget")


async def api_get_badge_data(request: Request) -> Response:
    """Return JSON attestation and badge status for a given URL or content hash."""
    identifier = request.path_params.get("identifier", "").strip()
    if not identifier:
        return JSONResponse({"error": "Missing identifier"}, status_code=400)

    await init_db()
    async with get_async_session() as session:
        # Try matching by content_sha256 or URL
        stmt = (
            select(Audit, Snapshot)
            .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
            .where((col(Audit.content_sha256) == identifier) | (col(Snapshot.url) == identifier))
            .order_by(col(Audit.audited_at).desc())
        )
        result = (await session.exec(stmt)).first()

        if not result:
            return JSONResponse(
                {
                    "status": "UNAUDITED",
                    "identifier": identifier,
                    "message": "No verified attestation found for this content.",
                },
                status_code=404,
            )

        audit, snapshot = result

        # Fetch violations count
        v_stmt = select(col(Violation.id)).where(col(Violation.audit_id) == audit.id)
        v_res = await session.exec(v_stmt)
        v_count = len(v_res.all())

        receipt = {
            "origin_url": snapshot.url,
            "content_sha256": audit.content_sha256,
            "simhash_64": snapshot.simhash_64,
            "audited_at": audit.audited_at.isoformat(),
            "suspicion_score": audit.suspicion_score,
            "classification": audit.classification,
            "node_pubkey": audit.node_pubkey,
            "node_signature": audit.node_signature,
            "taxonomies_used": json.loads(audit.taxonomies_used_json) if audit.taxonomies_used_json else {},
        }

        verdict_badge = (
            "VERIFIED" if audit.suspicion_score < 20.0 else ("ATTENTION" if audit.suspicion_score < 70.0 else "FLAGGED")
        )

        return JSONResponse(
            {
                "status": verdict_badge,
                "score": round(100.0 - audit.suspicion_score, 1),
                "suspicion_score": audit.suspicion_score,
                "classification": audit.classification,
                "url": snapshot.url,
                "title": snapshot.title,
                "revision_index": snapshot.revision_index,
                "violations_count": v_count,
                "receipt": receipt,
            },
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=60"},
        )


async def api_get_history(request: Request) -> Response:
    """Return full temporal revision history and score trajectory for a URL."""
    identifier = request.path_params.get("identifier", "").strip()
    if not identifier:
        return JSONResponse({"error": "Missing identifier"}, status_code=400)

    await init_db()
    async with get_async_session() as session:
        trajectory = await get_url_revision_history(session, identifier)

        if trajectory.total_revisions == 0:
            # Try to resolve by sha256 to URL
            stmt = select(Snapshot.url).where(Snapshot.content_sha256 == identifier)
            url_match = (await session.exec(stmt)).first()
            if url_match:
                trajectory = await get_url_revision_history(session, url_match)

        if trajectory.total_revisions == 0:
            return JSONResponse(
                {"error": "No revision history found", "identifier": identifier},
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"},
            )

        return JSONResponse(
            trajectory.model_dump(mode="json"),
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=30"},
        )
