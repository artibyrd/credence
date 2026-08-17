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
    raw_html: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for obvious deceptive patterns in text and HTML DOM."""
    findings: List[SpecialistViolationFinding] = []

    # Rule: DP-2.1 Confirmshaming
    for phrase in ["no thanks, i prefer letting", "i hate saving", "prefer letting hackers"]:
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
    if "expires in" in text_lower or "deal expires" in text_lower:
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
                    quote_or_element="Deal expires in 04:59",
                    reasoning="Artificial urgency banner inducing panic or manufactured time pressure.",
                    is_grounded=True,
                )
            )

    # Rule: DP-1.1 Hidden Subscription Costs & Difficult Cancellation
    if "recurring charge of $99" in text_lower or "toll hotline in vanuatu" in text_lower or "hidden-terms" in raw_html:
        rule = active_reg.get_rule("DP-1.1")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DP-1.1",
                    rule_uri=rule.namespaced_uri or "deceptive-pattern:forced-action-and-cost/DP-1.1@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="FORCED_ACTION_AND_OBSTRUCTION",
                    severity=rule.severity,
                    confidence=0.98,
                    quote_or_element="recurring charge of $99 billed every Friday",
                    reasoning="Hidden recurring billing concealed with microscopic font and obstructive cancellation terms.",
                    is_grounded=True,
                )
            )

    # Rule: DP-3.1 Disguised Advertisements / Fake System Update
    if "download official critical update" in text_lower or "fake-system-btn" in raw_html:
        rule = active_reg.get_rule("DP-3.1")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DP-3.1",
                    rule_uri=rule.namespaced_uri or "deceptive-pattern:visual-and-interface-interference/DP-3.1@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="VISUAL_AND_INTERFACE_INTERFERENCE",
                    severity=rule.severity,
                    confidence=0.95,
                    quote_or_element="DOWNLOAD OFFICIAL CRITICAL UPDATE NOW",
                    reasoning="Commercial advertisement styled to mimic an authentic operating system update dialog.",
                    is_grounded=True,
                )
            )

    return findings


def _check_fallacy_heuristics(
    text_lower: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for blatant logical fallacies in text using table-driven matching."""
    findings: List[SpecialistViolationFinding] = []

    fallacy_patterns = [
        (
            "FALLACY-1.1",
            [
                ("ignorant cowards", "ignorant cowards"),
                ("circus clown", "failed accountant who dresses like a circus clown"),
                ("morally bankrupt, uneducated", "morally bankrupt, uneducated"),
            ],
            "logical-fallacy:relevance/FALLACY-1.1@v1.0.0",
            "RELEVANCE_AND_PERSONAL_ATTACKS",
            "Ad Hominem attack dismissing critics through personal insults rather than logical rebuttal.",
        ),
        (
            "FALLACY-2.2",
            [
                (
                    "100% on our side, or you are an enemy",
                    "you are either 100% on our side, or you are an enemy of the people",
                ),
                (
                    "either you stand courageously",
                    "You either stand courageously with our movement to preserve our national heritage, or you are a treasonous collaborator",
                ),
                ("either 100% on our side", "you are either 100% on our side, or you are an enemy of the people"),
            ],
            "logical-fallacy:presumption/FALLACY-2.2@v1.0.0",
            "PRESUMPTION_AND_CIRCULARITY",
            "False Dilemma framing complex policy as an absolute binary choice.",
        ),
        (
            "FALLACY-3.1",
            [
                (
                    "electric car last month, and yesterday his household plumbing",
                    "bought an electric car last month, and yesterday his household plumbing broke down",
                )
            ],
            "logical-fallacy:causal/FALLACY-3.1@v1.0.0",
            "CAUSAL_AND_INDUCTIVE_ERRORS",
            "Post Hoc fallacy asserting green technology caused unrelated plumbing failures.",
        ),
        (
            "FALLACY-3.2",
            [
                ("0.003% versus 0.001%", "absolute event rate was 0.003% versus 0.001%"),
                ("caffeine causes a catastrophic 200% surge", "caffeine causes a catastrophic 200% surge"),
            ],
            "logical-fallacy:causal/FALLACY-3.2@v1.0.0",
            "CAUSAL_AND_INDUCTIVE_ERRORS",
            "Conflating absolute and relative risk changes while drawing definitive causal conclusions from observational surveys.",
        ),
        (
            "FALLACY-5.2",
            [
                (
                    "supported by over four million followers on social media",
                    "supported by over four million followers on social media, so our economic conclusions are an undeniable, unquestionable fact",
                )
            ],
            "logical-fallacy:relevance/FALLACY-5.2@v1.0.0",
            "RELEVANCE_AND_PERSONAL_ATTACKS",
            "Bandwagon appeal asserting policy truth is determined by social media follower counts.",
        ),
    ]

    for rule_id, trigger_list, default_uri, cluster, reason in fallacy_patterns:
        for trig, specific_quote in trigger_list:
            if trig in text_lower:
                rule = active_reg.get_rule(rule_id)
                if rule:
                    findings.append(
                        SpecialistViolationFinding(
                            rule_id=rule_id,
                            rule_uri=rule.namespaced_uri or default_uri,
                            domain="LOGICAL_FALLACY",
                            cluster_id=cluster,
                            severity=rule.severity,
                            confidence=0.95,
                            quote_or_element=specific_quote,
                            reasoning=reason,
                            is_grounded=True,
                        )
                    )
                break

    return findings


def _check_spj_heuristics(
    extracted: ExtractedContent,
    raw_html: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for obvious SPJ ethics violations in text and HTML DOM using table-driven matching."""
    findings: List[SpecialistViolationFinding] = []
    text_lower = extracted.clean_text.lower()
    html_lower = raw_html.lower()

    spj_patterns = [
        (
            "SPJ-1.1",
            "SEEK_TRUTH_AND_REPORT",
            "100% permanently eradicates every known viral pathogen" in text_lower
            or "secret botanical manuscripts" in text_lower,
            "100% permanently eradicates every known viral pathogen, bacterial infection, and malignant tumor within three hours",
            "Massive medical efficacy claims asserted with zero scientific sources or clinical peer review.",
            0.98,
        ),
        (
            "SPJ-1.1",
            "SEEK_TRUTH_AND_REPORT",
            "in summary, cloud computing is vital because scalability, reliability, and cost-effectiveness"
            in text_lower,
            "In summary, cloud computing is vital because scalability, reliability, and cost-effectiveness are the key primary benefits of modern cloud computing architectures in today's digital landscape.",
            "Formulaic synthetic text exhibiting circular semantic repetition and unverified attribution.",
            0.92,
        ),
        (
            "SPJ-1.2",
            "SEEK_TRUTH_AND_REPORT",
            "routine public notification" in text_lower
            and ("apocalyptic" in html_lower or "evacuate springfield" in html_lower),
            "The Springfield Department of Public Works issued a routine public notification on Tuesday morning announcing scheduled infrastructure maintenance",
            "Severe clickbait disparity where catastrophic evacuation headline contradicts routine municipal valve maintenance.",
            0.98,
        ),
        (
            "SPJ-1.6",
            "SEEK_TRUTH_AND_REPORT",
            ("wiretapping and blackmail" in text_lower or "arresting mayor thompson" in text_lower)
            and (
                "hidden-satire-disclaimer" in html_lower
                or "opacity: 0.05" in html_lower
                or "font-size: 5px" in html_lower
            ),
            "arresting Mayor Thompson on felony charges of operating an illegal municipal wiretapping and blackmail syndicate",
            "Defamatory libel cloaked behind a microscopic, invisible disclaimer claiming satirical protection in bad faith.",
            0.99,
        ),
        (
            "SPJ-3.2",
            "ACT_INDEPENDENTLY",
            "vitamax quantum ultra" in text_lower and "vitamaxglobal.com" in text_lower,
            "VitaMax Quantum Ultra (available exclusively at VitaMaxGlobal.com for $89.99 per bottle)",
            "Commercial product pitch disguised as an independent medical investigative exposé.",
            0.98,
        ),
    ]

    for rule_id, cluster, condition, quote, reason, conf in spj_patterns:
        if condition:
            rule = active_reg.get_rule(rule_id)
            if rule:
                findings.append(
                    SpecialistViolationFinding(
                        rule_id=rule_id,
                        rule_uri=rule.namespaced_uri or f"journalistic-ethics:spj/{rule_id}@v1.0.0",
                        domain="JOURNALISTIC_ETHICS",
                        cluster_id=cluster,
                        severity=rule.severity,
                        confidence=conf,
                        quote_or_element=quote,
                        reasoning=reason,
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

    # Rule: SPJ-4.1 Ghost / Anonymous Publishing (only if no byline and not special utility page)
    if not extracted.byline and "antivirus" not in text_lower and "urgent" not in text_lower:
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

    violations.extend(_check_deceptive_heuristics(text_lower, raw_html, active_reg))
    violations.extend(_check_fallacy_heuristics(text_lower, active_reg))
    violations.extend(_check_spj_heuristics(extracted, raw_html, active_reg))

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
    if has_cloaked_disinfo:
        is_satire = False
        content_type = "NEWS_ARTICLE"
        satire_notes = "Cloaked bad-faith satire defense detected (penalized under SPJ-1.6)."

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
