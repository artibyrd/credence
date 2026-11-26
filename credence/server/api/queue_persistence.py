"""Submission Persistence, Worker Telemetry Updates & Consensus Finalization for Mempool API.

Extracted from queue.py to uphold the 500 LOC Ceiling Law with strict DAG imports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import settings
from credence.mesh.models import BadgeAward
from credence.mesh.worker_badges import evaluate_worker_badges
from credence.models import Audit, AuditJob, DomainMetric, FeedItem, Snapshot, Violation, WorkerRecord
from credence.pipeline.schemas import AuditReport
from credence.server.api.queue_guards import (
    MAX_TOKENS_DONATED_PER_SUBMIT,
    compute_consensus_verdict,
)
from credence.server.api.workers import compute_worker_quality_score
from credence.subjects.expertise import (
    RECENT_WINDOW_SIZE,
    SLASH_STREAK_THRESHOLD,
    _compute_prior_baseline,
    _parse_recent_deviations,
    compute_divergence_acceleration_dampening,
    get_node_subject_expertise,
    record_domain_evaluation,
)
from credence.worker.leases import resolve_model_family


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
        worker.divergence_slashes_count,
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
        worker.divergence_slashes_count,
    )

    awards = evaluate_worker_badges(worker)
    worker.badges_unlocked_json = json.dumps([a.model_dump() for a in awards])
    session.add(worker)

    # Finalize Bayesian consensus scoped strictly to this job's participating workers
    if len(completed_models) >= job.target_quorum:
        await session.flush()

        subject_id: Optional[str] = getattr(job, "subject_id", None) or getattr(job, "subject_tag", None)
        if not subject_id:
            feed_item = (await session.exec(select(FeedItem).where(FeedItem.item_url == job.url))).first()
            if feed_item and feed_item.subject_id:
                subject_id = feed_item.subject_id

        job_audits = (
            await session.exec(
                select(Audit)
                .where(
                    Audit.snapshot_id == snapshot.id,
                    col(Audit.node_pubkey).in_(completed_workers),
                )
                .order_by(col(Audit.id))
            )
        ).all()
        audit_by_pubkey: Dict[str, Audit] = {}
        for audit_row in job_audits:
            if audit_row.node_pubkey:
                audit_by_pubkey[audit_row.node_pubkey] = audit_row

        participating_workers = (
            await session.exec(select(WorkerRecord).where(col(WorkerRecord.worker_pubkey).in_(completed_workers)))
        ).all()
        worker_by_pubkey = {w.worker_pubkey: w for w in participating_workers}
        worker_qualities = {w.worker_pubkey: w.quality_score for w in participating_workers}
        peer_recent_deviations: Dict[str, List[float]] = {}
        peer_baseline_deviations: Dict[str, Optional[float]] = {}
        for w in participating_workers:
            w_recent = _parse_recent_deviations(w.recent_deviations_json)
            prior_evals = (
                w.consensus_evaluations_count
                if w.consensus_evaluations_count > 0
                else max(0, w.total_completed - (1 if w.worker_pubkey == worker_pubkey else 0))
            )
            w_baseline = _compute_prior_baseline(prior_evals, w.median_deviations_sum, w_recent)
            peer_recent_deviations[w.worker_pubkey] = w_recent
            peer_baseline_deviations[w.worker_pubkey] = w_baseline

        subject_expertise_map: Optional[Dict[str, float]] = None
        if subject_id:
            subject_expertise_map = {
                w.worker_pubkey: await get_node_subject_expertise(session, w.worker_pubkey, subject_id)
                for w in participating_workers
            }
            dm_rows = (
                await session.exec(
                    select(DomainMetric).where(
                        DomainMetric.subject_id == subject_id,
                        col(DomainMetric.node_pubkey).in_(completed_workers),
                    )
                )
            ).all()
            for dm in dm_rows:
                dm_recent = _parse_recent_deviations(dm.recent_deviations_json)
                dm_baseline = _compute_prior_baseline(dm.evaluations_count, dm.median_deviations_sum, dm_recent)
                dm_damp = compute_divergence_acceleration_dampening(dm_recent, baseline_deviation=dm_baseline)
                w_damp = compute_divergence_acceleration_dampening(
                    peer_recent_deviations.get(dm.node_pubkey, []),
                    baseline_deviation=peer_baseline_deviations.get(dm.node_pubkey),
                )
                if dm_damp < w_damp:
                    peer_recent_deviations[dm.node_pubkey] = dm_recent
                    peer_baseline_deviations[dm.node_pubkey] = dm_baseline

        audits_list: List[Dict[str, Any]] = []
        viols_by_pubkey: Dict[str, List[Violation]] = {}
        for pubkey in completed_workers:
            a = audit_by_pubkey.get(pubkey)
            if not a:
                continue
            viols = list((await session.exec(select(Violation).where(Violation.audit_id == a.id))).all())
            viols_by_pubkey[pubkey] = viols
            w_rec = worker_by_pubkey.get(pubkey)
            family = (
                resolve_model_family(a.evaluation_model)
                if a.evaluation_model
                else (w_rec.model_family if w_rec else "general")
            )
            audits_list.append(
                {
                    "url": job.url,
                    "content_sha256": a.content_sha256,
                    "node_pubkey": a.node_pubkey,
                    "model_family": family,
                    "suspicion_score": a.suspicion_score,
                    "confidence_score": a.confidence_score,
                    "classification": a.classification,
                    "is_satire": a.is_satire,
                    "violations": [v.model_dump() for v in viols],
                }
            )

        verdict_dict = compute_consensus_verdict(
            audits_list,
            worker_qualities,
            peer_recent_deviations=peer_recent_deviations,
            subject_id=subject_id,
            subject_expertise_map=subject_expertise_map,
            peer_baseline_deviations=peer_baseline_deviations,
        )

        # Single-Lineage Galileo Auto-Escalation: expand quorum +1 (up to cap 4) before finality
        grounded_families = {
            a["model_family"] for a in audits_list if any(v.get("is_grounded", True) for v in a.get("violations", []))
        }
        other_families = {a["model_family"] for a in audits_list} - grounded_families
        all_other_clean = bool(other_families) and all(
            float(a.get("suspicion_score", 0.0)) <= 15.0 for a in audits_list if a["model_family"] in other_families
        )

        if (
            settings.MEMPOOL_GALILEO_ESCALATION_ENABLED
            and verdict_dict.get("galileo_override") is True
            and len(grounded_families) == 1
            and all_other_clean
            and job.target_quorum < 4
        ):
            verdict_dict["provisional_galileo"] = True
            job.target_quorum = min(4, job.target_quorum + 1)
            job.is_consensus_ready = False
            job.status = "claimed" if remaining_leases else "pending"
            job.completed_at = None
            job.consensus_verdict_json = json.dumps(verdict_dict)
            session.add(job)
            await session.commit()
            return awards, False

        job.status = "completed"
        job.is_consensus_ready = True
        job.completed_at = now
        job.consensus_verdict_json = json.dumps(verdict_dict)
        worker.consensus_anchors_count += 1
        session.add(worker)

        # Record live worker deviations, divergence slashing, and optional subject DomainMetric
        median_score = float(verdict_dict["median_score"])
        parsed_host = urlparse(job.url).netloc or None
        for pubkey in completed_workers:
            w_rec = worker_by_pubkey.get(pubkey)
            a = audit_by_pubkey.get(pubkey)
            if not w_rec or not a:
                continue

            deviation = abs(float(a.suspicion_score) - median_score)
            prior_evals = (
                w_rec.consensus_evaluations_count
                if w_rec.consensus_evaluations_count > 0
                else max(0, w_rec.total_completed - (1 if w_rec.worker_pubkey == worker_pubkey else 0))
            )
            w_rec.consensus_evaluations_count = prior_evals + 1
            w_rec.median_deviations_sum += deviation

            recent_devs = _parse_recent_deviations(w_rec.recent_deviations_json)
            recent_devs = (recent_devs + [deviation])[-RECENT_WINDOW_SIZE:]
            w_rec.recent_deviations_json = json.dumps(recent_devs)

            baseline = _compute_prior_baseline(
                max(w_rec.consensus_evaluations_count, w_rec.total_completed),
                w_rec.median_deviations_sum,
                recent_devs,
            )
            dampening = compute_divergence_acceleration_dampening(recent_devs, baseline_deviation=baseline)
            if dampening == 0.0:
                w_rec.consecutive_zero_dampening += 1
            else:
                w_rec.consecutive_zero_dampening = 0

            if w_rec.consecutive_zero_dampening >= SLASH_STREAK_THRESHOLD:
                w_rec.divergence_slashes_count += 1
                w_rec.consecutive_zero_dampening = 0

            w_rec.quality_score = compute_worker_quality_score(
                w_rec.total_completed,
                w_rec.bounties_cleared,
                w_rec.grounded_violations_count,
                w_rec.first_seen,
                w_rec.grounding_rejections_count,
                w_rec.divergence_slashes_count,
            )
            session.add(w_rec)

            if subject_id:
                viols = viols_by_pubkey.get(pubkey, [])
                await record_domain_evaluation(
                    session=session,
                    node_pubkey=w_rec.worker_pubkey,
                    subject_id=subject_id,
                    median_deviation=deviation,
                    grounded_quotes=len(viols),
                    total_quotes=len(viols),
                    origin_fqdn=parsed_host,
                )

    session.add(job)
    await session.commit()
    return awards, job.is_consensus_ready
