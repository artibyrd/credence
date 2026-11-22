"""Unit tests verifying all 10 registered volunteer worker achievement badges."""

from __future__ import annotations

import json

import pytest

from credence.mesh.worker_badges import evaluate_worker_badges
from credence.models import WorkerRecord


@pytest.mark.unit
def test_all_10_worker_badges_awarded_at_thresholds() -> None:
    """Verify every one of the 10 registered worker badges awards when criteria are satisfied."""
    worker = WorkerRecord(
        worker_pubkey="a" * 64,
        worker_alias="ten-badge-champion",
        total_completed=500,
        bounties_cleared=100,
        grounded_violations_count=60,
        grounding_rejections_count=0,
        distinct_models_json=json.dumps(["google/gemini", "anthropic/claude", "deepseek/deepseek"]),
        fastest_turnaround_sec=9.4,
        weekend_completed_count=12,
        night_owl_completed_count=2,
        pioneer_families_count=1,
        quality_score=0.92,
    )

    awards = evaluate_worker_badges(worker)
    unlocked = {a.badge_id for a in awards}

    expected_all_10 = {
        "first_bounty",
        "speed_demon",
        "bounty_hunter",
        "bounty_legend",
        "diversity_champion",
        "model_pioneer",
        "night_owl",
        "weekend_warrior",
        "precision_striker",
        "iron_worker",
    }
    assert unlocked == expected_all_10


@pytest.mark.unit
def test_grounding_rejections_block_precision_and_iron_badges() -> None:
    """Verify zero-rejection gates block precision_striker and iron_worker when rejections > 0."""
    worker = WorkerRecord(
        worker_pubkey="b" * 64,
        worker_alias="slashed-worker",
        total_completed=600,
        bounties_cleared=150,
        grounded_violations_count=80,
        grounding_rejections_count=1,
        quality_score=0.88,
    )
    unlocked = {a.badge_id for a in evaluate_worker_badges(worker)}
    assert "bounty_legend" in unlocked
    assert "precision_striker" not in unlocked
    assert "iron_worker" not in unlocked
