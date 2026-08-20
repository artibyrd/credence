"""Revision history querying, DAG snapshot tracking, and trajectory calculations.

Provides:
- Asynchronous database queries for URL revision chains.
- Score trajectory velocity and lifetime delta computation.
- Snapshot diff retrieval.
"""

from __future__ import annotations

import json
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import Audit, Snapshot, Violation


class RevisionEntry(BaseModel):
    """Structured representation of a single snapshot revision and its audit outcome."""

    snapshot_id: Optional[int] = None
    revision_index: int

    captured_at: str
    content_sha256: str
    simhash_64: str
    title: Optional[str] = None
    suspicion_score: float
    classification: str
    score_delta: Optional[float] = None
    is_editorial_update: bool = False
    diff_summary: Optional[str] = None
    violations_count: int = 0
    node_pubkey: Optional[str] = None


class TrajectorySummary(BaseModel):
    """Aggregate trajectory overview for a URL across all revisions."""

    url: str
    total_revisions: int
    initial_score: float
    current_score: float
    lifetime_score_delta: float
    status: str = Field(description="IMPROVING, DEGRADING, or STABLE")
    revisions: List[RevisionEntry] = Field(default_factory=list)


def compute_audit_trajectory(revisions: List[RevisionEntry]) -> TrajectorySummary:
    """Compute aggregate trajectory summary and directional status across revisions."""
    if not revisions:
        return TrajectorySummary(
            url="",
            total_revisions=0,
            initial_score=0.0,
            current_score=0.0,
            lifetime_score_delta=0.0,
            status="STABLE",
            revisions=[],
        )

    sorted_revs = sorted(revisions, key=lambda r: r.revision_index)
    initial_score = sorted_revs[0].suspicion_score
    current_score = sorted_revs[-1].suspicion_score
    lifetime_delta = round(current_score - initial_score, 2)

    if lifetime_delta <= -5.0:
        status = "IMPROVING"
    elif lifetime_delta >= 5.0:
        status = "DEGRADING"
    else:
        status = "STABLE"

    return TrajectorySummary(
        url="",
        total_revisions=len(sorted_revs),
        initial_score=initial_score,
        current_score=current_score,
        lifetime_score_delta=lifetime_delta,
        status=status,
        revisions=sorted_revs,
    )


async def get_url_revision_history(session: AsyncSession, url: str) -> TrajectorySummary:
    """Query all historical snapshots and audits for a given URL, returning trajectory data."""
    stmt = (
        select(Snapshot, Audit)
        .join(Audit, col(Audit.snapshot_id) == col(Snapshot.id))
        .where(col(Snapshot.url) == url)
        .order_by(col(Snapshot.captured_at).asc())
    )

    result = await session.exec(stmt)
    rows = result.all()

    if not rows:
        return TrajectorySummary(
            url=url,
            total_revisions=0,
            initial_score=0.0,
            current_score=0.0,
            lifetime_score_delta=0.0,
            status="STABLE",
            revisions=[],
        )

    entries: List[RevisionEntry] = []
    for snap, audit in rows:
        v_stmt = select(col(Violation.id)).where(col(Violation.audit_id) == audit.id)
        v_res = await session.exec(v_stmt)
        v_count = len(v_res.all())

        diff_summary = None
        if snap.content_diff:
            try:
                diff_data = json.loads(snap.content_diff)
                diff_summary = diff_data.get("diff_summary")
            except Exception:
                diff_summary = str(snap.content_diff)

        entries.append(
            RevisionEntry(
                snapshot_id=snap.id,
                revision_index=snap.revision_index or (len(entries) + 1),
                captured_at=snap.captured_at.isoformat(),
                content_sha256=snap.content_sha256,
                simhash_64=snap.simhash_64,
                title=snap.title,
                suspicion_score=audit.suspicion_score,
                classification=audit.classification,
                score_delta=audit.score_delta,
                is_editorial_update=snap.is_editorial_update,
                diff_summary=diff_summary,
                violations_count=v_count,
                node_pubkey=audit.node_pubkey,
            )
        )

    summary = compute_audit_trajectory(entries)
    summary.url = url
    return summary
