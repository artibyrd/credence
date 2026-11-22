"""Submission Persistence, Worker Telemetry Updates & Consensus Finalization for Mempool API.

Extracted from queue.py to uphold the 500 LOC Ceiling Law with strict DAG imports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.mesh.models import BadgeAward
from credence.mesh.worker_badges import evaluate_worker_badges
from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord
from credence.pipeline.schemas import AuditReport
from credence.server.api.queue_guards import (
    MAX_TOKENS_DONATED_PER_SUBMIT,
    compute_consensus_verdict,
)
from credence.server.api.workers import compute_worker_quality_score


def parse_iso_utc(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp string and ensure UTC timezone awareness."""
    dt = datetime.fromisoformat(raw)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


async def record_grounding_rejection(
    session: AsyncSession,
    worker: WorkerRecord,
    job: AuditJob,
    remaining_leases: List[Dict[str, Any]],
    now: datetime,
) -> None:
    """Slash worker quality score and release lease on ungrounded submission."""
    worker.grounding_rejections_count += 1
    worker.quality_score = compute_worker_quality_score(
        worker.total_completed,
        worker.bounties_cleared,
        worker.grounded_violations_count,
        worker.first_seen,
        worker.grounding_rejections_count,
    )
    worker.last_seen = now
    job.active_leases_json = json.dumps(remaining_leases)
    if not remaining_leases and job.status == "claimed":
        job.status = "pending"
    session.add(worker)
    session.add(job)
    await session.commit()


async def persist_verified_submission(
    session: AsyncSession,
    job: AuditJob,
    worker: WorkerRecord,
    report_obj: AuditReport,
    model_family: str,
    model_slug: str,
    worker_pubkey: str,
    matched_lease: Dict[str, Any],
    remaining_leases: List[Dict[str, Any]],
    completed_models: List[str],
    completed_workers: List[str],
    raw_tokens: Any,
    now: datetime,
) -> Tuple[List[BadgeAward], bool]:
    """Persist verified worker audit, update telemetry/badges, and finalize consensus if quorum met."""
    # Check Model Pioneer status across existing workers before recording this family
    existing_workers = (await session.exec(select(WorkerRecord))).all()
    known_families = set()
    for ew in existing_workers:
        if ew.worker_pubkey == worker_pubkey and ew.total_completed == 0:
            continue
        if ew.total_completed > 0 and ew.model_family:
            known_families.add(ew.model_family)
        for mf in json.loads(ew.distinct_models_json or "[]"):
            known_families.add(mf)
    if model_family not in known_families:
        worker.pioneer_families_count += 1

    # Update job lease & completion sets
    job.active_leases_json = json.dumps(remaining_leases)
    completed_models.append(model_family)
    completed_workers.append(worker_pubkey)
    job.completed_models_json = json.dumps(completed_models)
    job.completed_workers_json = json.dumps(completed_workers)
    if not remaining_leases and len(completed_models) < job.target_quorum:
        job.status = "pending"

    # Upsert Snapshot & persist Audit + Violations
    snapshot = (await session.exec(select(Snapshot).where(Snapshot.url == job.url))).first()
    if not snapshot:
        snapshot = Snapshot(
            url=job.url,
            content_sha256=job.content_sha256 or report_obj.content_sha256,
            simhash_64=report_obj.simhash_64 or "0x0",
            clean_text_length=len(job.normalized_text or ""),
            word_count=len((job.normalized_text or "").split()),
        )
        session.add(snapshot)
        await session.flush()

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
    await session.flush()

    for v in report_obj.violations:
        session.add(
            Violation(
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
        )

    # Update worker telemetry, quality score, and all 10 achievement badges
    try:
        clamped_tokens = max(0, min(int(raw_tokens), MAX_TOKENS_DONATED_PER_SUBMIT))
    except (TypeError, ValueError):
        clamped_tokens = 0

    distinct_models = json.loads(worker.distinct_models_json or "[]")
    if model_family not in distinct_models:
        distinct_models.append(model_family)
    worker.distinct_models_json = json.dumps(distinct_models)

    acquired_raw: Optional[str] = matched_lease.get("acquired_at")
    if acquired_raw:
        elapsed = max(0.0, (now - parse_iso_utc(acquired_raw)).total_seconds())
        if worker.fastest_turnaround_sec is None or elapsed < worker.fastest_turnaround_sec:
            worker.fastest_turnaround_sec = round(elapsed, 3)

    if now.weekday() >= 5:
        worker.weekend_completed_count += 1
    if 0 <= now.hour < 6:
        worker.night_owl_completed_count += 1

    worker.model_slug = model_slug
    worker.model_family = model_family
    worker.total_completed += 1
    worker.bounties_cleared += 1
    worker.tokens_donated += clamped_tokens
    worker.grounded_violations_count += len(report_obj.violations)
    worker.last_seen = now
    worker.quality_score = compute_worker_quality_score(
        worker.total_completed,
        worker.bounties_cleared,
        worker.grounded_violations_count,
        worker.first_seen,
        worker.grounding_rejections_count,
    )

    awards = evaluate_worker_badges(worker)
    worker.badges_unlocked_json = json.dumps([a.model_dump() for a in awards])
    session.add(worker)

    # Finalize Bayesian consensus scoped strictly to this job's participating workers
    if len(completed_models) >= job.target_quorum:
        job.status = "completed"
        job.is_consensus_ready = True
        job.completed_at = now
        worker.consensus_anchors_count += 1
        session.add(worker)

        job_audits = (
            await session.exec(
                select(Audit).where(
                    Audit.snapshot_id == snapshot.id,
                    col(Audit.node_pubkey).in_(completed_workers),
                )
            )
        ).all()
        worker_qualities = {
            w.worker_pubkey: w.quality_score
            for w in (
                await session.exec(select(WorkerRecord).where(col(WorkerRecord.worker_pubkey).in_(completed_workers)))
            ).all()
        }
        audits_list = []
        for a in job_audits:
            viols = (await session.exec(select(Violation).where(Violation.audit_id == a.id))).all()
            audits_list.append(
                {
                    "url": job.url,
                    "content_sha256": a.content_sha256,
                    "node_pubkey": a.node_pubkey,
                    "suspicion_score": a.suspicion_score,
                    "confidence_score": a.confidence_score,
                    "classification": a.classification,
                    "is_satire": a.is_satire,
                    "violations": [v.model_dump() for v in viols],
                }
            )
        job.consensus_verdict_json = json.dumps(compute_consensus_verdict(audits_list, worker_qualities))

    session.add(job)
    await session.commit()
    return awards, job.is_consensus_ready
