"""Dynamic Node Merit, Epistemic Tier Progression, and Leaderboards.

Governed by Invariant 8: Universal 4-Way Feature Parity & compute_* naming ontology.
Architecture: Modular P2P Merit Engine (<450 LOC).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.identity import load_or_create_node_identity
from credence.mesh.badges import (
    compute_half_life_uptime,
    compute_longevity_days,
    determine_node_tier,
    evaluate_node_badges,
    generate_svg_badge,
)
from credence.mesh.models import BADGE_REGISTRY, BadgeAward, BadgeInfo
from credence.models import DomainMetric, EpistemicTier, FeedItem, PeerMetric


@dataclass
class LeaderboardEntry:
    """Structured ranking record for public node reputation dashboards."""

    rank: int
    node_pubkey: str
    node_alias: str
    team_tag: Optional[str]
    tier: str
    score: float
    grounding_ratio: float
    quality_score: float
    uptime_ratio: float
    longevity_days: float
    tokens_seeded: int
    usd_saved_estimate: float
    evaluations_count: int
    badges_count: int
    traffic_class: str
    is_seed_candidate: bool


@dataclass
class NodeMeritCard:
    """Comprehensive merit profile for a local or remote node."""

    node_pubkey: str
    node_alias: str
    team_tag: Optional[str]
    tier: str
    quality_score: float
    uptime_ratio: float
    grounding_ratio: float
    concordance_factor: float
    longevity_days: float
    traffic_class: str
    tokens_seeded: int
    usd_saved_estimate: float
    attestations_seeded: int
    galileo_discoveries: int
    rank_overall: int
    total_nodes: int
    is_seed_candidate: bool
    unlocked_badges: List[BadgeAward] = field(default_factory=list)
    next_tier: Optional[str] = None
    next_tier_progress: float = 0.0


async def get_leaderboard(
    session: AsyncSession,
    category: str = "quality",
    limit: int = 50,
    team_filter: Optional[str] = None,
    now: Optional[datetime] = None,
) -> List[LeaderboardEntry]:
    """Retrieve global node reputation rankings with deterministic multi-level tie-breaking."""
    current_time = now or datetime.now(timezone.utc)
    stmt = select(PeerMetric)
    peers = list((await session.exec(stmt)).all())

    stmt_d = select(DomainMetric)
    domain_records = list((await session.exec(stmt_d)).all())

    stmt_feed = select(FeedItem)
    feed_count = len(list((await session.exec(stmt_feed)).all()))

    entries: List[LeaderboardEntry] = []
    for p in peers:
        p_doms = [d for d in domain_records if d.node_pubkey == p.node_pubkey]
        longevity = compute_longevity_days(p.first_seen, now=current_time)
        uptime = compute_half_life_uptime(
            p.successful_heartbeats, p.total_heartbeats_sent, p.last_seen, now=current_time
        )
        total_quotes = max(1, p.total_citations_count)
        grounding = round(p.grounded_citations_count / total_quotes, 4)
        max_exp = max([d.expertise_score for d in p_doms], default=0.05)
        badges = evaluate_node_badges(p, p_doms, feed_items_count=feed_count, now=current_time)
        tier = determine_node_tier(
            quality_score=p.quality_score,
            evaluations_count=p.total_attestations_evaluated,
            grounding_ratio=grounding,
            max_domain_expertise=max_exp,
            longevity_days=longevity,
        )

        usd_saved = round((p.tokens_seeded_count / 1_000_000.0) * 0.075, 4)
        cat = category.lower()
        score = p.quality_score
        if cat == "uptime":
            score = uptime
        elif cat == "grounding":
            score = grounding
        elif cat == "tokens":
            score = float(p.tokens_seeded_count)
        elif cat == "longevity":
            score = longevity

        entries.append(
            LeaderboardEntry(
                rank=1,
                node_pubkey=p.node_pubkey,
                node_alias=p.node_alias,
                team_tag=p.team_tag,
                tier=tier.value,
                score=score,
                grounding_ratio=grounding,
                quality_score=p.quality_score,
                uptime_ratio=uptime,
                longevity_days=round(longevity, 1),
                tokens_seeded=p.tokens_seeded_count,
                usd_saved_estimate=usd_saved,
                evaluations_count=p.total_attestations_evaluated,
                badges_count=len(badges),
                traffic_class=p.traffic_class or "STANDARD",
                is_seed_candidate=p.is_seed_candidate,
            )
        )

    entries.sort(key=lambda e: (-e.score, -e.grounding_ratio, -e.quality_score, e.node_pubkey))
    for idx, e in enumerate(entries):
        e.rank = idx + 1

    return entries[:limit]


async def get_local_node_merit(
    session: AsyncSession,
    local_pubkey: Optional[str] = None,
    now: Optional[datetime] = None,
) -> NodeMeritCard:
    """Retrieve full merit score card and badge progression for local node."""
    current_time = now or datetime.now(timezone.utc)
    if not local_pubkey:
        identity = load_or_create_node_identity()
        local_pubkey = identity.public_key_hex

    stmt = select(PeerMetric).where(PeerMetric.node_pubkey == local_pubkey)
    peer = (await session.exec(stmt)).first()

    stmt_d = select(DomainMetric).where(DomainMetric.node_pubkey == local_pubkey)
    dom_records = list((await session.exec(stmt_d)).all())

    stmt_feed = select(FeedItem)
    feed_count = len(list((await session.exec(stmt_feed)).all()))

    leaderboard = await get_leaderboard(session, category="quality", limit=1000, now=current_time)
    rank_overall = 1
    for entry in leaderboard:
        if entry.node_pubkey == local_pubkey:
            rank_overall = entry.rank
            break

    if not peer:
        badges = evaluate_node_badges(None, dom_records, feed_items_count=feed_count, now=current_time)
        return NodeMeritCard(
            node_pubkey=local_pubkey,
            node_alias="local-node",
            team_tag=None,
            tier=EpistemicTier.SPROUT.value,
            quality_score=0.85,
            uptime_ratio=1.0,
            grounding_ratio=1.0,
            concordance_factor=0.85,
            longevity_days=0.0,
            traffic_class="STANDARD",
            tokens_seeded=0,
            usd_saved_estimate=0.0,
            attestations_seeded=0,
            galileo_discoveries=0,
            rank_overall=1,
            total_nodes=max(1, len(leaderboard)),
            is_seed_candidate=False,
            unlocked_badges=badges,
            next_tier=EpistemicTier.SIFTER.value,
            next_tier_progress=min(1.0, feed_count / 100.0),
        )

    longevity = compute_longevity_days(peer.first_seen, now=current_time)
    uptime = compute_half_life_uptime(
        peer.successful_heartbeats, peer.total_heartbeats_sent, peer.last_seen, now=current_time
    )
    total_q = max(1, peer.total_citations_count)
    grounding = round(peer.grounded_citations_count / total_q, 4)
    max_exp = max([d.expertise_score for d in dom_records], default=0.05)
    badges = evaluate_node_badges(peer, dom_records, feed_items_count=feed_count, now=current_time)
    tier = determine_node_tier(
        quality_score=peer.quality_score,
        evaluations_count=peer.total_attestations_evaluated,
        grounding_ratio=grounding,
        max_domain_expertise=max_exp,
        longevity_days=longevity,
    )

    next_tier_name: Optional[str] = None
    next_prog = 1.0
    if tier == EpistemicTier.SPROUT:
        next_tier_name = EpistemicTier.SIFTER.value
        next_prog = min(1.0, max(0.0, peer.total_attestations_evaluated / 10.0))
    elif tier == EpistemicTier.SIFTER:
        next_tier_name = EpistemicTier.AUDITOR.value
        next_prog = min(1.0, max(0.0, peer.total_attestations_evaluated / 50.0))
    elif tier == EpistemicTier.AUDITOR:
        next_tier_name = EpistemicTier.SPECIALIST.value
        next_prog = min(1.0, max(0.0, max_exp / 0.80))
    elif tier == EpistemicTier.SPECIALIST:
        next_tier_name = EpistemicTier.ROOT_ANCHOR.value
        next_prog = min(1.0, max(0.0, longevity / 30.0))

    usd_saved = round((peer.tokens_seeded_count / 1_000_000.0) * 0.075, 4)

    return NodeMeritCard(
        node_pubkey=peer.node_pubkey,
        node_alias=peer.node_alias,
        team_tag=peer.team_tag,
        tier=tier.value,
        quality_score=peer.quality_score,
        uptime_ratio=uptime,
        grounding_ratio=grounding,
        concordance_factor=0.85,
        longevity_days=round(longevity, 1),
        traffic_class=peer.traffic_class or "STANDARD",
        tokens_seeded=peer.tokens_seeded_count,
        usd_saved_estimate=usd_saved,
        attestations_seeded=peer.attestations_seeded_count,
        galileo_discoveries=peer.galileo_discoveries_count,
        rank_overall=rank_overall,
        total_nodes=len(leaderboard),
        is_seed_candidate=peer.is_seed_candidate,
        unlocked_badges=badges,
        next_tier=next_tier_name,
        next_tier_progress=round(next_prog, 2),
    )


__all__ = [
    "BADGE_REGISTRY",
    "BadgeAward",
    "BadgeInfo",
    "generate_svg_badge",
    "get_leaderboard",
    "get_local_node_merit",
    "compute_half_life_uptime",
    "compute_longevity_days",
    "determine_node_tier",
    "evaluate_node_badges",
    "LeaderboardEntry",
    "NodeMeritCard",
]
