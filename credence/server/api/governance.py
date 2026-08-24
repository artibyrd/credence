"""Standards Ratification & Governance REST API Endpoints (Phase 1).

Provides:
- GET /api/rfcs: List RFC standard proposals filtered by tier and stage
- GET /api/rfcs/{rfc_id}: Retrieve full RFC proposal, YAML catalog, and metrics
- POST /api/rfcs/validate: Hermetic AST and rule schema linting (<0.3s)
- POST /api/rfcs/benchmark: Synthetic Benchmark Gauntlet execution
"""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from credence.pipeline.rfc import (
    RFCStage,
    StandardTier,
    rfc_registry,
    run_synthetic_benchmark,
    validate_catalog_yaml,
)


async def api_list_rfcs(request: Request) -> Response:
    """REST API: List RFC standard proposals with optional tier and stage filtering."""
    tier_param = request.query_params.get("tier")
    stage_param = request.query_params.get("stage")

    tier_enum = None
    if tier_param:
        try:
            tier_enum = StandardTier(tier_param.upper())
        except ValueError:
            pass

    stage_enum = None
    if stage_param:
        try:
            stage_enum = RFCStage(stage_param.upper())
        except ValueError:
            pass

    proposals = rfc_registry.list_proposals(tier=tier_enum, stage=stage_enum)
    return JSONResponse(
        [p.model_dump(mode="json") for p in proposals],
        headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=30"},
    )


async def api_get_rfc(request: Request) -> Response:
    """REST API: Retrieve full RFC proposal by ID."""
    rfc_id = request.path_params.get("rfc_id", "").strip().upper()
    proposal = rfc_registry.get_proposal(rfc_id)
    if not proposal:
        return JSONResponse(
            {"error": f"RFC proposal '{rfc_id}' not found."},
            status_code=404,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    votes = rfc_registry.get_votes(rfc_id)
    payload = proposal.model_dump(mode="json")
    payload["votes"] = [v.model_dump(mode="json") for v in votes]

    return JSONResponse(
        payload,
        headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=30"},
    )


async def api_validate_rfc(request: Request) -> Response:
    """REST API: Hermetic schema and signal linting for candidate YAML catalogs (<0.3s)."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    yaml_content = body.get("yaml", body.get("catalog_yaml", ""))
    is_valid, errors, catalog = validate_catalog_yaml(yaml_content)

    return JSONResponse(
        {
            "valid": is_valid,
            "errors": errors,
            "catalog_hash": catalog.catalog_hash if catalog else None,
            "catalog_id": catalog.catalog_id if catalog else None,
            "rules_count": sum(len(c.rules) for c in catalog.clusters) if catalog else 0,
        },
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def api_benchmark_rfc(request: Request) -> Response:
    """REST API: Execute Synthetic Benchmark Gauntlet against fixtures and Golden Baseline."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    yaml_content = body.get("yaml", body.get("catalog_yaml", ""))
    fixtures = body.get("fixtures", [])

    is_valid, errors, catalog = validate_catalog_yaml(yaml_content)
    if not is_valid or not catalog:
        return JSONResponse(
            {"error": "Cannot benchmark invalid catalog.", "errors": errors},
            status_code=422,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    report = run_synthetic_benchmark(catalog, fixtures)
    return JSONResponse(
        report.model_dump(mode="json"),
        headers={"Access-Control-Allow-Origin": "*"},
    )
