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

import json
import time
from typing import List, Optional

from mcp.server.mcpserver import MCPServer
from sqlmodel import select

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
    from credence.config import COST_PROFILES, CostProfile

    @server.tool(
        name="credence_check_url",
        description="Audit a webpage for journalistic ethics, logical fallacies, and deceptive patterns.",
    )
    async def check_url(
        url: str,
        force_refresh: bool = False,
        profile: Optional[str] = None,
    ) -> str:
        if not _global_rate_limiter.check_and_record(len(url)):
            raise ValueError("FastMCP tool rate limit exceeded (maximum 60 requests/minute). Please retry shortly.")
        await init_db()
        prof_cfg = None
        if profile:
            try:
                prof_cfg = COST_PROFILES.get(CostProfile(profile.lower()))
            except ValueError:
                pass
        report = await audit_url(url, force_refresh=force_refresh, profile_override=prof_cfg)
        return json.dumps(report.model_dump(mode="json"), indent=2)

    @server.tool(
        name="credence_evaluate_text",
        description="Directly evaluate raw prose text without web scraping.",
    )
    async def evaluate_text(
        text: str,
        title: str = "Pasted Text Snippet",
        byline: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> str:
        if not _global_rate_limiter.check_and_record(len(text)):
            raise ValueError("FastMCP tool rate limit exceeded (maximum 60 requests/minute). Please retry shortly.")
        await init_db()
        content_hash = compute_content_sha256(text)
        simhash_hex = compute_simhash(text)

        prof_cfg = None
        if profile:
            try:
                prof_cfg = COST_PROFILES.get(CostProfile(profile.lower()))
            except ValueError:
                pass

        extracted = ExtractedContent(
            title=title,
            clean_text=text,
            byline=byline,
            word_count=len(text.split()),
            char_count=len(text),
        )
        snapshot = DualCaptureResult(
            url="text://inline",
            content_sha256=content_hash,
            simhash_64=simhash_hex,
            raw_html=f"<html><body><h1>{title}</h1><p>{text}</p></body></html>",
            extracted=extracted,
        )

        async for s in get_session():
            report = await evaluate_snapshot(snapshot, session=s, sign_result=True, profile_override=prof_cfg)
            return json.dumps(report.model_dump(mode="json"), indent=2)

        return "{}"


def _register_query_tools(server: MCPServer) -> None:
    """Register cache lookup and quota tools."""

    @server.tool(
        name="credence_get_audit",
        description="Lookup a cached audit report by URL or content SHA-256.",
    )
    async def get_audit(identifier: str) -> str:
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
