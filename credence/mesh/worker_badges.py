"""Worker Achievement Badge Evaluation and Dynamic SVG Rendering.

Evaluates all 10 registered worker contributor badges from BADGE_REGISTRY.
Governed by Invariant 1 (500 LOC Ceiling Law) and inv-unified-merit-and-attestation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Set

from credence.mesh.badges import generate_svg_badge
from credence.mesh.models import BADGE_REGISTRY, BadgeAward
from credence.models import WorkerRecord


def _grant_badge(badge_id: str, unlocked_ids: Set[str], awards: List[BadgeAward], now_iso: str) -> None:
    if badge_id in unlocked_ids or badge_id not in BADGE_REGISTRY:
        return
    info = BADGE_REGISTRY[badge_id]
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
    unlocked_ids.add(badge_id)


def evaluate_worker_badges(worker_record: WorkerRecord) -> List[BadgeAward]:
    """Evaluate and award all 10 registered achievement badges for a volunteer compute worker."""
    awards: List[BadgeAward] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    unlocked_ids: Set[str] = set()

    # Preserve already-unlocked badges and original timestamps
    if worker_record.badges_unlocked_json:
        try:
            stored = json.loads(worker_record.badges_unlocked_json)
            if isinstance(stored, list):
                for item in stored:
                    if isinstance(item, dict) and "badge_id" in item:
                        bid = item["badge_id"]
                        unlocked_ids.add(bid)
                        fallback = BADGE_REGISTRY.get(bid, BADGE_REGISTRY["first_bounty"])
                        awards.append(
                            BadgeAward(
                                badge_id=bid,
                                name=item.get("name", fallback.name),
                                tier=item.get("tier", fallback.tier.value),
                                icon=item.get("icon", fallback.icon),
                                description=item.get("description", fallback.description),
                                unlocked_at=item.get("unlocked_at", now_iso),
                            )
                        )
                    elif isinstance(item, str) and item in BADGE_REGISTRY:
                        _grant_badge(item, unlocked_ids, awards, now_iso)
        except (json.JSONDecodeError, TypeError):
            pass

    distinct_models: List[str] = []
    if worker_record.distinct_models_json:
        try:
            parsed_models = json.loads(worker_record.distinct_models_json)
            if isinstance(parsed_models, list):
                distinct_models = [str(m) for m in parsed_models if m]
        except (json.JSONDecodeError, TypeError):
            distinct_models = []

    zero_rejections = worker_record.grounding_rejections_count == 0

    # 1. first_bounty: First completed audit bounty
    if worker_record.total_completed >= 1 or worker_record.bounties_cleared >= 1:
        _grant_badge("first_bounty", unlocked_ids, awards, now_iso)

    # 2. speed_demon: Verified turnaround under 15 seconds
    if worker_record.fastest_turnaround_sec is not None and worker_record.fastest_turnaround_sec < 15.0:
        _grant_badge("speed_demon", unlocked_ids, awards, now_iso)

    # 3. bounty_hunter: 25+ bounties cleared
    if worker_record.bounties_cleared >= 25:
        _grant_badge("bounty_hunter", unlocked_ids, awards, now_iso)

    # 4. bounty_legend: 100+ bounties cleared
    if worker_record.bounties_cleared >= 100:
        _grant_badge("bounty_legend", unlocked_ids, awards, now_iso)

    # 5. diversity_champion: 3+ distinct canonical model families
    if len(set(distinct_models)) >= 3:
        _grant_badge("diversity_champion", unlocked_ids, awards, now_iso)

    # 6. model_pioneer: First worker to anchor a new model family on this coordinator
    if worker_record.pioneer_families_count >= 1:
        _grant_badge("model_pioneer", unlocked_ids, awards, now_iso)

    # 7. night_owl: Audited during off-peak UTC window (00:00 - 06:00 UTC)
    if worker_record.night_owl_completed_count >= 1:
        _grant_badge("night_owl", unlocked_ids, awards, now_iso)

    # 8. weekend_warrior: 10+ audits completed on UTC Saturday/Sunday
    if worker_record.weekend_completed_count >= 10:
        _grant_badge("weekend_warrior", unlocked_ids, awards, now_iso)

    # 9. precision_striker: 50+ grounded citations, zero rejections, quality >= 0.80
    if worker_record.grounded_violations_count >= 50 and zero_rejections and worker_record.quality_score >= 0.80:
        _grant_badge("precision_striker", unlocked_ids, awards, now_iso)

    # 10. iron_worker: 500+ completed audits, zero rejections, quality >= 0.85
    if worker_record.total_completed >= 500 and zero_rejections and worker_record.quality_score >= 0.85:
        _grant_badge("iron_worker", unlocked_ids, awards, now_iso)

    return awards


def generate_worker_profile_badge_svg(
    worker_record: WorkerRecord,
    style: str = "shield",
    theme: str = "dark",
    custom_badge_id: Optional[str] = None,
) -> str:
    """Generate high-DPI vector SVG badge for a volunteer worker profile."""
    badge_id = custom_badge_id or "first_bounty"
    if worker_record.total_completed >= 500 and worker_record.grounding_rejections_count == 0:
        badge_id = "iron_worker"
    elif worker_record.bounties_cleared >= 100:
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
