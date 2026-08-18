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
from typing import Any, List, Optional

from mcp.server.mcpserver import MCPServer
from sqlmodel import col, select

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_session, init_db
from credence.identity import load_or_create_node_identity, verify_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord
from credence.pipeline.evaluator import audit_url, evaluate_snapshot
from credence.pipeline.governor import get_token_headroom_status
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


def _register_eval_tools(server: MCPServer) -> None:
    """Register evaluation tools."""

    @server.tool(
        name="credence_check_url",
        description="Fetch a URL snapshot, extract structured text, and evaluate against epistemic taxonomies.",
    )
    async def check_url(url: str, force: bool = False, profile: Optional[str] = None) -> str:
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
        await init_db()
        async for s in get_session():
            status = await get_token_headroom_status(s)
            return json.dumps(status.model_dump(mode="json"), indent=2)
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
    """REST API: Health check endpoint."""
    from starlette.responses import JSONResponse

    from credence import __version__

    return JSONResponse(
        {
            "status": "healthy",
            "service": "credence",
            "version": __version__,
        }
    )


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
    """REST API: Get complete audit report by SHA-256 or URL identifier."""
    from starlette.responses import JSONResponse

    identifier = request.path_params.get("identifier", "")
    if not identifier:
        identifier = request.query_params.get("q", "")

    report_dict = await _reconstitute_report_from_db(identifier)
    if not report_dict:
        return JSONResponse({"error": f"Report not found for identifier: '{identifier}'"}, status_code=404)
    return JSONResponse(report_dict)


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


def create_mcp_server() -> MCPServer:
    """Instantiate and configure the Credence FastMCP server."""
    server = MCPServer(
        name="credence",
        instructions="Autonomous Epistemic Evaluation Engine, FastMCP Server, and Trust Network.",
        version="0.1.0",
    )
    _register_eval_tools(server)
    _register_query_tools(server)
    _register_consensus_tools(server)
    _register_mesh_tools(server)
    _register_feed_sync_tools(server)
    _register_feed_management_tools(server)
    _register_taxonomy_resources(server)
    _register_subject_resources(server)
    _register_prompts(server)
    return server


mcp_server = create_mcp_server()


def create_server_app(
    transport_security: Optional[Any] = None,
    enable_sifter: bool = False,
) -> Any:
    """Create a unified Starlette application hosting FastMCP SSE, REST API, and Sifter."""
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
        Route("/api/reports", endpoint=api_reports, methods=["GET", "OPTIONS"]),
        Route("/api/reports/{identifier:path}", endpoint=api_get_report, methods=["GET", "OPTIONS"]),
        Route("/api/audit", endpoint=api_audit_url, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/germinate", endpoint=api_germinate, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/sifter/status", endpoint=api_sifter_status, methods=["GET", "OPTIONS"]),
        Route("/api/sifter/cycle", endpoint=api_sifter_cycle, methods=["POST", "OPTIONS"]),
        Route("/api/feeds/stream", endpoint=api_feeds_stream, methods=["GET", "OPTIONS"]),
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

    # Lifespan task for Sifter Daemon & Auto-Germination
    should_sift = enable_sifter or os.environ.get("CREDENCE_SIFTER_ENABLED", "").lower() in ("1", "true")
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def combined_lifespan(app_instance: Starlette):
        from sqlmodel import col, func, select

        from credence.db import get_async_session, init_db
        from credence.feeds.sifter import SifterDaemon
        from credence.germinate import germinate_node
        from credence.models import AuditRecord, FeedSubscriptionRecord

        await init_db()

        # Check for zero-touch auto-germination on blank databases
        try:
            async with get_async_session() as session:
                stmt_a = select(func.count(col(AuditRecord.id)))
                total_a = (await session.exec(stmt_a)).first() or 0
                stmt_f = select(func.count(col(FeedSubscriptionRecord.id)))
                total_f = (await session.exec(stmt_f)).first() or 0

                if total_a == 0 and total_f == 0:
                    logger.info("🌱 Blank node detected — auto-germinating identity, mesh attestations, and feeds...")
                    await germinate_node(session=session, burst_items=3, sync_mesh=True, verbose=True)
        except Exception as e:
            logger.warning("Auto-germination background check encountered error: %s", e)

        sifter_daemon = None
        sifter_task = None
        if should_sift:
            sifter_daemon = SifterDaemon(poll_interval_seconds=300, auto_audit=True)
            sifter_task = asyncio.create_task(sifter_daemon.start())

        if original_lifespan:
            async with original_lifespan(app_instance) as state:
                yield state
        else:
            yield {}

        if sifter_daemon and sifter_task:
            sifter_daemon.stop()
            sifter_task.cancel()
            try:
                await sifter_task
            except asyncio.CancelledError:
                pass

    app.router.lifespan_context = combined_lifespan
    return app
