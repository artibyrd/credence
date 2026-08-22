"""SVG Badge and Visual Merit Rendering for P2P Mesh Nodes."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, List, Optional

from credence.mesh.models import BADGE_REGISTRY, BadgeAward
from credence.models import DomainMetric, EpistemicTier, PeerMetric


def compute_longevity_days(first_seen: datetime, now: Optional[datetime] = None) -> float:
    """Calculate active longevity in days clamped safely to [0.0, 3650.0]."""
    current_time = now or datetime.now(timezone.utc)
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    delta_seconds = max(0.0, (current_time - first_seen).total_seconds())
    return min(3650.0, delta_seconds / 86400.0)


def compute_half_life_uptime(
    successful: int,
    total: int,
    last_seen: datetime,
    now: Optional[datetime] = None,
    half_life_hours: float = 24.0,
) -> float:
    """Calculate uptime ratio with an exponential half-life grace period for transient reboots."""
    current_time = now or datetime.now(timezone.utc)
    if total <= 0:
        return 1.0

    raw_ratio = successful / max(1, total)

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    inactive_hours = max(0.0, (current_time - last_seen).total_seconds() / 3600.0)

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
    peer_record: Optional[PeerMetric],
    domain_records: List[DomainMetric],
    feed_items_count: int = 0,
    now: Optional[datetime] = None,
) -> List[BadgeAward]:
    """Evaluate unlocked badges for a node from database metric records."""
    current_time = now or datetime.now(timezone.utc)
    now_iso = current_time.isoformat()
    awards: List[BadgeAward] = []

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

    longevity = compute_longevity_days(peer_record.first_seen, now=current_time)
    total_q = max(1, peer_record.total_citations_count)
    grounding_ratio = peer_record.grounded_citations_count / total_q

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

    if (
        peer_record.quality_score >= 0.85
        and longevity >= 30.0
        and grounding_ratio >= 0.80
        and getattr(peer_record, "has_valid_catalog_hashes", True)
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
    bg_left = "#0f172a" if theme == "dark" else "#1e293b"
    bg_right = "#0284c7"
    if "root" in badge_id or "seed" in badge_id:
        bg_right = "#059669"
    elif "galileo" in badge_id or "specialist" in badge_id:
        bg_right = "#7c3aed"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="220" height="28" role="img" aria-label="{node_alias} - {badge_title}: {score_or_val}">
  <title>{node_alias} - {badge_title}</title>
  <g shape-rendering="crispEdges">
    <rect width="130" height="28" fill="{bg_left}"/>
    <rect x="130" width="90" height="28" fill="{bg_right}"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text x="650" y="180" transform="scale(.1)" fill="#fff" textLength="1100">{icon} {badge_title}</text>
    <text x="1750" y="180" transform="scale(.1)" font-weight="bold" fill="#fff" textLength="700">{score_or_val}</text>
  </g>
</svg>"""
