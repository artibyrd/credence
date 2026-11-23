"""Open Epistemic Mempool Queue Endpoints & Consensus Aggregation.

Governed by Invariant 1 (500 LOC Ceiling Law), inv-cart-before-horse,
inv-verbatim-grounding, inv-byzantine-cartel-resistance, and inv-galileo-rule.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import OrderedDict
from datetime import timedelta
from typing import Any, Dict, List, Optional

from sqlmodel import col, select
from starlette.requests import Request
from starlette.responses import JSONResponse

from credence.config import settings
from credence.db import get_async_session
from credence.identity import verify_audit_signature
from credence.models import AuditJob, WorkerRecord, utc_now
from credence.pipeline.schemas import AuditReport
from credence.pipeline.subagents import validate_grounded_quote
from credence.server.api.queue_guards import (
    MODEL_SLUG_REGEX,
    check_public_enqueue_rate_limit,
    compute_consensus_verdict,
    is_authenticated_operator,
    resolve_authoritative_enqueue_content,
    sanitize_worker_alias,
    validate_enqueue_payload,
    validate_violation_safety,
    validate_worker_pubkey,
    verify_claim_proof,
)
from credence.server.api.queue_persistence import (
    parse_iso_utc,
    persist_verified_submission,
    record_grounding_rejection,
)
from credence.worker.leases import resolve_model_family

__all__ = [
    "MODEL_SLUG_REGEX",
    "api_queue_claim",
    "api_queue_enqueue",
    "api_queue_stats",
    "api_queue_submit",
    "clear_completion_state",
    "compute_consensus_verdict",
    "compute_estimated_queue_wait",
    "get_completed_report",
    "register_completion_listener",
]

# Bounded in-memory synchronization handles for instant FastMCP client unblocking
_MAX_COMPLETION_CACHE = 500
_COMPLETION_EVENTS: OrderedDict[str, asyncio.Event] = OrderedDict()
_COMPLETED_REPORTS: OrderedDict[str, Dict[str, Any]] = OrderedDict()
_CLAIM_LOCK = asyncio.Lock()


def compute_estimated_queue_wait(queue_depth: int, active_workers_count: int) -> float:
    """Calculate estimated queue wait time in seconds based on active worker throughput."""
    workers = max(1, active_workers_count)
    return round((queue_depth / workers) * 12.0, 2)


def _evict_if_over_cap(store: OrderedDict[str, Any]) -> None:
    while len(store) > _MAX_COMPLETION_CACHE:
        store.popitem(last=False)


def register_completion_listener(url: str) -> asyncio.Event:
    """Register an in-memory event listener for FastMCP adaptive wait window."""
    if url in _COMPLETION_EVENTS:
        _COMPLETION_EVENTS.move_to_end(url)
        return _COMPLETION_EVENTS[url]
    ev = asyncio.Event()
    _COMPLETION_EVENTS[url] = ev
    _evict_if_over_cap(_COMPLETION_EVENTS)
    return ev


def clear_completion_state(url: str) -> None:
    """Reset any cached completion event or report for a URL (used on fresh or forced enqueue)."""
    _COMPLETED_REPORTS.pop(url, None)
    _COMPLETION_EVENTS.pop(url, None)


def get_completed_report(url: str) -> Optional[Dict[str, Any]]:
    """Retrieve completed report payload if populated."""
    return _COMPLETED_REPORTS.get(url)


async def api_queue_enqueue(request: Request) -> JSONResponse:
    """POST /api/queue/enqueue: Enqueue an audit request into the mempool."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    validated, err = validate_enqueue_payload(body)
    if err or validated is None:
        return JSONResponse({"error": err or "Invalid enqueue payload"}, status_code=400)

    url = validated["url"]
    is_operator = is_authenticated_operator(request)
    if not is_operator and not url.startswith("text://") and not check_public_enqueue_rate_limit(request):
        return JSONResponse({"error": "Public enqueue rate limit exceeded; retry shortly"}, status_code=429)

    async with get_async_session() as session:
        stmt = select(AuditJob).where(AuditJob.url == url, col(AuditJob.status).in_(["pending", "claimed"]))
        existing_job = (await session.exec(stmt)).first()

        if existing_job and not validated["force"]:
            return JSONResponse(
                {
                    "status": "already_queued",
                    "job_id": existing_job.job_id,
                    "url": existing_job.url,
                    "priority": existing_job.priority,
                    "target_quorum": existing_job.target_quorum,
                }
            )

        norm_text, content_sha, fetch_err = await resolve_authoritative_enqueue_content(
            session=session,
            url=url,
            caller_text=validated["normalized_text"],
            caller_sha256=validated["content_sha256"],
            is_operator=is_operator,
        )
        if fetch_err:
            return JSONResponse({"error": fetch_err}, status_code=422)

        job = AuditJob(
            job_id=str(uuid.uuid4()),
            url=url,
            content_sha256=content_sha,
            normalized_text=norm_text,
            priority=validated["priority"],
            client_affinity=validated["client_affinity"],
            target_quorum=validated["target_quorum"],
            status="pending",
        )
        session.add(job)
        await session.commit()

        clear_completion_state(url)
        register_completion_listener(url)

        return JSONResponse(
            {
                "status": "queued",
                "job_id": job.job_id,
                "url": job.url,
                "priority": job.priority,
                "target_quorum": job.target_quorum,
            }
        )


async def api_queue_claim(request: Request) -> JSONResponse:
    """POST /api/queue/claim: Atomically claim a pending job with Ed25519 PoP and lease enforcement."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    raw_pubkey = body.get("worker_pubkey")
    if not validate_worker_pubkey(raw_pubkey):
        return JSONResponse({"error": "Invalid or missing 64-hex Ed25519 worker_pubkey"}, status_code=400)
    worker_pubkey = str(raw_pubkey).strip().lower()

    model_slug = str(body.get("model_slug") or settings.DEFAULT_WORKER_MODEL).strip()
    if not MODEL_SLUG_REGEX.match(model_slug) or ".." in model_slug:
        return JSONResponse({"error": "Invalid model_slug format"}, status_code=400)

    # Server-side canonical model family resolution (never trust caller-supplied model_family)
    model_family = resolve_model_family(model_slug)
    client_affinity = body.get("client_affinity")

    # Ed25519 Proof-of-Possession prevents third-party pubkey quota-exhaustion DoS
    proof_err = verify_claim_proof(
        worker_pubkey=worker_pubkey,
        model_slug=model_slug,
        claim_timestamp=body.get("claim_timestamp"),
        claim_signature=body.get("claim_signature"),
    )
    if proof_err:
        return JSONResponse({"error": proof_err}, status_code=401)

    async with _CLAIM_LOCK:
        async with get_async_session() as session:
            now = utc_now()
            all_claimed = (await session.exec(select(AuditJob).where(AuditJob.status == "claimed"))).all()

            # Reclaim expired leases first so stale leases never falsely rate-limit workers
            worker_active_count = 0
            for cj in all_claimed:
                leases = json.loads(cj.active_leases_json or "[]")
                valid_leases = []
                expired_found = False
                for entry in leases:
                    if parse_iso_utc(entry["expires_at"]) > now:
                        valid_leases.append(entry)
                        if entry.get("worker_pubkey") == worker_pubkey:
                            worker_active_count += 1
                    else:
                        expired_found = True
                if expired_found:
                    cj.active_leases_json = json.dumps(valid_leases)
                    if not valid_leases and cj.status == "claimed":
                        cj.status = "pending"
                    session.add(cj)
            await session.commit()

            if worker_active_count >= 3:
                return JSONResponse({"error": "Too many active unfulfilled leases (max 3)"}, status_code=429)

            candidates = (
                await session.exec(select(AuditJob).where(col(AuditJob.status).in_(["pending", "claimed"])))
            ).all()
            eligible = []
            for job in candidates:
                leases = json.loads(job.active_leases_json or "[]")
                completed_models = json.loads(job.completed_models_json or "[]")
                completed_workers = json.loads(job.completed_workers_json or "[]")

                if model_family in completed_models or worker_pubkey in completed_workers:
                    continue
                if any(entry.get("model_family") == model_family for entry in leases):
                    continue
                if any(entry.get("worker_pubkey") == worker_pubkey for entry in leases):
                    continue
                if len(completed_models) >= job.target_quorum:
                    continue
                if client_affinity and job.client_affinity != client_affinity:
                    continue

                affinity_match = 1 if (client_affinity and job.client_affinity == client_affinity) else 0
                eligible.append((affinity_match, -job.priority, job.created_at, job))

            if not eligible:
                return JSONResponse({"job": None})

            eligible.sort(key=lambda x: (-x[0], -x[1], x[2]))
            selected_job = eligible[0][3]

            lease_seconds = 15 if selected_job.priority == 1 else 180
            expires_at = now + timedelta(seconds=lease_seconds)
            lease_id = str(uuid.uuid4())

            existing_leases = json.loads(selected_job.active_leases_json or "[]")
            existing_leases.append(
                {
                    "lease_id": lease_id,
                    "worker_pubkey": worker_pubkey,
                    "model_family": model_family,
                    "model_slug": model_slug,
                    "acquired_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                }
            )
            selected_job.active_leases_json = json.dumps(existing_leases)
            selected_job.status = "claimed"
            session.add(selected_job)
            await session.commit()

            return JSONResponse(
                {
                    "job": {
                        "job_id": selected_job.job_id,
                        "url": selected_job.url,
                        "content_sha256": selected_job.content_sha256,
                        "normalized_text": selected_job.normalized_text,
                        "priority": selected_job.priority,
                        "lease_id": lease_id,
                        "lease_seconds": lease_seconds,
                    }
                }
            )


async def api_queue_submit(request: Request) -> JSONResponse:
    """POST /api/queue/submit: Verify lease, Ed25519 signature, G=1.00 grounding, and aggregate consensus."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    job_id = body.get("job_id")
    raw_pubkey = body.get("worker_pubkey")
    report_dict = body.get("report")
    if not job_id or not validate_worker_pubkey(raw_pubkey) or not report_dict:
        return JSONResponse({"error": "Missing or invalid required submit fields"}, status_code=400)

    worker_pubkey = str(raw_pubkey).strip().lower()
    model_slug = str(body.get("model_slug") or settings.DEFAULT_WORKER_MODEL).strip()
    if not MODEL_SLUG_REGEX.match(model_slug) or ".." in model_slug:
        return JSONResponse({"error": "Invalid model_slug format"}, status_code=400)
    model_family = resolve_model_family(model_slug)

    # 1. Cryptographic signature & pubkey binding (Vector 6 Defense)
    try:
        report_obj = AuditReport.model_validate(report_dict)
        if not verify_audit_signature(report_obj):
            return JSONResponse({"error": "Invalid Ed25519 signature on audit report"}, status_code=422)
    except Exception as e:
        return JSONResponse({"error": f"Schema or signature validation failed: {e}"}, status_code=422)

    if (report_obj.node_pubkey or "").strip().lower() != worker_pubkey:
        return JSONResponse({"error": "Report node_pubkey does not match submitting worker_pubkey"}, status_code=422)

    # 2. XSS & empty-quote defense (Vector 5)
    xss_err = validate_violation_safety(report_obj.violations)
    if xss_err:
        return JSONResponse({"error": xss_err}, status_code=422)

    async with _CLAIM_LOCK:
        async with get_async_session() as session:
            now = utc_now()
            job = (await session.exec(select(AuditJob).where(AuditJob.job_id == job_id))).first()
            if not job:
                return JSONResponse({"error": "Job not found"}, status_code=404)
            if job.status == "completed":
                return JSONResponse({"error": "Job is already completed"}, status_code=409)

            if report_obj.url != job.url:
                return JSONResponse({"error": "Report URL does not match claimed job URL"}, status_code=422)
            if (
                job.content_sha256
                and job.content_sha256 != "sha256:unknown"
                and report_obj.content_sha256 != job.content_sha256
            ):
                return JSONResponse(
                    {"error": "Report content_sha256 does not match job snapshot hash"}, status_code=422
                )

            leases = json.loads(job.active_leases_json or "[]")
            matched_lease: Optional[Dict[str, Any]] = None
            remaining_leases: List[Dict[str, Any]] = []
            for entry in leases:
                is_live = parse_iso_utc(entry["expires_at"]) > now
                if entry.get("worker_pubkey") == worker_pubkey and is_live and matched_lease is None:
                    matched_lease = entry
                elif is_live:
                    remaining_leases.append(entry)
            if matched_lease is None:
                return JSONResponse({"error": "No active unexpired lease held by worker for this job"}, status_code=403)

            completed_models = json.loads(job.completed_models_json or "[]")
            completed_workers = json.loads(job.completed_workers_json or "[]")
            if worker_pubkey in completed_workers or model_family in completed_models:
                return JSONResponse({"error": "Worker or model family already submitted for this job"}, status_code=409)

            worker = (
                await session.exec(select(WorkerRecord).where(WorkerRecord.worker_pubkey == worker_pubkey))
            ).first()
            sanitized_alias = sanitize_worker_alias(body.get("worker_alias"), worker_pubkey)
            if not worker:
                worker = WorkerRecord(
                    worker_pubkey=worker_pubkey,
                    worker_alias=sanitized_alias,
                    model_family=model_family,
                    model_slug=model_slug,
                )
                session.add(worker)
                await session.flush()
            elif body.get("worker_alias"):
                worker.worker_alias = sanitized_alias

            # 3. Fail-Closed Verbatim Grounding Verification (G=1.00)
            if report_obj.violations:
                grounding_failed = not job.normalized_text.strip() or any(
                    not validate_grounded_quote(v.quote_or_element, job.normalized_text, "")
                    for v in report_obj.violations
                )
                if grounding_failed:
                    await record_grounding_rejection(session, worker, job, remaining_leases, now)
                    return JSONResponse(
                        {"error": "Grounding precision G < 1.00: Quote not found verbatim in coordinator source text"},
                        status_code=422,
                    )

            awards, is_consensus_ready = await persist_verified_submission(
                session=session,
                job=job,
                worker=worker,
                report_obj=report_obj,
                model_family=model_family,
                model_slug=model_slug,
                worker_pubkey=worker_pubkey,
                matched_lease=matched_lease,
                remaining_leases=remaining_leases,
                completed_models=completed_models,
                completed_workers=completed_workers,
                raw_tokens=body.get("tokens_donated", 0),
                now=now,
            )

            _COMPLETED_REPORTS[job.url] = report_dict
            _COMPLETED_REPORTS.move_to_end(job.url)
            _evict_if_over_cap(_COMPLETED_REPORTS)
            if job.url in _COMPLETION_EVENTS:
                _COMPLETION_EVENTS[job.url].set()

            return JSONResponse(
                {
                    "status": "accepted",
                    "job_id": job.job_id,
                    "is_consensus_ready": is_consensus_ready,
                    "bounties_cleared": worker.bounties_cleared,
                    "quality_score": worker.quality_score,
                    "badges_awarded": [a.badge_id for a in awards],
                }
            )


async def api_queue_stats(request: Request) -> JSONResponse:
    """GET /api/queue/stats: Return mempool queue vitals, active workers, and estimated wait."""
    async with get_async_session() as session:
        pending = len((await session.exec(select(AuditJob).where(AuditJob.status == "pending"))).all())
        claimed = len((await session.exec(select(AuditJob).where(AuditJob.status == "claimed"))).all())
        workers = len((await session.exec(select(WorkerRecord))).all())
        wait_sec = compute_estimated_queue_wait(pending, workers)

        return JSONResponse(
            {
                "depth": pending,
                "active_leases": claimed,
                "registered_workers": workers,
                "estimated_wait_seconds": wait_sec,
            }
        )
