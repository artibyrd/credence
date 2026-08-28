"""Antigravity-Native Agent Execution Driver for Credence Pipeline.

Enables direct cognitive auditing within Antigravity's agentic context and subagent
swarms, utilizing internal agent reasoning tokens and eliminating external API rate limits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from credence.ingestion.extractor import ExtractedContent
from credence.pipeline.schemas import SpecialistViolationFinding
from credence.pipeline.subagents import (
    build_cluster_specialist_prompt,
    build_satire_provenance_prompt,
    parse_cluster_response,
    parse_satire_response,
)
from credence.taxonomy_loader import TaxonomyCluster, TaxonomyRegistry


class AgentEvaluationDriver:
    """Antigravity-native driver orchestrating agent-level forensic auditing."""

    def __init__(self, model_name: str = "antigravity_pro") -> None:
        self.model_name = model_name

    def prepare_cluster_evaluation_payload(
        self,
        cluster: TaxonomyCluster,
        extracted: ExtractedContent,
        domain_name: str = "GENERAL",
    ) -> Dict[str, Any]:
        """Generate structured prompt payload for an Antigravity specialist subagent."""
        prompt = build_cluster_specialist_prompt(cluster, extracted, domain_name=domain_name)
        return {
            "cluster_id": cluster.cluster_id,
            "cluster_name": cluster.name,
            "domain": domain_name,
            "rules_count": len(cluster.rules),
            "prompt": prompt,
            "model": self.model_name,
        }

    def prepare_satire_evaluation_payload(
        self,
        extracted: ExtractedContent,
        reg: Optional[TaxonomyRegistry] = None,
    ) -> Dict[str, Any]:
        """Generate structured prompt payload for the Satire & Provenance specialist."""
        prompt = build_satire_provenance_prompt(extracted, reg=reg)
        return {
            "specialist": "satire_provenance",
            "prompt": prompt,
            "model": self.model_name,
        }

    def parse_cluster_findings(
        self,
        raw_response: str,
        cluster: TaxonomyCluster,
        domain_name: str = "GENERAL",
        reg: Optional[TaxonomyRegistry] = None,
    ) -> List[SpecialistViolationFinding]:
        """Parse structured response from an Antigravity specialist subagent."""
        report = parse_cluster_response(raw_response, cluster, domain_name=domain_name, reg=reg)
        return report.violations

    def parse_satire_verdict(self, raw_response: str) -> Dict[str, Any]:
        """Parse structured satire verdict from an Antigravity specialist subagent."""
        verdict = parse_satire_response(raw_response)
        return verdict.model_dump()
