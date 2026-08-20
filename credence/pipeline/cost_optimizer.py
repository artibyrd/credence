"""Autonomous Cost Profile Optimizer & Trend Recommendation Engine.

Analyzes 24-hour and 7-day rolling usage metrics (token burn rate, throttle events,
circuit breaker trips, sifter queue backlog, and P2P mesh adoption) to recommend
optimal cost profile upgrades or downgrades with 1-click execution.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from credence.config import COST_PROFILES, CostProfile, settings

logger = logging.getLogger("credence.pipeline.cost_optimizer")


class CostRecommendation(BaseModel):
    """Structured cost optimization recommendation."""

    current_profile: CostProfile
    recommended_profile: CostProfile
    action: str = Field(..., description="'UPGRADE', 'DOWNGRADE', or 'OPTIMAL'")
    estimated_monthly_delta_usd: float = Field(default=0.0, description="Monthly cost increase (+) or savings (-)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    rationale: str
    key_metrics: Dict[str, Any] = Field(default_factory=dict)


def evaluate_cost_profile_recommendation(
    current_profile: Optional[CostProfile] = None,
    trips_last_72h: int = 0,
    hours_throttled_last_72h: float = 0.0,
    sifter_deferred_count: int = 0,
    long_article_ratio: float = 0.0,
    avg_daily_spend_usd: float = 0.0,
    mesh_adoption_ratio: float = 0.0,
) -> CostRecommendation:
    """Evaluate trending usage metrics and calculate optimal cost profile recommendation."""
    active_profile = current_profile or settings.CREDENCE_PROFILE
    curr_cfg = COST_PROFILES.get(active_profile, COST_PROFILES[CostProfile.ECONOMY])
    max_daily = curr_cfg.max_daily_budget_usd

    # 1. Check Upgrade Triggers
    if trips_last_72h >= 3 or hours_throttled_last_72h >= 4.0 or sifter_deferred_count >= 20:
        if active_profile in (CostProfile.OFFLINE, CostProfile.FREE):
            target = CostProfile.ECONOMY
            delta = COST_PROFILES[target].max_daily_budget_usd * 30.0
            return CostRecommendation(
                current_profile=active_profile,
                recommended_profile=target,
                action="UPGRADE",
                estimated_monthly_delta_usd=round(delta, 2),
                confidence=0.95,
                rationale=(
                    f"Your node experienced {trips_last_72h} throttle trips and {sifter_deferred_count} deferred articles. "
                    f"Upgrading to ECONOMY unlocks Gemini 3.7 Flash reasoning with thinking tokens for up to $4.50/mo."
                ),
                key_metrics={
                    "trips_last_72h": trips_last_72h,
                    "hours_throttled": hours_throttled_last_72h,
                    "sifter_deferred": sifter_deferred_count,
                },
            )
        elif active_profile == CostProfile.ECONOMY:
            target = CostProfile.BALANCED
            delta = (COST_PROFILES[target].max_daily_budget_usd - curr_cfg.max_daily_budget_usd) * 30.0
            return CostRecommendation(
                current_profile=active_profile,
                recommended_profile=target,
                action="UPGRADE",
                estimated_monthly_delta_usd=round(delta, 2),
                confidence=0.90,
                rationale=(
                    f"Your node reached budget saturation ({trips_last_72h} throttle events). "
                    f"Upgrading to BALANCED doubles token throughput to 100k/hr and raises thinking budget to 1024 tokens."
                ),
                key_metrics={
                    "trips_last_72h": trips_last_72h,
                    "hours_throttled": hours_throttled_last_72h,
                    "sifter_deferred": sifter_deferred_count,
                },
            )
        elif active_profile == CostProfile.BALANCED and (long_article_ratio >= 0.30 or sifter_deferred_count >= 50):
            target = CostProfile.ULTRA
            delta = (COST_PROFILES[target].max_daily_budget_usd - curr_cfg.max_daily_budget_usd) * 30.0
            return CostRecommendation(
                current_profile=active_profile,
                recommended_profile=target,
                action="UPGRADE",
                estimated_monthly_delta_usd=round(delta, 2),
                confidence=0.85,
                rationale=(
                    f"Heavy investigative workload detected ({int(long_article_ratio * 100)}% long-form articles). "
                    f"Upgrading to ULTRA enables 4k-16k deep thinking and Gemini 1.5 Pro escalation."
                ),
                key_metrics={
                    "long_article_ratio": long_article_ratio,
                    "sifter_deferred": sifter_deferred_count,
                },
            )

    # 2. Check Downgrade Triggers (Cost Optimization / Waste Elimination)
    if trips_last_72h == 0 and hours_throttled_last_72h == 0.0:
        if active_profile == CostProfile.ULTRA and avg_daily_spend_usd < (max_daily * 0.15):
            target = CostProfile.BALANCED
            savings = (curr_cfg.max_daily_budget_usd - COST_PROFILES[target].max_daily_budget_usd) * 30.0
            return CostRecommendation(
                current_profile=active_profile,
                recommended_profile=target,
                action="DOWNGRADE",
                estimated_monthly_delta_usd=-round(savings, 2),
                confidence=0.92,
                rationale=(
                    f"Your node utilized only ${avg_daily_spend_usd:.2f}/day of the $5.00 ceiling with 0 throttles. "
                    f"Downgrading to BALANCED saves up to ${savings:.2f}/month with zero throughput loss."
                ),
                key_metrics={
                    "avg_daily_spend_usd": avg_daily_spend_usd,
                    "utilization_pct": round((avg_daily_spend_usd / max_daily) * 100, 1),
                },
            )
        elif active_profile == CostProfile.BALANCED and (avg_daily_spend_usd < 0.10 or mesh_adoption_ratio >= 0.85):
            target = CostProfile.ECONOMY
            savings = (curr_cfg.max_daily_budget_usd - COST_PROFILES[target].max_daily_budget_usd) * 30.0
            return CostRecommendation(
                current_profile=active_profile,
                recommended_profile=target,
                action="DOWNGRADE",
                estimated_monthly_delta_usd=-round(savings, 2),
                confidence=0.88,
                rationale=(
                    f"Low direct inference demand (${avg_daily_spend_usd:.2f}/day) and {int(mesh_adoption_ratio * 100)}% mesh attestation reuse. "
                    f"Downgrading to ECONOMY saves up to ${savings:.2f}/month while preserving Gemini 3.7 Flash reasoning."
                ),
                key_metrics={"avg_daily_spend_usd": avg_daily_spend_usd, "mesh_adoption_ratio": mesh_adoption_ratio},
            )

    # 3. Status Optimal
    return CostRecommendation(
        current_profile=active_profile,
        recommended_profile=active_profile,
        action="OPTIMAL",
        estimated_monthly_delta_usd=0.0,
        confidence=1.0,
        rationale=f"Your current profile '{active_profile.value.upper()}' is well-calibrated for current workload trends.",
        key_metrics={"avg_daily_spend_usd": avg_daily_spend_usd, "trips_last_72h": trips_last_72h},
    )
