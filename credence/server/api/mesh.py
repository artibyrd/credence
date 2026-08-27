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


async def api_mesh_submit_attestation(request: Any) -> Any:
    """Public Zero-Auth REST Ingestion Gate: Verify and adopt a signed AuditReport into SQLite."""
    import json

    from sqlmodel import col, select

    from credence.identity import verify_audit_signature
    from credence.ingestion.security import is_safe_url
    from credence.models import Audit, Snapshot, Violation
    from credence.pipeline.schemas import AuditReport

    await init_db()

    try:
        data = await request.json()
        report = AuditReport.model_validate(data)
    except Exception as e:
        return JSONResponse({"error": f"Invalid audit report payload: {e}"}, status_code=400)

    # Invariant 1: SSRF & Untrusted Ingestion Boundary Defense
    if not is_safe_url(report.url):
        logger.warning(f"SSRF rejection on public mesh gate: {report.url}")
        return JSONResponse({"error": "SSRF violation: target URL blocked by node policy"}, status_code=422)

    # Invariant 2: RFC 8785 Canonical JSON & Ed25519 Signature Verification
    if not report.node_pubkey or not report.node_signature:
        return JSONResponse(
            {"error": "Cryptographic violation: attestation missing Ed25519 signature or node_pubkey"}, status_code=422
        )

    if not verify_audit_signature(report):
        logger.warning(f"Invalid Ed25519 signature on submission for {report.url} from {report.node_pubkey[:16]}...")
        return JSONResponse(
            {"error": "Cryptographic violation: signature mismatch over RFC 8785 canonical bytes"}, status_code=422
        )

    # Invariant 3: Verbatim Grounding & Quote Defense
    for v in report.violations:
        if v.quote_or_element and "<script" in v.quote_or_element.lower():
            return JSONResponse(
                {"error": "Security violation: malicious script tag in violation quote"}, status_code=422
            )

    # Inoculate into SQLite database
    async with get_async_session() as session:
        # Check or create Snapshot
        stmt = select(Snapshot).where(col(Snapshot.url) == report.url).order_by(col(Snapshot.captured_at).desc())
        existing_snap = (await session.exec(stmt)).first()

        if existing_snap:
            snap_id = existing_snap.id
        else:
            new_snap = Snapshot(
                url=report.url,
                content_sha256=report.content_sha256,
                simhash_64=report.simhash_64,
                title=f"Mesh Submission: {report.url}",
                word_count=len(report.violations) * 50,
            )
            session.add(new_snap)
            await session.commit()
            await session.refresh(new_snap)
            snap_id = new_snap.id

        # Insert Audit Record
        audit_record = Audit(
            snapshot_id=snap_id,
            audited_at=report.audited_at,
            content_sha256=report.content_sha256,
            suspicion_score=report.suspicion_score,
            suspicion_density=report.suspicion_density,
            confidence_score=report.confidence_score,
            classification=report.classification,
            is_satire=report.is_satire,
            content_type=report.content_type or "NEWS_ARTICLE",
            satire_notes=report.satire_notes,
            node_pubkey=report.node_pubkey,
            node_signature=report.node_signature,
            taxonomies_used_json=json.dumps(report.taxonomies_used),
            quota_preserved=report.quota_preserved,
            evaluation_method=report.evaluation_method or "mesh_contributed",
        )
        session.add(audit_record)
        await session.commit()
        await session.refresh(audit_record)

        for v in report.violations:
            vr = Violation(
                audit_id=audit_record.id,
                rule_id=v.rule_id,
                rule_uri=v.rule_uri,
                domain=v.domain,
                cluster_id=v.cluster_id,
                severity=v.severity,
                confidence=v.confidence,
                quote_or_element=v.quote_or_element,
                reasoning=v.reasoning,
                line_or_selector=v.line_or_selector,
            )
            session.add(vr)
        await session.commit()

    logger.info(
        f"Adopted mesh attestation for {report.url} (Score: {report.suspicion_score} pts, Pubkey: {report.node_pubkey[:16]}...)"
    )
    return JSONResponse(
        {
            "status": "adopted",
            "url": report.url,
            "content_sha256": report.content_sha256,
            "suspicion_score": report.suspicion_score,
            "node_pubkey": report.node_pubkey,
        },
        status_code=200,
    )


async def api_mesh_submit_batch(request: Any) -> Any:
    """Public Zero-Auth REST Batch Ingestion Gate: Adopt multiple signed AuditReports."""
    import json

    await init_db()

    try:
        body = await request.json()
        if isinstance(body, dict):
            items = body.get("attestations") or body.get("reports") or [body]
        elif isinstance(body, list):
            items = body
        else:
            return JSONResponse({"error": "Invalid batch payload format"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Failed to parse JSON body: {e}"}, status_code=400)

    accepted = 0
    rejected = 0
    errors: list[dict[str, Any]] = []

    # Mock a single request object for each item
    class _MockRequest:
        def __init__(self, data: dict[str, Any]):
            self._data = data

        async def json(self) -> dict[str, Any]:
            return self._data

    for idx, item in enumerate(items):
        mock_req = _MockRequest(item)
        resp = await api_mesh_submit_attestation(mock_req)
        if resp.status_code == 200:
            accepted += 1
        else:
            rejected += 1
            try:
                err_data = json.loads(resp.body.decode("utf-8"))
            except Exception:
                err_data = {"error": "Unknown error"}
            errors.append({"index": idx, "url": item.get("url"), "error": err_data.get("error")})

    return JSONResponse(
        {
            "total": len(items),
            "accepted": accepted,
            "rejected": rejected,
            "errors": errors,
        },
        status_code=200 if rejected == 0 else 207,
    )
