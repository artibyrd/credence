import json
from pathlib import Path
from typing import Any

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
async def test_cli_quota() -> None:
    """Verify quota command outputs headroom metrics without errors."""
    from credence.cli.main import cli_quota

    await cli_quota()


@pytest.mark.unit
async def test_cli_audit_and_lookup(fixtures_dir: Path) -> None:
    """Verify CLI audit and lookup workflows."""
    file_url = f"file://{fixtures_dir / 'clean_article.html'}"
    await cli_audit(file_url, force=True)
    await cli_lookup(file_url)


@pytest.mark.unit
async def test_cli_verify_file_and_export(tmp_path: Path) -> None:
    """Verify verify-file and export-report CLI subcommands."""
    import json

    from credence.cli.main import cli_export_report, cli_verify_file, report_to_markdown
    from credence.identity import load_or_create_node_identity, sign_audit_report

    report = AuditReport(
        url="https://example.org/test-export",
        content_sha256="sha256:abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
        simhash_64="0x1234567890abcdef",
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=1.0,
        classification="CLEAN",
        is_satire=False,
    )
    identity = load_or_create_node_identity()
    signed_report = sign_audit_report(report, identity)

    # Test report_to_markdown
    md_content = report_to_markdown(signed_report)
    assert "# Credence Epistemic Audit Report" in md_content
    assert "https://example.org/test-export" in md_content

    # Save to disk
    attestation_file = tmp_path / "attestation.json"
    attestation_file.write_text(json.dumps(signed_report.model_dump(mode="json")), encoding="utf-8")

    # Test verify-file
    cli_verify_file(str(attestation_file))

    # Test export-report markdown and json
    export_md = tmp_path / "export.md"
    export_json = tmp_path / "export.json"
    await cli_export_report("https://example.org/test-export", format_type="markdown", output_path=str(export_md))
    await cli_export_report("https://example.org/test-export", format_type="json", output_path=str(export_json))

    assert export_md.exists()
    assert export_json.exists()


@pytest.mark.unit
async def test_cli_db_clean() -> None:
    """Verify db-clean CLI subcommand."""
    from credence.cli.main import cli_db_clean

    await cli_db_clean(retention_days=30)


@pytest.mark.unit
async def test_cli_seeds_and_rank(tmp_path: Path) -> None:
    """Verify seeds and rank CLI subcommands."""
    from credence.cli.main import cli_rank, cli_seeds

    # Test seed generation
    seed_output = tmp_path / "seeds.json"
    await cli_seeds(action="generate", output_path=str(seed_output), valid_hours=48)
    assert seed_output.exists()

    # Test seed verification
    await cli_seeds(action="verify", url_or_path=str(seed_output))

    # Test seed fetch from local path
    await cli_seeds(action="fetch", url_or_path=str(seed_output))

    # Test node quality rank leaderboard
    await cli_rank()


@pytest.mark.unit
async def test_cli_feeds_and_subjects() -> None:
    """Verify feeds and subjects CLI subcommands."""
    from credence.cli.main import cli_feeds, cli_subjects

    # Test feeds add, list, stats, sync, remove
    await cli_feeds(
        action="add",
        url="https://example.com/feed.xml",
        title="Test Feed",
        priority=1,
        tag="journalism.news",
        satire=False,
    )
    await cli_feeds(action="list")
    await cli_feeds(action="stats")
    await cli_feeds(action="sync", dry_run=True, evaluate=False)
    await cli_feeds(action="remove", url="https://example.com/feed.xml")

    # Test subjects list and show
    cli_subjects(action="list")
    cli_subjects(action="show", subject_id="apiculture.equipment")


@pytest.mark.unit
async def test_cli_browse_and_formats(fixtures_dir: Path) -> None:
    """Verify CLI multi-format output (compact, json, ndjson, tsv) and discovery browsing."""
    from credence.cli.main import cli_audit, cli_browse_audits, cli_lookup, cli_report_view

    file_url = f"file://{fixtures_dir / 'clean_article.html'}"
    await cli_audit(file_url, force=True, format_type="compact")
    await cli_audit(file_url, force=False, format_type="json")
    await cli_audit(file_url, force=False, format_type="ndjson")
    await cli_audit(file_url, force=False, format_type="tsv")

    # Test lookup with various formats
    await cli_lookup(file_url, format_type="compact")
    await cli_lookup(file_url, format_type="json")
    await cli_lookup(file_url, format_type="ndjson")
    await cli_lookup(file_url, format_type="tsv")

    # Test lookup with category flags
    await cli_lookup(category="best", format_type="compact")
    await cli_lookup(category="recent", format_type="human")
    await cli_lookup(random_pick=True, format_type="json")

    # Test browse audits across categories and formats
    await cli_browse_audits(category="recent", limit=5, format_type="human")
    await cli_browse_audits(category="best", limit=5, format_type="compact")
    await cli_browse_audits(category="worst", limit=5, format_type="json")
    await cli_browse_audits(category="satire", limit=5, format_type="ndjson")
    await cli_browse_audits(category="random", limit=5, format_type="tsv")

    # Test report view routing
    await cli_report_view(identifier="browse", category="best", format_type="compact")
    await cli_report_view(identifier=file_url, format_type="human")
    await cli_report_view(identifier=file_url, format_type="compact")


@pytest.mark.asyncio
async def test_cli_export_catalog(tmp_path: Any, db_session: Any) -> None:
    """Verify cli_export_catalog exports valid JSON catalog."""
    from credence.cli.main import cli_export_catalog

    out_dir = tmp_path / "web_export"
    await cli_export_catalog(output_dir=str(out_dir))

    json_file = out_dir / "reports.json"
    assert json_file.exists()
    content = json.loads(json_file.read_text(encoding="utf-8"))
    assert isinstance(content, list)
