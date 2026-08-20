"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging
from typing import Optional

from mcp.server.mcpserver import MCPServer
from sqlmodel import col, select

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.evaluator import evaluate_snapshot

logger = logging.getLogger("credence.server.mcp")


def _register_eval_tools(server: MCPServer) -> None:
    """Register evaluation tools."""

    @server.tool(
        name="credence_check_url",
        description="Fetch a URL snapshot, extract structured text, and evaluate against epistemic taxonomies.",
    )
    async def check_url(url: str, force: bool = False, profile: Optional[str] = None) -> str:
        from credence.pipeline.evaluator import audit_url

        prof_cfg = COST_PROFILES.get(CostProfile(profile.lower())) if profile else None
        report = await audit_url(url, force_refresh=force, profile_override=prof_cfg)
        return json.dumps(report.model_dump(mode="json"), indent=2)

    @server.tool(
        name="credence_evaluate_text",
        description="Evaluate arbitrary plain text for logical fallacies, deceptive patterns, and bias without network requests.",
    )
    async def evaluate_text(
        text: str,
        title: str = "Pasted Text Analysis",
        byline: str = "Direct MCP Input",
        profile: Optional[str] = None,
    ) -> str:
        from credence.ingestion.extractor import ExtractedContent
        from credence.ingestion.hasher import compute_content_sha256, compute_simhash
        from credence.ingestion.snapshot import DualCaptureResult

        prof_cfg = COST_PROFILES.get(CostProfile(profile.lower())) if profile else None
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
        await init_db()
        async with get_async_session() as s:
            report = await evaluate_snapshot(snapshot, session=s, sign_result=True, profile_override=prof_cfg)

            # Persist to database for cache & resource lookups
            snap_record = Snapshot(
                url="text://inline",
                content_sha256=snapshot.content_sha256,
                simhash_64=snapshot.simhash_64,
                clean_text_length=snapshot.extracted.char_count,
                word_count=snapshot.extracted.word_count,
                title=snapshot.extracted.title,
                byline=snapshot.extracted.byline,
                is_satire_cue=snapshot.extracted.is_satire_cue,
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

            return json.dumps(report.model_dump(mode="json"), indent=2)

        return "{}"


async def _execute_browse_audits(category: str = "recent", limit: int = 10, format: str = "human") -> str:
    """Helper to browse stored audit records for FastMCP tools and resources."""
    import secrets

    await init_db()
    async with get_async_session() as s:
        cat = category.lower()
        if cat in ("best", "clean"):
            stmt = (
                select(Audit)
                .where(Audit.suspicion_score <= 15.0)
                .order_by(col(Audit.suspicion_score).asc(), col(Audit.audited_at).desc())
                .limit(limit)
            )
        elif cat in ("worst", "flagged", "deceptive"):
            stmt = (
                select(Audit)
                .where(Audit.suspicion_score >= 60.0)
                .order_by(col(Audit.suspicion_score).desc(), col(Audit.audited_at).desc())
                .limit(limit)
            )
        elif cat == "satire":
            stmt = select(Audit).where(Audit.is_satire).order_by(col(Audit.audited_at).desc()).limit(limit)
        elif cat == "random":
            stmt = select(Audit).limit(limit * 3)
        else:  # "recent"
            stmt = select(Audit).order_by(col(Audit.audited_at).desc()).limit(limit)

        audits = list((await s.exec(stmt)).all())
        if cat == "random" and audits:
            secrets.SystemRandom().shuffle(audits)
            audits = audits[:limit]

        if not audits:
            return json.dumps({"message": f"No audit records found for category '{category}'."})

        fmt = format.lower()
        if fmt == "ndjson":
            lines = []
            for a in audits:
                d = a.to_dict() if hasattr(a, "to_dict") else a.model_dump()
                lines.append(json.dumps(d, default=str))
            return "\n".join(lines)
        elif fmt == "tsv":
            lines = ["content_sha256\tsuspicion_score\tclassification\tconfidence_score\taudited_at"]
            for a in audits:
                lines.append(
                    f"{a.content_sha256}\t{a.suspicion_score:.1f}\t{a.classification}\t{a.confidence_score:.2f}\t{a.audited_at}"
                )
            return "\n".join(lines)
        elif fmt == "compact":
            lines = []
            for a in audits:
                badge = "SATIRE" if a.is_satire else a.classification
                lines.append(
                    f"[{a.suspicion_score:4.1f}] {badge:12} | SHA: {a.content_sha256[:20]}... | {a.audited_at}"
                )
            return "\n".join(lines)
        elif fmt in ("human", "markdown", "summary"):
            lines = [f"### 🛡️ Credence Epistemic Audits Stream: {category.upper()}", ""]
            for idx, a in enumerate(audits, 1):
                badge = "🎭 SATIRE" if a.is_satire else a.classification
                lines.append(
                    f"{idx}. **{badge}** (Score: `{a.suspicion_score:.1f}/100.0`, Density: `{a.suspicion_density:.1f}/1k`) — SHA: `{a.content_sha256[:16]}...` ({a.audited_at})"
                )
            return "\n".join(lines)
        else:
            records = [a.to_dict() if hasattr(a, "to_dict") else a.model_dump() for a in audits]
            return json.dumps(records, indent=2, default=str)

    return "{}"
