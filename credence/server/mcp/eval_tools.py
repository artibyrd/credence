"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import asyncio
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
        description="Fetch a URL snapshot, extract structured text, and evaluate against epistemic taxonomies with adaptive 25s mempool consensus wait.",
    )
    async def check_url(url: str, force: bool = False, profile: Optional[str] = None) -> str:
        from credence.models import AuditJob
        from credence.pipeline.evaluator import audit_url
        from credence.server.api.queue import get_completed_report, register_completion_listener

        # If not force, check if already completed
        if not force:
            await init_db()
            async with get_async_session() as s:
                stmt = select(AuditJob).where(AuditJob.url == url, AuditJob.status == "completed")
                res = await s.exec(stmt)
                existing = res.first()
                if existing and existing.consensus_verdict_json:
                    return json.dumps(
                        {
                            "url": url,
                            "status": "completed",
                            "consensus": json.loads(existing.consensus_verdict_json),
                        },
                        indent=2,
                    )

        # Enqueue with priority 1 for IDE FastMCP session and register completion event
        event = register_completion_listener(url)
        try:
            await init_db()
            async with get_async_session() as s:
                enq_stmt = select(AuditJob).where(AuditJob.url == url, col(AuditJob.status).in_(["pending", "claimed"]))
                enq_res = await s.exec(enq_stmt)
                if not enq_res.first():
                    job = AuditJob(
                        url=url,
                        priority=1,
                        client_affinity="fastmcp-ide-session",
                        target_quorum=1,
                        status="pending",
                    )
                    s.add(job)
                    await s.commit()

            # Adaptive wait window (25s epistemic brake)
            await asyncio.wait_for(event.wait(), timeout=25.0)
            completed = get_completed_report(url)
            if completed:
                return json.dumps(completed, indent=2)
        except asyncio.TimeoutError:
            logger.info("FastMCP 25s adaptive wait window expired; proceeding with local pipeline.")
        except Exception as e:
            logger.debug("FastMCP queue listener fallback: %s", e)

        prof_cfg = COST_PROFILES.get(CostProfile(profile.lower())) if profile else None
        report = await audit_url(url, force_refresh=force, profile_override=prof_cfg)
        return json.dumps(report.model_dump(mode="json"), indent=2)

    @server.tool(
        name="credence_verify_and_anchor",
        description="Verify and anchor in-chat evaluated findings with verbatim grounding (G=1.00) and Ed25519 cryptographic attestation.",
    )
    async def verify_and_anchor(
        url: str,
        normalized_text: str,
        suspicion_score: float,
        classification: str,
        violations: list[dict],
        model_name: str = "anthropic/claude-3-7-sonnet",
    ) -> str:
        from credence.identity import load_or_create_node_identity, sign_audit_report
        from credence.ingestion.hasher import compute_content_sha256, compute_simhash
        from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding

        # 1. Grounding check: G=1.00 assertion
        validated_violations = []
        for v in violations:
            quote = v.get("quote_or_element", "")
            if quote and quote not in normalized_text:
                return json.dumps(
                    {
                        "error": f"Grounding precision G < 1.00: Quote '{quote[:40]}...' not found in source text",
                        "status": "rejected",
                    },
                    indent=2,
                )
            validated_violations.append(
                SpecialistViolationFinding(
                    rule_id=v.get("rule_id", "GENERAL-1.0"),
                    rule_uri=v.get("rule_uri", f"general:{v.get('rule_id', '1.0')}@v1.0.0"),
                    domain=v.get("domain", "GENERAL"),
                    cluster_id=v.get("cluster_id", "GENERAL"),
                    severity=int(v.get("severity", 2)),
                    confidence=float(v.get("confidence", 0.95)),
                    quote_or_element=quote,
                    reasoning=v.get("reasoning", "In-chat evaluation finding"),
                )
            )

        # 2. Construct and sign AuditReport
        ident = load_or_create_node_identity()
        sha256 = compute_content_sha256(normalized_text)
        simhash = compute_simhash(normalized_text)
        word_count = len(normalized_text.split())
        density = round((len(validated_violations) / max(1, word_count)) * 1000, 2)
        report = AuditReport(
            url=url,
            content_sha256=sha256,
            simhash_64=simhash,
            suspicion_score=suspicion_score,
            suspicion_density=density,
            confidence_score=0.95,
            classification=classification.upper(),
            is_satire=False,
            content_type="NEWS_ARTICLE",
            violations=validated_violations,
            evaluation_method="fastmcp_in_chat_verified",
            evaluation_model=model_name,
        )
        signed = sign_audit_report(report, ident)

        # 3. Persist Snapshot and Audit
        await init_db()
        async with get_async_session() as s:
            snap_stmt = select(Snapshot).where(Snapshot.url == url)
            snap = (await s.exec(snap_stmt)).first()
            if not snap:
                snap = Snapshot(
                    url=url,
                    content_sha256=sha256,
                    simhash_64=simhash,
                    clean_text_length=len(normalized_text),
                    word_count=word_count,
                )
                s.add(snap)
                await s.commit()
                await s.refresh(snap)

            audit_rec = Audit(
                snapshot_id=snap.id,
                content_sha256=sha256,
                suspicion_score=suspicion_score,
                suspicion_density=signed.suspicion_density,
                confidence_score=signed.confidence_score,
                classification=signed.classification,
                node_pubkey=signed.node_pubkey,
                node_signature=signed.node_signature,
                evaluation_method="fastmcp_in_chat_verified",
                evaluation_model=model_name,
            )
            s.add(audit_rec)
            await s.commit()
            await s.refresh(audit_rec)

            for vf in validated_violations:
                vr = Violation(
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
                s.add(vr)
            await s.commit()

        return json.dumps(
            {
                "status": "anchored",
                "url": url,
                "content_sha256": sha256,
                "node_pubkey": signed.node_pubkey,
                "node_signature": signed.node_signature,
                "violations_anchored": len(validated_violations),
                "classification": signed.classification,
                "suspicion_score": signed.suspicion_score,
            },
            indent=2,
        )

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

    @server.tool(
        name="credence_compare_models",
        description="Compare multi-model evaluation passes and score discrepancies for a given URL or article.",
    )
    async def compare_models(url: str) -> str:
        from credence.storage.revisions import get_model_comparison_matrix

        await init_db()
        async with get_async_session() as session:
            matrix = await get_model_comparison_matrix(session, url)
            return matrix.model_dump_json(indent=2)

    @server.tool(
        name="credence_run_heuristics_benchmark",
        description="Run Tier 2 empirical calibration benchmark against the N=100+ static anchor corpus.",
    )
    async def run_heuristics_benchmark(corpus_path: Optional[str] = None) -> str:
        from pathlib import Path

        from credence.pipeline.heuristics.benchmark import run_empirical_heuristic_calibration

        c_path = Path(corpus_path) if corpus_path else None
        result = run_empirical_heuristic_calibration(corpus_path=c_path)
        return result.model_dump_json(indent=2)


async def _execute_browse_audits(category: str = "recent", limit: int = 10, format: str = "human") -> str:
    """Helper to browse stored audit records for FastMCP tools and resources."""

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

        res = await s.exec(stmt)
        audits = res.all()

        if not audits:
            return f"No audit records found for category: '{category}'"

        fmt = format.lower()
        if fmt in ("table", "grid"):
            lines = [f"{'SCORE':6} | {'VERDICT':12} | {'SHA-256':24} | {'TIMESTAMP'}", "-" * 70]
            for a in audits:
                badge = "SATIRE" if a.is_satire else a.classification
                lines.append(
                    f"[{a.suspicion_score:4.1f}] {badge:12} | SHA: {a.content_sha256[:20]}... | {a.audited_at}"
                )
            return "\n".join(lines)
        elif fmt == "ndjson":
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
