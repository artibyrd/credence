"""SVG Badge and Visual Merit Rendering for P2P Mesh Nodes."""

from __future__ import annotations

import html
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from credence.mesh.models import BADGE_REGISTRY, BadgeAward
from credence.models import DomainMetric, EpistemicTier, PeerMetric

# Extensible Canonical Theming Architecture (Default: Credence Cyber Dark)
BADGE_THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg_top": "#0d121f",
        "bg_bottom": "#07090e",
        "border": "rgba(56, 189, 248, 0.35)",
        "text": "#f8fafc",
        "text_dim": "#94a3b8",
    },
    "midnight": {
        "bg_top": "#1e293b",
        "bg_bottom": "#0f172a",
        "border": "rgba(148, 163, 184, 0.3)",
        "text": "#f8fafc",
        "text_dim": "#cbd5e1",
    },
    "light": {
        "bg_top": "#ffffff",
        "bg_bottom": "#f1f5f9",
        "border": "rgba(100, 116, 139, 0.3)",
        "text": "#0f172a",
        "text_dim": "#475569",
    },
}

BADGE_ACCENTS: Dict[str, Tuple[str, str, str]] = {
    "emerald": ("#34d399", "#059669", "rgba(52, 211, 153, 0.45)"),
    "violet": ("#c084fc", "#7c3aed", "rgba(192, 132, 252, 0.45)"),
    "amber": ("#fbbf24", "#d97706", "rgba(251, 191, 36, 0.45)"),
    "cyan": ("#38bdf8", "#0284c7", "rgba(56, 189, 248, 0.45)"),
    "rose": ("#f87171", "#dc2626", "rgba(248, 113, 113, 0.45)"),
    "slate": ("#94a3b8", "#475569", "rgba(148, 163, 184, 0.45)"),
}


def _get_badge_palette(badge_id: str) -> Tuple[str, str, str]:
    """Resolve accent start, accent end, and border glow for a given badge or tier identifier."""
    b_id = badge_id.lower()
    if any(k in b_id for k in ("century", "root", "seed", "sybil", "pristine")):
        return BADGE_ACCENTS["emerald"]
    if any(k in b_id for k in ("galileo", "specialist", "astroturf")):
        return BADGE_ACCENTS["violet"]
    if any(k in b_id for k in ("relay", "philanthropic", "cadence", "moderate", "attention")):
        return BADGE_ACCENTS["amber"]
    if any(k in b_id for k in ("flagged", "deceptive", "modified")):
        return BADGE_ACCENTS["rose"]
    if any(k in b_id for k in ("sprout", "neutral")):
        return BADGE_ACCENTS["slate"]
    return BADGE_ACCENTS["cyan"]


def generate_svg_badge(
    badge_id: str,
    node_alias: str = "credence-node",
    score_or_val: Any = "VERIFIED",
    style: str = "shield",
    theme: str = "dark",
    custom_title: Optional[str] = None,
    custom_icon: Optional[str] = None,
    is_unlocked: Optional[bool] = None,
) -> str:
    """Generate a vector SVG badge with Cyber Dark styling tokens and dynamic width arithmetic."""
    badge = BADGE_REGISTRY.get(badge_id)
    raw_title = (
        custom_title if custom_title is not None else (badge.name if badge else badge_id.replace("_", " ").title())
    )
    raw_icon = custom_icon if custom_icon is not None else (badge.icon if badge else "🛡️")
    raw_val = str(score_or_val)

    unlocked = (
        is_unlocked
        if is_unlocked is not None
        else ("LOCKED" not in raw_val.upper() and "UNEARNED" not in raw_val.upper())
    )

    # Safe XML character escaping
    title_escaped = html.escape(raw_title)
    node_escaped = html.escape(node_alias)
    val_escaped = html.escape(raw_val)
    icon_escaped = html.escape(raw_icon)

    theme_cfg = BADGE_THEMES.get(theme.lower(), BADGE_THEMES["dark"])
    if unlocked:
        accent_start, accent_end, accent_border = _get_badge_palette(badge_id)
        border_color = accent_border if theme.lower() == "dark" else theme_cfg["border"]
    else:
        accent_start, accent_end = "#475569", "#334155"
        border_color = "rgba(148, 163, 184, 0.3)"

    # Modern Shield vector layout (Crisp dual-tone container with precise text bounding)
    char_w_title = 7.2
    char_w_val = 7.8
    w_title_text = max(32, int(len(raw_title) * char_w_title))
    w_val_text = max(24, int(len(raw_val) * char_w_val))

    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", f"{badge_id}-shield-{theme}").lower()

    w_left = w_title_text + 32  # 10px padding + 16px icon + 6px gap
    w_val = w_val_text + 20  # 10px left/right padding
    total_w = w_left + w_val

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="28" '
        f'viewBox="0 0 {total_w} 28" fill="none" role="img" '
        f'aria-label="{node_escaped} - {title_escaped}: {val_escaped}">\n'
        f"  <title>{node_escaped} - {title_escaped}: {val_escaped}</title>\n"
        f"  <defs>\n"
        f'    <linearGradient id="bg-left-{slug}" x1="0" y1="0" x2="0" y2="28" gradientUnits="userSpaceOnUse">\n'
        f'      <stop offset="0%" stop-color="{theme_cfg["bg_top"]}"/>\n'
        f'      <stop offset="100%" stop-color="{theme_cfg["bg_bottom"]}"/>\n'
        f"    </linearGradient>\n"
        f'    <linearGradient id="bg-right-{slug}" x1="0" y1="0" x2="0" y2="28" gradientUnits="userSpaceOnUse">\n'
        f'      <stop offset="0%" stop-color="{accent_start}"/>\n'
        f'      <stop offset="100%" stop-color="{accent_end}"/>\n'
        f"    </linearGradient>\n"
        f'    <clipPath id="clip-{slug}">\n'
        f'      <rect width="{total_w}" height="28" rx="6" fill="#fff"/>\n'
        f"    </clipPath>\n"
        f"  </defs>\n"
        f'  <g clip-path="url(#clip-{slug})">\n'
        f'    <rect width="{w_left}" height="28" fill="url(#bg-left-{slug})"/>\n'
        f'    <rect x="{w_left}" width="{w_val}" height="28" fill="url(#bg-right-{slug})"/>\n'
        f'    <rect width="{total_w}" height="28" rx="6" fill="none" stroke="{border_color}" stroke-width="1"/>\n'
        f"  </g>\n"
        f'  <g fill="{theme_cfg["text"]}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11" font-weight="600" text-rendering="geometricPrecision">\n'
        f'    <text x="10" y="18">{icon_escaped} {title_escaped}</text>\n'
        f"  </g>\n"
        f'  <g fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11" font-weight="700" text-anchor="middle" text-rendering="geometricPrecision">\n'
        f'    <text x="{w_left + (w_val / 2):.1f}" y="18">{val_escaped}</text>\n'
        f"  </g>\n"
        f"</svg>"
    )


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
    if max_domain_expertise >= 0.80 and quality_score >= 0.75 and evaluations_count >= 50:
        return EpistemicTier.SPECIALIST
    if quality_score >= 0.70 and evaluations_count >= 50 and grounding_ratio >= 0.85:
        return EpistemicTier.AUDITOR
    if evaluations_count >= 10 and quality_score >= 0.60 and grounding_ratio >= 0.70:
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
    uptime = compute_half_life_uptime(
        peer_record.successful_heartbeats,
        peer_record.total_heartbeats_sent,
        peer_record.last_seen,
        now=current_time,
    )
    total_q = max(1, peer_record.total_citations_count)
    grounding_ratio = peer_record.grounded_citations_count / total_q
    total_evals = peer_record.total_attestations_evaluated + feed_items_count

    # Tier 1 (SPROUT) - Welcome & First Ingestion
    if total_evals >= 5:
        awards.append(
            BadgeAward(
                badge_id="first_attestation",
                name=BADGE_REGISTRY["first_attestation"].name,
                tier=BADGE_REGISTRY["first_attestation"].tier.value,
                icon=BADGE_REGISTRY["first_attestation"].icon,
                description=BADGE_REGISTRY["first_attestation"].description,
                unlocked_at=now_iso,
            )
        )

    # Tier 2 (SIFTER) - Operational Cadence & Volume
    if total_evals >= 100:
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

    if longevity >= 7.0 and uptime >= 0.98:
        awards.append(
            BadgeAward(
                badge_id="cadence_keeper",
                name=BADGE_REGISTRY["cadence_keeper"].name,
                tier=BADGE_REGISTRY["cadence_keeper"].tier.value,
                icon=BADGE_REGISTRY["cadence_keeper"].icon,
                description=BADGE_REGISTRY["cadence_keeper"].description,
                unlocked_at=now_iso,
            )
        )

    # Tier 3 (AUDITOR) - Epistemic Rigor & Swarm Philanthropy
    if peer_record.quality_score >= 0.70 and total_evals >= 100 and grounding_ratio >= 0.95:
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

    # Tier 4 (SPECIALIST) - Domain Authority & Scientific Discovery
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

    # Tier 5 (ROOT_ANCHOR) - Prestige Sentinel & Sovereign Foundation
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

    if (
        longevity >= 100.0
        and peer_record.quality_score >= 0.90
        and grounding_ratio >= 0.98
        and getattr(peer_record, "has_valid_catalog_hashes", True)
    ):
        awards.append(
            BadgeAward(
                badge_id="century_anchor",
                name=BADGE_REGISTRY["century_anchor"].name,
                tier=BADGE_REGISTRY["century_anchor"].tier.value,
                icon=BADGE_REGISTRY["century_anchor"].icon,
                description=BADGE_REGISTRY["century_anchor"].description,
                unlocked_at=now_iso,
            )
        )

    return awards


__all__ = [
    "BADGE_ACCENTS",
    "BADGE_THEMES",
    "compute_half_life_uptime",
    "compute_longevity_days",
    "determine_node_tier",
    "evaluate_node_badges",
    "generate_svg_badge",
]
