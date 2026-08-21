"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging
from typing import Optional

from mcp.server.mcpserver import MCPServer

from credence.db import get_async_session, init_db

logger = logging.getLogger("credence.server.mcp")


def _register_merit_and_analytics_tools(server: MCPServer) -> None:
    """Register gamification, leaderboard, and web analytics tools."""

    @server.tool(
        name="credence_get_leaderboard",
        description="Retrieve ranked P2P mesh node leaderboard across categories: quality, subjects, philanthropy, galileo, or teams.",
    )
    async def get_leaderboard_tool(
        category: str = "quality",
        limit: int = 50,
        team: Optional[str] = None,
    ) -> str:
        from dataclasses import asdict

        from credence.mesh.merit import get_leaderboard

        await init_db()
        async with get_async_session() as session:
            entries = await get_leaderboard(session, category=category, limit=limit, team_filter=team)
            return json.dumps([asdict(e) for e in entries], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_node_merit",
        description="Inspect a mesh node's full merit card, unlocked badges, traffic class, and compute impact.",
    )
    async def get_node_merit_tool(node_pubkey: Optional[str] = None) -> str:
        from dataclasses import asdict

        from credence.mesh.merit import get_local_node_merit

        await init_db()
        async with get_async_session() as session:
            card = await get_local_node_merit(session, local_pubkey=node_pubkey)
            card_dict = asdict(card)
            card_dict["unlocked_badges"] = [
                b.model_dump() if hasattr(b, "model_dump") else asdict(b) if hasattr(b, "__dataclass_fields__") else b
                for b in card.unlocked_badges
            ]
            return json.dumps(card_dict, indent=2)
        return "{}"

    @server.tool(
        name="credence_get_domain_rankings",
        description="Retrieve Domain Credence Index (DCI) publisher trust rankings: best (Honor Roll), worst (Wall of Shame), or astroturf.",
    )
    async def get_domain_rankings_tool(
        category: str = "best",
        min_audits: int = 1,
        limit: int = 50,
    ) -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_domain_leaderboard

        await init_db()
        async with get_async_session() as session:
            ranks = await get_domain_leaderboard(session, category=category, min_audits=min_audits, limit=limit)
            return json.dumps([asdict(r) for r in ranks], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_taxonomy_analytics",
        description="Retrieve analytics on the Top 10 most frequently violated rules across the web.",
    )
    async def get_taxonomy_analytics_tool(limit: int = 10) -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_top_violated_rules

        await init_db()
        async with get_async_session() as session:
            rules = await get_top_violated_rules(session, limit=limit)
            return json.dumps([asdict(r) for r in rules], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_epistemic_weather",
        description="Retrieve the global macro Epistemic Weather report and category integrity gauges.",
    )
    async def get_epistemic_weather_tool() -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_global_epistemic_weather

        await init_db()
        async with get_async_session() as session:
            weather = await get_global_epistemic_weather(session)
            return json.dumps(asdict(weather), indent=2)
        return "{}"

    @server.tool(
        name="credence_get_bounties",
        description="Retrieve open community verification quests and bounties for breaking or unaudited articles.",
    )
    async def get_bounties_tool(limit: int = 20) -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_community_bounties

        await init_db()
        async with get_async_session() as session:
            bounties = await get_community_bounties(session, limit=limit)
            return json.dumps([asdict(b) for b in bounties], indent=2)
        return "[]"

    @server.tool(
        name="credence_get_publisher_analytics",
        description="Retrieve deep aggregate public analytics, DEI score, forensic sourcing ratios, astroturf entropy, and trend timelines for any specific news publisher.",
    )
    async def get_publisher_analytics_tool(domain: str) -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_publisher_analytics

        await init_db()
        async with get_async_session() as session:
            profile = await get_publisher_analytics(session, domain=domain)
            if profile:
                return json.dumps(asdict(profile), indent=2)
            return json.dumps({"error": f"No audit records found for publisher '{domain}'."})
        return "{}"


def _register_merit_and_analytics_resources(server: MCPServer) -> None:
    """Register merit, leaderboard, and web analytics resources."""

    @server.resource("credence://analytics/publishers")
    async def list_publishers_resource() -> str:
        from credence.subjects.analytics import list_all_publishers_summary

        await init_db()
        async with get_async_session() as session:
            summaries = await list_all_publishers_summary(session)
            return json.dumps(summaries, indent=2)
        return "[]"

    @server.resource("credence://analytics/publisher/{domain}")
    async def get_publisher_analytics_resource(domain: str) -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_publisher_analytics

        await init_db()
        async with get_async_session() as session:
            profile = await get_publisher_analytics(session, domain=domain)
            if profile:
                return json.dumps(asdict(profile), indent=2)
            return json.dumps({"error": f"No analytics found for domain: '{domain}'"})
        return "{}"

    @server.resource("credence://leaderboard/{category}")
    async def get_leaderboard_resource(category: str) -> str:
        from dataclasses import asdict

        from credence.mesh.merit import get_leaderboard

        await init_db()
        async with get_async_session() as session:
            entries = await get_leaderboard(session, category=category, limit=50)
            return json.dumps([asdict(e) for e in entries], indent=2)
        return "[]"

    @server.resource("credence://node/merit")
    async def get_node_merit_resource() -> str:
        from dataclasses import asdict

        from credence.mesh.merit import get_local_node_merit

        await init_db()
        async with get_async_session() as session:
            card = await get_local_node_merit(session)
            return json.dumps(asdict(card), indent=2)
        return "{}"

    @server.resource("credence://merit/badges")
    def get_merit_badges_resource() -> str:
        from dataclasses import asdict

        from credence.mesh.merit import BADGE_REGISTRY

        return json.dumps([asdict(b) for b in BADGE_REGISTRY.values()], indent=2)

    @server.resource("credence://rankings/domains/{category}")
    async def get_domain_rankings_resource(category: str) -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_domain_leaderboard

        await init_db()
        async with get_async_session() as session:
            ranks = await get_domain_leaderboard(session, category=category, limit=50)
            return json.dumps([asdict(r) for r in ranks], indent=2)
        return "[]"

    @server.resource("credence://rankings/rules")
    async def get_rankings_rules_resource() -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_top_violated_rules

        await init_db()
        async with get_async_session() as session:
            rules = await get_top_violated_rules(session, limit=10)
            return json.dumps([asdict(r) for r in rules], indent=2)
        return "[]"

    @server.resource("credence://weather/global")
    async def get_weather_resource() -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_global_epistemic_weather

        await init_db()
        async with get_async_session() as session:
            weather = await get_global_epistemic_weather(session)
            return json.dumps(asdict(weather), indent=2)
        return "{}"

    @server.resource("credence://bounties")
    async def get_bounties_resource() -> str:
        from dataclasses import asdict

        from credence.subjects.analytics import get_community_bounties

        await init_db()
        async with get_async_session() as session:
            bounties = await get_community_bounties(session, limit=20)
            return json.dumps([asdict(b) for b in bounties], indent=2)
        return "[]"
