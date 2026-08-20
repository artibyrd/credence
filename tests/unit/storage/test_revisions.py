"""Hermetic unit tests for revision querying and trajectory calculations."""

import pytest

from credence.storage.revisions import RevisionEntry, compute_audit_trajectory

pytestmark = pytest.mark.unit


def test_compute_audit_trajectory_improving():
    revs = [
        RevisionEntry(
            snapshot_id=1,
            revision_index=1,
            captured_at="2026-08-01T00:00:00Z",
            content_sha256="sha256:111",
            simhash_64="0x111",
            suspicion_score=45.0,
            classification="NOTABLE_FLAGS",
        ),
        RevisionEntry(
            snapshot_id=2,
            revision_index=2,
            captured_at="2026-08-15T00:00:00Z",
            content_sha256="sha256:222",
            simhash_64="0x222",
            suspicion_score=2.1,
            classification="PRISTINE",
            is_editorial_update=True,
        ),
    ]

    summary = compute_audit_trajectory(revs)
    assert summary.total_revisions == 2
    assert summary.initial_score == 45.0
    assert summary.current_score == 2.1
    assert summary.lifetime_score_delta == -42.9
    assert summary.status == "IMPROVING"


def test_compute_audit_trajectory_degrading():
    revs = [
        RevisionEntry(
            snapshot_id=1,
            revision_index=1,
            captured_at="2026-08-01T00:00:00Z",
            content_sha256="sha256:111",
            simhash_64="0x111",
            suspicion_score=5.0,
            classification="CLEAN",
        ),
        RevisionEntry(
            snapshot_id=2,
            revision_index=2,
            captured_at="2026-08-15T00:00:00Z",
            content_sha256="sha256:222",
            simhash_64="0x222",
            suspicion_score=68.0,
            classification="DECEPTIVE",
        ),
    ]

    summary = compute_audit_trajectory(revs)
    assert summary.status == "DEGRADING"
    assert summary.lifetime_score_delta == 63.0
