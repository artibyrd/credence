"""Hermetic Unit Tests for credence mesh audit-feed CLI command.

Governed by: inv-hermetic-unit-tests, inv-clean-scratch-scripts
"""

from unittest.mock import AsyncMock, patch

import pytest

from credence.cli.commands.mesh import run_mesh_audit_feed_command
from credence.feeds.parser import FeedEntry, ParsedFeed
from credence.pipeline.schemas import AuditReport


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_mesh_audit_feed_command_success():
    """Assert mesh audit-feed runs cleanly on discovered entries."""
    mock_feed = ParsedFeed(
        title="InMaricopa",
        entries=[
            FeedEntry(
                url="https://inmaricopa.com/sample-article-1",
                title="Sample Clean News",
                summary="Factual news",
            ),
            FeedEntry(
                url="https://inmaricopa.com/sample-article-2",
                title="Sample Blotter",
                summary="Police blotter",
            ),
        ],
    )

    mock_report_1 = AuditReport(
        url="https://inmaricopa.com/sample-article-1",
        content_sha256="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        simhash_64="0x1111111111111111",
        suspicion_score=4.0,
        suspicion_density=0.0,
        confidence_score=0.95,
        classification="CLEAN",
        violations=[],
    )

    mock_report_2 = AuditReport(
        url="https://inmaricopa.com/sample-article-2",
        content_sha256="sha256:2222222222222222222222222222222222222222222222222222222222222222",
        simhash_64="0x2222222222222222",
        suspicion_score=38.0,
        suspicion_density=0.0,
        confidence_score=0.90,
        classification="LOW SUSPICION",
        violations=[],
    )

    with (
        patch("credence.feeds.parser.fetch_and_parse_feed", new_callable=AsyncMock) as mock_fetch,
        patch("credence.pipeline.evaluator.audit_url", new_callable=AsyncMock) as mock_audit,
        patch("credence.db.init_db", new_callable=AsyncMock),
    ):
        mock_fetch.return_value = mock_feed
        mock_audit.side_effect = [mock_report_1, mock_report_2]

        code = await run_mesh_audit_feed_command(
            feed_or_domain="inmaricopa.com",
            limit=2,
            profile="balanced",
            json_output=False,
        )

        assert code == 0
        assert mock_fetch.call_count == 1
        assert mock_audit.call_count == 2
