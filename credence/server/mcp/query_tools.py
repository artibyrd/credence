"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging

from mcp.server.mcpserver import MCPServer
from sqlmodel import col, select

from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.governor import get_token_headroom_status
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.middleware.telemetry import global_telemetry

logger = logging.getLogger("credence.server.mcp")


async def _execute_browse_audits(category: str = "recent", limit: int = 10, format: str = "human") -> str:
    """Helper to browse stored audit records for FastMCP tools and resources."""
    import secrets

    from sqlmodel import select

    from credence.db import get_async_session, init_db
    from credence.models import Audit

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
                d = a.model_dump(mode="json")
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
            records = [a.model_dump(mode="json") for a in audits]
            return json.dumps(records, indent=2, default=str)


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
        async with get_async_session() as s:
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
        from credence.db import get_async_session, init_db
        from credence.mesh.stats import compute_mesh_stats

        await init_db()
        snapshot = global_telemetry.get_snapshot()
        async with get_async_session() as s:
            stats = await compute_mesh_stats(s, telemetry_snapshot=snapshot)
            return json.dumps(stats, indent=2)
        return "{}"

    @server.tool(
        name="credence_get_mesh_network_health",
        description="Retrieve comprehensive Whole-Mesh Network Health, 13-node Watts-Strogatz topology, and Byzantine quorum metrics.",
    )
    async def get_mesh_network_health() -> str:
        from credence.db import get_async_session, init_db
        from credence.mesh.stats import compute_network_mesh_health

        await init_db()
        async with get_async_session() as s:
            health = await compute_network_mesh_health(s)
            return json.dumps(health, indent=2)
        health = await compute_network_mesh_health(None)
        return json.dumps(health, indent=2)
