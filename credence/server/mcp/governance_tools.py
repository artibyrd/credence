"""FastMCP 2.0 Governance & Standards RFC Tools for Credence (Phase 2).

Provides agentic MCP tools:
- credence_list_rfcs
- credence_get_rfc
- credence_validate_standard
- credence_benchmark_standard
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from mcp.server.mcpserver import MCPServer

from credence.pipeline.rfc import (
    RFCStage,
    StandardTier,
    rfc_registry,
    run_synthetic_benchmark,
    validate_catalog_yaml,
)

logger = logging.getLogger("credence.server.mcp")


def _register_governance_tools(server: MCPServer) -> None:
    """Register RFC standards governance tools."""

    @server.tool(
        name="credence_list_rfcs",
        description="List all active, candidate, and ratified RFC standard proposals in the Credence mesh with optional tier filtering.",
    )
    async def list_rfcs(tier: Optional[str] = None, stage: Optional[str] = None) -> str:
        tier_enum = None
        if tier:
            try:
                tier_enum = StandardTier(tier.upper())
            except ValueError:
                pass

        stage_enum = None
        if stage:
            try:
                stage_enum = RFCStage(stage.upper())
            except ValueError:
                pass

        proposals = rfc_registry.list_proposals(tier=tier_enum, stage=stage_enum)
        return json.dumps([p.model_dump(mode="json") for p in proposals], indent=2)

    @server.tool(
        name="credence_get_rfc",
        description="Retrieve deep technical specification, rule catalog, and recorded vote envelopes for an RFC standard by ID.",
    )
    async def get_rfc(rfc_id: str) -> str:
        clean_id = rfc_id.strip().upper()
        proposal = rfc_registry.get_proposal(clean_id)
        if not proposal:
            return json.dumps({"error": f"RFC proposal '{clean_id}' not found."}, indent=2)

        votes = rfc_registry.get_votes(clean_id)
        data = proposal.model_dump(mode="json")
        data["votes"] = [v.model_dump(mode="json") for v in votes]
        return json.dumps(data, indent=2)

    @server.tool(
        name="credence_validate_standard",
        description="Lint and validate a candidate YAML standard catalog string against AST rules (<0.3s gate).",
    )
    async def validate_standard(yaml_content: str) -> str:
        is_valid, errors, catalog = validate_catalog_yaml(yaml_content)
        return json.dumps(
            {
                "valid": is_valid,
                "errors": errors,
                "catalog_hash": catalog.catalog_hash if catalog else None,
                "catalog_id": catalog.catalog_id if catalog else None,
                "rules_count": sum(len(c.rules) for c in catalog.clusters) if catalog else 0,
            },
            indent=2,
        )

    @server.tool(
        name="credence_benchmark_standard",
        description="Execute the Synthetic Benchmark Gauntlet on a candidate standard YAML against test fixtures and Golden Baseline.",
    )
    async def benchmark_standard(yaml_content: str, fixtures_json: Optional[str] = None) -> str:
        is_valid, errors, catalog = validate_catalog_yaml(yaml_content)
        if not is_valid or not catalog:
            return json.dumps({"error": "Invalid catalog YAML", "errors": errors}, indent=2)

        fixtures = []
        if fixtures_json:
            try:
                fixtures = json.loads(fixtures_json)
            except Exception as e:
                return json.dumps({"error": f"Failed to parse fixtures_json: {e}"}, indent=2)

        report = run_synthetic_benchmark(catalog, fixtures)
        return json.dumps(report.model_dump(mode="json"), indent=2)
