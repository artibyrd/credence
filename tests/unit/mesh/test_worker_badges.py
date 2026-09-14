"""Unit tests for worker achievement badges and SVG generation."""

import pytest

from credence.mesh.worker_badges import evaluate_worker_badges, generate_worker_profile_badge_svg
from credence.models import WorkerRecord


@pytest.mark.unit
def test_worker_badge_milestones() -> None:
    """Verify worker milestones unlock dynamically as contributions increase."""
    worker = WorkerRecord(
        worker_pubkey="aabbcc112233",
        worker_alias="alice-gpu",
        total_completed=0,
        bounties_cleared=0,
    )

    # Initially zero badges
    awards_0 = evaluate_worker_badges(worker)
    assert len(awards_0) == 0

    # 1st bounty
    worker.total_completed = 1
    worker.bounties_cleared = 1
    awards_1 = evaluate_worker_badges(worker)
    badge_ids_1 = {a.badge_id for a in awards_1}
    assert "first_bounty" in badge_ids_1

    # 25 bounties
    worker.total_completed = 25
    worker.bounties_cleared = 25
    awards_25 = evaluate_worker_badges(worker)
    badge_ids_25 = {a.badge_id for a in awards_25}
    assert "first_bounty" in badge_ids_25
    assert "bounty_hunter" in badge_ids_25

    # 100 bounties
    worker.total_completed = 100
    worker.bounties_cleared = 100
    awards_100 = evaluate_worker_badges(worker)
    badge_ids_100 = {a.badge_id for a in awards_100}
    assert "bounty_legend" in badge_ids_100


@pytest.mark.unit
def test_worker_profile_badge_svg_rendering() -> None:
    """Verify SVG badge rendering for worker profile produces valid vector graphics."""
    worker = WorkerRecord(
        worker_pubkey="aabbcc112233",
        worker_alias="bob-rig",
        total_completed=30,
        bounties_cleared=30,
        tokens_donated=45000,
    )

    svg = generate_worker_profile_badge_svg(worker, style="shield", theme="dark")
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Worker: bob-rig" in svg
    assert "30 Bounties" in svg
