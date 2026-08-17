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
        description="Get Bayesian consensus suspicion score across known mesh peer attestations.",
    )
    async def get_consensus(content_sha256: str) -> str:
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

            aggregator = BayesianConsensusAggregator()
            verdict = aggregator.calculate_consensus(reports)
            if verdict:
                return json.dumps(verdict.model_dump(mode="json"), indent=2)
            return json.dumps({"error": "Failed to calculate consensus verdict."})

        return "{}"


def _register_resources(server: MCPServer) -> None:
    """Register all FastMCP dynamic resources."""

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
    _register_resources(server)
    _register_prompts(server)
    return server


mcp_server = create_mcp_server()
