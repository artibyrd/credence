"""Unit tests for Credence Rich CLI commands."""

from pathlib import Path

import pytest

from credence.cli.main import cli_audit, cli_identity, cli_lookup, cli_taxonomy, render_audit_report
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


@pytest.mark.unit
def test_render_audit_report_clean() -> None:
    """Verify render_audit_report executes cleanly for a report with no violations."""
    report = AuditReport(
        url="https://example.org/clean",
        content_sha256="sha256:0000000000000000000000000000000000000000000000000000000000000000",
        simhash_64="0x0000000000000000",
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=1.0,
        classification="CLEAN",
        is_satire=False,
    )
    # Should not raise exception
    render_audit_report(report)


@pytest.mark.unit
def test_render_audit_report_with_violations() -> None:
    """Verify render_audit_report renders tables for reports with violations."""
    v = SpecialistViolationFinding(
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=4,
        confidence=1.0,
        quote_or_element="Unverified breaking news.",
        reasoning="Sourcing missing.",
    )
    report = AuditReport(
        url="https://example.org/deceptive",
        content_sha256="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        simhash_64="0x1111111111111111",
        suspicion_score=45.0,
        suspicion_density=5.0,
        confidence_score=1.0,
        classification="SUSPICIOUS",
        is_satire=False,
        violations=[v],
        node_pubkey="0" * 64,
        node_signature="1" * 128,
    )
    render_audit_report(report)


@pytest.mark.unit
def test_cli_identity() -> None:
    """Verify identity command displays public key panel."""
    cli_identity("show")


@pytest.mark.unit
def test_cli_taxonomy() -> None:
    """Verify taxonomy list and show commands."""
    cli_taxonomy("list")
    cli_taxonomy("show", "spj_ethics")


@pytest.mark.unit
async def test_cli_audit_and_lookup(fixtures_dir: Path) -> None:
    """Verify CLI audit and lookup workflows."""
    file_url = f"file://{fixtures_dir / 'clean_article.html'}"
    await cli_audit(file_url, force=True)
    await cli_lookup(file_url)
