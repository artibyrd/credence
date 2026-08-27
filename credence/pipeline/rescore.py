"""Aggressive Heuristic Re-scoring Engine for Evaluator Nodes.

Provides:
- Automated discovery of low-confidence heuristic fallback audits.
- Deep re-evaluation using active multi-agent LLM specialist swarms.
- Revision history and model provenance tracking across evaluation passes.
- Governor headroom protection and rate limiting.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import NodeRole, settings
from credence.ingestion.extractor import ExtractedContent, extract_clean_content
from credence.ingestion.snapshot import DualCaptureResult
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.governor import check_budget_before_call, get_active_api_key
from credence.pipeline.schemas import AuditReport

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def rescore_heuristic_audits(
    session: AsyncSession,
    limit: int = 20,
    force: bool = False,
) -> List[AuditReport]:
    """Scan SQLite for low-confidence heuristic fallback audits and re-evaluate with LLM."""
    if not force:
        # SERVING nodes do not run active LLM sweeps
        if settings.CREDENCE_NODE_ROLE == NodeRole.SERVING:
            logger.debug("Node role is SERVING; skipping active heuristic re-scoring sweep.")
            return []

        # Check governor budget headroom
        api_key, _ = get_active_api_key()
        if not api_key:
            logger.debug("No active LLM API key configured; skipping re-scoring sweep.")
            return []

        allowed, reason = await check_budget_before_call(session, estimated_tokens=4000)
        if not allowed:
            logger.warning("Token governor headroom throttled re-scoring sweep: %s", reason)
            return []

    # Find audits generated via heuristic fallback or quota_preserved=True
    stmt = (
        select(Audit, Snapshot)
        .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
        .where(
            (col(Audit.quota_preserved) == True)  # noqa: E712
            | (col(Audit.evaluation_method).like("offline_structural_heuristic%"))
        )
        .order_by(col(Audit.audited_at).asc())
        .limit(limit)
    )

    results = (await session.exec(stmt)).all()
    if not results:
        return []

    rescored_reports: List[AuditReport] = []

    for old_audit, snap in results:
        # Reconstruct extracted content & dual capture
        raw_html = ""
        if snap.dom_file_path and Path(snap.dom_file_path).exists():
            try:
                raw_html = Path(snap.dom_file_path).read_text(encoding="utf-8")
            except Exception:
                raw_html = ""

        if raw_html:
            extracted = extract_clean_content(raw_html, snap.url)
        else:
            title = snap.title or "Article"
            raw_html = f"<html><body><h1>{title}</h1></body></html>"
            extracted = ExtractedContent(
                title=title,
                byline=snap.byline,
                site_name=snap.site_name,
                clean_text="",
                word_count=snap.word_count,
                char_count=snap.clean_text_length,
                is_satire_cue=snap.is_satire_cue,
            )

        dual_snap = DualCaptureResult(
            url=snap.url,
            content_sha256=snap.content_sha256,
            simhash_64=snap.simhash_64,
            raw_html=raw_html,
            screenshot_bytes=b"",
            extracted=extracted,
        )

        try:
            # Re-evaluate with LLM pipeline
            new_report = await evaluate_snapshot(
                dual_snap,
                session=session,
                sign_result=True,
            )

            if not new_report.quota_preserved and "llm" in (new_report.evaluation_method or ""):
                # Update audit record with deep findings and score delta
                score_delta = round(new_report.suspicion_score - old_audit.suspicion_score, 2)

                # Remove legacy heuristic violations
                v_del = select(Violation).where(col(Violation.audit_id) == old_audit.id)
                old_violations = (await session.exec(v_del)).all()
                for ov in old_violations:
                    await session.delete(ov)

                # Update old audit fields
                old_audit.suspicion_score = new_report.suspicion_score
                old_audit.suspicion_density = new_report.suspicion_density
                old_audit.confidence_score = new_report.confidence_score
                old_audit.classification = new_report.classification
                old_audit.score_delta = score_delta
                old_audit.quota_preserved = False
                old_audit.evaluation_method = new_report.evaluation_method
                old_audit.audited_at = utc_now()
                old_audit.node_pubkey = new_report.node_pubkey
                old_audit.node_signature = new_report.node_signature
                old_audit.taxonomies_used_json = json.dumps(new_report.taxonomies_used)

                session.add(old_audit)

                # Add new verified LLM violations
                for v in new_report.violations:
                    vr = Violation(
                        audit_id=old_audit.id,
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
                    session.add(vr)

                await session.commit()
                rescored_reports.append(new_report)
                logger.info(
                    f"Successfully rescored {snap.url} ({old_audit.suspicion_score} -> {new_report.suspicion_score} pts via {new_report.evaluation_method})"
                )

        except Exception as e:
            logger.error(f"Failed to rescore audit {old_audit.id} for {snap.url}: {e}")
            continue

    return rescored_reports
