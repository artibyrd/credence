"""Verification & Cryptographic Anchoring Service for FastMCP `credence_verify_and_anchor`.

Enforces Decision 1 (Combined Synthesis Trust Boundary):
- Local stdio mode or authenticated operator: signs with node Ed25519 key against a
  real server-captured Snapshot for http(s):// URLs (or strictly text://inline).
- Remote unauthenticated MCP callers: coordinator sovereign key signing is disabled;
  caller must supply a valid Ed25519 worker_pubkey + worker_signature matching a
  server-captured Snapshot and passing G=1.00 verbatim grounding.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import desc, select

from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report, verify_audit_signature
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.security import is_safe_url
from credence.models import Audit, Snapshot, Violation, utc_now
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.pipeline.subagents import validate_grounded_quote
from credence.server.api.queue_guards import validate_violation_safety, validate_worker_pubkey


async def execute_verify_and_anchor(
    url: str,
    normalized_text: str,
    suspicion_score: float,
    classification: str,
    violations: list[dict[str, Any]],
    model_name: str,
    is_stdio: bool,
    is_operator: bool,
    worker_pubkey: Optional[str] = None,
    worker_signature: Optional[str] = None,
    audited_at: Optional[str] = None,
) -> str:
    """Verify grounding, snapshot authenticity, and Ed25519 trust boundaries before anchoring."""
    can_sign_locally = is_stdio or is_operator
    clean_url = (url or "").strip()

    if not is_safe_url(clean_url, allow_local=is_stdio):
        return json.dumps({"status": "rejected", "error": "Target URL blocked by SSRF security policy"}, indent=2)
    if not normalized_text or not normalized_text.strip():
        return json.dumps({"status": "rejected", "error": "normalized_text must be non-empty"}, indent=2)
    if not (0.0 <= float(suspicion_score) <= 100.0):
        return json.dumps({"status": "rejected", "error": "suspicion_score must be between 0.0 and 100.0"}, indent=2)

    # 1. Validate violations: reject empty quotes, XSS markup, and ungrounded citations (G=1.00)
    validated_violations: list[SpecialistViolationFinding] = []
    for v in violations:
        quote = str(v.get("quote_or_element", "") or "").strip()
        if not quote:
            return json.dumps(
                {"status": "rejected", "error": "Grounding precision G < 1.00: Empty quote_or_element is forbidden"},
                indent=2,
            )
        validated_violations.append(
            SpecialistViolationFinding(
                rule_id=str(v.get("rule_id", "GENERAL-1.0")),
                rule_uri=str(v.get("rule_uri", f"general:{v.get('rule_id', '1.0')}@v1.0.0")),
                domain=str(v.get("domain", "GENERAL")),
                cluster_id=str(v.get("cluster_id", "GENERAL")),
                severity=max(1, min(5, int(v.get("severity", 2)))),
                confidence=max(0.0, min(1.0, float(v.get("confidence", 0.95)))),
                quote_or_element=quote,
                reasoning=str(v.get("reasoning", "In-chat evaluation finding")),
            )
        )

    xss_err = validate_violation_safety(validated_violations)
    if xss_err:
        return json.dumps({"status": "rejected", "error": xss_err}, indent=2)

    for vf in validated_violations:
        if not validate_grounded_quote(vf.quote_or_element, normalized_text, ""):
            return json.dumps(
                {
                    "status": "rejected",
                    "error": "Grounding precision G < 1.00: Quote not found verbatim in source text",
                },
                indent=2,
            )

    sha256 = compute_content_sha256(normalized_text)
    simhash = compute_simhash(normalized_text)
    word_count = len(normalized_text.split())
    density = round((len(validated_violations) / max(1, word_count)) * 1000, 2)

    await init_db()
    async with get_async_session() as s:
        # 2. Enforce Snapshot authenticity for http(s):// URLs
        snap: Optional[Snapshot] = None
        if clean_url.startswith(("http://", "https://")):
            snap = (
                await s.exec(
                    select(Snapshot)
                    .where(Snapshot.url == clean_url, Snapshot.content_sha256 == sha256)
                    .order_by(desc(Snapshot.captured_at))
                    .limit(1)
                )
            ).first()
            if not snap:
                return json.dumps(
                    {
                        "status": "rejected",
                        "error": (
                            "No server-captured Snapshot matches this URL and content_sha256. "
                            "Run credence_check_url first, or anchor inline prose strictly under url='text://inline'."
                        ),
                    },
                    indent=2,
                )
        elif not can_sign_locally:
            return json.dumps(
                {
                    "status": "rejected",
                    "error": "Remote unauthenticated callers may only anchor against server-captured http(s):// Snapshots",
                },
                indent=2,
            )

        parsed_audited_at = utc_now()
        if audited_at:
            try:
                dt = datetime.fromisoformat(audited_at.replace("Z", "+00:00"))
                parsed_audited_at = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except ValueError:
                return json.dumps({"status": "rejected", "error": "Invalid audited_at ISO-8601 timestamp"}, indent=2)

        report = AuditReport(
            url=clean_url,
            content_sha256=sha256,
            simhash_64=simhash,
            audited_at=parsed_audited_at,
            suspicion_score=float(suspicion_score),
            suspicion_density=density,
            confidence_score=0.95,
            classification=classification.upper(),
            is_satire=False,
            content_type="NEWS_ARTICLE",
            violations=validated_violations,
            evaluation_method="fastmcp_in_chat_verified",
            evaluation_model=model_name,
        )

        # 3. Trust Boundary Enforcement
        if worker_pubkey or worker_signature:
            if not validate_worker_pubkey(worker_pubkey) or not worker_signature:
                return json.dumps(
                    {"status": "rejected", "error": "Invalid 64-hex worker_pubkey or missing worker_signature"},
                    indent=2,
                )
            report.node_pubkey = str(worker_pubkey).strip().lower()
            report.node_signature = str(worker_signature).strip().lower()
            if not verify_audit_signature(report):
                return json.dumps(
                    {"status": "rejected", "error": "Invalid Ed25519 worker_signature for AuditReport"},
                    indent=2,
                )
            signed = report
        elif can_sign_locally:
            ident = load_or_create_node_identity()
            signed = sign_audit_report(report, ident)
        else:
            return json.dumps(
                {
                    "status": "rejected",
                    "error": (
                        "Remote MCP verify_and_anchor requires a valid worker_pubkey and Ed25519 worker_signature; "
                        "coordinator sovereign key signing is disabled for untrusted callers."
                    ),
                },
                indent=2,
            )

        # 4. Persist Snapshot (only for local/operator text://inline) and Audit
        if snap is None:
            snap = Snapshot(
                url=clean_url,
                content_sha256=sha256,
                simhash_64=simhash,
                clean_text_length=len(normalized_text),
                word_count=word_count,
            )
            s.add(snap)
            await s.flush()

        audit_rec = Audit(
            snapshot_id=snap.id,
            audited_at=signed.audited_at,
            content_sha256=sha256,
            suspicion_score=signed.suspicion_score,
            suspicion_density=signed.suspicion_density,
            confidence_score=signed.confidence_score,
            classification=signed.classification,
            node_pubkey=signed.node_pubkey,
            node_signature=signed.node_signature,
            evaluation_method="fastmcp_in_chat_verified",
            evaluation_model=model_name,
        )
        s.add(audit_rec)
        await s.flush()

        for vf in validated_violations:
            s.add(
                Violation(
                    audit_id=audit_rec.id,
                    rule_id=vf.rule_id,
                    rule_uri=vf.rule_uri,
                    domain=vf.domain,
                    cluster_id=vf.cluster_id,
                    severity=vf.severity,
                    confidence=vf.confidence,
                    quote_or_element=vf.quote_or_element,
                    reasoning=vf.reasoning,
                )
            )
        await s.commit()

    return json.dumps(
        {
            "status": "anchored",
            "url": clean_url,
            "content_sha256": sha256,
            "node_pubkey": signed.node_pubkey,
            "node_signature": signed.node_signature,
            "violations_anchored": len(validated_violations),
            "classification": signed.classification,
            "suspicion_score": signed.suspicion_score,
        },
        indent=2,
    )
