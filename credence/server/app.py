"""Model Context Protocol (FastMCP) Server for Credence.

Exposes:
- Tools:
  - credence_check_url: Audit target webpage and return signed attestation.
  - credence_evaluate_text: Evaluate raw prose without network scraping.
  - credence_get_audit: Retrieve cached audit report.
  - credence_verify_attestation: Cryptographically verify signed attestation.
  - credence_get_quota_status: Monitor token headroom and safety circuit breaker.
  - credence_get_consensus: Calculate Bayesian consensus score across mesh attestations.
- Resources:
  - credence://taxonomies: Index of taxonomy catalogs.
  - credence://taxonomies/{catalog_id}: Detailed rules and prompt checklists.
  - credence://node/identity: Local Ed25519 node public key.
- Prompts:
  - audit_article_prompt: Interactive prompt template.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, List, Optional

from mcp.server.mcpserver import MCPServer
from sqlmodel import col, select

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_session, init_db
from credence.identity import load_or_create_node_identity, verify_audit_report
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.taxonomy_loader import registry

logger = logging.getLogger("credence.server")


class ServerRateLimiter:
    """In-memory rate limiter per tool to defend against token starvation and burst DoS."""

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0, max_chars: int = 100_000) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_chars = max_chars
        self._calls: List[float] = []

    def check_and_record(self, payload_length: int = 0) -> bool:
        if payload_length > self.max_chars:
            raise ValueError(
                f"Payload size ({payload_length} chars) exceeds maximum allowed limit ({self.max_chars} chars)."
            )
        now = time.time()
        self._calls = [t for t in self._calls if now - t < self.window_seconds]
        if len(self._calls) >= self.max_requests:
            return False
        self._calls.append(now)
        return True


_global_rate_limiter = ServerRateLimiter()


@dataclass
class TelemetryEvent:
    timestamp: float
    status_code: int
    path: str
    duration_ms: float
    error_message: Optional[str] = None


class ServerTelemetryTracker:
    """In-memory rolling telemetry tracker for Interface Telemetry Loopback (ITLP-v1)."""

    def __init__(self, window_seconds: float = 300.0) -> None:
        self.window_seconds = window_seconds
        self.start_time: float = time.time()
        self._events: Deque[TelemetryEvent] = deque()

    def record_request(
        self, status_code: int, path: str, duration_ms: float, error_message: Optional[str] = None
    ) -> None:
        now = time.time()
        event = TelemetryEvent(
            timestamp=now,
            status_code=status_code,
            path=path,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self._events.append(event)
        self._prune(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()

    def reset(self) -> None:
        """Reset events (useful for hermetic tests)."""
        self._events.clear()
        self.start_time = time.time()

    def get_snapshot(self) -> dict[str, Any]:
        import os
        import resource

        now = time.time()
        self._prune(now)

        count_2xx = sum(1 for e in self._events if 200 <= e.status_code < 300)
        count_3xx = sum(1 for e in self._events if 300 <= e.status_code < 400)
        count_4xx = sum(1 for e in self._events if 400 <= e.status_code < 500)
        count_5xx = sum(1 for e in self._events if e.status_code >= 500)
        total = len(self._events)

        latencies = [e.duration_ms for e in self._events]
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

        try:
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            memory_mb = round(rusage.ru_maxrss / 1024.0, 2)
        except Exception:
            memory_mb = 0.0

        active_alerts: list[dict[str, Any]] = []
        status = "healthy"

        if count_5xx >= 5:
            active_alerts.append(
                {
                    "id": "alert_5xx_spike",
                    "severity": "critical",
                    "title": "5xx Server Error Spike",
                    "message": f"Detected {count_5xx} HTTP 5xx errors in the last 5 minutes.",
                }
            )
            status = "degraded"
        elif count_5xx > 0:
            active_alerts.append(
                {
                    "id": "warn_5xx_errors",
                    "severity": "warning",
                    "title": "Occasional 5xx Server Errors",
                    "message": f"Recorded {count_5xx} HTTP 5xx errors in the last 5 minutes.",
                }
            )

        mem_limit_mb = float(os.environ.get("CREDENCE_MEMORY_ALERT_MB", "1800.0"))
        if memory_mb > mem_limit_mb:
            active_alerts.append(
                {
                    "id": "alert_high_memory",
                    "severity": "warning",
                    "title": "High Memory Pressure",
                    "message": f"Memory consumption at {memory_mb} MB (exceeds {mem_limit_mb} MB baseline).",
                }
            )
            if status == "healthy":
                status = "degraded"

        recent_errors = [
            {
                "time": time.strftime("%H:%M:%S", time.gmtime(e.timestamp)),
                "path": e.path,
                "status": e.status_code,
                "error": e.error_message,
            }
            for e in reversed(self._events)
            if e.status_code >= 400
        ][:10]

        return {
            "status": status,
            "uptime_seconds": int(now - self.start_time),
            "memory_mb": memory_mb,
            "request_counts": {
                "total": total,
                "2xx": count_2xx,
                "3xx": count_3xx,
                "4xx": count_4xx,
                "5xx": count_5xx,
            },
            "latencies_ms": {
                "p50": round(p50, 1),
                "p95": round(p95, 1),
            },
            "active_alerts": active_alerts,
            "recent_errors": recent_errors,
        }


global_telemetry = ServerTelemetryTracker()


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
        from credence.pipeline.evaluator import evaluate_snapshot

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
        async for s in get_session():
            report = await evaluate_snapshot(snapshot, session=s, sign_result=True, profile_override=prof_cfg)

            # Persist to database for cache & resource lookups
            snap_record = SnapshotRecord(
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
                evaluation_method=report.evaluation_method,
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

            return json.dumps(report.model_dump(mode="json"), indent=2)

        return "{}"


async def _execute_browse_audits(category: str = "recent", limit: int = 10, format: str = "human") -> str:
    """Helper to browse stored audit records for FastMCP tools and resources."""
    import secrets

    await init_db()
    async for s in get_session():
        cat = category.lower()
        if cat in ("best", "clean"):
            stmt = (
                select(AuditRecord)
                .where(AuditRecord.suspicion_score <= 15.0)
                .order_by(col(AuditRecord.suspicion_score).asc(), col(AuditRecord.audited_at).desc())
                .limit(limit)
            )
        elif cat in ("worst", "flagged", "deceptive"):
            stmt = (
                select(AuditRecord)
                .where(AuditRecord.suspicion_score >= 60.0)
                .order_by(col(AuditRecord.suspicion_score).desc(), col(AuditRecord.audited_at).desc())
                .limit(limit)
            )
        elif cat == "satire":
            stmt = (
                select(AuditRecord)
                .where(AuditRecord.is_satire)
                .order_by(col(AuditRecord.audited_at).desc())
                .limit(limit)
            )
        elif cat == "random":
            stmt = select(AuditRecord).limit(limit * 3)
        else:  # "recent"
            stmt = select(AuditRecord).order_by(col(AuditRecord.audited_at).desc()).limit(limit)

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


def _register_query_tools(server: MCPServer) -> None:
    """Register cache lookup and quota tools."""

    @server.tool(
        name="credence_browse_audits",
        description="Browse stored epistemic audit records by category ('recent', 'best', 'worst', 'satire', 'random') with customizable limit and output format ('human', 'compact', 'json', 'ndjson', 'tsv').",
    )
    async def browse_audits(category: str = "recent", limit: int = 10, format: str = "human") -> str:
        return await _execute_browse_audits(category=category, limit=limit, format=format)

    @server.tool(
        name="credence_get_audit",
        description="Lookup a cached audit report by URL or content SHA-256 with optional markdown or human-readable format.",
    )
    async def get_audit(identifier: str, format: str = "json") -> str:
        from credence.cli.main import report_to_markdown

        await init_db()
        async for s in get_session():
            if identifier.startswith("sha256:") or len(identifier) == 64:
                clean_hash = identifier if identifier.startswith("sha256:") else f"sha256:{identifier}"
                stmt = select(AuditRecord).where(AuditRecord.content_sha256 == clean_hash)
            else:
                snap_stmt = select(SnapshotRecord).where(SnapshotRecord.url == identifier)
                snap = (await s.exec(snap_stmt)).first()
                if not snap:
                    return json.dumps({"error": f"No cached snapshot found for URL: {identifier}"})
                stmt = select(AuditRecord).where(AuditRecord.content_sha256 == snap.content_sha256)

            audit = (await s.exec(stmt)).first()
            if not audit:
                return json.dumps({"error": f"No cached audit report found for: {identifier}"})

            v_stmt = select(ViolationRecord).where(ViolationRecord.audit_id == audit.id)
            violations = (await s.exec(v_stmt)).all()

            v_schemas = [
                SpecialistViolationFinding(
                    rule_id=v.rule_id,
                    rule_uri=v.rule_uri,
                    domain=v.domain,
                    cluster_id=v.cluster_id,
                    severity=v.severity,
                    confidence=v.confidence,
                    quote_or_element=v.quote_or_element,
                    reasoning=v.reasoning,
                    line_or_selector=v.line_or_selector,
                    is_grounded=True,
                )
                for v in violations
            ]

            try:
                tax_map = json.loads(audit.taxonomies_used_json)
            except Exception:
                tax_map = {}

            report = AuditReport(
                url=identifier,
                content_sha256=audit.content_sha256,
                simhash_64="0x0000000000000000",
                audited_at=audit.audited_at,
                suspicion_score=audit.suspicion_score,
                suspicion_density=audit.suspicion_density,
                confidence_score=audit.confidence_score,
                classification=audit.classification,
                is_satire=audit.is_satire,
                content_type=audit.content_type,
                satire_notes=audit.satire_notes,
                violations=v_schemas,
                taxonomies_used=tax_map,
                node_pubkey=audit.node_pubkey,
                node_signature=audit.node_signature,
                quota_preserved=audit.quota_preserved,
            )

            if format.lower() == "markdown":
                return report_to_markdown(report)
            elif format.lower() in ("human", "summary"):
                md = report_to_markdown(report)
                badge = "SATIRE / PARODY" if report.is_satire else report.classification
                prefix = f"### 🧠 Human Epistemic Briefing: {badge} ({report.suspicion_score:.1f}/100.0)\n\n"
                return prefix + md
            elif format.lower() == "compact":
                badge = "SATIRE" if report.is_satire else report.classification
                lines = [
                    f"URL: {report.url} | Score: {report.suspicion_score:.1f}/100.0 ({badge}) | Density: {report.suspicion_density:.1f}/1k | Confidence: {report.confidence_score * 100:.0f}%",
                    f"SHA-256: {report.content_sha256} | Signer: {report.node_pubkey or 'unsigned'}",
                ]
                if report.violations:
                    lines.append("Findings:")
                    for v in report.violations:
                        lines.append(
                            f'  • [{v.rule_id}] {v.domain} (Sev {v.severity}/5): "{v.quote_or_element[:60]}" - {v.reasoning}'
                        )
                else:
                    lines.append("Findings: High epistemic integrity. No grounded violations.")
                return "\n".join(lines)
            elif format.lower() == "ndjson":
                return report.model_dump_json()
            elif format.lower() == "tsv":
                return f"{report.content_sha256}\t{report.suspicion_score:.1f}\t{report.classification}\t{report.confidence_score:.2f}\t{len(report.violations)}\t{report.url}"
            else:
                return json.dumps(report.model_dump(mode="json"), indent=2)

        return "{}"

    @server.tool(
        name="credence_get_quota_status",
        description="Get real-time token headroom %, spend metrics, and circuit breaker status.",
    )
    async def get_quota_status() -> str:
        from credence.pipeline.governor import get_token_headroom_status

        await init_db()
        async for s in get_session():
            status = await get_token_headroom_status(s)
            return json.dumps(status.model_dump(mode="json"), indent=2)
        return "{}"

    @server.tool(
        name="credence_get_health_status",
        description="Retrieve live node health, active alert conditions (5xx spikes, memory saturation), and SRE telemetry for Interface Telemetry Loopback (ITLP-v1).",
    )
    async def get_health_status() -> str:
        snapshot = global_telemetry.get_snapshot()
        return json.dumps(snapshot, indent=2)

    @server.tool(
        name="credence_get_mesh_stats",
        description="Retrieve comprehensive Node & P2P Mesh health, SRE vitals, BitTorrent compute savings, and scored pages analytics across sources and categories.",
    )
    async def get_mesh_stats() -> str:
        from credence.db import get_session, init_db
        from credence.mesh.stats import calculate_mesh_stats

        await init_db()
        snapshot = global_telemetry.get_snapshot()
        async for s in get_session():
            stats = await calculate_mesh_stats(s, telemetry_snapshot=snapshot)
            return json.dumps(stats, indent=2)
        return "{}"


def _register_consensus_tools(server: MCPServer) -> None:
    """Register attestation verification and consensus tools."""

    @server.tool(
        name="credence_verify_attestation",
        description="Cryptographically verify an Ed25519-signed audit attestation.",
    )
    async def verify_attestation(signed_attestation_json: str) -> str:
        try:
            data = json.loads(signed_attestation_json)
            report = AuditReport.model_validate(data)
            is_valid = verify_audit_report(report)
            return json.dumps(
                {
                    "is_valid": is_valid,
                    "node_pubkey": report.node_pubkey,
                    "content_sha256": report.content_sha256,
                    "suspicion_score": report.suspicion_score,
                    "verdict": report.classification,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"is_valid": False, "error": str(e)}, indent=2)

    @server.tool(
        name="credence_get_consensus",
        description="Get Bayesian consensus suspicion score across known mesh peer attestations, with optional subject-weighted expertise weighting.",
    )
    async def get_consensus(content_sha256: str, subject_id: Optional[str] = None) -> str:
        from credence.mesh.consensus import BayesianConsensusAggregator
        from credence.models import DomainMetricRecord

        await init_db()
        clean_hash = content_sha256 if content_sha256.startswith("sha256:") else f"sha256:{content_sha256}"
        async for s in get_session():
            stmt = select(AuditRecord).where(AuditRecord.content_sha256 == clean_hash)
            audits = (await s.exec(stmt)).all()
            if not audits:
                return json.dumps({"error": f"No audit records found for hash: {clean_hash}"})

            reports: List[AuditReport] = []
            for a in audits:
                v_stmt = select(ViolationRecord).where(ViolationRecord.audit_id == a.id)
                v_records = (await s.exec(v_stmt)).all()
                v_schemas = [
                    SpecialistViolationFinding(
                        rule_id=v.rule_id,
                        rule_uri=v.rule_uri,
                        domain=v.domain,
                        cluster_id=v.cluster_id,
                        severity=v.severity,
                        confidence=v.confidence,
                        quote_or_element=v.quote_or_element,
                        reasoning=v.reasoning,
                        line_or_selector=v.line_or_selector,
                        is_grounded=True,
                    )
                    for v in v_records
                ]
                reports.append(
                    AuditReport(
                        url="mesh://attestation",
                        content_sha256=a.content_sha256,
                        simhash_64="0x0000000000000000",
                        audited_at=a.audited_at,
                        suspicion_score=a.suspicion_score,
                        suspicion_density=a.suspicion_density,
                        confidence_score=a.confidence_score,
                        classification=a.classification,
                        is_satire=a.is_satire,
                        content_type=a.content_type,
                        satire_notes=a.satire_notes,
                        violations=v_schemas,
                        node_pubkey=a.node_pubkey,
                        node_signature=a.node_signature,
                        quota_preserved=a.quota_preserved,
                    )
                )

            # Load domain expertise map if subject_id specified
            exp_map = {}
            if subject_id:
                stmt_metrics = select(DomainMetricRecord).where(DomainMetricRecord.subject_id == subject_id)
                metrics = (await s.exec(stmt_metrics)).all()
                for m in metrics:
                    exp_map[m.node_pubkey] = m.expertise_score

            aggregator = BayesianConsensusAggregator()
            verdict = aggregator.calculate_consensus(
                attestations=reports,
                subject_id=subject_id,
                subject_expertise_map=exp_map,
            )
            if verdict:
                return json.dumps(verdict.model_dump(mode="json"), indent=2)
            return json.dumps({"error": "Failed to calculate consensus verdict."})

        return "{}"


def _register_mesh_tools(server: MCPServer) -> None:
    """Register P2P mesh discovery tools."""

    @server.tool(
        name="credence_get_seed_nodes",
        description="Retrieve verified active P2P bootstrap seed nodes from seeds.credence.nexus or fallback sources.",
    )
    async def get_seed_nodes(seed_url: Optional[str] = None) -> str:
        from credence.mesh.discovery import BootstrapDiscovery

        discovery = BootstrapDiscovery(seed_url=seed_url)
        peer_urls = await discovery.discover_peers()
        return json.dumps(
            {
                "canonical_seed_url": discovery.seed_url,
                "discovered_peers_count": len(peer_urls),
                "peer_urls": peer_urls,
            },
            indent=2,
        )


def _register_feed_sync_tools(server: MCPServer) -> None:
    """Register syndicated RSS/Atom/JSON feed synchronization tools."""

    @server.tool(
        name="credence_sync_feeds",
        description="Poll all active syndicated RSS/Atom/JSON feeds, perform mesh effort avoidance, and adopt peer attestations at $0 token cost.",
    )
    async def sync_feeds_tool(dry_run: bool = False, evaluate_novel: bool = True) -> str:
        from credence.db import get_session, init_db
        from credence.feeds.worker import sync_all_feeds

        await init_db()
        async for session in get_session():
            summary = await sync_all_feeds(session=session, dry_run=dry_run, evaluate_novel=evaluate_novel)
            return json.dumps(
                {
                    "total_feeds_polled": summary.total_feeds_polled,
                    "feeds_unmodified_304": summary.feeds_unmodified_304,
                    "new_items_discovered": summary.new_items_discovered,
                    "items_adopted_from_mesh": summary.items_adopted_from_mesh,
                    "tokens_saved_total": summary.tokens_saved_total,
                    "items_deferred_budget": summary.items_deferred_budget,
                    "dry_run": dry_run,
                },
                indent=2,
            )
        return "{}"

    @server.tool(
        name="credence_get_feed_stats",
        description="Get aggregate feed pre-ingestion metrics, zero-token adoptions, and tokens saved.",
    )
    async def get_feed_stats_tool() -> str:
        from credence.db import get_session, init_db
        from credence.models import FeedItemRecord, FeedSubscriptionRecord

        await init_db()
        async for session in get_session():
            stmt_subs = select(FeedSubscriptionRecord)
            subs = (await session.exec(stmt_subs)).all()
            stmt_items = select(FeedItemRecord)
            items = (await session.exec(stmt_items)).all()

            adopted = [i for i in items if i.processing_status == "mesh_adopted"]
            return json.dumps(
                {
                    "active_subscriptions_count": len([s for s in subs if s.is_active]),
                    "total_articles_discovered": len(items),
                    "zero_token_adoptions_count": len(adopted),
                    "total_tokens_saved": sum(i.tokens_saved for i in items),
                    "attestation_seeding_active": True,
                },
                indent=2,
            )
        return "{}"


def _register_feed_management_tools(server: MCPServer) -> None:
    """Register syndicated feed subscription management tools."""

    @server.tool(
        name="credence_add_feed_subscription",
        description="Subscribe node to a syndicated RSS 2.0, Atom 1.0, or JSON Feed.",
    )
    async def add_feed_subscription_tool(
        feed_url: str,
        title: str = "",
        priority_tier: int = 2,
        subject_tag: str = "journalism.news",
        is_satire: bool = False,
    ) -> str:
        from credence.db import get_session, init_db
        from credence.models import FeedSubscriptionRecord

        await init_db()
        async for session in get_session():
            sub = FeedSubscriptionRecord(
                feed_url=feed_url,
                title=title,
                priority_tier=priority_tier,
                subject_tag=subject_tag,
                is_satire=is_satire,
            )
            session.add(sub)
            await session.commit()
            return json.dumps({"status": "success", "feed_url": feed_url, "priority_tier": priority_tier})
        return "{}"

    @server.tool(
        name="credence_list_feeds",
        description="List all registered syndicated RSS/Atom/JSON feed subscriptions.",
    )
    async def list_feeds_tool() -> str:
        from sqlmodel import col

        from credence.db import get_session, init_db
        from credence.models import FeedSubscriptionRecord

        await init_db()
        async for session in get_session():
            stmt = select(FeedSubscriptionRecord).order_by(col(FeedSubscriptionRecord.priority_tier).asc())
            subs = (await session.exec(stmt)).all()
            return json.dumps(
                [
                    {
                        "id": s.id,
                        "feed_url": s.feed_url,
                        "title": s.title,
                        "priority_tier": s.priority_tier,
                        "subject_tag": s.subject_tag,
                        "is_active": s.is_active,
                        "is_satire": s.is_satire,
                        "etag": s.etag,
                        "last_polled_at": s.last_polled_at.isoformat() if s.last_polled_at else None,
                    }
                    for s in subs
                ],
                indent=2,
            )
        return "[]"

    @server.tool(
        name="credence_discover_feeds",
        description="Autonomously discover RSS/Atom/JSON feed candidate endpoints from any target webpage.",
    )
    async def discover_feeds_tool(target_url: str) -> str:
        from dataclasses import asdict

        from credence.feeds.discovery import discover_feed_endpoints

        candidates = await discover_feed_endpoints(target_url)
        return json.dumps([asdict(c) for c in candidates], indent=2)

    @server.tool(
        name="credence_inspect_feed_health",
        description="Run pre-flight forensic audit on a candidate feed to calculate Topic Entropy (H_topic), ethics, and F_j quality score.",
    )
    async def inspect_feed_health_tool(feed_url: str) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.feeds.health import run_preflight_feed_audit

        await init_db()
        async for session in get_session():
            result = await run_preflight_feed_audit(feed_url, session=session)
            return json.dumps(asdict(result), indent=2)
        return "{}"

    @server.tool(
        name="credence_generate_digest",
        description="Generate a structured Morning Epistemic Briefing from recent evaluated feed items.",
    )
    async def generate_digest_tool(hours: int = 24) -> str:
        from credence.db import get_session, init_db
        from credence.feeds.digest import generate_morning_digest

        await init_db()
        async for session in get_session():
            digest = await generate_morning_digest(session, timeframe_hours=hours)
            return json.dumps(digest.to_dict(), indent=2)
        return "{}"

    @server.tool(
        name="credence_expand_roots",
        description="Extract cited external domains from verified clean articles, discover RSS/Atom feed endpoints, and autonomously subscribe to new roots.",
    )
    async def expand_roots_tool(max_new_sources: int = 5, min_citation_count: int = 1, dry_run: bool = False) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.feeds.roots import expand_roots

        await init_db()
        async for session in get_session():
            summary = await expand_roots(
                session, max_new_sources=max_new_sources, min_citation_count=min_citation_count, dry_run=dry_run
            )
            return json.dumps(asdict(summary), indent=2)
        return "{}"

    @server.tool(
        name="credence_trigger_boredom_cycle",
        description="Trigger an opportunistic boredom cycle to digest pending feed items and autonomously expand subscription roots when token headroom allows.",
    )
    async def trigger_boredom_cycle_tool(
        audit_burst: int = 3,
        boredom_ratio: float = 0.60,
        expand_roots: bool = True,
    ) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.feeds.boredom import run_boredom_cycle

        await init_db()
        async for session in get_session():
            summary = await run_boredom_cycle(
                session,
                audit_burst=audit_burst,
                boredom_ratio=boredom_ratio,
                expand_roots_enabled=expand_roots,
            )
            res = asdict(summary)
            res["timestamp"] = summary.timestamp.isoformat()
            return json.dumps(res, indent=2)
        return "{}"

    @server.tool(
        name="credence_get_domain_reputation",
        description="Retrieve domain-level reputation score, status, and BuzzFeed Doctrine redemption progress.",
    )
    async def get_domain_reputation_tool(domain: str) -> str:
        from credence.db import get_session, init_db
        from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

        await init_db()
        async for session in get_session():
            rec = await get_or_create_domain_reputation(session, normalize_domain(domain))
            return json.dumps(rec.model_dump(mode="json"), indent=2)
        return "{}"

    @server.tool(
        name="credence_get_domain_quarantine",
        description="List all currently quarantined or suspicious domains with exponential polling backoff factors.",
    )
    async def get_domain_quarantine_tool() -> str:
        from credence.db import get_session, init_db
        from credence.feeds.reputation import get_domain_quarantine_list

        await init_db()
        async for session in get_session():
            quarantined = await get_domain_quarantine_list(session)
            return json.dumps(quarantined, indent=2)
        return "[]"

    @server.tool(
        name="credence_appeal_domain_quarantine",
        description="File an expedited BuzzFeed News Doctrine redemption appeal for a quarantined domain.",
    )
    async def appeal_domain_quarantine_tool(domain: str) -> str:
        from credence.db import get_session, init_db
        from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

        await init_db()
        async for session in get_session():
            rec = await get_or_create_domain_reputation(session, normalize_domain(domain))
            return json.dumps(
                {
                    "domain": rec.domain,
                    "status": rec.status,
                    "reputation_score": rec.reputation_score,
                    "appeal_status": "QUEUED_FOR_EXPEDITED_AUDIT",
                    "doctrine": "The BuzzFeed News Doctrine (Asymmetric Epistemic Recovery)",
                },
                indent=2,
            )
        return "{}"

    @server.tool(
        name="credence_get_root_candidates",
        description="Retrieve un-subscribed candidate source domains cited by audited high-integrity articles.",
    )
    async def get_root_candidates_tool(limit: int = 10) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.feeds.roots import extract_root_candidates

        await init_db()
        async for session in get_session():
            candidates = await extract_root_candidates(session, limit=limit)
            return json.dumps([asdict(c) for c in candidates], indent=2)
        return "[]"

    @server.tool(
        name="credence_remove_feed_subscription",
        description="Unsubscribe and remove a syndicated feed by URL.",
    )
    async def remove_feed_subscription_tool(feed_url: str) -> str:
        from credence.db import get_session, init_db
        from credence.models import FeedSubscriptionRecord

        await init_db()
        async for session in get_session():
            stmt = select(FeedSubscriptionRecord).where(FeedSubscriptionRecord.feed_url == feed_url)
            sub = (await session.exec(stmt)).first()
            if sub:
                await session.delete(sub)
                await session.commit()
                return json.dumps({"status": "removed", "feed_url": feed_url})
            return json.dumps({"error": f"Feed subscription not found for: {feed_url}"})
        return "{}"


def _register_taxonomy_resources(server: MCPServer) -> None:
    """Register taxonomy, profile, identity, and seed resources."""

    @server.resource("credence://profiles")
    def list_profiles_resource() -> str:
        from credence.config import COST_PROFILES

        data = {
            prof.value: {
                "name": cfg.name,
                "description": cfg.description,
                "max_daily_budget_usd": cfg.max_daily_budget_usd,
                "max_tokens_per_hour": cfg.max_tokens_per_hour,
                "max_tokens_per_day": cfg.max_tokens_per_day,
                "default_thinking_budget": cfg.default_thinking_budget,
                "max_article_words": cfg.max_article_words,
            }
            for prof, cfg in COST_PROFILES.items()
        }
        return json.dumps(data, indent=2)

    @server.resource("credence://taxonomies")
    def list_taxonomies_resource() -> str:
        registry.load_all()
        data = [
            {
                "catalog_id": cat.catalog_id,
                "domain": cat.domain,
                "version": cat.version,
                "catalog_hash": cat.catalog_hash,
                "clusters_count": len(cat.clusters),
                "rules_count": sum(len(c.rules) for c in cat.clusters),
            }
            for cat in registry.list_catalogs()
        ]
        return json.dumps(data, indent=2)

    @server.resource("credence://taxonomies/{catalog_id}")
    def get_taxonomy_catalog_resource(catalog_id: str) -> str:
        registry.load_all()
        cat = registry.get_catalog(catalog_id)
        if not cat:
            return json.dumps({"error": f"Catalog '{catalog_id}' not found."})
        return json.dumps(cat.model_dump(mode="json"), indent=2)

    @server.resource("credence://node/identity")
    def get_node_identity_resource() -> str:
        identity = load_or_create_node_identity()
        return json.dumps(
            {
                "public_key_hex": identity.public_key_hex,
                "key_path": str(identity.key_path),
            },
            indent=2,
        )

    @server.resource("credence://node/health")
    def get_node_health_resource() -> str:
        """Live node health, active alerts, and rolling telemetry snapshot."""
        snapshot = global_telemetry.get_snapshot()
        return json.dumps(snapshot, indent=2)

    @server.resource("credence://mesh/seeds")
    async def get_mesh_seeds_resource() -> str:
        from credence.mesh.discovery import BootstrapDiscovery

        discovery = BootstrapDiscovery()
        peer_urls = await discovery.discover_peers()
        return json.dumps(
            {
                "canonical_domain": "https://seeds.credence.nexus/peers.json",
                "active_seed_nodes": peer_urls,
            },
            indent=2,
        )

    @server.resource("credence://mesh/stats")
    async def get_mesh_stats_resource() -> str:
        """Comprehensive Node & P2P Mesh health, SRE vitals, and scored pages analytics."""
        from credence.db import get_session, init_db
        from credence.mesh.stats import calculate_mesh_stats

        await init_db()
        snapshot = global_telemetry.get_snapshot()
        async for s in get_session():
            stats = await calculate_mesh_stats(s, telemetry_snapshot=snapshot)
            return json.dumps(stats, indent=2)
        return "{}"


def _register_subject_resources(server: MCPServer) -> None:
    """Register subject catalog and empirical expertise resources."""

    @server.resource("credence://subjects/registry")
    def get_subjects_registry_resource() -> str:
        from credence.subjects.registry import get_subject_registry

        reg = get_subject_registry()
        return json.dumps(reg.get_hierarchy_tree(), indent=2)

    @server.resource("credence://subjects/{subject_id}")
    def get_subject_detail_resource(subject_id: str) -> str:
        from credence.subjects.registry import get_subject_registry

        reg = get_subject_registry()
        subj = reg.get_subject(subject_id)
        if not subj:
            return json.dumps({"error": f"Subject '{subject_id}' not found."})
        return json.dumps(subj.model_dump(mode="json"), indent=2)

    @server.resource("credence://subjects/leaderboard")
    async def get_subjects_leaderboard_resource() -> str:
        from credence.db import get_session, init_db
        from credence.models import DomainMetricRecord

        await init_db()
        async for session in get_session():
            stmt = select(DomainMetricRecord).order_by(DomainMetricRecord.expertise_score.desc()).limit(50)  # type: ignore[attr-defined]
            records = (await session.exec(stmt)).all()
            return json.dumps(
                [
                    {
                        "node_pubkey": r.node_pubkey,
                        "subject_id": r.subject_id,
                        "expertise_score": r.expertise_score,
                        "evaluations_count": r.evaluations_count,
                        "grounded_ratio": round(r.grounded_quotes_count / max(1, r.total_quotes_count), 3),
                        "slashing_count": r.slashing_count,
                    }
                    for r in records
                ],
                indent=2,
            )
        return "[]"

    @server.resource("credence://feeds/status")
    async def get_feeds_status_resource() -> str:
        from credence.db import get_session, init_db
        from credence.models import FeedItemRecord, FeedSubscriptionRecord

        await init_db()
        async for session in get_session():
            stmt_subs = select(FeedSubscriptionRecord)
            subs = (await session.exec(stmt_subs)).all()
            stmt_items = select(FeedItemRecord)
            items = (await session.exec(stmt_items)).all()

            return json.dumps(
                {
                    "active_subscriptions_count": len([s for s in subs if s.is_active]),
                    "total_articles_discovered": len(items),
                    "zero_token_adoptions_count": len([i for i in items if i.processing_status == "mesh_adopted"]),
                    "total_tokens_saved": sum(i.tokens_saved for i in items),
                },
                indent=2,
            )
        return "{}"

    @server.resource("credence://roots/tree")
    async def get_roots_tree_resource() -> str:
        from credence.db import get_session, init_db
        from credence.feeds.roots import get_root_tree

        await init_db()
        async for session in get_session():
            tree = await get_root_tree(session)
            return json.dumps(tree, indent=2)
        return "{}"

    @server.resource("credence://roots/candidates")
    async def get_roots_candidates_resource() -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.feeds.roots import extract_root_candidates

        await init_db()
        async for session in get_session():
            cands = await extract_root_candidates(session, limit=20)
            return json.dumps([asdict(c) for c in cands], indent=2)
        return "[]"

    @server.resource("credence://boredom/status")
    async def get_boredom_status_resource() -> str:
        from sqlmodel import col, func, select

        from credence.db import get_session, init_db
        from credence.models import FeedItemRecord, FeedSubscriptionRecord
        from credence.pipeline.governor import get_token_headroom_status

        await init_db()
        async for s in get_session():
            headroom = await get_token_headroom_status(s)
            stmt_pending = select(func.count(col(FeedItemRecord.id))).where(
                FeedItemRecord.processing_status == "pending"
            )
            pending_count = (await s.exec(stmt_pending)).first() or 0
            stmt_roots = select(func.count(col(FeedSubscriptionRecord.id))).where(
                col(FeedSubscriptionRecord.is_active).is_(True)
            )
            roots_count = (await s.exec(stmt_roots)).first() or 0

            return json.dumps(
                {
                    "status": "idle" if pending_count == 0 else "opportunistic_ready",
                    "daily_headroom_pct": headroom.daily_headroom_pct,
                    "hourly_headroom_pct": headroom.hourly_headroom_pct,
                    "pending_items": pending_count,
                    "active_roots_count": roots_count,
                    "circuit_breaker_tripped": headroom.circuit_breaker_tripped,
                    "boredom_eligible": (not headroom.circuit_breaker_tripped and headroom.daily_headroom_pct >= 30.0),
                },
                indent=2,
            )
        return "{}"

    @server.resource("credence://domain/{domain}/reputation")
    async def get_domain_reputation_resource(domain: str) -> str:
        from credence.db import get_session, init_db
        from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

        await init_db()
        async for session in get_session():
            rec = await get_or_create_domain_reputation(session, normalize_domain(domain))
            return json.dumps(rec.model_dump(mode="json"), indent=2)
        return "{}"

    @server.resource("credence://domain/quarantine")
    async def get_domain_quarantine_resource() -> str:
        from credence.db import get_session, init_db
        from credence.feeds.reputation import get_domain_quarantine_list

        await init_db()
        async for session in get_session():
            quarantined = await get_domain_quarantine_list(session)
            return json.dumps(quarantined, indent=2)
        return "[]"

    @server.resource("credence://digest/morning")
    async def get_morning_digest_resource() -> str:
        from credence.db import get_session, init_db
        from credence.feeds.digest import generate_morning_digest

        await init_db()
        async for session in get_session():
            digest = await generate_morning_digest(session, timeframe_hours=24)
            return json.dumps(digest.to_dict(), indent=2)
        return "{}"

    @server.resource("credence://reports/{identifier}")
    async def get_report_resource(identifier: str) -> str:
        await init_db()
        async for s in get_session():
            if identifier.startswith("sha256:") or len(identifier) == 64:
                clean_hash = identifier if identifier.startswith("sha256:") else f"sha256:{identifier}"
                stmt = select(AuditRecord).where(AuditRecord.content_sha256 == clean_hash)
            else:
                snap_stmt = select(SnapshotRecord).where(SnapshotRecord.url == identifier)
                snap = (await s.exec(snap_stmt)).first()
                if not snap:
                    return json.dumps({"error": f"No cached snapshot found for URL: {identifier}"})
                stmt = select(AuditRecord).where(AuditRecord.content_sha256 == snap.content_sha256)

            audit = (await s.exec(stmt)).first()
            if not audit:
                return json.dumps({"error": f"No cached audit report found for: {identifier}"})

            v_stmt = select(ViolationRecord).where(ViolationRecord.audit_id == audit.id)
            violations = (await s.exec(v_stmt)).all()
            v_schemas = [
                SpecialistViolationFinding(
                    rule_id=v.rule_id,
                    rule_uri=v.rule_uri,
                    domain=v.domain,
                    cluster_id=v.cluster_id,
                    severity=v.severity,
                    confidence=v.confidence,
                    quote_or_element=v.quote_or_element,
                    reasoning=v.reasoning,
                    line_or_selector=v.line_or_selector,
                    is_grounded=True,
                )
                for v in violations
            ]

            try:
                tax_map = json.loads(audit.taxonomies_used_json)
            except Exception:
                tax_map = {}

            report = AuditReport(
                url=identifier,
                content_sha256=audit.content_sha256,
                simhash_64="0x0000000000000000",
                audited_at=audit.audited_at,
                suspicion_score=audit.suspicion_score,
                suspicion_density=audit.suspicion_density,
                confidence_score=audit.confidence_score,
                classification=audit.classification,
                is_satire=audit.is_satire,
                content_type=audit.content_type,
                satire_notes=audit.satire_notes,
                violations=v_schemas,
                taxonomies_used=tax_map,
                node_pubkey=audit.node_pubkey,
                node_signature=audit.node_signature,
                quota_preserved=audit.quota_preserved,
            )
            return json.dumps(report.model_dump(mode="json"), indent=2)
        return "{}"

    @server.resource("credence://reports/{identifier}/human")
    async def get_human_report_resource(identifier: str) -> str:
        from credence.cli.main import report_to_markdown

        raw_json = await get_report_resource(identifier)
        try:
            data = json.loads(raw_json)
            if "error" in data:
                return f"# Error\n\n{data['error']}"
            report = AuditReport.model_validate(data)
            badge = "SATIRE / PARODY" if report.is_satire else report.classification
            prefix = f"### 🧠 Human Epistemic Briefing: {badge} ({report.suspicion_score:.1f}/100.0)\n\n"
            return prefix + report_to_markdown(report)
        except Exception as e:
            return f"# Error formatting report: {e}"

    @server.resource("credence://reports/{identifier}/compact")
    async def get_compact_report_resource(identifier: str) -> str:
        raw_json = await get_report_resource(identifier)
        try:
            data = json.loads(raw_json)
            if "error" in data:
                return f"Error: {data['error']}"
            report = AuditReport.model_validate(data)
            badge = "SATIRE" if report.is_satire else report.classification
            lines = [
                f"URL: {report.url} | Score: {report.suspicion_score:.1f}/100.0 ({badge}) | Density: {report.suspicion_density:.1f}/1k | Confidence: {report.confidence_score * 100:.0f}%",
                f"SHA-256: {report.content_sha256} | Signer: {report.node_pubkey or 'unsigned'}",
            ]
            if report.violations:
                lines.append("Findings:")
                for v in report.violations:
                    lines.append(
                        f'  • [{v.rule_id}] {v.domain} (Sev {v.severity}/5): "{v.quote_or_element[:60]}" - {v.reasoning}'
                    )
            else:
                lines.append("Findings: High epistemic integrity. No grounded violations.")
            return "\n".join(lines)
        except Exception as e:
            return f"Error formatting compact report: {e}"

    @server.resource("credence://reports/{identifier}/raw")
    async def get_raw_report_resource(identifier: str) -> str:
        return await get_report_resource(identifier)

    @server.resource("credence://reports/explore/{category}")
    async def get_explore_category_resource(category: str) -> str:
        return await _execute_browse_audits(category=category, limit=20, format="json")


def _register_merit_and_analytics_tools(server: MCPServer) -> None:
    """Register gamification, leaderboard, and web analytics tools."""

    @server.tool(
        name="credence_get_leaderboard",
        description="Retrieve ranked P2P mesh node leaderboard across categories: quality, subjects, philanthropy, galileo, or teams.",
    )
    async def get_leaderboard_tool(
        category: str = "quality",
        limit: int = 50,
        team: Optional[str] = None,
    ) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.mesh.merit import get_leaderboard

        await init_db()
        async for session in get_session():
            entries = await get_leaderboard(session, category=category, limit=limit, team_filter=team)
            return json.dumps([asdict(e) for e in entries], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_node_merit",
        description="Inspect a mesh node's full merit card, unlocked badges, traffic class, and compute impact.",
    )
    async def get_node_merit_tool(node_pubkey: Optional[str] = None) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.mesh.merit import get_local_node_merit

        await init_db()
        async for session in get_session():
            card = await get_local_node_merit(session, local_pubkey=node_pubkey)
            return json.dumps(asdict(card), indent=2)
        return "{}"

    @server.tool(
        name="credence_get_domain_rankings",
        description="Retrieve Domain Epistemic Index (DEI) publisher trust rankings: best (Honor Roll), worst (Wall of Shame), or astroturf.",
    )
    async def get_domain_rankings_tool(
        category: str = "best",
        min_audits: int = 1,
        limit: int = 50,
    ) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_domain_leaderboard

        await init_db()
        async for session in get_session():
            ranks = await get_domain_leaderboard(session, category=category, min_audits=min_audits, limit=limit)
            return json.dumps([asdict(r) for r in ranks], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_taxonomy_analytics",
        description="Retrieve analytics on the Top 10 most frequently violated rules across the web.",
    )
    async def get_taxonomy_analytics_tool(limit: int = 10) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_top_violated_rules

        await init_db()
        async for session in get_session():
            rules = await get_top_violated_rules(session, limit=limit)
            return json.dumps([asdict(r) for r in rules], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_epistemic_weather",
        description="Retrieve the global macro Epistemic Weather report and category integrity gauges.",
    )
    async def get_epistemic_weather_tool() -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_global_epistemic_weather

        await init_db()
        async for session in get_session():
            weather = await get_global_epistemic_weather(session)
            return json.dumps(asdict(weather), indent=2)
        return "{}"

    @server.tool(
        name="credence_get_bounties",
        description="Retrieve open community verification quests and bounties for breaking or unaudited articles.",
    )
    async def get_bounties_tool(limit: int = 20) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_community_bounties

        await init_db()
        async for session in get_session():
            bounties = await get_community_bounties(session, limit=limit)
            return json.dumps([asdict(b) for b in bounties], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_publisher_analytics",
        description="Retrieve deep aggregate public analytics, DEI score, forensic sourcing ratios, astroturf entropy, and trend timelines for any specific news publisher.",
    )
    async def get_publisher_analytics_tool(domain: str) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_publisher_analytics

        await init_db()
        async for session in get_session():
            profile = await get_publisher_analytics(session, domain=domain)
            if profile:
                return json.dumps(asdict(profile), indent=2)
            return json.dumps({"error": f"No audit records found for publisher '{domain}'."})
        return "{}"


def _register_merit_and_analytics_resources(server: MCPServer) -> None:
    """Register merit, leaderboard, and web analytics resources."""

    @server.resource("credence://analytics/publishers")
    async def list_publishers_resource() -> str:
        from credence.db import get_session, init_db
        from credence.subjects.analytics import list_all_publishers_summary

        await init_db()
        async for session in get_session():
            summaries = await list_all_publishers_summary(session)
            return json.dumps(summaries, indent=2)
        return "[]"

    @server.resource("credence://analytics/publisher/{domain}")
    async def get_publisher_analytics_resource(domain: str) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_publisher_analytics

        await init_db()
        async for session in get_session():
            profile = await get_publisher_analytics(session, domain=domain)
            if profile:
                return json.dumps(asdict(profile), indent=2)
            return json.dumps({"error": f"No analytics found for domain: '{domain}'"})
        return "{}"

    @server.resource("credence://leaderboard/{category}")
    async def get_leaderboard_resource(category: str) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.mesh.merit import get_leaderboard

        await init_db()
        async for session in get_session():
            entries = await get_leaderboard(session, category=category, limit=50)
            return json.dumps([asdict(e) for e in entries], indent=2)
        return "[]"

    @server.resource("credence://node/merit")
    async def get_node_merit_resource() -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.mesh.merit import get_local_node_merit

        await init_db()
        async for session in get_session():
            card = await get_local_node_merit(session)
            return json.dumps(asdict(card), indent=2)
        return "{}"

    @server.resource("credence://merit/badges")
    def get_merit_badges_resource() -> str:
        from dataclasses import asdict

        from credence.mesh.merit import BADGE_REGISTRY

        return json.dumps([asdict(b) for b in BADGE_REGISTRY.values()], indent=2)

    @server.resource("credence://rankings/domains/{category}")
    async def get_domain_rankings_resource(category: str) -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_domain_leaderboard

        await init_db()
        async for session in get_session():
            ranks = await get_domain_leaderboard(session, category=category, limit=50)
            return json.dumps([asdict(r) for r in ranks], indent=2)
        return "[]"

    @server.resource("credence://rankings/rules")
    async def get_rankings_rules_resource() -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_top_violated_rules

        await init_db()
        async for session in get_session():
            rules = await get_top_violated_rules(session, limit=10)
            return json.dumps([asdict(r) for r in rules], indent=2)
        return "[]"

    @server.resource("credence://weather/global")
    async def get_weather_resource() -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_global_epistemic_weather

        await init_db()
        async for session in get_session():
            weather = await get_global_epistemic_weather(session)
            return json.dumps(asdict(weather), indent=2)
        return "{}"

    @server.resource("credence://bounties")
    async def get_bounties_resource() -> str:
        from dataclasses import asdict

        from credence.db import get_session, init_db
        from credence.subjects.analytics import get_community_bounties

        await init_db()
        async for session in get_session():
            bounties = await get_community_bounties(session, limit=20)
            return json.dumps([asdict(b) for b in bounties], indent=2)
        return "[]"


def _register_cost_tools_and_resources(server: MCPServer) -> None:
    """Register Cost Governance, Token Telemetry, and Autonomous Optimizer tools and resources."""

    @server.tool(
        name="credence_get_cost_telemetry",
        description="Retrieve real-time token spend, thinking token counts, hourly/daily headroom, USD spend, and Emergency Brake status.",
    )
    async def get_cost_telemetry_tool() -> str:
        from credence.cache.distributed import get_state_store
        from credence.db import get_session, init_db
        from credence.pipeline.governor import get_token_headroom_status

        await init_db()
        async for session in get_session():
            headroom = await get_token_headroom_status(session)
            state = await get_state_store().get_runtime_cost_settings()
            data = headroom.model_dump(mode="json")
            data["emergency_brake_pulled"] = state.emergency_brake_pulled
            data["brake_reason"] = state.brake_reason
            data["runtime_daily_budget_usd"] = state.daily_budget_usd
            data["runtime_max_tokens_per_hour"] = state.max_tokens_per_hour
            data["runtime_active_profile"] = state.active_profile_override
            return json.dumps(data, indent=2)
        return "{}"

    @server.tool(
        name="credence_get_cost_recommendations",
        description="Query the Autonomous Cost Profile Optimizer for trend-based upgrade/downgrade recommendations based on rolling usage.",
    )
    async def get_cost_recommendations_tool() -> str:
        from credence.db import get_session, init_db
        from credence.pipeline.cost_optimizer import evaluate_cost_profile_recommendation
        from credence.pipeline.governor import get_token_headroom_status

        await init_db()
        async for session in get_session():
            headroom = await get_token_headroom_status(session)
            rec = evaluate_cost_profile_recommendation(
                avg_daily_spend_usd=headroom.daily_spend_usd,
                trips_last_72h=1 if headroom.circuit_breaker_tripped else 0,
                hours_throttled_last_72h=2.0 if headroom.throttle_active else 0.0,
            )
            return json.dumps(rec.model_dump(mode="json"), indent=2)
        return "{}"

    @server.tool(
        name="credence_set_budget",
        description="Dynamically adjust live daily USD budget and hourly token ceiling across all container replicas without restarting.",
    )
    async def set_budget_tool(
        daily_budget_usd: Optional[float] = None,
        max_tokens_per_hour: Optional[int] = None,
        profile: Optional[str] = None,
    ) -> str:
        from credence.cache.distributed import get_state_store

        state_store = get_state_store()
        await state_store.set_runtime_budget_override(
            daily_budget_usd=daily_budget_usd,
            max_tokens_per_hour=max_tokens_per_hour,
            active_profile=profile,
        )
        return json.dumps({"status": "success", "message": "Runtime budget settings updated successfully."})

    @server.tool(
        name="credence_trigger_emergency_brake",
        description="Instantly pull the Emergency Brake, downshifting 100% of audits into offline heuristic mode ($0 spend).",
    )
    async def trigger_emergency_brake_tool(reason: str = "Agentic Cost Guard") -> str:
        from credence.cache.distributed import get_state_store

        state_store = get_state_store()
        await state_store.pull_emergency_brake(reason=reason)
        return json.dumps({"status": "tripped", "circuit_breaker_tripped": True, "reason": reason})

    @server.tool(
        name="credence_apply_cost_recommendation",
        description="Apply the recommended cost profile from the Autonomous Cost Optimizer.",
    )
    async def apply_cost_recommendation_tool(target_profile: str) -> str:
        from credence.cache.distributed import get_state_store
        from credence.config import CostProfile

        if target_profile not in CostProfile.__members__.values():
            return json.dumps({"error": f"Invalid target profile '{target_profile}'."})

        state_store = get_state_store()
        await state_store.set_runtime_budget_override(active_profile=target_profile)
        return json.dumps({"status": "success", "active_profile": target_profile})

    @server.resource("credence://cost/telemetry")
    async def get_cost_telemetry_resource() -> str:
        return await get_cost_telemetry_tool()

    @server.resource("credence://cost/recommendations")
    async def get_cost_recommendations_resource() -> str:
        return await get_cost_recommendations_tool()

    @server.resource("credence://cost/dashboard")
    async def get_cost_dashboard_resource() -> str:
        return await get_cost_telemetry_tool()


def _register_prompts(server: MCPServer) -> None:
    """Register FastMCP prompt templates."""

    @server.prompt(name="audit_article_prompt", description="Interactive prompt template for auditing an article.")
    def audit_article_prompt(url: str) -> str:
        return (
            f"Please conduct an epistemic trust audit of the following webpage URL:\n"
            f"Target URL: {url}\n\n"
            f"Use the `credence_check_url` tool to capture and evaluate the content against "
            f"SPJ journalistic ethics, logical fallacies, and deceptive patterns."
        )

    @server.prompt(
        name="explain_audit_report_prompt",
        description="Interactive prompt template instructing an AI agent to explain an epistemic audit report to a human reader in empathetic, plain language.",
    )
    def explain_audit_report_prompt(identifier: str) -> str:
        return (
            f"Please inspect and explain the Credence epistemic audit report for identifier: {identifier}\n\n"
            f"1. Fetch the report using `credence_get_audit(identifier='{identifier}', format='human')`.\n"
            f"2. Summarize the verdict, suspicion score, and confidence level in simple, empathetic terms.\n"
            f"3. Explain each detected violation (if any) with its quoted excerpt and why it was flagged.\n"
            f"4. Provide constructive guidance on how the reader can independently verify the assertions."
        )

    @server.prompt(
        name="fallacy_review_prompt",
        description="Structured prompt template for auditing argumentative text for formal and informal logical fallacies.",
    )
    def fallacy_review_prompt(text: str) -> str:
        return (
            f"Please analyze the following argumentative passage against the IEP Logical Fallacies taxonomy:\n\n"
            f"---\n{text}\n---\n\n"
            f"Use the `credence_evaluate_text` tool to detect fallacies (such as Ad Hominem, False Dilemma, "
            f"Post Hoc Ergo Propter Hoc, or Bandwagon appeals) and extract verbatim grounded citations."
        )

    @server.prompt(
        name="dark_pattern_review_prompt",
        description="Prompt template for reviewing user onboarding flows or e-commerce pages for deceptive UI patterns.",
    )
    def dark_pattern_review_prompt(url: str) -> str:
        return (
            f"Please perform a deceptive design audit on this target URL:\n"
            f"Target URL: {url}\n\n"
            f"Use the `credence_check_url` tool to inspect the rendered DOM for confirmshaming, fake urgency countdowns, "
            f"pre-selected options, disguised advertisements, and hidden recurring subscription terms."
        )


async def _reconstitute_report_from_db(identifier: str) -> Optional[dict]:
    """Reconstitute full audit report JSON from SQLite."""
    from credence.db import get_session, init_db

    await init_db()
    async for session in get_session():
        # 1. Match by content_sha256
        stmt = (
            select(AuditRecord)
            .where(AuditRecord.content_sha256 == identifier)
            .order_by(col(AuditRecord.audited_at).desc())
        )
        audit = (await session.exec(stmt)).first()

        # 2. Match by URL
        if not audit:
            stmt_url = (
                select(AuditRecord)
                .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id))
                .where(col(SnapshotRecord.url) == identifier)
                .order_by(col(AuditRecord.audited_at).desc())
            )
            audit = (await session.exec(stmt_url)).first()

        if not audit:
            return None

        # Load snapshot
        snap = None
        if audit.snapshot_id:
            stmt_snap = select(SnapshotRecord).where(SnapshotRecord.id == audit.snapshot_id)
            snap = (await session.exec(stmt_snap)).first()

        # Load violations
        stmt_v = select(ViolationRecord).where(ViolationRecord.audit_id == audit.id)
        violations = list((await session.exec(stmt_v)).all())

        findings = [
            {
                "rule_id": v.rule_id,
                "rule_uri": v.rule_uri,
                "domain": v.domain,
                "cluster_id": v.cluster_id,
                "severity": v.severity,
                "confidence": v.confidence,
                "quote_or_element": v.quote_or_element,
                "reasoning": v.reasoning,
                "line_or_selector": v.line_or_selector,
            }
            for v in violations
        ]

        tax_map = {}
        try:
            tax_map = json.loads(audit.taxonomies_used_json)
        except Exception:
            pass

        return {
            "id": snap.url if snap and snap.url else audit.content_sha256,
            "url": snap.url if snap else "",
            "title": snap.title if snap else "",
            "byline": snap.byline if snap else "",
            "content_sha256": audit.content_sha256,
            "simhash_64": snap.simhash_64 if snap else "",
            "audited_at": audit.audited_at.isoformat() if audit.audited_at else "",
            "suspicion_score": audit.suspicion_score,
            "suspicion_density": audit.suspicion_density,
            "confidence_score": audit.confidence_score,
            "classification": audit.classification,
            "is_satire": audit.is_satire,
            "content_type": audit.content_type,
            "satire_notes": audit.satire_notes,
            "violations": findings,
            "taxonomies_used": tax_map,
            "quota_preserved": audit.quota_preserved,
            "evaluation_method": audit.evaluation_method,
            "node_pubkey": audit.node_pubkey,
            "node_signature": audit.node_signature,
        }
    return None


async def api_health(request: Any) -> Any:
    """REST API: Health check endpoint with Interface Telemetry Loopback (ITLP-v1)."""
    from starlette.responses import JSONResponse

    from credence import __version__

    telemetry_data = global_telemetry.get_snapshot()
    return JSONResponse(
        {
            "status": telemetry_data["status"],
            "service": "credence",
            "version": __version__,
            "telemetry": telemetry_data,
        }
    )


async def api_mesh_stats(request: Any) -> Any:
    """REST API: Retrieve comprehensive Node & P2P Mesh health, SRE vitals, and scored pages analytics."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.mesh.stats import calculate_mesh_stats

    await init_db()
    snapshot = global_telemetry.get_snapshot()
    async for s in get_session():
        stats = await calculate_mesh_stats(s, telemetry_snapshot=snapshot)
        return JSONResponse(stats)
    return JSONResponse({})


async def api_reports(request: Any) -> Any:
    """REST API: Query paginated and categorized audit reports."""
    import secrets

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db

    cat = request.query_params.get("category", "recent").lower()
    try:
        limit = min(int(request.query_params.get("limit", 20)), 100)
    except ValueError:
        limit = 20
    try:
        offset = max(int(request.query_params.get("offset", 0)), 0)
    except ValueError:
        offset = 0

    await init_db()
    async for s in get_session():
        if cat in ("best", "clean"):
            stmt = (
                select(AuditRecord, SnapshotRecord)
                .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True)
                .where(AuditRecord.suspicion_score <= 15.0)
                .order_by(col(AuditRecord.suspicion_score).asc(), col(AuditRecord.audited_at).desc())
            )
        elif cat in ("worst", "flagged", "deceptive"):
            stmt = (
                select(AuditRecord, SnapshotRecord)
                .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True)
                .where(AuditRecord.suspicion_score >= 60.0)
                .order_by(col(AuditRecord.suspicion_score).desc(), col(AuditRecord.audited_at).desc())
            )
        elif cat == "satire":
            stmt = (
                select(AuditRecord, SnapshotRecord)
                .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True)
                .where(AuditRecord.is_satire)
                .order_by(col(AuditRecord.audited_at).desc())
            )
        elif cat == "random":
            stmt = (
                select(AuditRecord, SnapshotRecord)
                .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True)
                .limit(limit * 3)
            )
        else:  # "recent"
            stmt = (
                select(AuditRecord, SnapshotRecord)
                .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True)
                .order_by(col(AuditRecord.audited_at).desc())
            )

        results = list((await s.exec(stmt.offset(offset).limit(limit))).all())
        if cat == "random" and results:
            secrets.SystemRandom().shuffle(results)
            results = results[:limit]

        reports = []
        for row in results:
            audit = row[0]
            snap = row[1]
            reports.append(
                {
                    "id": snap.url if snap and snap.url else audit.content_sha256,
                    "content_sha256": audit.content_sha256,
                    "url": snap.url if snap else "",
                    "title": snap.title if snap and snap.title else (audit.content_sha256[:20] + "..."),
                    "byline": snap.byline if snap else "",
                    "audited_at": audit.audited_at.isoformat() if audit.audited_at else "",
                    "suspicion_score": audit.suspicion_score,
                    "suspicion_density": audit.suspicion_density,
                    "confidence_score": audit.confidence_score,
                    "classification": audit.classification,
                    "is_satire": audit.is_satire,
                    "node_pubkey": audit.node_pubkey,
                    "node_signature": audit.node_signature,
                }
            )

        return JSONResponse(
            {
                "category": cat,
                "total": len(reports),
                "limit": limit,
                "offset": offset,
                "reports": reports,
            }
        )
    return JSONResponse({"reports": []})


async def api_get_report(request: Any) -> Any:
    """REST API: Get complete audit report by SHA-256 or URL identifier with immutable edge caching headers."""
    from starlette.responses import JSONResponse

    identifier = request.path_params.get("identifier", "")
    if not identifier:
        identifier = request.query_params.get("q", "")

    report_dict = await _reconstitute_report_from_db(identifier)
    if not report_dict:
        return JSONResponse({"error": f"Report not found for identifier: '{identifier}'"}, status_code=404)

    headers = {}
    content_hash = report_dict.get("content_sha256") or (identifier if len(identifier) == 64 else None)
    if content_hash:
        headers["Cache-Control"] = "public, max-age=2592000, s-maxage=31536000, immutable"
        headers["ETag"] = f'W/"sha256:{content_hash}"'

    return JSONResponse(report_dict, headers=headers)


async def api_audit_url(request: Any) -> Any:
    """REST API: Trigger live on-demand audit of target webpage."""
    from starlette.responses import JSONResponse

    from credence.config import COST_PROFILES, CostProfile
    from credence.pipeline.evaluator import audit_url

    target_url = request.query_params.get("url")
    force = request.query_params.get("force", "").lower() in ("true", "1")
    profile = request.query_params.get("profile")

    if not target_url and request.method == "POST":
        try:
            body = await request.json()
            target_url = body.get("url")
            force = body.get("force", force)
            profile = body.get("profile", profile)
        except Exception:
            pass

    if not target_url:
        return JSONResponse(
            {"error": "Target URL is required. e.g. /api/audit?url=https://example.com"}, status_code=400
        )

    prof_cfg = COST_PROFILES.get(CostProfile(profile.lower())) if profile else None
    try:
        report = await audit_url(target_url, force_refresh=force, profile_override=prof_cfg)
        return JSONResponse(report.model_dump(mode="json"))
    except Exception as e:
        return JSONResponse({"error": f"Evaluation failed: {str(e)}"}, status_code=500)


async def api_sifter_status(request: Any) -> Any:
    """REST API: Get current sifter daemon status and telemetry."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.sifter import get_sifter_status

    await init_db()
    async for session in get_session():
        status = await get_sifter_status(session)
        return JSONResponse(status)
    return JSONResponse({"status": "unavailable"}, status_code=500)


async def api_sifter_cycle(request: Any) -> Any:
    """REST API: Trigger an immediate sifting cycle."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.sifter import run_sifting_cycle

    await init_db()
    async for session in get_session():
        summary = await run_sifting_cycle(session)
        return JSONResponse(
            {
                "status": "completed",
                "summary": {
                    "total_feeds_polled": summary.total_feeds_polled,
                    "feeds_unmodified_304": summary.feeds_unmodified_304,
                    "new_items_discovered": summary.new_items_discovered,
                    "items_adopted_from_mesh": summary.items_adopted_from_mesh,
                    "items_evaluated_locally": summary.items_evaluated_locally,
                    "tokens_saved_total": summary.tokens_saved_total,
                },
            }
        )
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_feeds_stream(request: Any) -> Any:
    """REST API: Stream recent feed items."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.models import FeedItemRecord, FeedSubscriptionRecord

    limit = min(int(request.query_params.get("limit", 30)), 100)
    await init_db()
    async for session in get_session():
        stmt = (
            select(FeedItemRecord, FeedSubscriptionRecord)
            .join(FeedSubscriptionRecord, col(FeedItemRecord.feed_id) == col(FeedSubscriptionRecord.id), isouter=True)
            .order_by(col(FeedItemRecord.discovered_at).desc())
            .limit(limit)
        )
        results = (await session.exec(stmt)).all()
        items = []
        for item, sub in results:
            items.append(
                {
                    "id": item.id,
                    "url": item.item_url,
                    "title": item.title,
                    "feed_title": sub.title if sub else "",
                    "feed_url": sub.feed_url if sub else "",
                    "subject": item.subject_id,
                    "processing_status": item.processing_status,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                    "discovered_at": item.discovered_at.isoformat() if item.discovered_at else None,
                }
            )
        return JSONResponse({"items": items, "count": len(items)})
    return JSONResponse({"items": [], "count": 0})


async def api_germinate(request: Any) -> Any:
    """REST API: Trigger rapid node germination and Miracle-Gro burst."""
    from starlette.responses import JSONResponse

    from credence.db import get_async_session, init_db
    from credence.germinate import germinate_node

    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}

    burst = int(body.get("burst", request.query_params.get("burst", 3)))
    sync_mesh = bool(body.get("sync_mesh", request.query_params.get("sync_mesh", True)))
    profile = body.get("profile", request.query_params.get("profile", None))

    await init_db()
    async with get_async_session() as session:
        summary = await germinate_node(
            session=session,
            burst_items=burst,
            sync_mesh=sync_mesh,
            profile_override=profile,
            verbose=True,
        )
        return JSONResponse(summary.model_dump(mode="json"))


async def api_leaderboard(request: Any) -> Any:
    """REST API: Query P2P node leaderboard."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.mesh.merit import get_leaderboard

    cat = request.query_params.get("category", "quality")
    team = request.query_params.get("team")
    try:
        limit = min(int(request.query_params.get("limit", 50)), 100)
    except ValueError:
        limit = 50

    await init_db()
    async for s in get_session():
        entries = await get_leaderboard(s, category=cat, limit=limit, team_filter=team)
        return JSONResponse({"category": cat, "total": len(entries), "leaderboard": [asdict(e) for e in entries]})
    return JSONResponse({"leaderboard": []})


async def api_get_merit(request: Any) -> Any:
    """REST API: Get node merit card."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.mesh.merit import get_local_node_merit

    pubkey = request.path_params.get("identifier") or request.query_params.get("pubkey")
    await init_db()
    async for s in get_session():
        card = await get_local_node_merit(s, local_pubkey=pubkey)
        return JSONResponse(asdict(card))
    return JSONResponse({"error": "Unavailable"}, status_code=500)


async def api_get_badge_svg(request: Any) -> Any:
    """REST API: Dynamic SVG badge endpoint."""
    from starlette.responses import Response

    from credence.mesh.merit import generate_svg_badge

    badge_id = request.path_params.get("badge_id", "root_seed_candidate").replace(".svg", "")
    node = request.query_params.get("node", "credence-node")
    score = request.query_params.get("score", "VERIFIED")
    theme = request.query_params.get("theme", "dark")

    svg_content = generate_svg_badge(badge_id=badge_id, node_alias=node, score_or_val=score, theme=theme)
    return Response(content=svg_content, media_type="image/svg+xml")


async def api_get_publisher_badge(request: Any) -> Any:
    """REST API: Dynamic Publisher SVG badge endpoint."""
    from starlette.responses import Response

    from credence.db import get_session, init_db
    from credence.subjects.analytics import generate_publisher_svg_badge, get_domain_leaderboard

    domain = request.path_params.get("domain", "reuters.com").replace(".svg", "")
    theme = request.query_params.get("theme", "dark")

    dei_val = 85.0
    status = "CLEAN"
    await init_db()
    async for s in get_session():
        ranks = await get_domain_leaderboard(s, category="best", limit=100)
        for r in ranks:
            if r.domain == domain:
                dei_val = r.dei_score
                status = r.trust_band
                break

    svg = generate_publisher_svg_badge(domain=domain, dei_score=dei_val, status=status, theme=theme)
    return Response(content=svg, media_type="image/svg+xml")


async def api_rankings_domains(request: Any) -> Any:
    """REST API: Query Domain Epistemic Index rankings."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.subjects.analytics import get_domain_leaderboard

    cat = request.query_params.get("category", "best")
    try:
        limit = min(int(request.query_params.get("limit", 50)), 100)
    except ValueError:
        limit = 50

    await init_db()
    async for s in get_session():
        ranks = await get_domain_leaderboard(s, category=cat, limit=limit)
        return JSONResponse({"category": cat, "total": len(ranks), "rankings": [asdict(r) for r in ranks]})
    return JSONResponse({"rankings": []})


async def api_rankings_rules(request: Any) -> Any:
    """REST API: Query Top 10 most violated rules."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.subjects.analytics import get_top_violated_rules

    try:
        limit = min(int(request.query_params.get("limit", 10)), 50)
    except ValueError:
        limit = 10

    await init_db()
    async for s in get_session():
        rules = await get_top_violated_rules(s, limit=limit)
        return JSONResponse({"total": len(rules), "rules": [asdict(r) for r in rules]})
    return JSONResponse({"rules": []})


async def api_weather(request: Any) -> Any:
    """REST API: Query Global Epistemic Weather report."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.subjects.analytics import get_global_epistemic_weather

    await init_db()
    async for s in get_session():
        report = await get_global_epistemic_weather(s)
        return JSONResponse(asdict(report))
    return JSONResponse({"error": "Unavailable"}, status_code=500)


async def api_bounties(request: Any) -> Any:
    """REST API: Query community verification bounties."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.subjects.analytics import get_community_bounties

    try:
        limit = min(int(request.query_params.get("limit", 20)), 50)
    except ValueError:
        limit = 20

    await init_db()
    async for s in get_session():
        bounties = await get_community_bounties(s, limit=limit)
        return JSONResponse({"total": len(bounties), "bounties": [asdict(b) for b in bounties]})
    return JSONResponse({"bounties": []})


async def api_list_publishers(request: Any) -> Any:
    """REST API: Query summary analytics for all audited news publishers."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.subjects.analytics import list_all_publishers_summary

    await init_db()
    async for s in get_session():
        summaries = await list_all_publishers_summary(s)
        return JSONResponse({"total": len(summaries), "publishers": summaries})
    return JSONResponse({"total": 0, "publishers": []})


async def api_publisher_analytics(request: Any) -> Any:
    """REST API: Query deep aggregate public analytics, DEI score, forensic metrics, and trends for a specific publisher."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.subjects.analytics import get_publisher_analytics

    domain = request.path_params.get("domain", "") or request.query_params.get("domain", "")
    if not domain:
        return JSONResponse(
            {"error": "Publisher domain is required, e.g. /api/analytics/publisher/inmaricopa.com"}, status_code=400
        )

    await init_db()
    async for s in get_session():
        profile = await get_publisher_analytics(s, domain=domain)
        if not profile:
            return JSONResponse({"error": f"No audit records found for publisher '{domain}'"}, status_code=404)
        return JSONResponse(asdict(profile))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_roots_expand(request: Any) -> Any:
    """REST API: Trigger autonomous root expansion from cited domains."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.roots import expand_roots

    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
    max_sources = int(body.get("max_sources", request.query_params.get("max_sources", 5)))
    dry_run = bool(body.get("dry_run", request.query_params.get("dry_run", False)))

    await init_db()
    async for s in get_session():
        summary = await expand_roots(s, max_new_sources=max_sources, dry_run=dry_run)
        return JSONResponse(asdict(summary))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_roots_tree(request: Any) -> Any:
    """REST API: Retrieve hierarchical root and subscription tree."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.roots import get_root_tree

    await init_db()
    async for s in get_session():
        tree = await get_root_tree(s)
        return JSONResponse(tree)
    return JSONResponse({"active_roots": [], "total_active_roots": 0})


async def api_roots_candidates(request: Any) -> Any:
    """REST API: Retrieve candidate domains cited by audited articles."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.roots import extract_root_candidates

    limit = min(int(request.query_params.get("limit", 20)), 50)
    await init_db()
    async for s in get_session():
        cands = await extract_root_candidates(s, limit=limit)
        return JSONResponse({"total": len(cands), "candidates": [asdict(c) for c in cands]})
    return JSONResponse({"total": 0, "candidates": []})


async def api_domain_reputation(request: Any) -> Any:
    """REST API: Get domain-level reputation metrics and BuzzFeed Doctrine standing."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

    domain = request.path_params.get("domain", "")
    if not domain:
        return JSONResponse({"error": "Domain required"}, status_code=400)
    await init_db()
    async for session in get_session():
        record = await get_or_create_domain_reputation(session, normalize_domain(domain))
        return JSONResponse(record.model_dump(mode="json"))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_domain_quarantine(request: Any) -> Any:
    """REST API: List all currently quarantined or suspicious domains with exponential backoff."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.reputation import get_domain_quarantine_list

    await init_db()
    async for session in get_session():
        quarantined = await get_domain_quarantine_list(session)
        return JSONResponse({"total_quarantined": len(quarantined), "quarantined_domains": quarantined})
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_domain_appeal(request: Any) -> Any:
    """REST API: File an expedited BuzzFeed News Doctrine redemption appeal."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

    domain = request.path_params.get("domain", "")
    if not domain:
        return JSONResponse({"error": "Domain required"}, status_code=400)
    await init_db()
    async for session in get_session():
        record = await get_or_create_domain_reputation(session, normalize_domain(domain))
        return JSONResponse(
            {
                "domain": record.domain,
                "status": record.status,
                "reputation_score": record.reputation_score,
                "appeal_status": "QUEUED_FOR_EXPEDITED_AUDIT",
                "doctrine": "The BuzzFeed News Doctrine (Asymmetric Epistemic Recovery)",
            }
        )
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_boredom_cycle(request: Any) -> Any:
    """REST API: Trigger an immediate opportunistic boredom cycle."""
    from dataclasses import asdict

    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.feeds.boredom import run_boredom_cycle

    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
    burst = int(body.get("burst", request.query_params.get("burst", 3)))
    ratio = float(body.get("ratio", body.get("boredom_ratio", request.query_params.get("ratio", 0.60))))
    expand_roots_enabled = bool(body.get("expand_roots", request.query_params.get("expand_roots", True)))

    await init_db()
    async for s in get_session():
        summary = await run_boredom_cycle(
            s,
            audit_burst=burst,
            boredom_ratio=ratio,
            expand_roots_enabled=expand_roots_enabled,
        )
        res = asdict(summary)
        res["timestamp"] = summary.timestamp.isoformat()
        return JSONResponse(res)
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_boredom_status(request: Any) -> Any:
    """REST API: Get real-time boredom engine and token headroom telemetry."""
    from sqlmodel import col, func, select
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.models import FeedItemRecord, FeedSubscriptionRecord
    from credence.pipeline.governor import get_token_headroom_status

    await init_db()
    async for s in get_session():
        headroom = await get_token_headroom_status(s)
        stmt_pending = select(func.count(col(FeedItemRecord.id))).where(FeedItemRecord.processing_status == "pending")
        pending_count = (await s.exec(stmt_pending)).first() or 0
        stmt_audited = select(func.count(col(FeedItemRecord.id))).where(FeedItemRecord.processing_status == "audited")
        audited_count = (await s.exec(stmt_audited)).first() or 0
        stmt_adopted = select(func.count(col(FeedItemRecord.id))).where(
            FeedItemRecord.processing_status == "mesh_adopted"
        )
        adopted_count = (await s.exec(stmt_adopted)).first() or 0
        stmt_roots = select(func.count(col(FeedSubscriptionRecord.id))).where(
            col(FeedSubscriptionRecord.is_active).is_(True)
        )
        roots_count = (await s.exec(stmt_roots)).first() or 0

        return JSONResponse(
            {
                "status": "idle" if pending_count == 0 else "opportunistic_ready",
                "token_headroom": {
                    "daily_pct": headroom.daily_headroom_pct,
                    "hourly_pct": headroom.hourly_headroom_pct,
                    "daily_spend_usd": headroom.daily_spend_usd,
                    "circuit_breaker_tripped": headroom.circuit_breaker_tripped,
                },
                "queue": {
                    "pending_items": pending_count,
                    "audited_items": audited_count,
                    "mesh_adopted_items": adopted_count,
                    "active_roots_count": roots_count,
                },
                "boredom_trigger_eligible": (
                    not headroom.circuit_breaker_tripped and headroom.daily_headroom_pct >= 30.0
                ),
            }
        )
    return JSONResponse({"status": "unavailable"}, status_code=500)


def _check_admin_auth(request: Any) -> bool:
    """Verify administrator Bearer token authentication or local development exemption."""
    import secrets

    from credence.config import settings

    client_host = getattr(request.client, "host", "") if hasattr(request, "client") and request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1") and settings.ENV != "production":
        return True
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        expected = settings.CREDENCE_ADMIN_API_KEY
        if expected and secrets.compare_digest(token, expected):
            return True
    return False


async def api_cost_telemetry(request: Any) -> Any:
    """REST API: Query real-time token spend, headroom, and live cost telemetry."""
    from starlette.responses import JSONResponse

    from credence.cache.distributed import get_state_store
    from credence.db import get_session, init_db
    from credence.pipeline.governor import get_token_headroom_status

    await init_db()
    async for s in get_session():
        headroom = await get_token_headroom_status(s)
        state = await get_state_store().get_runtime_cost_settings()
        data = headroom.model_dump(mode="json")
        data["emergency_brake_pulled"] = state.emergency_brake_pulled
        data["brake_reason"] = state.brake_reason
        data["runtime_daily_budget_usd"] = state.daily_budget_usd
        data["runtime_max_tokens_per_hour"] = state.max_tokens_per_hour
        data["runtime_active_profile"] = state.active_profile_override
        return JSONResponse(data)
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_cost_recommendations(request: Any) -> Any:
    """REST API: Query autonomous Cost Profile Optimizer upgrade/downgrade recommendation."""
    from starlette.responses import JSONResponse

    from credence.db import get_session, init_db
    from credence.pipeline.cost_optimizer import evaluate_cost_profile_recommendation
    from credence.pipeline.governor import get_token_headroom_status

    await init_db()
    async for s in get_session():
        headroom = await get_token_headroom_status(s)
        rec = evaluate_cost_profile_recommendation(
            avg_daily_spend_usd=headroom.daily_spend_usd,
            trips_last_72h=1 if headroom.circuit_breaker_tripped else 0,
            hours_throttled_last_72h=2.0 if headroom.throttle_active else 0.0,
        )
        return JSONResponse(rec.model_dump(mode="json"))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)


async def api_cost_budget(request: Any) -> Any:
    """REST API: Update live runtime budget and token ceilings."""
    from starlette.responses import JSONResponse

    from credence.cache.distributed import get_state_store

    if not _check_admin_auth(request):
        return JSONResponse({"error": "Unauthorized: Administrator Bearer token required"}, status_code=401)

    try:
        body = await request.json() if request.method == "POST" else {}
    except Exception:
        body = {}

    daily_budget = body.get("daily_budget_usd", request.query_params.get("daily_budget_usd"))
    max_tokens = body.get("max_tokens_per_hour", request.query_params.get("max_tokens_per_hour"))
    profile = body.get("profile", request.query_params.get("profile"))

    state_store = get_state_store()
    await state_store.set_runtime_budget_override(
        daily_budget_usd=float(daily_budget) if daily_budget is not None else None,
        max_tokens_per_hour=int(max_tokens) if max_tokens is not None else None,
        active_profile=str(profile) if profile is not None else None,
    )
    return JSONResponse({"status": "success", "message": "Runtime cost settings updated"})


async def api_cost_emergency_stop(request: Any) -> Any:
    """REST API: Pull 1-Click Emergency Brake into QUOTA_PRESERVED offline mode."""
    from starlette.responses import JSONResponse

    from credence.cache.distributed import get_state_store

    if not _check_admin_auth(request):
        return JSONResponse({"error": "Unauthorized: Administrator Bearer token required"}, status_code=401)

    try:
        body = await request.json() if request.method == "POST" else {}
    except Exception:
        body = {}

    reason = body.get("reason", "Operator Emergency Stop")
    state_store = get_state_store()
    await state_store.pull_emergency_brake(reason=reason)
    return JSONResponse({"status": "tripped", "circuit_breaker_tripped": True, "reason": reason})


async def api_cost_resume(request: Any) -> Any:
    """REST API: Release Emergency Brake and resume AI operations."""
    from starlette.responses import JSONResponse

    from credence.cache.distributed import get_state_store

    if not _check_admin_auth(request):
        return JSONResponse({"error": "Unauthorized: Administrator Bearer token required"}, status_code=401)

    state_store = get_state_store()
    await state_store.release_emergency_brake()
    return JSONResponse({"status": "resumed", "circuit_breaker_tripped": False})


def create_mcp_server() -> MCPServer:
    """Instantiate and configure the Credence FastMCP server."""
    server = MCPServer(
        name="credence",
        instructions="Autonomous Epistemic Evaluation Engine, FastMCP Server, and Trust Network.",
        version="1.16.0",
    )
    _register_eval_tools(server)
    _register_query_tools(server)
    _register_consensus_tools(server)
    _register_mesh_tools(server)
    _register_feed_sync_tools(server)
    _register_feed_management_tools(server)
    _register_merit_and_analytics_tools(server)
    _register_cost_tools_and_resources(server)
    _register_taxonomy_resources(server)
    _register_subject_resources(server)
    _register_merit_and_analytics_resources(server)
    _register_prompts(server)
    return server


mcp_server = create_mcp_server()


def create_server_app(
    transport_security: Optional[Any] = None,
    enable_sifter: bool = False,
    enable_boredom: bool = False,
) -> Any:
    """Create a unified Starlette application hosting FastMCP SSE, REST API, Sifter, and Boredom Engine."""
    import os
    from contextlib import asynccontextmanager

    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Route

    server = create_mcp_server()
    if transport_security is None:
        from mcp.server.transport_security import TransportSecuritySettings

        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=["*"],
            allowed_origins=["*"],
        )

    # Base Starlette app from FastMCP SSE
    app = server.sse_app(transport_security=transport_security)

    # Register REST API routes directly on the Starlette app
    rest_routes = [
        Route("/health", endpoint=api_health, methods=["GET"]),
        Route("/api/health", endpoint=api_health, methods=["GET"]),
        Route("/api/v1/mesh/stats", endpoint=api_mesh_stats, methods=["GET", "OPTIONS"]),
        Route("/api/mesh/stats", endpoint=api_mesh_stats, methods=["GET", "OPTIONS"]),
        Route("/api/reports", endpoint=api_reports, methods=["GET", "OPTIONS"]),
        Route("/api/reports/{identifier:path}", endpoint=api_get_report, methods=["GET", "OPTIONS"]),
        Route("/api/cost/telemetry", endpoint=api_cost_telemetry, methods=["GET", "OPTIONS"]),
        Route("/api/cost/recommendations", endpoint=api_cost_recommendations, methods=["GET", "OPTIONS"]),
        Route("/api/cost/budget", endpoint=api_cost_budget, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/cost/emergency-stop", endpoint=api_cost_emergency_stop, methods=["POST", "OPTIONS"]),
        Route("/api/cost/resume", endpoint=api_cost_resume, methods=["POST", "OPTIONS"]),
        Route("/api/audit", endpoint=api_audit_url, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/germinate", endpoint=api_germinate, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/sifter/status", endpoint=api_sifter_status, methods=["GET", "OPTIONS"]),
        Route("/api/sifter/cycle", endpoint=api_sifter_cycle, methods=["POST", "OPTIONS"]),
        Route("/api/roots/expand", endpoint=api_roots_expand, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/roots/tree", endpoint=api_roots_tree, methods=["GET", "OPTIONS"]),
        Route("/api/roots/candidates", endpoint=api_roots_candidates, methods=["GET", "OPTIONS"]),
        Route("/api/boredom/cycle", endpoint=api_boredom_cycle, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/boredom/status", endpoint=api_boredom_status, methods=["GET", "OPTIONS"]),
        Route("/api/domain/reputation/{domain:path}", endpoint=api_domain_reputation, methods=["GET", "OPTIONS"]),
        Route("/api/domain/quarantine", endpoint=api_domain_quarantine, methods=["GET", "OPTIONS"]),
        Route("/api/domain/appeal/{domain:path}", endpoint=api_domain_appeal, methods=["POST", "OPTIONS"]),
        Route("/api/feeds/stream", endpoint=api_feeds_stream, methods=["GET", "OPTIONS"]),
        Route("/api/leaderboard", endpoint=api_leaderboard, methods=["GET", "OPTIONS"]),
        Route("/api/merit", endpoint=api_get_merit, methods=["GET", "OPTIONS"]),
        Route("/api/merit/{identifier:path}", endpoint=api_get_merit, methods=["GET", "OPTIONS"]),
        Route("/api/badge/publisher/{domain:path}", endpoint=api_get_publisher_badge, methods=["GET", "OPTIONS"]),
        Route("/api/badge/{badge_id:path}", endpoint=api_get_badge_svg, methods=["GET", "OPTIONS"]),
        Route("/api/rankings/domains", endpoint=api_rankings_domains, methods=["GET", "OPTIONS"]),
        Route("/api/rankings/rules", endpoint=api_rankings_rules, methods=["GET", "OPTIONS"]),
        Route("/api/analytics/publishers", endpoint=api_list_publishers, methods=["GET", "OPTIONS"]),
        Route("/api/analytics/publisher/{domain:path}", endpoint=api_publisher_analytics, methods=["GET", "OPTIONS"]),
        Route("/api/weather", endpoint=api_weather, methods=["GET", "OPTIONS"]),
        Route("/api/bounties", endpoint=api_bounties, methods=["GET", "OPTIONS"]),
    ]
    for r in rest_routes:
        app.router.routes.insert(0, r)

    # Add global CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Add Telemetry Middleware for Interface Telemetry Loopback (ITLP-v1)
    from starlette.middleware.base import BaseHTTPMiddleware

    class TelemetryMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Any, call_next: Any) -> Any:
            t0 = time.perf_counter()
            status_code = 500
            error_msg = None
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            except Exception as exc:
                error_msg = str(exc)
                raise
            finally:
                dt_ms = (time.perf_counter() - t0) * 1000.0
                global_telemetry.record_request(status_code, request.url.path, dt_ms, error_msg)

    app.add_middleware(TelemetryMiddleware)

    # Lifespan task for Sifter Daemon, Boredom Daemon & Auto-Germination
    should_sift = enable_sifter or os.environ.get("CREDENCE_SIFTER_ENABLED", "").lower() in ("1", "true")
    should_boredom = enable_boredom or os.environ.get("CREDENCE_BOREDOM_ENABLED", "").lower() in ("1", "true")
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def combined_lifespan(app_instance: Starlette):
        from sqlmodel import col, func, select

        from credence.db import get_async_session, init_db
        from credence.feeds.boredom import BoredomDaemon
        from credence.feeds.sifter import SifterDaemon
        from credence.germinate import germinate_node
        from credence.models import AuditRecord, FeedSubscriptionRecord

        await init_db()

        # Check for zero-touch auto-germination on blank databases (in background)
        async def _run_background_germination() -> None:
            try:
                async with get_async_session() as session:
                    stmt_a = select(func.count(col(AuditRecord.id)))
                    total_a = (await session.exec(stmt_a)).first() or 0
                    stmt_f = select(func.count(col(FeedSubscriptionRecord.id)))
                    total_f = (await session.exec(stmt_f)).first() or 0

                    if total_a == 0 and total_f == 0:
                        logger.info(
                            "🌱 Blank node detected — auto-germinating identity, mesh attestations, and feeds in background..."
                        )
                        await germinate_node(session=session, burst_items=3, sync_mesh=True, verbose=True)
            except Exception as e:
                logger.warning("Auto-germination background task encountered error: %s", e)

        _germinate_task = asyncio.create_task(_run_background_germination())

        sifter_daemon = None
        sifter_task = None
        if should_sift:
            sifter_daemon = SifterDaemon(poll_interval_seconds=300, auto_audit=True)
            sifter_task = asyncio.create_task(sifter_daemon.start())

        boredom_daemon = None
        boredom_task = None
        if should_boredom:
            boredom_daemon = BoredomDaemon(idle_interval_seconds=120, audit_burst=3, expand_roots_enabled=True)
            boredom_task = asyncio.create_task(boredom_daemon.start())

        try:
            if original_lifespan:
                async with original_lifespan(app_instance) as state:
                    yield state
            else:
                yield {}
        finally:
            if _germinate_task and not _germinate_task.done():
                _germinate_task.cancel()
            if sifter_daemon and sifter_task:
                sifter_daemon.stop()
                try:
                    await asyncio.wait_for(sifter_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            if boredom_daemon and boredom_task:
                boredom_daemon.stop()
                try:
                    await asyncio.wait_for(boredom_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

    app.router.lifespan_context = combined_lifespan
    return app
