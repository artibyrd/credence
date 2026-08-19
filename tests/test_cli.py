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


@pytest.mark.integration
async def test_cli_audit_and_lookup(fixtures_dir: Path) -> None:
    """Verify CLI audit and lookup workflows."""
    file_url = f"file://{fixtures_dir / 'clean_article.html'}"
    await cli_audit(file_url, force=True)
    await cli_lookup(file_url)


@pytest.mark.integration
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
    from unittest.mock import AsyncMock, patch

    from credence.cli.main import cli_feeds, cli_subjects
    from credence.feeds.parser import ParsedFeed

    mock_feed = ParsedFeed(title="Test Feed", is_modified=True, entries=[])

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
    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock, return_value=mock_feed):
        await cli_feeds(action="sync", dry_run=True, evaluate=False)
    await cli_feeds(action="remove", url="https://example.com/feed.xml")

    # Test subjects list and show
    cli_subjects(action="list")
    cli_subjects(action="show", subject_id="apiculture.equipment")


@pytest.mark.integration
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


@pytest.mark.asyncio
async def test_cli_germinate(db_session: Any) -> None:
    """Verify cli_germinate runs botanical lifecycle without exceptions."""
    from unittest.mock import AsyncMock, patch

    from credence.cli.main import cli_germinate
    from credence.feeds.parser import ParsedFeed

    mock_feed = ParsedFeed(title="Mock Stream", is_modified=True, entries=[])

    with patch("credence.feeds.worker.fetch_and_parse_feed", new_callable=AsyncMock, return_value=mock_feed):
        await cli_germinate(burst=0, no_mesh=False, profile="free")
        await cli_germinate(burst=0, no_mesh=True, profile="free")


@pytest.mark.unit
def test_cli_health_and_alerts() -> None:
    """Verify cli_health and cli_alerts render panels cleanly."""
    from credence.cli.main import cli_health

    # In-process fallback path
    cli_health(url="")
    cli_health(url="http://localhost:8000")


@pytest.mark.unit
async def test_cli_roots_and_boredom(db_session: Any) -> None:
    """Verify expand-roots, roots tree, and boredom CLI commands."""
    from unittest.mock import AsyncMock, patch

    from credence.cli.main import cli_boredom, cli_expand_roots, cli_roots
    from credence.feeds.roots import RootExpansionSummary

    # Test roots tree and candidates
    await cli_roots(action="tree", format_type="human")
    await cli_roots(action="tree", format_type="json")
    await cli_roots(action="candidates", format_type="human")
    await cli_roots(action="candidates", format_type="json")

    # Test expand-roots with mock
    mock_summary = RootExpansionSummary(
        candidates_scanned=2,
        candidate_domains_evaluated=2,
        new_feeds_discovered=1,
        new_feeds_subscribed=1,
        initial_items_harvested=3,
        details=[{"domain": "sciencewire.org", "status": "subscribed", "items_harvested": 3}],
    )
    with patch("credence.feeds.roots.expand_roots", new=AsyncMock(return_value=mock_summary)):
        await cli_expand_roots(max_sources=2, dry_run=True, format_type="human")
        await cli_expand_roots(max_sources=2, dry_run=False, format_type="json")

    # Test boredom single pass
    with patch(
        "credence.feeds.boredom.run_boredom_cycle",
        new=AsyncMock(
            return_value=AsyncMock(
                pending_items_scanned=1,
                pending_items_audited=1,
                mesh_attestations_adopted=0,
                tokens_saved_mesh=0,
                new_roots_subscribed=1,
                initial_items_harvested=2,
                headroom_daily_pct=95.0,
                circuit_breaker_tripped=False,
            )
        ),
    ):
        await cli_boredom(burst=1, expand_roots_enabled=True, continuous=False)
