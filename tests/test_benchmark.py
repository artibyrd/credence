"""Unit and integration tests for the Golden 12 Epistemic Benchmark Suite."""

from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.cli.main import cli_benchmark
from credence.pipeline.benchmark import (
    GOLDEN_12_METADATA,
    render_benchmark_table,
    run_epistemic_benchmark,
    run_single_fixture_benchmark,
)


@pytest.mark.unit
def test_golden_12_metadata_completeness() -> None:
    """Verify that all 12 benchmark fixtures are registered in metadata and exist on disk."""
    assert len(GOLDEN_12_METADATA) == 12
    fixtures_dir = Path("tests/fixtures/html")

    for filename, (title, desc) in GOLDEN_12_METADATA.items():
        fixture_path = fixtures_dir / filename
        assert fixture_path.exists(), f"Missing benchmark fixture file: {fixture_path}"
        assert len(title) > 0
        assert len(desc) > 0


@pytest.mark.unit
async def test_run_single_fixture_benchmark(db_session: AsyncSession) -> None:
    """Verify single fixture evaluation across FREE, BALANCED, and ULTRA profiles."""
    fixture_path = Path("tests/fixtures/html/clean_article.html")
    result = await run_single_fixture_benchmark(fixture_path, session=db_session)

    assert result.fixture_name == "clean_article.html"
    assert "free" in result.reports
    assert "balanced" in result.reports
    assert "ultra" in result.reports

    # Clean article should have 0.0 suspicion across all profiles
    assert result.reports["free"].suspicion_score == 0.0
    assert result.reports["balanced"].suspicion_score == 0.0
    assert result.consensus_score == 0.0
    assert result.consensus_verdict == "CLEAN"


@pytest.mark.unit
async def test_run_full_epistemic_benchmark_suite(db_session: AsyncSession) -> None:
    """Verify that the full Golden 12 benchmark suite executes and aggregates correctly."""
    suite = await run_epistemic_benchmark(session=db_session)

    assert suite.total_fixtures == 12
    assert len(suite.items) == 12
    assert suite.avg_consensus_score >= 0.0

    # Ensure table rendering executes cleanly
    render_benchmark_table(suite)


@pytest.mark.unit
async def test_cli_benchmark_execution() -> None:
    """Verify CLI benchmark runner executes without exception."""
    await cli_benchmark()
