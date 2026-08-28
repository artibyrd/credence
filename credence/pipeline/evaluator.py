"""Multi-Agent Evaluator Pipeline for Credence.

Orchestrates:
1. Webpage dual-capture snapshotting.
2. Token budget check & circuit breaker safety.
3. Taxonomy state hashing & delta inspection.
4. Satire & Provenance evaluation.
5. Granular cluster-level specialist swarm auditing (SPJ, IEP, Deceptive, Domain Catalogs).
6. Grounded quote verification & G=1.00 verbatim enforcement.
7. Longitudinal sourcing ratio & DCI metric calculation.
8. Ed25519 cryptographic attestation signing.
9. Database caching, token recording, and persistence.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import select
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
    compute_sourcing_ratios,
    compute_suspicion_density,
)
from credence.pipeline.subagents import (
    build_cluster_specialist_prompt,
    build_satire_provenance_prompt,
    parse_cluster_response,
    parse_satire_response,
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
    """Execute the granular cluster-swarm evaluation pipeline against a captured snapshot."""
    active_reg = reg or registry
    if not active_reg.list_catalogs():
        active_reg.load_all()

    # Step 0: Cart-Before-Horse Taxonomy Hashing
    taxonomy_root_hash = active_reg.get_composite_catalog_hash()
    taxonomies_used = active_reg.get_catalog_hashes()
    clusters = active_reg.get_granular_evaluation_clusters(max_rules_per_cluster=6)

    # Check Token Budget Governor and API Key status
    quota_preserved = False
    api_key, key_source = get_active_api_key()
    if not api_key:
        quota_preserved = True

    if session is not None and not quota_preserved:
        estimated_tok = 1000 + (len(clusters) * 800)
        budget_ok, reason = await check_budget_before_call(
            session, estimated_tokens=estimated_tok, profile_override=profile_override
        )
        if not budget_ok:
            quota_preserved = True

    # Step 1: Satire & Specialist Cluster Swarm Evaluations
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
    model_name: Optional[str] = None

    provider = get_llm_provider()
    if provider is not None and not quota_preserved:
        try:
            model_name = provider.model_name
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

            # 1b. Granular Cluster-Level Specialist Swarm
            specialist_tasks = []
            for cluster in clusters:
                # Find matching catalog domain
                cat = next(
                    (
                        c
                        for c in active_reg.list_catalogs()
                        if any(
                            cl.cluster_id == cluster.cluster_id or cluster.cluster_id.startswith(cl.cluster_id)
                            for cl in c.clusters
                        )
                    ),
                    None,
                )
                domain_name = cat.domain if cat else "GENERAL"
                p_text = build_cluster_specialist_prompt(cluster, snapshot.extracted, domain_name=domain_name)
                specialist_tasks.append((cluster, domain_name, provider.generate(p_text, thinking_budget=2048)))

            results = await asyncio.gather(*[t[2] for t in specialist_tasks], return_exceptions=True)
            total_prompt_tok = satire_resp.prompt_tokens
            total_comp_tok = satire_resp.completion_tokens
            total_think_tok = satire_resp.thinking_tokens

            existing_keys = {(v.rule_id, v.quote_or_element) for v in discovered_violations}
            for (cluster, domain_name, _), resp in zip(specialist_tasks, results, strict=True):
                if isinstance(resp, LLMResponse):
                    total_prompt_tok += resp.prompt_tokens
                    total_comp_tok += resp.completion_tokens
                    total_think_tok += resp.thinking_tokens
                    parsed_rep = parse_cluster_response(resp.text, cluster, domain_name=domain_name, reg=active_reg)
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
            model_name = "offline_structural_heuristic"
            is_satire = snapshot.extracted.is_satire_cue
            content_type = "SATIRE_PARODY" if is_satire else "NEWS_ARTICLE"
            satire_notes = (
                f"Satire cues detected: {'; '.join(snapshot.extracted.satire_cue_reasons)}" if is_satire else None
            )

    # Fallback to offline structural heuristics if LLM unavailable or failed
    if not used_llm:
        discovered_violations = heuristic_evaluate_content(snapshot.extracted, snapshot.raw_html, reg=active_reg)
        model_name = "offline_structural_heuristic"

    # Step 2: Grounded Quote Validation (G=1.00 Invariant)
    full_source_text = (
        f"{snapshot.extracted.title or ''}\n{snapshot.extracted.byline or ''}\n{snapshot.extracted.clean_text}"
    )
    validated_violations = validate_all_violations(
        discovered_violations,
        raw_text=full_source_text,
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

    # Step 4: Sourcing Ratios Computation
    sourcing_ratios = compute_sourcing_ratios(
        byline=snapshot.extracted.byline or "",
        content_type=content_type,
        violations=validated_violations,
        suspicion_score=calibrated_score,
    )

    # Step 5: Truthful Attestation Tagging & Structural Disclosure
    if used_llm and not quota_preserved:
        eval_method = f"llm_multi_agent_{provider.model_name if provider else 'active'}"
        eval_model = provider.model_name if provider else (model_name or "unknown_llm")
    else:
        from credence.config import settings

        confidence_score = min(settings.HEURISTIC_MAX_CONFIDENCE_CEILING, confidence_score)
        eval_method = f"offline_structural_heuristic@{settings.HEURISTIC_ENGINE_VERSION}"
        eval_model = model_name or f"heuristic_engine_v{settings.HEURISTIC_ENGINE_VERSION}"
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
        evaluation_model=eval_model,
        taxonomy_root_hash=taxonomy_root_hash,
        sourcing_ratios=sourcing_ratios,
        is_taxonomy_stale=False,
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

                try:
                    ratios_map = (
                        json.loads(cached_audit.sourcing_ratios_json)
                        if hasattr(cached_audit, "sourcing_ratios_json") and cached_audit.sourcing_ratios_json
                        else {}
                    )
                except Exception:
                    ratios_map = {}

                # Check if taxonomy is stale
                is_stale, _ = registry.is_audit_stale(
                    tax_map, cached_audit.taxonomy_root_hash if hasattr(cached_audit, "taxonomy_root_hash") else None
                )

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
                    evaluation_model=getattr(cached_audit, "evaluation_model", None),
                    taxonomy_root_hash=getattr(cached_audit, "taxonomy_root_hash", None),
                    sourcing_ratios=ratios_map,
                    is_taxonomy_stale=is_stale,
                )

        # Step 3: Run fresh evaluation
        report = await evaluate_snapshot(snapshot_result, session=s, profile_override=profile_override)

        # Step 4: Persist Snapshot and Audit to Database
        snap_stmt = select(Snapshot).where(Snapshot.content_sha256 == snapshot_result.content_sha256)
        existing_snap = (await s.exec(snap_stmt)).first()

        if not existing_snap:
            from urllib.parse import urlparse

            domain_val = urlparse(snapshot_result.url).netloc or "direct-input"
            db_snap = Snapshot(
                url=snapshot_result.url,
                domain=domain_val,
                title=snapshot_result.extracted.title,
                byline=snapshot_result.extracted.byline,
                site_name=snapshot_result.extracted.site_name,
                content_sha256=snapshot_result.content_sha256,
                simhash_64=snapshot_result.simhash_64,
                html_sha256=getattr(snapshot_result, "html_sha256", snapshot_result.content_sha256),
                clean_text=snapshot_result.extracted.clean_text,
                raw_html=snapshot_result.raw_html,
                word_count=snapshot_result.extracted.word_count,
                reading_time_minutes=max(1, (snapshot_result.extracted.word_count or 0) // 200),
                is_satire_cue=snapshot_result.extracted.is_satire_cue,
                captured_at=getattr(snapshot_result, "captured_at", datetime.now(timezone.utc)),
            )
            s.add(db_snap)
            await s.flush()
            snap_id = db_snap.id
        else:
            snap_id = existing_snap.id

        db_audit = Audit(
            snapshot_id=snap_id,
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
            evaluation_model=report.evaluation_model,
            taxonomy_root_hash=report.taxonomy_root_hash,
            sourcing_ratios_json=json.dumps(report.sourcing_ratios),
            audited_at=report.audited_at,
        )
        s.add(db_audit)
        await s.flush()

        for v in report.violations:
            db_viol = Violation(
                audit_id=db_audit.id,
                rule_id=v.rule_id,
                rule_uri=v.rule_uri,
                domain=v.domain,
                cluster_id=v.cluster_id,
                severity=v.severity,
                confidence=v.confidence,
                quote_or_element=v.quote_or_element,
                reasoning=v.reasoning,
                line_or_selector=v.line_or_selector,
                is_grounded=v.is_grounded,
            )
            s.add(db_viol)

        await s.commit()
        return report

    if session is not None:
        return await _execute_with_session(session)

    async with get_async_session() as new_session:
        return await _execute_with_session(new_session)


async def evaluate_standalone_text(
    text: str,
    title: str = "Standalone Evaluation",
    byline: str = "Anonymous",
    domain: str = "direct-input",
    reg: Optional[TaxonomyRegistry] = None,
    session: Optional[AsyncSession] = None,
    profile_override: Optional[CostProfileConfig] = None,
) -> AuditReport:
    """Evaluate raw text input directly without a network fetch."""
    from credence.ingestion.hasher import compute_content_sha256, compute_simhash, normalize_text

    clean = normalize_text(text)
    content_sha = compute_content_sha256(clean)
    simhash = compute_simhash(clean)

    extracted = ExtractedContent(
        url="file://direct-text-audit",
        title=title,
        byline=byline,
        clean_text=clean,
        word_count=len(clean.split()),
        is_satire_cue=False,
    )

    snapshot = DualCaptureResult(
        url="file://direct-text-audit",
        content_sha256=content_sha,
        simhash_64=simhash,
        raw_html=f"<html><body><p>{text}</p></body></html>",
        extracted=extracted,
    )

    return await evaluate_snapshot(snapshot, reg=reg, session=session, profile_override=profile_override)
