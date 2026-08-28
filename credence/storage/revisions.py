"""Revision history querying, DAG snapshot tracking, trajectory, and model comparison diffs.

Provides:
- Asynchronous database queries for URL revision chains.
- Score trajectory velocity and lifetime delta computation.
- Snapshot diff retrieval.
- Side-by-side Model Comparison Matrix across evaluation engines (Heuristic vs LLM vs Ground Truth).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

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
    confidence_score: float = 0.95
    classification: str
    evaluation_method: Optional[str] = None
    quota_preserved: bool = False
    score_delta: Optional[float] = None
    is_editorial_update: bool = False
    diff_summary: Optional[str] = None
    violations_count: int = 0
    node_pubkey: Optional[str] = None
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    model_provenance: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TrajectorySummary(BaseModel):
    """Aggregate trajectory overview for a URL across all revisions."""

    url: str
    total_revisions: int
    initial_score: float
    current_score: float
    lifetime_score_delta: float
    status: str = Field(description="IMPROVING, DEGRADING, or STABLE")
    revisions: List[RevisionEntry] = Field(default_factory=list)


class ModelEvaluationDiff(BaseModel):
    """Side-by-side comparison between two evaluation passes of the same article."""

    url: str
    title: Optional[str] = None
    base_engine: str
    base_score: float
    base_confidence: float
    base_violations_count: int
    target_engine: str
    target_score: float
    target_confidence: float
    target_violations_count: int
    score_delta: float
    violations_overlap_count: int
    discrepancy_summary: str
    violations_added: List[str] = Field(default_factory=list)
    violations_removed: List[str] = Field(default_factory=list)

    @property
    def baseline_model(self) -> str:
        return self.base_engine

    @property
    def comparison_model(self) -> str:
        return self.target_engine


class ModelComparisonMatrix(BaseModel):
    """Matrix of all evaluations performed across engines for a given URL."""

    url: str
    title: Optional[str] = None
    content_sha256: str
    evaluations: List[RevisionEntry] = Field(default_factory=list)
    pairwise_diffs: List[ModelEvaluationDiff] = Field(default_factory=list)
    has_heuristic_fallback: bool = False
    has_llm_evaluation: bool = False

    @property
    def passes(self) -> List[RevisionEntry]:
        return self.evaluations

    @property
    def heuristic_baseline_used(self) -> bool:
        return self.has_heuristic_fallback


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
        .order_by(col(Snapshot.captured_at).asc(), col(Audit.audited_at).asc())
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
        v_stmt = select(Violation).where(col(Violation.audit_id) == audit.id)
        v_res = await session.exec(v_stmt)
        violations_objs = v_res.all()

        diff_summary = None
        if snap.content_diff:
            try:
                diff_data = json.loads(snap.content_diff)
                diff_summary = diff_data.get("diff_summary")
            except Exception:
                diff_summary = str(snap.content_diff)

        violations_list = [
            {
                "rule_id": v.rule_id,
                "rule_uri": v.rule_uri,
                "severity": v.severity,
                "quote": getattr(v, "quote_or_element", getattr(v, "quote", "")),
                "reasoning": getattr(v, "reasoning", getattr(v, "explanation", "")),
                "confidence": getattr(v, "confidence", 1.0),
            }
            for v in violations_objs
        ]

        entries.append(
            RevisionEntry(
                snapshot_id=snap.id,
                revision_index=snap.revision_index or (len(entries) + 1),
                captured_at=audit.audited_at.isoformat() if audit.audited_at else snap.captured_at.isoformat(),
                content_sha256=snap.content_sha256,
                simhash_64=snap.simhash_64,
                title=snap.title,
                suspicion_score=audit.suspicion_score,
                confidence_score=audit.confidence_score,
                classification=audit.classification,
                evaluation_method=audit.evaluation_method,
                quota_preserved=audit.quota_preserved,
                score_delta=audit.score_delta,
                is_editorial_update=snap.is_editorial_update,
                diff_summary=diff_summary,
                violations_count=len(violations_objs),
                node_pubkey=audit.node_pubkey,
                violations=violations_list,
                model_provenance={
                    "evaluation_method": audit.evaluation_method,
                    "confidence_score": audit.confidence_score,
                    "quota_preserved": audit.quota_preserved,
                    "node_pubkey": audit.node_pubkey,
                },
            )
        )

    summary = compute_audit_trajectory(entries)
    summary.url = url
    return summary


async def get_model_comparison_matrix(session: AsyncSession, url: str) -> ModelComparisonMatrix:
    """Compute a side-by-side comparison matrix of all evaluation passes for a URL."""
    trajectory = await get_url_revision_history(session, url)
    revisions = trajectory.revisions

    if not revisions:
        return ModelComparisonMatrix(
            url=url,
            title=None,
            content_sha256="",
            evaluations=[],
            pairwise_diffs=[],
            has_heuristic_fallback=False,
            has_llm_evaluation=False,
        )

    title = revisions[0].title
    content_sha = revisions[0].content_sha256
    has_heuristic = any(
        r.quota_preserved or (r.evaluation_method and "heuristic" in r.evaluation_method) for r in revisions
    )
    has_llm = any(not r.quota_preserved and r.evaluation_method and "llm" in r.evaluation_method for r in revisions)

    pairwise_diffs: List[ModelEvaluationDiff] = []
    if len(revisions) >= 2:
        for i in range(len(revisions) - 1):
            base = revisions[i]
            target = revisions[i + 1]

            base_rules: set[str] = {str(v.get("rule_id")) for v in base.violations if v.get("rule_id")}
            target_rules: set[str] = {str(v.get("rule_id")) for v in target.violations if v.get("rule_id")}
            overlap = len(base_rules.intersection(target_rules))

            delta = round(target.suspicion_score - base.suspicion_score, 2)
            discrepancy = (
                f"Score shift of {delta:+.1f} pts ({base.classification} -> {target.classification}). "
                f"{len(target_rules - base_rules)} new rule(s) detected by {target.evaluation_method or 'target'}."
            )

            pairwise_diffs.append(
                ModelEvaluationDiff(
                    url=url,
                    title=title,
                    base_engine=base.evaluation_method or "unknown",
                    base_score=base.suspicion_score,
                    base_confidence=base.confidence_score,
                    base_violations_count=base.violations_count,
                    target_engine=target.evaluation_method or "unknown",
                    target_score=target.suspicion_score,
                    target_confidence=target.confidence_score,
                    target_violations_count=target.violations_count,
                    score_delta=delta,
                    violations_overlap_count=overlap,
                    discrepancy_summary=discrepancy,
                    violations_added=sorted(target_rules - base_rules),
                    violations_removed=sorted(base_rules - target_rules),
                )
            )

    return ModelComparisonMatrix(
        url=url,
        title=title,
        content_sha256=content_sha,
        evaluations=revisions,
        pairwise_diffs=pairwise_diffs,
        has_heuristic_fallback=has_heuristic,
        has_llm_evaluation=has_llm,
    )
