"""Unit tests for model comparison matrix and temporal revision diffing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, Violation
from credence.storage.revisions import get_model_comparison_matrix


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_model_comparison_matrix_computes_pairwise_diffs() -> None:
    """Verify that get_model_comparison_matrix parses multiple passes and computes pairwise deltas."""
    await init_db()

    target_url = "https://local-herald.com/investigative/budget-audit-pass"
    sha1 = "sha256:aaaabbbbccccddddeeeeffff0000111122223333444455556666777788889999"

    async with get_async_session() as session:
        # Create Snapshot
        snap = Snapshot(
            url=target_url,
            content_sha256=sha1,
            simhash_64="0x1234567890abcdef",
            title="Budget Audit Report",
            word_count=500,
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        # Pass 1: Offline Structural Heuristic
        audit1 = Audit(
            snapshot_id=snap.id,
            content_sha256=sha1,
            suspicion_score=20.0,
            suspicion_density=1.5,
            confidence_score=0.25,
            classification="LOW_SUSPICION",
            audited_at=datetime.now(timezone.utc),
            quota_preserved=True,
            evaluation_method="offline_structural_heuristic@v1.1.0",
        )
        session.add(audit1)
        await session.commit()
        await session.refresh(audit1)

        v1 = Violation(
            audit_id=audit1.id,
            rule_id="SPJ-4.1",
            rule_uri="journalistic-ethics:spj/SPJ-4.1@v1.0.0",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="BE_ACCOUNTABLE_AND_TRANSPARENT",
            severity=3,
            confidence=0.85,
            quote_or_element="Editorial Staff",
            reasoning="Generic byline",
        )
        session.add(v1)

        # Pass 2: Gemini 3.7 Flash LLM Specialist Swarm
        audit2 = Audit(
            snapshot_id=snap.id,
            content_sha256=sha1,
            suspicion_score=35.0,
            suspicion_density=2.8,
            confidence_score=0.94,
            classification="LOW_SUSPICION",
            audited_at=datetime.now(timezone.utc),
            quota_preserved=False,
            evaluation_method="llm_multi_agent_gemini-3.7-flash",
        )
        session.add(audit2)
        await session.commit()
        await session.refresh(audit2)

        v2a = Violation(
            audit_id=audit2.id,
            rule_id="SPJ-4.1",
            rule_uri="journalistic-ethics:spj/SPJ-4.1@v1.0.0",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="BE_ACCOUNTABLE_AND_TRANSPARENT",
            severity=3,
            confidence=0.90,
            quote_or_element="Editorial Staff",
            reasoning="Generic byline",
        )
        v2b = Violation(
            audit_id=audit2.id,
            rule_id="FALLACY-2.1",
            rule_uri="logical-fallacy:faulty-deduction/FALLACY-2.1@v1.0.0",
            domain="LOGICAL_FALLACY",
            cluster_id="FAULTY_DEDUCTION",
            severity=4,
            confidence=0.92,
            quote_or_element="If the deficit grows, total economic collapse is guaranteed",
            reasoning="Slippery slope fallacy",
        )
        session.add(v2a)
        session.add(v2b)
        await session.commit()

        # Compute comparison matrix
        matrix = await get_model_comparison_matrix(session, target_url)

        assert matrix.url == target_url
        assert len(matrix.passes) >= 2
        assert matrix.heuristic_baseline_used is True
        assert len(matrix.pairwise_diffs) >= 1

        # Check pairwise diff
        diff = matrix.pairwise_diffs[0]
        assert diff.baseline_model == "offline_structural_heuristic@v1.1.0"
        assert diff.comparison_model == "llm_multi_agent_gemini-3.7-flash"
        assert diff.score_delta == 15.0
        assert "FALLACY-2.1" in diff.violations_added
