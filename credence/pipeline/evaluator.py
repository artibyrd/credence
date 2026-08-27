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

import asyncio
import json
import logging
from typing import List, Optional

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfileConfig
from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.snapshot import DualCaptureResult, capture_webpage_fastpath
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.adapters import LLMResponse, get_llm_provider
from credence.pipeline.governor import (
    check_budget_before_call,
    evaluate_quality_and_should_escalate,
    get_active_api_key,
    record_token_usage,
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
from credence.pipeline.subagents import (
    build_satire_provenance_prompt,
    build_specialist_prompt,
    parse_satire_response,
    parse_specialist_response,
    validate_all_violations,
)
from credence.taxonomy_loader import TaxonomyRegistry, registry

logger = logging.getLogger(__name__)


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

    # Step 1: Satire & Specialist Evaluations (LLM Provider with Heuristic Fallback)
    is_satire = snapshot.extracted.is_satire_cue
    satire_notes: Optional[str] = None
    content_type = "NEWS_ARTICLE"

    if is_satire:
        content_type = "SATIRE_PARODY"
        satire_notes = f"Satire cues detected: {'; '.join(snapshot.extracted.satire_cue_reasons)}"

    discovered_violations: List[SpecialistViolationFinding] = []
    # Always include DOM structural violations (e.g. microscopic disclaimers, disguised ads, hidden terms)
    dom_structural_violations = heuristic_evaluate_content(snapshot.extracted, snapshot.raw_html, reg=active_reg)
    discovered_violations.extend(dom_structural_violations)
    used_llm = False

    provider = get_llm_provider()
    if provider is not None and not quota_preserved:
        try:
            # 1a. Satire evaluation via LLM
            satire_prompt = build_satire_provenance_prompt(snapshot.extracted, reg=active_reg)
            satire_resp = await provider.generate(satire_prompt, thinking_budget=1024)
            satire_verdict = parse_satire_response(satire_resp.text)
            if satire_verdict.is_satire or snapshot.extracted.is_satire_cue:
                is_satire = True
                content_type = satire_verdict.classification if satire_verdict.is_satire else "SATIRE_PARODY"
                satire_notes = (
                    satire_verdict.notes
                    or f"Satire cues: {', '.join(satire_verdict.satire_cues_found or snapshot.extracted.satire_cue_reasons)}"
                )

            # 1b. Specialist evaluations via LLM
            catalogs_to_audit = ["spj_ethics", "iep_fallacies", "deceptive_patterns"]
            prompts = [
                build_specialist_prompt(cat_id, snapshot.extracted, reg=active_reg) for cat_id in catalogs_to_audit
            ]
            specialist_tasks = [provider.generate(p_text, thinking_budget=2048) for p_text in prompts]

            llm_responses = await asyncio.gather(*specialist_tasks, return_exceptions=True)
            total_prompt_tok = satire_resp.prompt_tokens
            total_comp_tok = satire_resp.completion_tokens
            total_think_tok = satire_resp.thinking_tokens

            for cat_id, resp in zip(catalogs_to_audit, llm_responses, strict=True):
                if isinstance(resp, LLMResponse):
                    total_prompt_tok += resp.prompt_tokens
                    total_comp_tok += resp.completion_tokens
                    total_think_tok += resp.thinking_tokens
                    parsed_rep = parse_specialist_response(resp.text, cat_id, reg=active_reg)
                    existing_keys = {(v.rule_id, v.quote_or_element) for v in discovered_violations}
                    for v in parsed_rep.violations:
                        if (v.rule_id, v.quote_or_element) not in existing_keys:
                            discovered_violations.append(v)
                            existing_keys.add((v.rule_id, v.quote_or_element))

            if session is not None:
                await record_token_usage(
                    session=session,
                    model_name=provider.model_name,
                    prompt_tokens=total_prompt_tok,
                    completion_tokens=total_comp_tok,
                    thinking_tokens=total_think_tok,
                    caller="evaluator_pipeline",
                )
            used_llm = True
        except Exception as e:
            logger.warning("LLM provider evaluation failed, falling back to offline heuristics: %s", e)
            quota_preserved = True
            used_llm = False
            # Restore initial extraction state for clean fallback
            is_satire = snapshot.extracted.is_satire_cue
            content_type = "SATIRE_PARODY" if is_satire else "NEWS_ARTICLE"
            satire_notes = (
                f"Satire cues detected: {'; '.join(snapshot.extracted.satire_cue_reasons)}" if is_satire else None
            )

    # Fallback to offline structural heuristics if LLM unavailable or failed
    if not used_llm:
        discovered_violations = heuristic_evaluate_content(snapshot.extracted, snapshot.raw_html, reg=active_reg)

    # Step 2: Grounded Quote Validation
    validated_violations = validate_all_violations(
        discovered_violations,
        raw_text=snapshot.extracted.clean_text,
        raw_html=snapshot.raw_html,
    )

    # Check for cloaked disinformation or commercial deceptive patterns overriding satire
    has_cloaked_disinfo = any(
        v.rule_id == "SPJ-1.6"
        and (
            "wiretapping" in v.quote_or_element.lower()
            or "blackmail" in v.quote_or_element.lower()
            or "felony" in v.quote_or_element.lower()
            or "arresting mayor" in v.quote_or_element.lower()
            or not snapshot.extracted.is_satire_cue
        )
        for v in validated_violations
    )
    has_deceptive_patterns = any(v.domain == "DECEPTIVE_PATTERN" and v.is_grounded for v in validated_violations)

    if has_cloaked_disinfo or has_deceptive_patterns:
        is_satire = False
        content_type = "NEWS_ARTICLE" if has_cloaked_disinfo else "DECEPTIVE_UI"
        if has_cloaked_disinfo:
            satire_notes = "Cloaked bad-faith satire defense detected (penalized under SPJ-1.6)."
        elif has_deceptive_patterns:
            satire_notes = "Commercial deceptive patterns detected (satire immunity overridden)."

    # Step 3: Calibrated Scoring
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

    # Step 4: Quality Gate & Escalation Assessment
    should_escalate, esc_reason = evaluate_quality_and_should_escalate(
        validated_violations, confidence_score, calibrated_score
    )

    taxonomies_used = active_reg.get_catalog_hashes()

    # Step 5: Truthful Attestation Tagging & Structural Disclosure
    if used_llm and not quota_preserved:
        eval_method = f"llm_multi_agent_{provider.model_name if provider else 'active'}"
    else:
        from credence.config import settings

        confidence_score = min(settings.HEURISTIC_MAX_CONFIDENCE_CEILING, confidence_score)
        eval_method = f"offline_structural_heuristic@{settings.HEURISTIC_ENGINE_VERSION}"
        quota_preserved = True

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
        # Step 1: Ingest snapshot (Fastpath with Playwright fallback)
        snapshot_result = await capture_webpage_fastpath(url, save_artifacts=True)

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

        # Step 4: Check for parent revision and calculate temporal differential
        parent_snapshot_id = None
        revision_index = 1
        content_diff_json = None
        token_drift_val = 0.0
        score_delta = None
        violations_added = 0
        violations_resolved = 0

        prev_snap_stmt = select(Snapshot).where(Snapshot.url == url).order_by(col(Snapshot.captured_at).desc())
        prev_snap = (await s.exec(prev_snap_stmt)).first()

        if prev_snap:
            parent_snapshot_id = prev_snap.id
            revision_index = (prev_snap.revision_index or 1) + 1

            # Compute text diff and token drift if parent dom file is available
            from credence.ingestion.hasher import compute_text_diff, compute_token_drift

            try:
                parent_clean_text = ""
                if prev_snap.dom_file_path:
                    try:
                        from credence.ingestion.extractor import extract_clean_content
                        from credence.storage.base import get_blob_storage

                        storage = get_blob_storage()
                        parent_bytes = await storage.get_blob(prev_snap.dom_file_path)
                        if parent_bytes:
                            parent_extracted = extract_clean_content(parent_bytes.decode("utf-8", errors="ignore"))
                            parent_clean_text = parent_extracted.clean_text
                    except Exception as parent_err:
                        logger.debug("Could not retrieve parent clean text from storage: %s", parent_err)

                diff_res = compute_text_diff(parent_clean_text, snapshot_result.extracted.clean_text)
                content_diff_json = json.dumps(diff_res)
                token_drift_val = compute_token_drift(parent_clean_text, snapshot_result.extracted.clean_text)
            except Exception as diff_err:
                logger.debug("Non-fatal diff calculation error: %s", diff_err)

            # Calculate score delta from previous audit
            prev_audit_stmt = (
                select(Audit).where(Audit.snapshot_id == prev_snap.id).order_by(col(Audit.audited_at).desc())
            )
            prev_audit = (await s.exec(prev_audit_stmt)).first()

            if prev_audit:
                score_delta = round(report.suspicion_score - prev_audit.suspicion_score, 2)
                # Count violation differences
                prev_v_stmt = select(Violation.rule_id).where(Violation.audit_id == prev_audit.id)
                prev_rule_ids = set((await s.exec(prev_v_stmt)).all())
                current_rule_ids = {v.rule_id for v in report.violations}
                violations_added = len(current_rule_ids - prev_rule_ids)
                violations_resolved = len(prev_rule_ids - current_rule_ids)

        # Step 5: Persist to database
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
            parent_snapshot_id=parent_snapshot_id,
            revision_index=revision_index,
            content_diff=content_diff_json,
            token_drift=token_drift_val,
            is_editorial_update=snapshot_result.extracted.is_editorial_update,
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
            score_delta=score_delta,
            violations_added_count=violations_added,
            violations_resolved_count=violations_resolved,
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
