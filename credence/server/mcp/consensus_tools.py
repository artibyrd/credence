"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from mcp.server.mcpserver import MCPServer
from sqlmodel import select

from credence.db import get_async_session, init_db
from credence.identity import verify_attestation_signature
from credence.models import Audit, Violation
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding

logger = logging.getLogger("credence.server.mcp")


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
            is_valid = verify_attestation_signature(report)
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
        from credence.models import DomainMetric

        await init_db()
        clean_hash = content_sha256 if content_sha256.startswith("sha256:") else f"sha256:{content_sha256}"
        async with get_async_session() as s:
            stmt = select(Audit).where(Audit.content_sha256 == clean_hash)
            audits = (await s.exec(stmt)).all()
            if not audits:
                return json.dumps({"error": f"No audit records found for hash: {clean_hash}"})

            reports: List[AuditReport] = []
            for a in audits:
                v_stmt = select(Violation).where(Violation.audit_id == a.id)
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
                stmt_metrics = select(DomainMetric).where(DomainMetric.subject_id == subject_id)
                metrics = (await s.exec(stmt_metrics)).all()
                for m in metrics:
                    exp_map[m.node_pubkey] = m.expertise_score

            aggregator = BayesianConsensusAggregator()
            verdict = aggregator.compute_consensus(
                attestations=reports,
                subject_id=subject_id,
                subject_expertise_map=exp_map,
            )
            if verdict:
                return json.dumps(verdict.model_dump(mode="json"), indent=2)
            return json.dumps({"error": "Failed to calculate consensus verdict."})

        return "{}"
