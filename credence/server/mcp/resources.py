"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging

from mcp.server.mcpserver import MCPServer
from sqlmodel import col, select

from credence.config import COST_PROFILES
from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.governor import get_token_headroom_status
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.mcp.query_tools import _execute_browse_audits
from credence.server.middleware.telemetry import global_telemetry
from credence.taxonomy_loader import registry

logger = logging.getLogger("credence.server.mcp")


def _register_taxonomy_resources(server: MCPServer) -> None:
    """Register taxonomy, profile, identity, and seed resources."""

    @server.resource("credence://profiles")
    def list_profiles_resource() -> str:
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
        from credence.db import get_async_session, init_db
        from credence.mesh.stats import compute_mesh_stats

        await init_db()
        snapshot = global_telemetry.get_snapshot()
        async with get_async_session() as s:
            stats = await compute_mesh_stats(s, telemetry_snapshot=snapshot)
            return json.dumps(stats, indent=2)
        return "{}"

    @server.resource("credence://mesh/network-health")
    async def get_mesh_network_health_resource() -> str:
        """Whole-Mesh Network Health, 13-node Watts-Strogatz topology, and Byzantine quorum metrics."""
        from credence.db import get_async_session, init_db
        from credence.mesh.stats import compute_network_mesh_health

        await init_db()
        async with get_async_session() as s:
            health = await compute_network_mesh_health(s)
            return json.dumps(health, indent=2)
        health = await compute_network_mesh_health(None)
        return json.dumps(health, indent=2)


def _register_subject_core_resources(server: MCPServer) -> None:
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
        from credence.db import get_async_session, init_db
        from credence.models import DomainMetric

        await init_db()
        async with get_async_session() as session:
            stmt = select(DomainMetric).order_by(DomainMetric.expertise_score.desc()).limit(50)  # type: ignore[attr-defined]
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


def _register_feed_and_root_resources(server: MCPServer) -> None:
    """Register syndicated feed status, boredom cycle, and root candidates resources."""

    @server.resource("credence://feeds/status")
    async def get_feeds_status_resource() -> str:
        from credence.db import get_async_session, init_db
        from credence.feeds.boredom import compute_curiosity_excitement
        from credence.models import Audit, FeedItem, FeedSubscription
        from credence.pipeline.governor import get_token_headroom_status

        await init_db()
        async with get_async_session() as session:
            stmt_subs = select(FeedSubscription)
            subs = (await session.exec(stmt_subs)).all()
            stmt_items = select(FeedItem)
            items = (await session.exec(stmt_items)).all()

            stmt_a = select(Audit).order_by(col(Audit.audited_at).desc()).limit(1)
            latest_audit = (await session.exec(stmt_a)).first()
            last_time = latest_audit.audited_at if latest_audit else None
            headroom = await get_token_headroom_status(session)
            total_audits_cnt = len((await session.exec(select(Audit.id))).all())

            decision = compute_curiosity_excitement(
                total_audits=total_audits_cnt,
                daily_headroom_pct=headroom.daily_headroom_pct,
                last_audit_time=last_time,
            )

            return json.dumps(
                {
                    "active_subscriptions_count": len([s for s in subs if s.is_active]),
                    "total_articles_discovered": len(items),
                    "zero_token_adoptions_count": len([i for i in items if i.processing_status == "mesh_adopted"]),
                    "total_tokens_saved": sum(i.tokens_saved for i in items),
                    "epistemic_excitement": {
                        "mode": decision.mode,
                        "score": decision.excitement_score,
                        "burst_size": decision.audit_burst,
                        "expand_roots_appetite": decision.expand_roots_appetite,
                        "heartbeat_cadence": "10m Cloud Scheduler Cron",
                        "scale_to_zero_idle_cost": "$0.00",
                        "reason": decision.reason,
                    },
                },
                indent=2,
            )
        return "{}"

    @server.resource("credence://roots/tree")
    async def get_roots_tree_resource() -> str:
        from credence.db import get_async_session, init_db
        from credence.feeds.roots import get_root_tree

        await init_db()
        async with get_async_session() as session:
            tree = await get_root_tree(session)
            return json.dumps(tree, indent=2)
        return "{}"

    @server.resource("credence://roots/candidates")
    async def get_roots_candidates_resource() -> str:
        from dataclasses import asdict

        from credence.db import get_async_session, init_db
        from credence.feeds.roots import extract_root_candidates

        await init_db()
        async with get_async_session() as session:
            cands = await extract_root_candidates(session, limit=20)
            return json.dumps([asdict(c) for c in cands], indent=2)
        return "[]"

    @server.resource("credence://boredom/status")
    async def get_boredom_status_resource() -> str:
        from sqlmodel import func, select

        from credence.db import get_async_session, init_db
        from credence.models import FeedItem, FeedSubscription

        await init_db()
        async with get_async_session() as s:
            headroom = await get_token_headroom_status(s)
            stmt_pending = select(func.count(col(FeedItem.id))).where(FeedItem.processing_status == "pending")
            pending_count = (await s.exec(stmt_pending)).first() or 0
            stmt_roots = select(func.count(col(FeedSubscription.id))).where(col(FeedSubscription.is_active).is_(True))
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

    @server.resource("credence://digest/morning")
    async def get_morning_digest_resource() -> str:
        from credence.db import get_async_session, init_db
        from credence.feeds.digest import generate_morning_digest

        await init_db()
        async with get_async_session() as session:
            digest = await generate_morning_digest(session, timeframe_hours=24)
            return json.dumps(digest.to_dict(), indent=2)
        return "{}"


def _register_domain_resources(server: MCPServer) -> None:
    """Register domain-level reputation and quarantine resources."""

    @server.resource("credence://domain/{domain}/reputation")
    async def get_domain_reputation_resource(domain: str) -> str:
        from credence.db import get_async_session, init_db
        from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

        await init_db()
        async with get_async_session() as session:
            rec = await get_or_create_domain_reputation(session, normalize_domain(domain))
            return json.dumps(rec.model_dump(mode="json"), indent=2)
        return "{}"

    @server.resource("credence://domain/quarantine")
    async def get_domain_quarantine_resource() -> str:
        from credence.db import get_async_session, init_db
        from credence.feeds.reputation import get_domain_quarantine_list

        await init_db()
        async with get_async_session() as session:
            quarantined = await get_domain_quarantine_list(session)
            return json.dumps(quarantined, indent=2)
        return "[]"


def _register_report_resources(server: MCPServer) -> None:
    """Register audit report retrieval, human formatting, compact rendering, and revision history resources."""

    @server.resource("credence://reports/{identifier}")
    async def get_report_resource(identifier: str) -> str:
        await init_db()
        async with get_async_session() as s:
            if identifier.startswith("sha256:") or len(identifier) == 64:
                clean_hash = identifier if identifier.startswith("sha256:") else f"sha256:{identifier}"
                stmt = select(Audit).where(Audit.content_sha256 == clean_hash)
            else:
                snap_stmt = select(Snapshot).where(Snapshot.url == identifier)
                snap = (await s.exec(snap_stmt)).first()
                if not snap:
                    return json.dumps({"error": f"No cached snapshot found for URL: {identifier}"})
                stmt = select(Audit).where(Audit.content_sha256 == snap.content_sha256)

            audit = (await s.exec(stmt)).first()
            if not audit:
                return json.dumps({"error": f"No cached audit report found for: {identifier}"})

            v_stmt = select(Violation).where(Violation.audit_id == audit.id)
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

    @server.resource("credence://history/{identifier}")
    async def get_history_resource(identifier: str) -> str:
        from credence.storage.revisions import get_url_revision_history

        await init_db()
        async with get_async_session() as s:
            trajectory = await get_url_revision_history(s, identifier)
            return json.dumps(trajectory.model_dump(mode="json"), indent=2)


def _register_subject_resources(server: MCPServer) -> None:
    """Register subject catalog, feeds, domains, and report resources via decoupled dispatchers."""
    _register_subject_core_resources(server)
    _register_feed_and_root_resources(server)
    _register_domain_resources(server)
    _register_report_resources(server)
