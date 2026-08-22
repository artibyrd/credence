"""REST API Handlers for Credence Server."""

from __future__ import annotations

import logging
from typing import Any

from starlette.responses import JSONResponse, Response

from credence.db import get_async_session, init_db

logger = logging.getLogger("credence.server.api")


async def api_leaderboard(request: Any) -> Any:
    """REST API: Query P2P node leaderboard."""
    from dataclasses import asdict

    from credence.mesh.merit import get_leaderboard

    cat = request.query_params.get("category", "quality")
    team = request.query_params.get("team")
    try:
        limit = min(int(request.query_params.get("limit", 50)), 100)
    except ValueError:
        limit = 50

    await init_db()
    async with get_async_session() as s:
        entries = await get_leaderboard(s, category=cat, limit=limit, team_filter=team)
        return JSONResponse({"category": cat, "total": len(entries), "leaderboard": [asdict(e) for e in entries]})
    return JSONResponse({"leaderboard": []})


async def api_get_merit(request: Any) -> Any:
    """REST API: Get node merit card."""
    from dataclasses import asdict

    from credence.mesh.merit import get_local_node_merit

    pubkey = request.path_params.get("identifier") or request.query_params.get("pubkey")
    await init_db()
    async with get_async_session() as s:
        card = await get_local_node_merit(s, local_pubkey=pubkey)
        card_dict = asdict(card)
        card_dict["unlocked_badges"] = [
            b.model_dump() if hasattr(b, "model_dump") else asdict(b) if hasattr(b, "__dataclass_fields__") else b
            for b in card.unlocked_badges
        ]
        return JSONResponse(card_dict)
    return JSONResponse({"error": "Unavailable"}, status_code=500)


async def api_verify_merit(request: Any) -> Any:
    """REST API: Cryptographically verify a node merit card attestation envelope."""
    from credence.mesh.merit import verify_node_merit_card

    try:
        data = await request.json()
        is_valid = verify_node_merit_card(data)
        return JSONResponse(
            {
                "valid": is_valid,
                "node_pubkey": data.get("node_pubkey"),
                "canonical_sha256": data.get("canonical_sha256"),
                "tampered": not is_valid,
            }
        )
    except Exception as e:
        return JSONResponse({"valid": False, "error": str(e), "tampered": True}, status_code=400)


async def api_get_badge_svg(request: Any) -> Any:
    """REST API: Dynamic SVG badge endpoint."""
    from credence.mesh.merit import generate_svg_badge

    badge_id = request.path_params.get("badge_id", "root_seed_candidate").replace(".svg", "")
    node = request.query_params.get("node", "credence-node")
    score = request.query_params.get("score", "VERIFIED")
    style = request.query_params.get("style", "pill")
    theme = request.query_params.get("theme", "dark")

    svg_content = generate_svg_badge(
        badge_id=badge_id,
        node_alias=node,
        score_or_val=score,
        style=style,
        theme=theme,
    )
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=300"},
    )


async def api_get_publisher_badge(request: Any) -> Any:
    """REST API: Dynamic Publisher SVG badge endpoint."""
    from credence.subjects.analytics import generate_publisher_svg_badge, get_domain_leaderboard

    domain = request.path_params.get("domain", "reuters.com").replace(".svg", "")
    style = request.query_params.get("style", "pill")
    theme = request.query_params.get("theme", "dark")

    dci_val = 85.0
    status = "CLEAN"
    await init_db()
    async with get_async_session() as s:
        ranks = await get_domain_leaderboard(s, category="best", limit=100)
        for r in ranks:
            if r.domain == domain:
                dci_val = r.dci_score
                status = r.trust_band
                break

    svg = generate_publisher_svg_badge(
        domain=domain,
        dci_score=dci_val,
        status=status,
        style=style,
        theme=theme,
    )
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=300"},
    )


async def api_rankings_rules(request: Any) -> Any:
    """REST API: Query Top 10 most violated rules."""
    from dataclasses import asdict

    from credence.subjects.analytics import get_top_violated_rules

    try:
        limit = min(int(request.query_params.get("limit", 10)), 50)
    except ValueError:
        limit = 10

    await init_db()
    async with get_async_session() as s:
        rules = await get_top_violated_rules(s, limit=limit)
        return JSONResponse({"total": len(rules), "rules": [asdict(r) for r in rules]})
    return JSONResponse({"rules": []})


async def api_weather(request: Any) -> Any:
    """REST API: Query Global Epistemic Weather report."""
    from dataclasses import asdict

    from credence.subjects.analytics import get_global_epistemic_weather

    await init_db()
    async with get_async_session() as s:
        report = await get_global_epistemic_weather(s)
        return JSONResponse(asdict(report))
    return JSONResponse({"error": "Unavailable"}, status_code=500)


async def api_bounties(request: Any) -> Any:
    """REST API: Query community verification bounties."""
    from dataclasses import asdict

    from credence.subjects.analytics import get_community_bounties

    try:
        limit = min(int(request.query_params.get("limit", 20)), 50)
    except ValueError:
        limit = 20

    await init_db()
    async with get_async_session() as s:
        bounties = await get_community_bounties(s, limit=limit)
        return JSONResponse({"total": len(bounties), "bounties": [asdict(b) for b in bounties]})
    return JSONResponse({"bounties": []})


async def api_list_publishers(request: Any) -> Any:
    """REST API: Query summary analytics for all audited news publishers."""

    from credence.subjects.analytics import list_all_publishers_summary

    await init_db()
    async with get_async_session() as s:
        summaries = await list_all_publishers_summary(s)
        return JSONResponse({"total": len(summaries), "publishers": summaries})
    return JSONResponse({"total": 0, "publishers": []})


async def api_publisher_analytics(request: Any) -> Any:
    """REST API: Query deep aggregate public analytics, DEI score, forensic metrics, and trends for a specific publisher."""
    from dataclasses import asdict

    from credence.subjects.analytics import get_publisher_analytics

    domain = request.path_params.get("domain", "") or request.query_params.get("domain", "")
    if not domain:
        return JSONResponse(
            {"error": "Publisher domain is required, e.g. /api/analytics/publisher/inmaricopa.com"}, status_code=400
        )

    await init_db()
    async with get_async_session() as s:
        profile = await get_publisher_analytics(s, domain=domain)
        if not profile:
            return JSONResponse({"error": f"No audit records found for publisher '{domain}'"}, status_code=404)
        return JSONResponse(asdict(profile))
    return JSONResponse({"error": "Database session unavailable"}, status_code=500)
