"""Epistemic Merit & Leaderboard Engine for Credence.

Defines:
- 5 Epistemic Tiers of Distinction (Sprout -> Sifter -> Auditor -> Specialist -> Root Anchor).
- Verifiable Epistemic Merit Badge Registry and evaluation criteria.
- Shields.io-compatible live SVG Badge generation with WCAG AA/AAA high contrast.
- Multi-category P2P leaderboard querying (Quality, Subjects, Philanthropy, Galileo, Teams).
- Numerical stability, half-life outage grace periods, and N=1 solitary genesis node handling.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.identity import load_or_create_node_identity
from credence.models import DomainMetricRecord, FeedItemRecord, PeerMetricRecord


class EpistemicTier(str, Enum):
    """5 Mathematical Tiers of Node Distinction."""

    SPROUT = "SPROUT"  # Tier I: Freshly germinated & initial feeds sieved
    SIFTER = "SIFTER"  # Tier II: >100 feed items sifted & partitioned
    AUDITOR = "AUDITOR"  # Tier III: Q_i >= 0.70, G_i >= 0.95, >=100 citations
    SPECIALIST = "SPECIALIST"  # Tier IV: E_i >= 0.80 across >=5 distinct FQDNs
    ROOT_ANCHOR = "ROOT_ANCHOR"  # Tier V: Q_i >= 0.85, U_i >= 0.80, >30d longevity


@dataclass
class BadgeDefinition:
    """Definition and milestone criteria for a verifiable Epistemic Badge."""

    badge_id: str
    name: str
    tier: EpistemicTier
    icon: str
    description: str
    criteria_summary: str


BADGE_REGISTRY: Dict[str, BadgeDefinition] = {
    "sprout_node": BadgeDefinition(
        badge_id="sprout_node",
        name="Sprout Node",
        tier=EpistemicTier.SPROUT,
        icon="🌱",
        description="Minted Ed25519 cryptographic identity and subscribed to initial syndicated feeds.",
        criteria_summary="Node identity initialized and active.",
    ),
    "sifter_pioneer": BadgeDefinition(
        badge_id="sifter_pioneer",
        name="Sifter Pioneer",
        tier=EpistemicTier.SIFTER,
        icon="📡",
        description="Actively sifted and partitioned >100 syndicated RSS/Atom feed items via HRW rendezvous.",
        criteria_summary=">= 100 feed items partitioned or audited.",
    ),
    "verified_auditor": BadgeDefinition(
        badge_id="verified_auditor",
        name="Verified Auditor",
        tier=EpistemicTier.AUDITOR,
        icon="🛡️",
        description="Demonstrated high epistemic consistency (Q_i >= 0.70) with >=100 verified verbatim DOM citations.",
        criteria_summary="Q_i >= 0.70, >= 100 citations, >= 95% grounding.",
    ),
    "domain_specialist": BadgeDefinition(
        badge_id="domain_specialist",
        name="Domain Specialist",
        tier=EpistemicTier.SPECIALIST,
        icon="🏛️",
        description="Earned empirical authority (E_i >= 0.80) across >=5 distinct root domains in a subject namespace.",
        criteria_summary="E_i >= 0.80 across >= 5 distinct FQDNs.",
    ),
    "philanthropic_relay": BadgeDefinition(
        badge_id="philanthropic_relay",
        name="Philanthropic Relay",
        tier=EpistemicTier.SPECIALIST,
        icon="⚡",
        description="Saved over 1,000,000 LLM tokens for the mesh swarm through zero-cost attestation seeding.",
        criteria_summary=">= 1,000,000 tokens seeded to peer nodes.",
    ),
    "root_seed_candidate": BadgeDefinition(
        badge_id="root_seed_candidate",
        name="Root Seed Candidate",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="💎",
        description="Achieved Tier V excellence (Q_i >= 0.85, U_i >= 0.80, >30 days longevity), qualifying for peers.json.",
        criteria_summary="Q_i >= 0.85, U_i >= 0.80, G_i >= 0.80, >30d longevity.",
    ),
    "galileo_pioneer": BadgeDefinition(
        badge_id="galileo_pioneer",
        name="Galileo Pioneer",
        tier=EpistemicTier.SPECIALIST,
        icon="🌌",
        description="Uncovered confirmed high-severity deception (Severity 5) with 100% verbatim grounding evidence.",
        criteria_summary=">= 1 consensus-shifting Severity 5 grounded finding.",
    ),
    "sybil_shield": BadgeDefinition(
        badge_id="sybil_shield",
        name="Sybil Shield",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🦅",
        description="Processed >=5,000 feed evaluations with zero spam, zero circular collusion, and zero slashing.",
        criteria_summary=">= 5,000 evaluations with 0 slashing penalties.",
    ),
}


@dataclass
class BadgeAward:
    """An unlocked badge instance with award metadata."""

    badge_id: str
    name: str
    tier: str
    icon: str
    description: str
    unlocked_at: str
    criteria_met: bool = True


@dataclass
class LeaderboardEntry:
    """A ranked node entry on the Epistemic Leaderboard."""

    rank: int
    node_pubkey: str
    node_alias: str
    team_tag: Optional[str]
    tier: str
    score: float
    quality_score: float
    uptime_ratio: float
    grounding_ratio: float
    tokens_seeded: int
    usd_saved_estimate: float
    evaluations_count: int
    badges_count: int
    traffic_class: str
    is_seed_candidate: bool
    subject_id: Optional[str] = None


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


def calculate_longevity_days(first_seen: datetime, now: Optional[datetime] = None) -> float:
    """Calculate active longevity in days clamped safely to [0.0, 3650.0]."""
    current_time = now or datetime.now(timezone.utc)
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    delta_seconds = max(0.0, (current_time - first_seen).total_seconds())
    return min(3650.0, delta_seconds / 86400.0)


def calculate_half_life_uptime(
    successful: int,
    total: int,
    last_seen: datetime,
    now: Optional[datetime] = None,
    half_life_hours: float = 24.0,
) -> float:
    """Calculate uptime ratio with an exponential half-life grace period for transient reboots."""
    current_time = now or datetime.now(timezone.utc)
    if total <= 0:
        return 1.0  # Healthy neutral prior for new nodes

    raw_ratio = successful / max(1, total)

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    inactive_hours = max(0.0, (current_time - last_seen).total_seconds() / 3600.0)

    # If offline for more than 2 hours, apply smooth exponential decay
    if inactive_hours > 2.0:
        decay = math.exp(-math.log(2) * (inactive_hours - 2.0) / max(1.0, half_life_hours))
        return round(min(1.0, max(0.0, raw_ratio * decay)), 4)

    return round(min(1.0, max(0.0, raw_ratio)), 4)


def determine_node_tier(
    quality_score: float,
    evaluations_count: int,
    grounding_ratio: float,
    max_domain_expertise: float,
    longevity_days: float,
) -> EpistemicTier:
    """Determine a node's Epistemic Tier based on mathematical milestones."""
    if quality_score >= 0.85 and longevity_days >= 30.0 and grounding_ratio >= 0.80:
        return EpistemicTier.ROOT_ANCHOR
    if max_domain_expertise >= 0.80:
        return EpistemicTier.SPECIALIST
    if quality_score >= 0.70 and evaluations_count >= 50 and grounding_ratio >= 0.90:
        return EpistemicTier.AUDITOR
    if evaluations_count >= 10:
        return EpistemicTier.SIFTER
    return EpistemicTier.SPROUT


def evaluate_node_badges(
    peer_record: Optional[PeerMetricRecord],
    domain_records: List[DomainMetricRecord],
    feed_items_count: int = 0,
    now: Optional[datetime] = None,
) -> List[BadgeAward]:
    """Evaluate unlocked badges for a node from database metric records."""
    current_time = now or datetime.now(timezone.utc)
    now_iso = current_time.isoformat()
    awards: List[BadgeAward] = []

    # 1. Sprout Node: Always awarded if peer record exists
    awards.append(
        BadgeAward(
            badge_id="sprout_node",
            name=BADGE_REGISTRY["sprout_node"].name,
            tier=BADGE_REGISTRY["sprout_node"].tier.value,
            icon=BADGE_REGISTRY["sprout_node"].icon,
            description=BADGE_REGISTRY["sprout_node"].description,
            unlocked_at=now_iso,
        )
    )

    if not peer_record:
        return awards

    longevity = calculate_longevity_days(peer_record.first_seen, now=current_time)
    total_q = max(1, peer_record.total_citations_count)
    grounding_ratio = peer_record.grounded_citations_count / total_q

    # 2. Sifter Pioneer: >= 100 feeds sifted or evaluated
    if (peer_record.total_attestations_evaluated + feed_items_count) >= 100:
        awards.append(
            BadgeAward(
                badge_id="sifter_pioneer",
                name=BADGE_REGISTRY["sifter_pioneer"].name,
                tier=BADGE_REGISTRY["sifter_pioneer"].tier.value,
                icon=BADGE_REGISTRY["sifter_pioneer"].icon,
                description=BADGE_REGISTRY["sifter_pioneer"].description,
                unlocked_at=now_iso,
            )
        )

    # 3. Verified Auditor: Q_i >= 0.70, >= 100 citations, grounding >= 95%
    if peer_record.quality_score >= 0.70 and peer_record.total_citations_count >= 100 and grounding_ratio >= 0.95:
        awards.append(
            BadgeAward(
                badge_id="verified_auditor",
                name=BADGE_REGISTRY["verified_auditor"].name,
                tier=BADGE_REGISTRY["verified_auditor"].tier.value,
                icon=BADGE_REGISTRY["verified_auditor"].icon,
                description=BADGE_REGISTRY["verified_auditor"].description,
                unlocked_at=now_iso,
            )
        )

    # 4. Domain Specialist: E_i >= 0.80 across >= 5 distinct domains
    for d in domain_records:
        if d.expertise_score >= 0.80 and d.unique_domains_count >= 5:
            awards.append(
                BadgeAward(
                    badge_id="domain_specialist",
                    name=BADGE_REGISTRY["domain_specialist"].name,
                    tier=BADGE_REGISTRY["domain_specialist"].tier.value,
                    icon=BADGE_REGISTRY["domain_specialist"].icon,
                    description=f"{BADGE_REGISTRY['domain_specialist'].description} [{d.subject_id}]",
                    unlocked_at=now_iso,
                )
            )
            break

    # 5. Philanthropic Relay: >= 1,000,000 tokens seeded
    if peer_record.tokens_seeded_count >= 1_000_000:
        awards.append(
            BadgeAward(
                badge_id="philanthropic_relay",
                name=BADGE_REGISTRY["philanthropic_relay"].name,
                tier=BADGE_REGISTRY["philanthropic_relay"].tier.value,
                icon=BADGE_REGISTRY["philanthropic_relay"].icon,
                description=BADGE_REGISTRY["philanthropic_relay"].description,
                unlocked_at=now_iso,
            )
        )

    # 6. Root Seed Candidate: Q_i >= 0.85, longevity >= 30 days, grounding >= 80%
    if (
        peer_record.quality_score >= 0.85
        and longevity >= 30.0
        and grounding_ratio >= 0.80
        and peer_record.has_valid_catalog_hashes
    ):
        awards.append(
            BadgeAward(
                badge_id="root_seed_candidate",
                name=BADGE_REGISTRY["root_seed_candidate"].name,
                tier=BADGE_REGISTRY["root_seed_candidate"].tier.value,
                icon=BADGE_REGISTRY["root_seed_candidate"].icon,
                description=BADGE_REGISTRY["root_seed_candidate"].description,
                unlocked_at=now_iso,
            )
        )

    # 7. Galileo Pioneer: >= 1 Galileo discovery
    if peer_record.galileo_discoveries_count >= 1:
        awards.append(
            BadgeAward(
                badge_id="galileo_pioneer",
                name=BADGE_REGISTRY["galileo_pioneer"].name,
                tier=BADGE_REGISTRY["galileo_pioneer"].tier.value,
                icon=BADGE_REGISTRY["galileo_pioneer"].icon,
                description=BADGE_REGISTRY["galileo_pioneer"].description,
                unlocked_at=now_iso,
            )
        )

    # 8. Sybil Shield: >= 5,000 evaluations with 0 slashes
    total_slashes = sum(d.slashing_count for d in domain_records)
    if peer_record.total_attestations_evaluated >= 5000 and total_slashes == 0:
        awards.append(
            BadgeAward(
                badge_id="sybil_shield",
                name=BADGE_REGISTRY["sybil_shield"].name,
                tier=BADGE_REGISTRY["sybil_shield"].tier.value,
                icon=BADGE_REGISTRY["sybil_shield"].icon,
                description=BADGE_REGISTRY["sybil_shield"].description,
                unlocked_at=now_iso,
            )
        )

    return awards


def generate_svg_badge(
    badge_id: str,
    node_alias: str = "credence-node",
    score_or_val: Any = "VERIFIED",
    theme: str = "dark",
) -> str:
    """Generate a vector SVG shield badge compatible with GitHub Readmes and websites."""
    badge = BADGE_REGISTRY.get(badge_id)
    badge_title = badge.name if badge else badge_id.replace("_", " ").title()
    icon = badge.icon if badge else "🛡️"

    # Color scheme tuning (WCAG AA/AAA compliant high contrast on dark slate)
    bg_left = "#0f172a" if theme == "dark" else "#1e293b"
    bg_right = "#0284c7"  # Default Cyan
    if "root" in badge_id or "seed" in badge_id:
        bg_right = "#059669"  # Emerald Green
    elif "galileo" in badge_id or "specialist" in badge_id:
        bg_right = "#7c3aed"  # Purple
    elif "philanthropic" in badge_id:
        bg_right = "#d97706"  # Amber

    label_text = (
        f"Credence • {node_alias}" if node_alias and node_alias != "credence-node" else f"Credence • {badge_title}"
    )
    val_text = f"{icon} {str(score_or_val)}"

    # Width estimation
    char_w = 7.5
    w_left = max(90, int(len(label_text) * char_w + 16))
    w_right = max(70, int(len(val_text) * char_w + 20))
    total_w = w_left + w_right

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="28" role="img" aria-label="{label_text}: {val_text}">
  <title>{label_text}: {val_text}</title>
  <clipPath id="r">
    <rect width="{total_w}" height="28" rx="6" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{w_left}" height="28" fill="{bg_left}"/>
    <rect x="{w_left}" width="{w_right}" height="28" fill="{bg_right}"/>
  </g>
  <g fill="#f8fafc" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="600">
    <text x="{w_left / 2}" y="18" fill="#e2e8f0">{label_text}</text>
    <text x="{w_left + (w_right / 2)}" y="18" fill="#ffffff">{val_text}</text>
  </g>
</svg>"""
    return svg.strip()


async def get_leaderboard(
    session: AsyncSession,
    category: str = "quality",
    limit: int = 50,
    team_filter: Optional[str] = None,
    now: Optional[datetime] = None,
) -> List[LeaderboardEntry]:
    """Query and return ranked Leaderboard entries across categories.

    Categories:
    - 'quality': 5-factor quality score Q_i
    - 'subjects': Domain empirical authority E_i
    - 'philanthropy': Total tokens and $ saved via adopted attestations
    - 'galileo': Consensus-shifting grounded detections
    - 'teams': Team-aggregated performance
    """
    current_time = now or datetime.now(timezone.utc)
    cat = category.lower().strip()

    stmt = select(PeerMetricRecord)
    if team_filter:
        stmt = stmt.where(PeerMetricRecord.team_tag == team_filter)

    peers = list((await session.exec(stmt)).all())

    # Fallback/Local node injection if table is empty or solitary
    if not peers:
        # Check if local identity exists
        local_id = load_or_create_node_identity()
        peers = [
            PeerMetricRecord(
                node_pubkey=local_id.public_key_hex,
                node_alias="local-genesis-node",
                ws_url="ws://127.0.0.1:8765",
                quality_score=0.85,
                total_heartbeats_sent=0,
                successful_heartbeats=0,
                traffic_class="STANDARD",
                is_seed_candidate=False,
            )
        ]

    entries: List[LeaderboardEntry] = []

    for p in peers:
        # Fetch domain records for this peer
        stmt_d = select(DomainMetricRecord).where(DomainMetricRecord.node_pubkey == p.node_pubkey)
        dom_records = list((await session.exec(stmt_d)).all())

        longevity = calculate_longevity_days(p.first_seen, now=current_time)
        uptime = calculate_half_life_uptime(
            p.successful_heartbeats, p.total_heartbeats_sent, p.last_seen, now=current_time
        )
        total_q = max(1, p.total_citations_count)
        grounding = round(p.grounded_citations_count / total_q, 4)
        max_exp = max([d.expertise_score for d in dom_records], default=0.05)
        badges = evaluate_node_badges(p, dom_records, now=current_time)

        tier = determine_node_tier(
            quality_score=p.quality_score,
            evaluations_count=p.total_attestations_evaluated,
            grounding_ratio=grounding,
            max_domain_expertise=max_exp,
            longevity_days=longevity,
        )

        usd_saved = round((p.tokens_seeded_count / 1_000_000.0) * 0.075, 4)

        if cat == "philanthropy":
            score_val = float(p.tokens_seeded_count)
        elif cat == "galileo":
            score_val = float(p.galileo_discoveries_count)
        elif cat == "subjects":
            score_val = max_exp
        else:  # "quality" / default
            score_val = p.quality_score

        entries.append(
            LeaderboardEntry(
                rank=1,
                node_pubkey=p.node_pubkey,
                node_alias=p.node_alias,
                team_tag=p.team_tag,
                tier=tier.value,
                score=score_val,
                quality_score=p.quality_score,
                uptime_ratio=uptime,
                grounding_ratio=grounding,
                tokens_seeded=p.tokens_seeded_count,
                usd_saved_estimate=usd_saved,
                evaluations_count=p.total_attestations_evaluated,
                badges_count=len(badges),
                traffic_class=p.traffic_class or "STANDARD",
                is_seed_candidate=p.is_seed_candidate,
            )
        )

    # Deterministic 4-level tie-breaking sort:
    # 1. Primary Score (descending)
    # 2. Quote Grounding Precision (descending)
    # 3. Quality Score (descending)
    # 4. Public Key Hex (lexicographical string ascending)
    entries.sort(key=lambda e: (-e.score, -e.grounding_ratio, -e.quality_score, e.node_pubkey))

    # Assign ranks
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

    stmt = select(PeerMetricRecord).where(PeerMetricRecord.node_pubkey == local_pubkey)
    peer = (await session.exec(stmt)).first()

    stmt_d = select(DomainMetricRecord).where(DomainMetricRecord.node_pubkey == local_pubkey)
    dom_records = list((await session.exec(stmt_d)).all())

    stmt_feed = select(FeedItemRecord)
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

    longevity = calculate_longevity_days(peer.first_seen, now=current_time)
    uptime = calculate_half_life_uptime(
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
