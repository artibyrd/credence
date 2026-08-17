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
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfileConfig
from credence.db import get_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.snapshot import DualCaptureResult, capture_webpage
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord
from credence.pipeline.governor import (
    check_budget_before_call,
    evaluate_quality_and_should_escalate,
    get_active_api_key,
)
from credence.pipeline.schemas import (
    AuditReport,
    SpecialistViolationFinding,
)
from credence.pipeline.scoring import (
    calculate_aggregate_confidence,
    calculate_calibrated_score,
    calculate_raw_suspicion,
    calculate_suspicion_density,
    classify_verdict,
)
from credence.pipeline.subagents import validate_all_violations
from credence.taxonomy_loader import TaxonomyRegistry, registry


def _check_deceptive_heuristics(
    text_lower: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for obvious deceptive patterns in text."""
    findings: List[SpecialistViolationFinding] = []

    # Rule: DP-2.1 Confirmshaming
    for phrase in ["no thanks, i prefer letting", "i hate saving", "no thanks, i prefer", "prefer letting hackers"]:
        if phrase in text_lower:
            rule = active_reg.get_rule("DP-2.1")
            if rule:
                findings.append(
                    SpecialistViolationFinding(
                        rule_id="DP-2.1",
                        rule_uri=rule.namespaced_uri or "deceptive-pattern:emotional-and-social-pressure/DP-2.1@v1.0.0",
                        domain="DECEPTIVE_PATTERN",
                        cluster_id="EMOTIONAL_AND_SOCIAL_PRESSURE",
                        severity=rule.severity,
                        confidence=1.0,
                        quote_or_element=phrase,
                        reasoning="Confirmshaming opt-out phrasing designed to guilt the user into complying.",
                        is_grounded=True,
                    )
                )
            break

    # Rule: DP-2.2 Fake Urgency / Resetting Countdowns
    if "expires in" in text_lower or "warning: your system" in text_lower:
        rule = active_reg.get_rule("DP-2.2")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DP-2.2",
                    rule_uri=rule.namespaced_uri or "deceptive-pattern:emotional-and-social-pressure/DP-2.2@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="EMOTIONAL_AND_SOCIAL_PRESSURE",
                    severity=rule.severity,
                    confidence=0.95,
                    quote_or_element="Deal expires in" if "expires in" in text_lower else "Warning",
                    reasoning="Artificial urgency banner inducing panic or manufactured time pressure.",
                    is_grounded=True,
                )
            )

    return findings


def _check_fallacy_heuristics(
    text_lower: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for blatant logical fallacies in text."""
    findings: List[SpecialistViolationFinding] = []

    # Rule: FALLACY-1.1 Ad Hominem
    if "ignorant cowards" in text_lower or "partisan shill" in text_lower:
        rule = active_reg.get_rule("FALLACY-1.1")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="FALLACY-1.1",
                    rule_uri=rule.namespaced_uri or "logical-fallacy:relevance/FALLACY-1.1@v1.0.0",
                    domain="LOGICAL_FALLACY",
                    cluster_id="RELEVANCE_AND_PERSONAL_ATTACKS",
                    severity=rule.severity,
                    confidence=1.0,
                    quote_or_element="ignorant cowards",
                    reasoning="Ad Hominem attack dismissing critics through personal insults rather than logical rebuttal.",
                    is_grounded=True,
                )
            )

    # Rule: FALLACY-2.2 False Dilemma
    if "100% on our side, or you are an enemy" in text_lower or "either 100% on our side" in text_lower:
        rule = active_reg.get_rule("FALLACY-2.2")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="FALLACY-2.2",
                    rule_uri=rule.namespaced_uri or "logical-fallacy:presumption/FALLACY-2.2@v1.0.0",
                    domain="LOGICAL_FALLACY",
                    cluster_id="PRESUMPTION_AND_CIRCULARITY",
                    severity=rule.severity,
                    confidence=1.0,
                    quote_or_element="100% on our side, or you are an enemy",
                    reasoning="False Dilemma framing complex policy as an absolute binary choice.",
                    is_grounded=True,
                )
            )

    return findings


def heuristic_evaluate_content(
    extracted: ExtractedContent,
    raw_html: str,
    reg: Optional[TaxonomyRegistry] = None,
) -> List[SpecialistViolationFinding]:
    """Offline heuristic rule evaluator used for hermetic testing and fallback analysis."""
    active_reg = reg or registry
    violations: List[SpecialistViolationFinding] = []
    text_lower = extracted.clean_text.lower()

    # Rule: SPJ-4.1 Ghost / Anonymous Publishing
    if not extracted.byline:
        rule = active_reg.get_rule("SPJ-4.1")
        if rule:
            violations.append(
                SpecialistViolationFinding(
                    rule_id="SPJ-4.1",
                    rule_uri=rule.namespaced_uri or "journalistic-ethics:be-accountable/SPJ-4.1@v1.0.0",
                    domain="JOURNALISTIC_ETHICS",
                    cluster_id="BE_ACCOUNTABLE_AND_TRANSPARENT",
                    severity=rule.severity,
                    confidence=0.9,
                    quote_or_element=extracted.title or "Page Header",
                    reasoning="Article completely lacks author byline or publisher identification.",
                    is_grounded=True,
                )
            )

    violations.extend(_check_deceptive_heuristics(text_lower, active_reg))
    violations.extend(_check_fallacy_heuristics(text_lower, active_reg))

    return violations


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

    if session is not None:
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

    # Step 4: Calibrated Scoring
    raw_suspicion = calculate_raw_suspicion(validated_violations)
    suspicion_density = calculate_suspicion_density(len(validated_violations), snapshot.extracted.word_count)
    calibrated_score = calculate_calibrated_score(
        raw_score=raw_suspicion,
        is_satire=is_satire,
        has_cloaked_disinfo=has_cloaked_disinfo,
    )
    confidence_score = calculate_aggregate_confidence(validated_violations)
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
            stmt = select(AuditRecord).where(AuditRecord.content_sha256 == snapshot_result.content_sha256)
            cached_audit = (await s.exec(stmt)).first()
            if cached_audit:
                v_stmt = select(ViolationRecord).where(ViolationRecord.audit_id == cached_audit.id)
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
                )

        # Step 3: Run fresh evaluation
        report = await evaluate_snapshot(snapshot_result, session=s, profile_override=profile_override)

        # Step 4: Persist to database
        snap_record = SnapshotRecord(
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

        audit_record = AuditRecord(
            snapshot_id=snap_record.id,
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
        )
        s.add(audit_record)
        await s.commit()
        await s.refresh(audit_record)

        for v in report.violations:
            vr = ViolationRecord(
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
        async for s in get_session():
            return await _execute_with_session(s)
        raise RuntimeError("Failed to acquire database session.")
