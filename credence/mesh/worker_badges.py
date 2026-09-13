"""Worker Achievement Badge Evaluation and Dynamic SVG Rendering.

Governed by Invariant 1 (500 LOC Ceiling Law) and inv-unified-merit-and-attestation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from credence.mesh.badges import generate_svg_badge
from credence.mesh.models import BADGE_REGISTRY, BadgeAward
from credence.models import WorkerRecord


def evaluate_worker_badges(worker_record: WorkerRecord) -> List[BadgeAward]:
    """Evaluate and award achievement badges for a volunteer compute worker."""
    awards: List[BadgeAward] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    # Parse already unlocked badges to preserve existing timestamps & event badges
    unlocked_ids = set()
    if worker_record.badges_unlocked_json:
        try:
            stored = json.loads(worker_record.badges_unlocked_json)
            if isinstance(stored, list):
                for item in stored:
                    if isinstance(item, dict) and "badge_id" in item:
                        unlocked_ids.add(item["badge_id"])
                        awards.append(
                            BadgeAward(
                                badge_id=item["badge_id"],
                                name=item.get("name", BADGE_REGISTRY.get(item["badge_id"], BADGE_REGISTRY["first_bounty"]).name),
                                tier=item.get("tier", "SPROUT"),
                                icon=item.get("icon", BADGE_REGISTRY.get(item["badge_id"], BADGE_REGISTRY["first_bounty"]).icon),
                                description=item.get("description", ""),
                                unlocked_at=item.get("unlocked_at", now_iso),
                            )
                        )
                    elif isinstance(item, str):
                        unlocked_ids.add(item)
                        if item in BADGE_REGISTRY:
                            info = BADGE_REGISTRY[item]
                            awards.append(
                                BadgeAward(
                                    badge_id=item,
                                    name=info.name,
                                    tier=info.tier.value,
                                    icon=info.icon,
                                    description=info.description,
                                    unlocked_at=now_iso,
                                )
                            )
        except (json.JSONDecodeError, TypeError):
            pass

    # Milestone 1: first_bounty
    if (worker_record.total_completed >= 1 or worker_record.bounties_cleared >= 1) and "first_bounty" not in unlocked_ids:
        info = BADGE_REGISTRY["first_bounty"]
        awards.append(
            BadgeAward(
                badge_id=info.badge_id,
                name=info.name,
                tier=info.tier.value,
                icon=info.icon,
                description=info.description,
                unlocked_at=now_iso,
            )
        )
        unlocked_ids.add("first_bounty")

    # Milestone 2: bounty_hunter (25+)
    if worker_record.bounties_cleared >= 25 and "bounty_hunter" not in unlocked_ids:
        info = BADGE_REGISTRY["bounty_hunter"]
        awards.append(
            BadgeAward(
                badge_id=info.badge_id,
                name=info.name,
                tier=info.tier.value,
                icon=info.icon,
                description=info.description,
                unlocked_at=now_iso,
            )
        )
        unlocked_ids.add("bounty_hunter")

    # Milestone 3: bounty_legend (100+)
    if worker_record.bounties_cleared >= 100 and "bounty_legend" not in unlocked_ids:
        info = BADGE_REGISTRY["bounty_legend"]
        awards.append(
            BadgeAward(
                badge_id=info.badge_id,
                name=info.name,
                tier=info.tier.value,
                icon=info.icon,
                description=info.description,
                unlocked_at=now_iso,
            )
        )
        unlocked_ids.add("bounty_legend")

    # Milestone 4: precision_striker (50+ grounded citations, quality >= 0.80)
    if (
        worker_record.grounded_violations_count >= 50
        and worker_record.quality_score >= 0.80
        and "precision_striker" not in unlocked_ids
    ):
        info = BADGE_REGISTRY["precision_striker"]
        awards.append(
            BadgeAward(
                badge_id=info.badge_id,
                name=info.name,
                tier=info.tier.value,
                icon=info.icon,
                description=info.description,
                unlocked_at=now_iso,
            )
        )
        unlocked_ids.add("precision_striker")

    # Milestone 5: iron_worker (500+ audits, quality >= 0.85)
    if (
        worker_record.total_completed >= 500
        and worker_record.quality_score >= 0.85
        and "iron_worker" not in unlocked_ids
    ):
        info = BADGE_REGISTRY["iron_worker"]
        awards.append(
            BadgeAward(
                badge_id=info.badge_id,
                name=info.name,
                tier=info.tier.value,
                icon=info.icon,
                description=info.description,
                unlocked_at=now_iso,
            )
        )
        unlocked_ids.add("iron_worker")

    return awards


def generate_worker_profile_badge_svg(
    worker_record: WorkerRecord,
    style: str = "shield",
    theme: str = "dark",
    custom_badge_id: Optional[str] = None,
) -> str:
    """Generate high-DPI vector SVG badge for a volunteer worker profile."""
    badge_id = custom_badge_id or "first_bounty"
    if worker_record.bounties_cleared >= 100:
        badge_id = "bounty_legend"
    elif worker_record.bounties_cleared >= 25:
        badge_id = "bounty_hunter"

    bounties = worker_record.bounties_cleared
    tokens = worker_record.tokens_donated

    score_or_val = f"{bounties} Bounties | {tokens:,} Tokens" if tokens > 0 else f"{bounties} Bounties"

    return generate_svg_badge(
        badge_id=badge_id,
        node_alias=worker_record.worker_alias,
        score_or_val=score_or_val,
        style=style,
        theme=theme,
        custom_title=f"Worker: {worker_record.worker_alias}",
        custom_icon="🛠️",
        is_unlocked=worker_record.total_completed > 0,
    )
