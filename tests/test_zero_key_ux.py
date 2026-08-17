"""Scenario 2: Zero-Key First-Boot UX & Onboarding Validation.

Tests that a user with zero environment variables and no Gemini API key configured:
1. Receives clean offline structural heuristic audits without exceptions.
2. Transparently discloses evaluation_method: 'offline_structural_heuristic' with confidence <= 0.50.
3. Can generate Ed25519 identity, inspect cost profiles, and run db maintenance via CLI cleanly.
"""

from typing import Any

import pytest

from credence.cli.main import cli_db_clean, cli_identity, cli_profile
from credence.config import settings
from credence.identity import NodeIdentity, load_or_create_node_identity
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.pipeline.evaluator import evaluate_snapshot


@pytest.mark.asyncio
async def test_zero_key_offline_heuristic_evaluation_fallback(monkeypatch: Any) -> None:
    """Verify that with no API key, the evaluation pipeline falls back to offline heuristic mode."""
    # Force empty API keys
    monkeypatch.setattr(settings, "CREDENCE_GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    sample_text = "The city council voted 5-2 to approve the municipal bridge renovation project yesterday."
    snapshot = DualCaptureResult(
        url="text://local-bridge",
        content_sha256=compute_content_sha256(sample_text),
        simhash_64=compute_simhash(sample_text),
        raw_html=f"<html><body><h1>Local Civic Project Approved</h1><p>{sample_text}</p></body></html>",
        extracted=ExtractedContent(
            title="Local Civic Project Approved",
            clean_text=sample_text,
            word_count=len(sample_text.split()),
            char_count=len(sample_text),
        ),
    )

    report = await evaluate_snapshot(snapshot, sign_result=True)

    assert report is not None
    assert report.evaluation_method == "offline_structural_heuristic"
    assert report.confidence_score <= 0.50
    assert report.classification in ("CLEAN", "LOW_SUSPICION")
    assert report.node_pubkey != ""


@pytest.mark.asyncio
async def test_zero_key_cli_first_boot_commands() -> None:
    """Verify that basic CLI management commands execute cleanly on a fresh boot."""
    # 1. Profile list
    cli_profile(action="list")

    # 2. DB clean
    await cli_db_clean(retention_days=30)

    # 3. Identity inspection
    cli_identity(action="show")

    # 4. Init identity
    identity = load_or_create_node_identity()
    assert isinstance(identity, NodeIdentity)
    assert len(identity.public_key_hex) == 64
