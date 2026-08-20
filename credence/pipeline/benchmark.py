"""Automated Cross-Profile Epistemic Benchmark Suite.

Executes the Golden 12 benchmark fixtures across FREE, BALANCED, and ULTRA
profiles, computing cross-profile score deltas, confidence differentials, and
Bayesian consensus convergence.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import COST_PROFILES, CostProfile, CostProfileConfig
from credence.ingestion.extractor import extract_clean_content
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.schemas import AuditReport

console = Console()


class BenchmarkItemResult(BaseModel):
    """Evaluation result for a single benchmark fixture across cost profiles."""

    fixture_name: str
    title: str
    expected_pattern: str
    reports: Dict[str, AuditReport]  # Keyed by profile name: 'free', 'balanced', 'ultra'
    consensus_score: float
    consensus_verdict: str
    consensus_confidence: float


class BenchmarkSuiteResult(BaseModel):
    """Aggregate result for the complete benchmark suite."""

    total_fixtures: int
    items: List[BenchmarkItemResult]
    avg_free_score: float
    avg_balanced_score: float
    avg_ultra_score: float
    avg_consensus_score: float


# Golden 12 metadata index
GOLDEN_12_METADATA = {
    "clean_article.html": ("Ground Truth News", "Balanced investigative report with citations"),
    "satire_article.html": ("Overt Satire", "Parody news with unmistakable humor tropes"),
    "deceptive_page.html": ("Deceptive UI / Dark Patterns", "Urgency countdowns and forced actions"),
    "fallacious_op_ed.html": ("Fallacious Editorial", "False dilemmas and ad hominem attacks"),
    "sensational_clickbait.html": (
        "Clickbait Delta",
        "Panic headline vs mundane municipal announcements",
    ),
    "cloaked_native_ad.html": (
        "Cloaked Native Ad",
        "Undisclosed commercial promotion disguised as news",
    ),
    "unsupported_medical_claim.html": (
        "Unsourced Health Claims",
        "Miracle cure assertions with zero citations",
    ),
    "subtle_propaganda_framing.html": (
        "Subtle Partisan Framing",
        "Selective cherry-picking and loaded pejoratives",
    ),
    "cloaked_satire_defense.html": (
        "Bad-Faith Satire Defense",
        "Libel cloaked by microscopic 8pt satire footer",
    ),
    "transparent_correction.html": (
        "Transparent Correction",
        "Prominent timestamped editor's note (SPJ-4.3)",
    ),
    "synthetic_ai_slop.html": (
        "Synthetic AI Slop",
        "Repetitive sentence loops & hallucinated quotes",
    ),
    "statistical_distortion.html": (
        "Statistical Distortion",
        "Relative vs absolute risk conflation",
    ),
}


async def run_single_fixture_benchmark(
    fixture_path: Path,
    session: Optional[AsyncSession] = None,
) -> BenchmarkItemResult:
    """Evaluate a single HTML fixture across FREE, BALANCED, and ULTRA profiles."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    extracted = extract_clean_content(html_content, url=f"file://{fixture_path.name}")
    content_hash = compute_content_sha256(extracted.clean_text)
    simhash_hex = compute_simhash(extracted.clean_text)

    snapshot = DualCaptureResult(
        url=f"file://{fixture_path.name}",
        content_sha256=content_hash,
        simhash_64=simhash_hex,
        raw_html=html_content,
        extracted=extracted,
    )

    profile_reports: Dict[str, AuditReport] = {}
    for prof in (CostProfile.FREE, CostProfile.BALANCED, CostProfile.ULTRA):
        prof_cfg: CostProfileConfig = COST_PROFILES[prof]
        report = await evaluate_snapshot(
            snapshot,
            session=session,
            sign_result=True,
            profile_override=prof_cfg,
        )
        profile_reports[prof.value] = report

    # Calculate Bayesian multi-tier consensus across all 3 profiles
    aggregator = BayesianConsensusAggregator()
    verdict = aggregator.compute_consensus(list(profile_reports.values()))

    consensus_score = verdict.consensus_score if verdict else 0.0
    consensus_label = verdict.classification if verdict else "UNKNOWN"
    consensus_conf = verdict.confidence if verdict else 0.0

    meta_title, expected_pat = GOLDEN_12_METADATA.get(
        fixture_path.name, (extracted.title or fixture_path.stem, "General Evaluation")
    )

    return BenchmarkItemResult(
        fixture_name=fixture_path.name,
        title=meta_title,
        expected_pattern=expected_pat,
        reports=profile_reports,
        consensus_score=consensus_score,
        consensus_verdict=consensus_label,
        consensus_confidence=consensus_conf,
    )


async def run_epistemic_benchmark(
    fixtures_dir: Optional[Path] = None,
    session: Optional[AsyncSession] = None,
) -> BenchmarkSuiteResult:
    """Execute the complete Golden 12 benchmark suite and compute comparative metrics."""
    base_dir = fixtures_dir or Path("tests/fixtures/html")
    fixture_files = sorted([f for f in base_dir.glob("*.html") if f.name in GOLDEN_12_METADATA])

    tasks = [run_single_fixture_benchmark(f, session=session) for f in fixture_files]
    results = await asyncio.gather(*tasks)

    free_scores = [r.reports["free"].suspicion_score for r in results]
    bal_scores = [r.reports["balanced"].suspicion_score for r in results]
    ultra_scores = [r.reports["ultra"].suspicion_score for r in results]
    consensus_scores = [r.consensus_score for r in results]

    return BenchmarkSuiteResult(
        total_fixtures=len(results),
        items=results,
        avg_free_score=sum(free_scores) / max(len(free_scores), 1),
        avg_balanced_score=sum(bal_scores) / max(len(bal_scores), 1),
        avg_ultra_score=sum(ultra_scores) / max(len(ultra_scores), 1),
        avg_consensus_score=sum(consensus_scores) / max(len(consensus_scores), 1),
    )


def render_benchmark_table(suite: BenchmarkSuiteResult) -> None:
    """Render a formatted Rich table comparing evaluation across all 3 cost profiles."""
    table = Table(
        title="[bold]Credence 'Golden 12' Epistemic Benchmark & Multi-Tier Matrix[/bold]",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Benchmark Scenario", style="cyan", no_wrap=True)
    table.add_column("FREE Profile\n(Lite / 0 tok)", justify="center")
    table.add_column("BALANCED Profile\n(1k-4k tok)", justify="center")
    table.add_column("ULTRA Profile\n(4k-16k tok)", justify="center")
    table.add_column("Bayesian\nConsensus", justify="center", style="bold")

    for item in suite.items:
        free_r = item.reports.get("free")
        bal_r = item.reports.get("balanced")
        ultra_r = item.reports.get("ultra")

        free_txt = f"{free_r.suspicion_score:.1f} ({len(free_r.violations)}v)" if free_r else "N/A"
        bal_txt = f"{bal_r.suspicion_score:.1f} ({len(bal_r.violations)}v)" if bal_r else "N/A"
        ultra_txt = f"{ultra_r.suspicion_score:.1f} ({len(ultra_r.violations)}v)" if ultra_r else "N/A"

        c_color = "green" if item.consensus_score < 10 else "yellow" if item.consensus_score < 20 else "red"
        consensus_txt = f"[{c_color}]{item.consensus_score:.1f}[/{c_color}] ({item.consensus_verdict[:10]})"

        table.add_row(item.title, free_txt, bal_txt, ultra_txt, consensus_txt)

    console.print(table)
    console.print(
        f"[dim]Total Evaluated: {suite.total_fixtures} Fixtures | "
        f"Avg Free: {suite.avg_free_score:.1f} | "
        f"Avg Balanced: {suite.avg_balanced_score:.1f} | "
        f"Avg Ultra: {suite.avg_ultra_score:.1f} | "
        f"Avg Consensus: {suite.avg_consensus_score:.1f}[/dim]\n"
    )


async def run_benchmark(*args: Any, **kwargs: Any) -> int:
    return 0
    return 0
