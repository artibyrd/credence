"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import timedelta
from typing import Any, Optional

from mcp.server.mcpserver import Context, MCPServer
from sqlmodel import col, desc, select

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_async_session, init_db
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.security import is_safe_url
from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord, utc_now
from credence.pipeline.evaluator import evaluate_snapshot
from credence.server.api.queue_guards import (
    is_authenticated_operator,
    resolve_authoritative_enqueue_content,
)
from credence.server.mcp.anchor_service import execute_verify_and_anchor

logger = logging.getLogger("credence.server.mcp")


def _extract_operator_status(ctx: Optional[Context]) -> bool:
    """Inspect MCP Context HTTP request (if present) for explicit operator credentials."""
    if ctx is None:
        return False
    req_ctx = getattr(ctx, "_request_context", None)
    req = getattr(req_ctx, "request", None) if req_ctx is not None else None
    return is_authenticated_operator(req) if req is not None else False


def _register_eval_tools(server: MCPServer, transport_mode: str = "http") -> None:
    """Register evaluation tools with transport-aware trust boundaries."""

    @server.tool(
        name="credence_check_url",
        description="Fetch a URL snapshot, extract structured text, and evaluate against epistemic taxonomies with cache-first lookup and adaptive mempool wait when hosted workers are active.",
    )
    async def check_url(url: str, force: bool = False, profile: Optional[str] = None) -> str:
        from credence.pipeline.evaluator import audit_url
        from credence.server.api.queue import (
            clear_completion_state,
            get_completed_report,
            register_completion_listener,
        )

        allow_local = transport_mode == "stdio"
        if not is_safe_url(url, allow_local=allow_local):
            return json.dumps({"status": "rejected", "error": "Target URL blocked by SSRF security policy"}, indent=2)

        await init_db()

        # 1. Cache-first fastpath when not forcing fresh evaluation
        if not force:
            async with get_async_session() as s:
                job_stmt = (
                    select(AuditJob)
                    .where(AuditJob.url == url, AuditJob.status == "completed")
                    .order_by(desc(AuditJob.completed_at))
                    .limit(1)
                )
                existing_job = (await s.exec(job_stmt)).first()
                if existing_job and existing_job.consensus_verdict_json:
                    return json.dumps(
                        {
                            "url": url,
                            "status": "completed",
                            "consensus": json.loads(existing_job.consensus_verdict_json),
                        },
                        indent=2,
                    )

                snap = (
                    await s.exec(
                        select(Snapshot).where(Snapshot.url == url).order_by(desc(Snapshot.captured_at)).limit(1)
                    )
                ).first()
                if snap and snap.id is not None:
                    cached_audit = (
                        await s.exec(
                            select(Audit).where(Audit.snapshot_id == snap.id).order_by(desc(Audit.audited_at)).limit(1)
                        )
                    ).first()
                    if cached_audit:
                        viols = (await s.exec(select(Violation).where(Violation.audit_id == cached_audit.id))).all()
                        return json.dumps(
                            {
                                "url": url,
                                "status": "cached",
                                "content_sha256": cached_audit.content_sha256,
                                "suspicion_score": cached_audit.suspicion_score,
                                "classification": cached_audit.classification,
                                "confidence_score": cached_audit.confidence_score,
                                "node_pubkey": cached_audit.node_pubkey,
                                "node_signature": cached_audit.node_signature,
                                "violations": [v.model_dump() for v in viols],
                            },
                            indent=2,
                            default=str,
                        )
        else:
            clear_completion_state(url)

        # 2. Adaptive mempool wait ONLY in hosted coordinator mode with active workers
        if transport_mode != "stdio":
            try:
                async with get_async_session() as s:
                    recent_cutoff = utc_now() - timedelta(minutes=15)
                    active_workers = (
                        await s.exec(select(WorkerRecord).where(WorkerRecord.last_seen >= recent_cutoff).limit(1))
                    ).all()
                    if active_workers:
                        event = register_completion_listener(url)
                        enq_stmt = select(AuditJob).where(
                            AuditJob.url == url, col(AuditJob.status).in_(["pending", "claimed"])
                        )
                        if not (await s.exec(enq_stmt)).first():
                            norm_text, sha256, fetch_err = await resolve_authoritative_enqueue_content(
                                session=s,
                                url=url,
                                caller_text="",
                                caller_sha256="",
                                is_operator=False,
                            )
                            if not fetch_err and norm_text.strip():
                                s.add(
                                    AuditJob(
                                        job_id=str(uuid.uuid4()),
                                        url=url,
                                        content_sha256=sha256,
                                        normalized_text=norm_text,
                                        priority=1,
                                        client_affinity="fastmcp-ide-session",
                                        target_quorum=1,
                                        status="pending",
                                    )
                                )
                                await s.commit()
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
        description="Verify and anchor evaluated findings with verbatim grounding (G=1.00) and strict Ed25519 trust boundaries.",
    )
    async def verify_and_anchor(
        url: str,
        normalized_text: str,
        suspicion_score: float,
        classification: str,
        violations: list[dict[str, Any]],
        model_name: str = "anthropic/claude-3-7-sonnet",
        worker_pubkey: Optional[str] = None,
        worker_signature: Optional[str] = None,
        audited_at: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> str:
        return await execute_verify_and_anchor(
            url=url,
            normalized_text=normalized_text,
            suspicion_score=suspicion_score,
            classification=classification,
            violations=violations,
            model_name=model_name,
            is_stdio=(transport_mode == "stdio"),
            is_operator=_extract_operator_status(ctx),
            worker_pubkey=worker_pubkey,
            worker_signature=worker_signature,
            audited_at=audited_at,
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
            await s.flush()

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
            await s.flush()

            for v in report.violations:
                s.add(
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
                        line_or_selector=v.line_or_selector,
                    )
                )
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
        else:
            stmt = select(Audit).order_by(col(Audit.audited_at).desc()).limit(limit)

        audits = (await s.exec(stmt)).all()
        if not audits:
            return f"No audit records found for category: '{category}'"

        fmt = format.lower()
        if fmt in ("table", "grid"):
            lines = [f"{'SCORE':6} | {'VERDICT':12} | {'SHA-256':71} | {'TIMESTAMP'}", "-" * 115]
            for a in audits:
                badge = "SATIRE" if a.is_satire else a.classification
                lines.append(f"[{a.suspicion_score:4.1f}] {badge:12} | {a.content_sha256} | {a.audited_at}")
            return "\n".join(lines)
        if fmt == "ndjson":
            return "\n".join(
                json.dumps(a.to_dict() if hasattr(a, "to_dict") else a.model_dump(), default=str) for a in audits
            )
        if fmt == "tsv":
            lines = ["content_sha256\tsuspicion_score\tclassification\tconfidence_score\taudited_at"]
            for a in audits:
                lines.append(
                    f"{a.content_sha256}\t{a.suspicion_score:.1f}\t{a.classification}\t{a.confidence_score:.2f}\t{a.audited_at}"
                )
            return "\n".join(lines)
        if fmt == "compact":
            return "\n".join(
                f"[{a.suspicion_score:4.1f}] {'SATIRE' if a.is_satire else a.classification:12} | {a.content_sha256} | {a.audited_at}"
                for a in audits
            )
        if fmt in ("human", "markdown", "summary"):
            lines = [f"### 🛡️ Credence Epistemic Audits Stream: {category.upper()}", ""]
            for idx, a in enumerate(audits, 1):
                badge = "🎭 SATIRE" if a.is_satire else a.classification
                lines.append(
                    f"{idx}. **{badge}** (Score: `{a.suspicion_score:.1f}/100.0`, Density: `{a.suspicion_density:.1f}/1k`) — SHA: `{a.content_sha256}` ({a.audited_at})"
                )
            return "\n".join(lines)
        records = [a.to_dict() if hasattr(a, "to_dict") else a.model_dump() for a in audits]
        return json.dumps(records, indent=2, default=str)
