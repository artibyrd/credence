"""Unit and Hermetic Pipeline Tests for Credence."""

from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.snapshot import capture_webpage
from credence.pipeline.evaluator import audit_url, evaluate_snapshot
from credence.pipeline.heuristics import heuristic_evaluate_content
from credence.pipeline.subagents import (
    parse_satire_response,
    parse_specialist_response,
    validate_grounded_quote,
)
from credence.taxonomy_loader import TaxonomyRegistry


@pytest.mark.unit
def test_heuristic_anonymous_byline_detection(test_registry: TaxonomyRegistry) -> None:
    """Verify generic/anonymous staff bylines trigger SPJ-4.1."""
    extracted = ExtractedContent(
        url="https://example.com/article",
        title="Local Road Construction Update",
        byline="InMaricopa Staff",
        clean_text="Road construction began on SR 347 today and will continue through Friday.",
        word_count=50,
    )
    violations = heuristic_evaluate_content(extracted, "<html></html>", reg=test_registry)
    byline_violations = [v for v in violations if v.rule_id == "SPJ-4.1"]
    assert len(byline_violations) >= 1
    assert "InMaricopa Staff" in byline_violations[0].quote_or_element


@pytest.mark.unit
def test_heuristic_advertising_byline_detection(test_registry: TaxonomyRegistry) -> None:
    """Verify advertising/sponsored bylines trigger SPJ-3.2."""
    extracted = ExtractedContent(
        url="https://example.com/article",
        title="A New Option for Laser Therapy",
        byline="InMaricopa Advertising Staff",
        clean_text="Advanced laser therapy is now available in town for all residents.",
        word_count=40,
    )
    violations = heuristic_evaluate_content(extracted, "<html></html>", reg=test_registry)
    ad_violations = [v for v in violations if v.rule_id == "SPJ-3.2"]
    assert len(ad_violations) >= 1


@pytest.mark.unit
def test_heuristic_police_blotter_detection(test_registry: TaxonomyRegistry) -> None:
    """Verify uncorroborated single-source police blotter reports trigger SPJ-1.3."""
    extracted = ExtractedContent(
        url="https://example.com/article",
        title="Suspect Arrested in Store Collision",
        byline="Jane Doe, Senior Reporter",
        clean_text="A local driver was arrested after police say he told officers that substance use caused the accident.",
        word_count=60,
    )
    violations = heuristic_evaluate_content(extracted, "<html></html>", reg=test_registry)
    blotter_violations = [v for v in violations if v.rule_id == "SPJ-1.3"]
    assert len(blotter_violations) >= 1
    assert "police say" in blotter_violations[0].quote_or_element.lower()


@pytest.mark.unit
def test_heuristic_commercial_cta_detection(test_registry: TaxonomyRegistry) -> None:
    """Verify direct embedded phone solicitations trigger SPJ-3.2."""
    extracted = ExtractedContent(
        url="https://example.com/article",
        title="AC Maintenance Tips",
        byline="Jane Doe, Senior Reporter",
        clean_text="Homeowners needing prompt service can call 520-555-0199 to schedule service today.",
        word_count=60,
    )
    violations = heuristic_evaluate_content(extracted, "<html></html>", reg=test_registry)
    cta_violations = [v for v in violations if v.rule_id == "SPJ-3.2"]
    assert len(cta_violations) >= 1
    assert "520-555-0199" in cta_violations[0].quote_or_element


@pytest.mark.unit
def test_heuristic_native_advertorial_detection(test_registry: TaxonomyRegistry) -> None:
    """Verify promotional advertorial cues trigger DP-1.1."""
    extracted = ExtractedContent(
        url="https://example.com/article",
        title="Summer Wellness Guide",
        byline="Jane Doe, Senior Reporter",
        clean_text="Readers interested in special treatments can book a consultation to receive a custom plan.",
        word_count=60,
    )
    violations = heuristic_evaluate_content(extracted, "<html></html>", reg=test_registry)
    dec_violations = [v for v in violations if v.rule_id == "DP-1.1"]
    assert len(dec_violations) >= 1
    assert "book a consultation" in dec_violations[0].quote_or_element.lower()


@pytest.mark.unit
def test_heuristic_clean_article_zero_violations(test_registry: TaxonomyRegistry) -> None:
    """Verify authentic, sourced news with proper byline generates zero spurious violations."""
    extracted = ExtractedContent(
        url="https://example.com/article",
        title="City Council Approves Annual Parks Budget",
        byline="Monica Spencer, Associate Editor",
        clean_text="The Maricopa City Council on Tuesday unanimously approved the municipal parks operating budget following two public hearings.",
        word_count=100,
    )
    violations = heuristic_evaluate_content(extracted, "<html></html>", reg=test_registry)
    assert len(violations) == 0


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
