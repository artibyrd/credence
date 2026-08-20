"""Hermetic unit tests for compute_text_diff and compute_token_drift."""

import pytest

from credence.ingestion.hasher import compute_text_diff, compute_token_drift

pytestmark = pytest.mark.unit


def test_compute_text_diff_identical():
    text = "The quick brown fox jumps over the lazy dog."
    diff = compute_text_diff(text, text)
    assert diff["added_lines_count"] == 0
    assert diff["removed_lines_count"] == 0
    assert diff["diff_summary"] == "Identical content"


def test_compute_text_diff_modifications():
    old = "Line 1\nLine 2 ungrounded claim\nLine 3"
    new = "Line 1\nLine 2 corrected fact [DOI: 10.1000/182]\nLine 3"
    diff = compute_text_diff(old, new)
    assert diff["added_lines_count"] == 1
    assert diff["removed_lines_count"] == 1
    assert "+1 lines / -1 lines" in diff["diff_summary"]


def test_compute_token_drift_scale():
    t1 = "Global temperatures have risen steadily over the past century."
    t2 = "Global temperatures have risen steadily over the past century."
    assert compute_token_drift(t1, t2) == 0.0

    t3 = "Global temperatures have risen steadily over the past century with minor regional variations."
    drift_minor = compute_token_drift(t1, t3)
    assert 0.0 < drift_minor < 0.40

    t4 = "Completely unrelated text about baking chocolate chip cookies in an oven."
    drift_major = compute_token_drift(t1, t4)
    assert drift_major > 0.40
