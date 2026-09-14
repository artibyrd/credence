"""Open Epistemic Mempool Queue Endpoints & Consensus Aggregation.

Governed by Invariant 1 (500 LOC Ceiling Law), inv-cart-before-horse,
inv-verbatim-grounding, inv-byzantine-cartel-resistance, and inv-galileo-rule.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlmodel import select
from starlette.requests import Request
from starlette.responses import JSONResponse

from credence.db import get_async_session
from credence.identity import canonical_json_bytes, verify_audit_signature
from credence.mesh.worker_badges import evaluate_worker_badges
from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord, utc_now
from credence.pipeline.schemas import AuditReport

# In-memory synchronization handles for instant FastMCP client unblocking
_COMPLETION_EVENTS: Dict[str, asyncio.Event] = {}
_COMPLETED_REPORTS: Dict[str, Dict[str, Any]] = {}

# Strict ASCII regex for model slugs (Vector 9 Defense: prevent traversal, confusables, and SQLi)
MODEL_SLUG_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.\/]{1,64}(?::[a-zA-Z0-9_\-\.]{1,32})?$")


def compute_estimated_queue_wait(queue_depth: int, active_workers_count: int) -> float:
    """Calculate estimated queue wait time in seconds based on active worker throughput."""
    workers = max(1, active_workers_count)
    return round((queue_depth / workers) * 12.0, 2)


def compute_consensus_verdict(audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute Bayesian consensus verdict and apply Galileo Rule override."""
    if not audits:
        return {"consensus_score": 0.0, "classification": "CLEAN", "galileo_override": False}

    scores = [float(a.get("suspicion_score", 0.0)) for a in audits]
    # Simple median for small quorums
    scores.sort()
    mid = len(scores) // 2
    median_score = scores[mid] if len(scores) % 2 != 0 else (scores[mid - 1] + scores[mid]) / 2.0

    # The Galileo Rule: If any audit provided verbatim-grounded violations, preserve them
    grounded_violations: List[Dict[str, Any]] = []
    has_grounded_violations = False
    for a in audits:
        violations = a.get("violations", [])
        if violations:
            has_grounded_violations = True
            for v in violations:
                grounded_violations.append(v)

    galileo_override = False
    final_score = median_score
    if has_grounded_violations and median_score < 25.0:
        # Grounded truth overrides ungrounded clean consensus
        galileo_override = True
        max_severity_score = max(scores)
        final_score = max(max_severity_score, 45.0)

    classification = "CLEAN" if final_score < 25.0 else ("SUSPICIOUS" if final_score < 60.0 else "DECEPTIVE")

    return {
        "consensus_score": round(final_score, 1),
        "median_score": round(median_score, 1),
        "classification": classification,
        "evaluations_count": len(audits),
        "galileo_override": galileo_override,
        "violations_count": len(grounded_violations),
    }


def register_completion_listener(url: str) -> asyncio.Event:
    """Register an in-memory event listener for FastMCP adaptive wait window."""
    if url not in _COMPLETION_EVENTS:
        _COMPLETION_EVENTS[url] = asyncio.Event()
    return _COMPLETION_EVENTS[url]


def get_completed_report(url: str) -> Optional[Dict[str, Any]]:
    """Retrieve completed report payload if populated."""
    return _COMPLETED_REPORTS.get(url)


async def api_queue_enqueue(request: Request) -> JSONResponse:
    """POST /api/queue/enqueue: Enqueue an audit request into the mempool."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    url = body.get("url")
    if not url:
        return JSONResponse({"error": "Missing required 'url' field"}, status_code=400)

    content_sha256 = body.get("content_sha256") or ""
    normalized_text = body.get("normalized_text") or ""
    priority = int(body.get("priority", 2))
    client_affinity = body.get("client_affinity")
    target_quorum = int(body.get("target_quorum", 1))

    async with get_async_session() as session:
        # Single-flight deduplication: check if pending or claimed job already exists
        statement = select(AuditJob).where(
            AuditJob.url == url,
            AuditJob.status.in_(["pending", "claimed"])
        )
        result = await session.exec(statement)
        existing_job = result.first()

        if existing_job:
            return JSONResponse({
                "status": "already_queued",
                "job_id": existing_job.job_id,
                "url": existing_job.url,
                "priority": existing_job.priority,
                "target_quorum": existing_job.target_quorum,
            })

        job_id = str(uuid.uuid4())
        job = AuditJob(
            job_id=job_id,
            url=url,
            content_sha256=content_sha256,
            normalized_text=normalized_text,
            priority=priority,
            client_affinity=client_affinity,
            target_quorum=target_quorum,
            status="pending",
        )
        session.add(job)
        await session.commit()

        # Register event for listeners
        register_completion_listener(url)

        return JSONResponse({
            "status": "queued",
            "job_id": job.job_id,
            "url": job.url,
            "priority": job.priority,
            "target_quorum": job.target_quorum,
        })


async def api_queue_claim(request: Request) -> JSONResponse:
    """POST /api/queue/claim: Atomically claim a pending job with lease enforcement."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    worker_pubkey = body.get("worker_pubkey")
    model_family = body.get("model_family", "general").strip().lower()
    model_slug = body.get("model_slug", "google/gemini-3.7-flash").strip()
    client_affinity = body.get("client_affinity")

    if not worker_pubkey:
        return JSONResponse({"error": "Missing worker_pubkey"}, status_code=400)

    # Vector 9: Validate model slug
    if not MODEL_SLUG_REGEX.match(model_slug) or ".." in model_slug:
        return JSONResponse({"error": "Invalid model_slug format"}, status_code=400)

    async with get_async_session() as session:
        # Vector 7: Rate limit active leases per worker (max 3)
        statement_active = select(AuditJob).where(AuditJob.status == "claimed")
        result_active = await session.exec(statement_active)
        all_claimed = result_active.all()

        worker_active_count = 0
        now = utc_now()
        for cj in all_claimed:
            leases = json.loads(cj.active_leases_json or "[]")
            for l in leases:
                if l.get("worker_pubkey") == worker_pubkey:
                    exp = datetime.fromisoformat(l["expires_at"])
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)
                    if exp > now:
                        worker_active_count += 1

        if worker_active_count >= 3:
            return JSONResponse({"error": "Too many active unfulfilled leases (max 3)"}, status_code=429)

        # Reclaim expired leases across all claimed jobs
        for cj in all_claimed:
            leases = json.loads(cj.active_leases_json or "[]")
            valid_leases = []
            expired_found = False
            for l in leases:
                exp = datetime.fromisoformat(l["expires_at"])
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp > now:
                    valid_leases.append(l)
                else:
                    expired_found = True
            if expired_found:
                cj.active_leases_json = json.dumps(valid_leases)
                if not valid_leases and cj.status == "claimed":
                    cj.status = "pending"
                session.add(cj)
        await session.commit()

        # Query eligible jobs
        statement = select(AuditJob).where(AuditJob.status.in_(["pending", "claimed"]))
        result = await session.exec(statement)
        candidates = result.all()

        # Filter and rank candidates
        eligible = []
        for job in candidates:
            leases = json.loads(job.active_leases_json or "[]")
            completed = json.loads(job.completed_models_json or "[]")

            # Check if this model family has already completed or is actively claimed
            if model_family in completed:
                continue
            if any(l.get("model_family") == model_family for l in leases):
                continue
            if len(completed) >= job.target_quorum:
                continue

            # Affinity check: if worker requested specific affinity, only pick matching jobs
            if client_affinity and job.client_affinity != client_affinity:
                continue

            # Affinity bonus score
            affinity_match = 1 if (client_affinity and job.client_affinity == client_affinity) else 0
            eligible.append((affinity_match, -job.priority, job.created_at, job))

        if not eligible:
            return JSONResponse({"job": None})

        # Sort: affinity match first, then priority (1 is highest), then oldest created
        eligible.sort(key=lambda x: (-x[0], -x[1], x[2]))
        selected_job = eligible[0][3]

        # Determine lease duration: Priority 1 gets tight 15s slice, else 180s
        lease_seconds = 15 if selected_job.priority == 1 else 180
        expires_at = now + timedelta(seconds=lease_seconds)
        lease_id = str(uuid.uuid4())

        existing_leases = json.loads(selected_job.active_leases_json or "[]")
        existing_leases.append({
            "lease_id": lease_id,
            "worker_pubkey": worker_pubkey,
            "model_family": model_family,
            "expires_at": expires_at.isoformat(),
        })
        selected_job.active_leases_json = json.dumps(existing_leases)
        selected_job.status = "claimed"
        session.add(selected_job)
        await session.commit()

        return JSONResponse({
            "job": {
                "job_id": selected_job.job_id,
                "url": selected_job.url,
                "content_sha256": selected_job.content_sha256,
                "normalized_text": selected_job.normalized_text,
                "priority": selected_job.priority,
                "lease_id": lease_id,
                "lease_seconds": lease_seconds,
            }
        })


async def api_queue_submit(request: Request) -> JSONResponse:
    """POST /api/queue/submit: Submit completed evaluation, verify grounding, and aggregate consensus."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    job_id = body.get("job_id")
    worker_pubkey = body.get("worker_pubkey")
    model_family = body.get("model_family", "general").strip().lower()
    model_slug = body.get("model_slug", "google/gemini-3.7-flash")
    report_dict = body.get("report")

    if not job_id or not worker_pubkey or not report_dict:
        return JSONResponse({"error": "Missing required submit fields"}, status_code=400)

    # 1. Cryptographic Signature Verification (Vector 6 Defense)
    try:
        report_obj = AuditReport.model_validate(report_dict)
        if not verify_audit_signature(report_obj):
            return JSONResponse({"error": "Invalid Ed25519 signature on audit report"}, status_code=422)
    except Exception as e:
        return JSONResponse({"error": f"Schema or signature validation failed: {e}"}, status_code=422)

    # 2. Stored XSS & Script Tag Defense (Vector 5)
    for v in report_obj.violations:
        if "<script" in v.quote_or_element.lower() or "javascript:" in v.quote_or_element.lower():
            return JSONResponse({"error": "XSS payload detected in violation quote"}, status_code=422)
        if "<script" in v.reasoning.lower():
            return JSONResponse({"error": "XSS payload detected in violation reasoning"}, status_code=422)

    async with get_async_session() as session:
        statement = select(AuditJob).where(AuditJob.job_id == job_id)
        result = await session.exec(statement)
        job = result.first()

        if not job:
            return JSONResponse({"error": "Job not found"}, status_code=404)

        # 3. Verbatim Grounding Verification (Vector 4: G=1.00 assertion)
        if job.normalized_text and report_obj.violations:
            for v in report_obj.violations:
                if v.quote_or_element and v.quote_or_element not in job.normalized_text:
                    return JSONResponse({
                        "error": f"Grounding precision G < 1.00: Quote '{v.quote_or_element[:40]}...' not found in source text"
                    }, status_code=422)

        # Update leases and completed models
        leases = json.loads(job.active_leases_json or "[]")
        valid_leases = [l for l in leases if l.get("worker_pubkey") != worker_pubkey]
        job.active_leases_json = json.dumps(valid_leases)

        completed_models = json.loads(job.completed_models_json or "[]")
        if model_family not in completed_models:
            completed_models.append(model_family)
        job.completed_models_json = json.dumps(completed_models)

        # Check or create Snapshot & persist Audit
        snap_stmt = select(Snapshot).where(Snapshot.url == job.url)
        snap_res = await session.exec(snap_stmt)
        snapshot = snap_res.first()
        if not snapshot:
            snapshot = Snapshot(
                url=job.url,
                content_sha256=job.content_sha256 or "sha256:unknown",
                simhash_64=report_obj.simhash_64 or "0x0",
                clean_text_length=len(job.normalized_text or ""),
                word_count=len((job.normalized_text or "").split()),
            )
            session.add(snapshot)
            await session.commit()
            await session.refresh(snapshot)

        audit_record = Audit(
            snapshot_id=snapshot.id,
            content_sha256=snapshot.content_sha256,
            suspicion_score=report_obj.suspicion_score,
            suspicion_density=report_obj.suspicion_density,
            confidence_score=report_obj.confidence_score,
            classification=report_obj.classification,
            is_satire=report_obj.is_satire,
            content_type=report_obj.content_type,
            node_pubkey=report_obj.node_pubkey,
            node_signature=report_obj.node_signature,
            evaluation_method="worker_volunteer_mempool",
            evaluation_model=model_slug,
        )
        session.add(audit_record)
        await session.commit()
        await session.refresh(audit_record)

        for v in report_obj.violations:
            viol_record = Violation(
                audit_id=audit_record.id,
                rule_id=v.rule_id,
                rule_uri=v.rule_uri,
                domain=v.domain,
                cluster_id=v.cluster_id,
                severity=v.severity,
                confidence=v.confidence,
                quote_or_element=v.quote_or_element,
                reasoning=v.reasoning,
            )
            session.add(viol_record)

        # Update WorkerRecord
        worker_stmt = select(WorkerRecord).where(WorkerRecord.worker_pubkey == worker_pubkey)
        worker_res = await session.exec(worker_stmt)
        worker = worker_res.first()
        if not worker:
            worker = WorkerRecord(
                worker_pubkey=worker_pubkey,
                worker_alias=body.get("worker_alias") or f"worker-{worker_pubkey[:8]}",
                model_family=model_family,
                model_slug=model_slug,
                total_completed=0,
                bounties_cleared=0,
                tokens_donated=0,
            )
            session.add(worker)
            await session.commit()
            await session.refresh(worker)

        worker.total_completed += 1
        worker.bounties_cleared += 1
        worker.tokens_donated += int(body.get("tokens_donated", 1500))
        worker.grounded_violations_count += len(report_obj.violations)
        worker.last_seen = utc_now()

        # Evaluate and unlock badges
        awards = evaluate_worker_badges(worker)
        worker.badges_unlocked_json = json.dumps([a.model_dump() for a in awards])
        session.add(worker)

        # Check Consensus
        if len(completed_models) >= job.target_quorum:
            job.status = "completed"
            job.is_consensus_ready = True
            job.completed_at = utc_now()
            # Compile audits for consensus verdict
            all_audits_stmt = select(Audit).where(Audit.snapshot_id == snapshot.id)
            all_audits_res = await session.exec(all_audits_stmt)
            all_audits = all_audits_res.all()
            audits_list = []
            for a in all_audits:
                v_stmt = select(Violation).where(Violation.audit_id == a.id)
                v_res = await session.exec(v_stmt)
                audits_list.append({
                    "suspicion_score": a.suspicion_score,
                    "violations": [v.model_dump() for v in v_res.all()],
                })
            job.consensus_verdict_json = json.dumps(compute_consensus_verdict(audits_list))

        session.add(job)
        await session.commit()

        # Unblock in-memory FastMCP listeners
        _COMPLETED_REPORTS[job.url] = report_dict
        if job.url in _COMPLETION_EVENTS:
            _COMPLETION_EVENTS[job.url].set()

        return JSONResponse({
            "status": "accepted",
            "job_id": job.job_id,
            "is_consensus_ready": job.is_consensus_ready,
            "bounties_cleared": worker.bounties_cleared,
            "badges_awarded": [a.badge_id for a in awards],
        })


async def api_queue_stats(request: Request) -> JSONResponse:
    """GET /api/queue/stats: Return mempool queue vitals, active workers, and estimated wait."""
    async with get_async_session() as session:
        stmt_pending = select(AuditJob).where(AuditJob.status == "pending")
        pending = len((await session.exec(stmt_pending)).all())

        stmt_claimed = select(AuditJob).where(AuditJob.status == "claimed")
        claimed = len((await session.exec(stmt_claimed)).all())

        stmt_workers = select(WorkerRecord)
        workers = len((await session.exec(stmt_workers)).all())

        wait_sec = compute_estimated_queue_wait(pending, workers)

        return JSONResponse({
            "depth": pending,
            "active_leases": claimed,
            "registered_workers": workers,
            "estimated_wait_seconds": wait_sec,
        })
