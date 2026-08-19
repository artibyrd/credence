"""Unit and Hermetic Pipeline Tests for Credence."""

from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.ingestion.snapshot import capture_webpage
from credence.pipeline.evaluator import audit_url, evaluate_snapshot
from credence.pipeline.subagents import (
    parse_satire_response,
    parse_specialist_response,
    validate_grounded_quote,
)
from credence.taxonomy_loader import TaxonomyRegistry


@pytest.mark.unit
def test_grounded_quote_validation() -> None:
    """Verify quote validation detects authentic vs hallucinated quotes."""
    source_text = "Global renewable energy adoption reached a record 24 percent increase in 2025."
    raw_html = f"<html><body><p>{source_text}</p></body></html>"

    # Authentic quote
    assert validate_grounded_quote("record 24 percent increase", source_text, raw_html) is True
    # Normalized whitespace quote
    assert validate_grounded_quote("record  24   percent\nincrease", source_text, raw_html) is True
    # Hallucinated quote
    assert (
        validate_grounded_quote("Solar energy caused massive blackouts across the continent", source_text, raw_html)
        is False
    )


@pytest.mark.unit
def test_parse_specialist_json_responses(test_registry: TaxonomyRegistry) -> None:
    """Verify robust JSON parsing from LLM markdown code blocks."""
    json_payload = """```json
    {
      "specialist_name": "spj_ethics_auditor",
      "domain": "JOURNALISTIC_ETHICS",
      "violations": [
        {
          "rule_id": "SPJ-1.1",
          "severity": 3,
          "confidence": 0.9,
          "quote_or_element": "Studies show that everyone agrees.",
          "reasoning": "Missing citation."
        }
      ],
      "summary": "Found 1 sourcing violation."
    }
    ```"""
    report = parse_specialist_response(json_payload, "spj_ethics", reg=test_registry)
    assert report.specialist_name == "spj_ethics_auditor"
    assert len(report.violations) == 1
    assert report.violations[0].rule_id == "SPJ-1.1"
    assert report.violations[0].severity == 3


@pytest.mark.unit
def test_parse_satire_json_response() -> None:
    """Verify satire verdict parsing."""
    json_payload = """```json
    {
      "is_satire": true,
      "confidence": 0.95,
      "classification": "SATIRE_PARODY",
      "satire_cues_found": ["Satire masthead", "Absurd premise"],
      "notes": "Comedic onion article."
    }
    ```"""
    verdict = parse_satire_response(json_payload)
    assert verdict.is_satire is True
    assert verdict.classification == "SATIRE_PARODY"
    assert verdict.confidence == 0.95


@pytest.mark.integration
async def test_evaluate_snapshot_clean_article(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify evaluation of a high-integrity clean news article."""
    file_url = f"file://{fixtures_dir / 'clean_article.html'}"
    snapshot = await capture_webpage(file_url, output_dir=tmp_path, save_artifacts=False)

    report = await evaluate_snapshot(snapshot, sign_result=True)
    assert report.url == file_url
    assert report.is_satire is False
    assert report.suspicion_score <= 15.0
    assert report.classification == "CLEAN"
    assert report.node_signature is not None


@pytest.mark.integration
async def test_evaluate_snapshot_satire_article(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify Poe's law satire filter neutralizes suspicion score."""
    file_url = f"file://{fixtures_dir / 'satire_article.html'}"
    snapshot = await capture_webpage(file_url, output_dir=tmp_path, save_artifacts=False)

    report = await evaluate_snapshot(snapshot, sign_result=True)
    assert report.is_satire is True
    assert report.classification == "SATIRE_PARODY"
    assert report.suspicion_score == 0.0


@pytest.mark.integration
async def test_evaluate_snapshot_deceptive_page(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify deceptive pattern detection flags violations and increases suspicion score."""
    file_url = f"file://{fixtures_dir / 'deceptive_page.html'}"
    snapshot = await capture_webpage(file_url, output_dir=tmp_path, save_artifacts=False)

    report = await evaluate_snapshot(snapshot, sign_result=True)
    assert len(report.violations) >= 2
    assert report.suspicion_score > 40.0
    assert report.classification in ["SUSPICIOUS", "DECEPTIVE"]


@pytest.mark.integration
async def test_audit_url_database_cache(fixtures_dir: Path, db_session: AsyncSession) -> None:
    """Verify audit_url persists to database and second call hits the cache."""
    file_url = f"file://{fixtures_dir / 'clean_article.html'}"

    # First audit (cache miss)
    report1 = await audit_url(file_url, session=db_session, force_refresh=False)
    assert report1.content_sha256.startswith("sha256:")

    # Second audit (cache hit)
    report2 = await audit_url(file_url, session=db_session, force_refresh=False)
    assert report1.content_sha256 == report2.content_sha256
    assert report1.suspicion_score == report2.suspicion_score
