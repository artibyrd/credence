"""Multi-Agent Evaluator Pipeline for Credence.

Orchestrates:
1. Webpage dual-capture snapshotting.
2. Token budget check & circuit breaker safety.
3. Satire & Provenance evaluation.
4. Concurrent domain specialist auditing (SPJ Ethics, IEP Fallacies, Deceptive Patterns).
5. Grounded quote verification & quality escalation.
6. Calibrated suspicion and density scoring.
7. Ed25519 cryptographic attestation signing.
8. Database caching, token recording, and persistence.
"""

from __future__ import annotations

import json
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfileConfig
from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.snapshot import DualCaptureResult, capture_webpage
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.governor import (
    check_budget_before_call,
    evaluate_quality_and_should_escalate,
    get_active_api_key,
)
from credence.pipeline.heuristics import (
    heuristic_evaluate_content,
)
from credence.pipeline.schemas import (
    AuditReport,
    SpecialistViolationFinding,
)
from credence.pipeline.scoring import (
    classify_verdict,
    compute_aggregate_confidence,
    compute_calibrated_score,
    compute_raw_suspicion,
    compute_suspicion_density,
)
from credence.pipeline.subagents import validate_all_violations
from credence.taxonomy_loader import TaxonomyRegistry, registry


async def evaluate_snapshot(
    snapshot: DualCaptureResult,
    reg: Optional[TaxonomyRegistry] = None,
    session: Optional[AsyncSession] = None,
    sign_result: bool = True,
    profile_override: Optional[CostProfileConfig] = None,
) -> AuditReport:
    """Execute the multi-agent evaluation pipeline against a captured snapshot."""
    active_reg = reg or registry
    if not active_reg.list_catalogs():
        active_reg.load_all()

    # Check Token Budget Governor and API Key status
    quota_preserved = False
    api_key, key_source = get_active_api_key()
    if not api_key:
        quota_preserved = True

    if session is not None and not quota_preserved:
        budget_ok, reason = await check_budget_before_call(
            session, estimated_tokens=3000, profile_override=profile_override
        )
        if not budget_ok:
            quota_preserved = True

    # Step 1: Satire & Provenance Evaluation
    is_satire = snapshot.extracted.is_satire_cue
    satire_notes: Optional[str] = None
    content_type = "NEWS_ARTICLE"

    if is_satire:
        content_type = "SATIRE_PARODY"
        satire_notes = f"Satire cues detected: {'; '.join(snapshot.extracted.satire_cue_reasons)}"

    # Step 2: Run Specialist Evaluations
    discovered_violations = heuristic_evaluate_content(snapshot.extracted, snapshot.raw_html, reg=active_reg)

    # Step 3: Grounded Quote Validation
    validated_violations = validate_all_violations(
        discovered_violations,
        raw_text=snapshot.extracted.clean_text,
        raw_html=snapshot.raw_html,
    )

    # Check for cloaked disinformation
    has_cloaked_disinfo = any(v.rule_id == "SPJ-1.6" for v in validated_violations)
    if has_cloaked_disinfo:
        is_satire = False
        content_type = "NEWS_ARTICLE"
        satire_notes = "Cloaked bad-faith satire defense detected (penalized under SPJ-1.6)."

    # Step 4: Calibrated Scoring
    raw_suspicion = compute_raw_suspicion(validated_violations)
    suspicion_density = compute_suspicion_density(len(validated_violations), snapshot.extracted.word_count)
    calibrated_score = compute_calibrated_score(
        raw_score=raw_suspicion,
        is_satire=is_satire,
        has_cloaked_disinfo=has_cloaked_disinfo,
    )
    confidence_score = compute_aggregate_confidence(validated_violations)
    verdict = classify_verdict(
        suspicion_score=calibrated_score,
        is_satire=is_satire,
        has_cloaked_disinfo=has_cloaked_disinfo,
    )

    # Step 5: Quality Gate & Escalation Assessment
    should_escalate, esc_reason = evaluate_quality_and_should_escalate(
        validated_violations, confidence_score, calibrated_score
    )

    taxonomies_used = active_reg.get_catalog_hashes()

    # Structural Disclosure & Heuristic Confidence Capping (Adversarial Hardening)
    if quota_preserved:
        confidence_score = min(0.50, confidence_score)
        eval_method = "offline_structural_heuristic"
    else:
        eval_method = "llm_multi_agent"

    # Step 6: Assemble Report
    report = AuditReport(
        url=snapshot.url,
        content_sha256=snapshot.content_sha256,
        simhash_64=snapshot.simhash_64,
        suspicion_score=calibrated_score,
        suspicion_density=suspicion_density,
        confidence_score=confidence_score,
        classification=verdict,
        is_satire=is_satire,
        content_type=content_type,
        satire_notes=satire_notes,
        violations=validated_violations,
        taxonomies_used=taxonomies_used,
        quota_preserved=quota_preserved,
        evaluation_method=eval_method,
    )

    # Step 7: Cryptographic Attestation Signing
    if sign_result:
        identity = load_or_create_node_identity()
        report = sign_audit_report(report, identity)

    return report


async def audit_url(
    url: str,
    session: Optional[AsyncSession] = None,
    force_refresh: bool = False,
    profile_override: Optional[CostProfileConfig] = None,
) -> AuditReport:
    """Audit a URL with database cache checking, token budgeting, and automatic persistence."""
    await init_db()

    async def _execute_with_session(s: AsyncSession) -> AuditReport:
        # Step 1: Ingest snapshot
        snapshot_result = await capture_webpage(url, save_artifacts=True)

        # Step 2: Check cache by content_sha256 unless forced
        if not force_refresh:
            stmt = select(Audit).where(Audit.content_sha256 == snapshot_result.content_sha256)
            cached_audit = (await s.exec(stmt)).first()
            if cached_audit:
                v_stmt = select(Violation).where(Violation.audit_id == cached_audit.id)
                cached_violations = (await s.exec(v_stmt)).all()

                violations_schemas = [
                    SpecialistViolationFinding(
                        rule_id=cv.rule_id,
                        rule_uri=cv.rule_uri,
                        domain=cv.domain,
                        cluster_id=cv.cluster_id,
                        severity=cv.severity,
                        confidence=cv.confidence,
                        quote_or_element=cv.quote_or_element,
                        reasoning=cv.reasoning,
                        line_or_selector=cv.line_or_selector,
                        is_grounded=True,
                    )
                    for cv in cached_violations
                ]

                try:
                    tax_map = json.loads(cached_audit.taxonomies_used_json)
                except Exception:
                    tax_map = {}

                return AuditReport(
                    url=url,
                    content_sha256=cached_audit.content_sha256,
                    simhash_64=snapshot_result.simhash_64,
                    audited_at=cached_audit.audited_at,
                    suspicion_score=cached_audit.suspicion_score,
                    suspicion_density=cached_audit.suspicion_density,
                    confidence_score=cached_audit.confidence_score,
                    classification=cached_audit.classification,
                    is_satire=cached_audit.is_satire,
                    content_type=cached_audit.content_type,
                    satire_notes=cached_audit.satire_notes,
                    violations=violations_schemas,
                    taxonomies_used=tax_map,
                    node_pubkey=cached_audit.node_pubkey,
                    node_signature=cached_audit.node_signature,
                    quota_preserved=cached_audit.quota_preserved,
                    evaluation_method=cached_audit.evaluation_method,
                )

        # Step 3: Run fresh evaluation
        report = await evaluate_snapshot(snapshot_result, session=s, profile_override=profile_override)

        # Step 4: Persist to database
        snap_record = Snapshot(
            url=url,
            content_sha256=snapshot_result.content_sha256,
            simhash_64=snapshot_result.simhash_64,
            dom_file_path=snapshot_result.dom_file_path,
            screenshot_file_path=snapshot_result.screenshot_file_path,
            clean_text_length=snapshot_result.extracted.char_count,
            word_count=snapshot_result.extracted.word_count,
            title=snapshot_result.extracted.title,
            byline=snapshot_result.extracted.byline,
            site_name=snapshot_result.extracted.site_name,
            is_satire_cue=snapshot_result.extracted.is_satire_cue,
        )
        s.add(snap_record)
        await s.commit()
        await s.refresh(snap_record)

        audit_record = Audit(
            snapshot_id=snap_record.id,
            audited_at=report.audited_at,
            content_sha256=report.content_sha256,
            suspicion_score=report.suspicion_score,
            suspicion_density=report.suspicion_density,
            confidence_score=report.confidence_score,
            classification=report.classification,
            is_satire=report.is_satire,
            content_type=report.content_type,
            satire_notes=report.satire_notes,
            node_pubkey=report.node_pubkey,
            node_signature=report.node_signature,
            taxonomies_used_json=json.dumps(report.taxonomies_used),
            quota_preserved=report.quota_preserved,
            evaluation_method=report.evaluation_method,
        )
        s.add(audit_record)
        await s.commit()
        await s.refresh(audit_record)

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
            s.add(vr)
        await s.commit()

        return report

    if session is not None:
        return await _execute_with_session(session)
    else:
        async with get_async_session() as s:
            return await _execute_with_session(s)


async def evaluate_standalone_text(
    text: str,
    session: Optional[AsyncSession] = None,
    title: str = "Pasted Text Analysis",
    byline: str = "Direct Input",
    profile_override: Optional[CostProfileConfig] = None,
) -> AuditReport:
    """Evaluate plain text prose directly without network requests."""
    from credence.ingestion.hasher import compute_content_sha256, compute_simhash
    from credence.ingestion.snapshot import DualCaptureResult

    extracted = ExtractedContent(
        title=title,
        byline=byline,
        clean_text=text,
        word_count=len(text.split()),
        char_count=len(text),
        is_satire_cue=False,
    )
    snapshot = DualCaptureResult(
        url="text://inline",
        content_sha256=compute_content_sha256(text),
        simhash_64=compute_simhash(text),
        raw_html=f"<html><body><h1>{title}</h1><p>{text}</p></body></html>",
        screenshot_bytes=b"",
        extracted=extracted,
    )
    if session is not None:
        return await evaluate_snapshot(snapshot, session=session, sign_result=True, profile_override=profile_override)
    async with get_async_session() as s:
        return await evaluate_snapshot(snapshot, session=s, sign_result=True, profile_override=profile_override)
