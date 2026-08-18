"""Dynamic Feed Quality Scoring & Pre-Flight Forensic Audit Engine.

Calculates the continuous Epistemic Feed Quality Metric (F_j):
  F_j = 0.35 * (1.0 - S_bar / 100) + 0.25 * G_j + 0.20 * H_topic + 0.20 * T_freshness

Protects the mesh from the 'Pizza Hut Problem' (corporate takeovers, commercial
astroturfing, and sudden drops in journalistic grounding).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.parser import ParsedFeed, fetch_and_parse_feed
from credence.ingestion.extractor import extract_clean_content
from credence.ingestion.snapshot import DualCaptureResult
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.schemas import AuditReport


@dataclass
class FeedQualityMetrics:
    """Itemized components of the dynamic feed health score."""

    composite_score_fj: float  # Range: 0.0 to 1.0
    avg_suspicion_score: float  # Range: 0.0 to 100.0
    grounding_ratio: float  # Range: 0.0 to 1.0 (Verbatim quote precision)
    topic_entropy: float  # Range: 0.0 to 1.0 (Diversity vs commercial clustering)
    freshness_index: float  # Range: 0.0 to 1.0
    status: str  # 'ACTIVE', 'PROBATION', 'QUARANTINE'
    total_articles_sampled: int
    summary: str


@dataclass
class PreflightAuditResult:
    """Result of an initial forensic audit on a candidate feed."""

    feed_url: str
    feed_title: str
    metrics: FeedQualityMetrics
    sampled_articles: List[dict]
    is_recommended: bool
    quarantine_reasons: List[str]


def calculate_topic_entropy(article_texts: List[str]) -> float:
    """Calculate normalized Shannon entropy over semantic content tokens.

    Detects sudden commercial astroturfing or single-product propaganda pivots.
    High entropy (0.7-1.0) = healthy diverse editorial coverage.
    Low entropy (<0.3) = single-topic repetitive promotional spam (e.g. 90% pizza articles).
    """
    if not article_texts:
        return 0.5

    all_tokens: List[str] = []
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "over",
        "after",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "they",
        "their",
        "them",
        "we",
        "our",
        "you",
        "your",
        "said",
        "will",
        "would",
        "could",
        "should",
        "not",
        "new",
        "also",
        "more",
        "one",
    }

    for text in article_texts:
        words = re.findall(r"\b[a-z]{3,15}\b", text.lower())
        meaningful = [w for w in words if w not in stop_words]
        all_tokens.extend(meaningful)

    if len(all_tokens) < 20:
        return 0.5

    counts = Counter(all_tokens)
    total = len(all_tokens)

    # Compute Shannon entropy H = - sum(p * log2(p))
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)

    # Calculate Top-3 Token Concentration Penalty (detects repetitive single-topic promotional spam)
    top_3_counts = sum(cnt for _, cnt in counts.most_common(3))
    concentration = top_3_counts / total  # e.g., 0.10 for diverse news, 0.40+ for repetitive spam

    # Max possible entropy over total token length
    max_entropy = math.log2(total) if total > 1 else 1.0
    raw_entropy_ratio = entropy / max_entropy if max_entropy > 0 else 0.5

    # Diversity score combines entropy and vocabulary dispersion
    diversity = raw_entropy_ratio * (1.0 - (concentration * 1.5))
    return round(min(1.0, max(0.0, diversity)), 3)


def calculate_feed_quality_score(
    reports: List[AuditReport],
    published_dates: Optional[List[datetime]] = None,
    now: Optional[datetime] = None,
) -> FeedQualityMetrics:
    """Calculate the 4-factor Epistemic Feed Quality Metric (F_j)."""
    current_time = now or datetime.now(timezone.utc)
    n = len(reports)
    if n == 0:
        return FeedQualityMetrics(
            composite_score_fj=0.50,
            avg_suspicion_score=0.0,
            grounding_ratio=1.0,
            topic_entropy=0.50,
            freshness_index=0.50,
            status="PROBATION",
            total_articles_sampled=0,
            summary="No articles evaluated yet (default baseline).",
        )

    # Factor 1: Average Suspicion Score S_bar (Inverted: low suspicion = high quality)
    avg_suspicion = sum(r.suspicion_score for r in reports) / n
    suspicion_component = max(0.0, min(1.0, 1.0 - (avg_suspicion / 100.0)))

    # Factor 2: Grounding Precision Ratio (G_j)
    total_violations = sum(len(r.violations) for r in reports)
    grounded_violations = sum(sum(1 for v in r.violations if v.is_grounded) for r in reports)
    grounding_ratio = (grounded_violations / total_violations) if total_violations > 0 else 1.0

    # Factor 3: Topic Entropy (H_topic)
    article_texts = [r.url for r in reports]  # Fallback text representation
    topic_entropy = calculate_topic_entropy(article_texts)

    # Factor 4: Freshness Index (T_freshness)
    freshness = 0.8
    if published_dates:
        valid_dates = [d for d in published_dates if d is not None]
        if valid_dates:
            newest = max(valid_dates)
            if newest.tzinfo is None:
                newest = newest.replace(tzinfo=timezone.utc)
            delta_hours = max(0.0, (current_time - newest).total_seconds() / 3600.0)
            # Decays linearly from 1.0 (0h) down to 0.2 (168h / 7 days)
            freshness = max(0.2, min(1.0, 1.0 - (delta_hours / 240.0)))

    # Compute Composite Metric: F_j = 0.35*S + 0.25*G + 0.20*H + 0.20*T
    composite_fj = 0.35 * suspicion_component + 0.25 * grounding_ratio + 0.20 * topic_entropy + 0.20 * freshness
    composite_fj = round(min(1.0, max(0.0, composite_fj)), 3)

    # Classify Status Thresholds
    if composite_fj >= 0.70:
        status = "ACTIVE"
        summary = f"High epistemic quality (F_j = {composite_fj:.2f}). Approved for active mesh rotation."
    elif composite_fj >= 0.40:
        status = "PROBATION"
        summary = f"Moderate quality / probation (F_j = {composite_fj:.2f}). Evaluated on token headroom."
    else:
        status = "QUARANTINE"
        summary = f"Low epistemic health (F_j = {composite_fj:.2f}). Evicted to quarantine."

    return FeedQualityMetrics(
        composite_score_fj=composite_fj,
        avg_suspicion_score=round(avg_suspicion, 1),
        grounding_ratio=round(grounding_ratio, 3),
        topic_entropy=round(topic_entropy, 3),
        freshness_index=round(freshness, 3),
        status=status,
        total_articles_sampled=n,
        summary=summary,
    )


async def run_preflight_feed_audit(
    feed_url: str,
    session: Optional[AsyncSession] = None,
    max_sample_articles: int = 5,
) -> PreflightAuditResult:
    """Execute an initial forensic pre-flight audit against a candidate feed."""
    parsed: ParsedFeed = await fetch_and_parse_feed(feed_url)
    if not parsed.entries:
        return PreflightAuditResult(
            feed_url=feed_url,
            feed_title=parsed.title or "Unknown Feed",
            metrics=FeedQualityMetrics(
                composite_score_fj=0.0,
                avg_suspicion_score=100.0,
                grounding_ratio=0.0,
                topic_entropy=0.0,
                freshness_index=0.0,
                status="QUARANTINE",
                total_articles_sampled=0,
                summary="Feed returned 0 entries or failed to parse.",
            ),
            sampled_articles=[],
            is_recommended=False,
            quarantine_reasons=["Feed contains no readable articles."],
        )

    # Sample top N articles
    sample_entries = parsed.entries[:max_sample_articles]
    reports: List[AuditReport] = []
    sampled_metadata: List[dict] = []
    article_texts: List[str] = []
    published_dates: List[datetime] = []
    quarantine_reasons: List[str] = []

    for entry in sample_entries:
        raw_html = f"<html><head><title>{entry.title}</title></head><body><h1>{entry.title}</h1><p>{entry.summary or entry.title}</p></body></html>"
        extracted = extract_clean_content(raw_html, url=entry.url)
        article_texts.append(f"{entry.title} {entry.summary or ''}")
        if entry.published_at:
            published_dates.append(entry.published_at)

        snapshot = DualCaptureResult(
            url=entry.url,
            raw_html=raw_html,
            extracted=extracted,
            content_sha256="sha256:preflight_sample",
            simhash_64="0x12345",
            screenshot_file_path=None,
        )

        report = await evaluate_snapshot(snapshot, session=session, sign_result=False)
        reports.append(report)
        sampled_metadata.append(
            {
                "url": entry.url,
                "title": entry.title,
                "score": report.suspicion_score,
                "verdict": report.classification,
            }
        )

    # Compute topic entropy over sampled article texts
    topic_entropy = calculate_topic_entropy(article_texts)
    metrics = calculate_feed_quality_score(reports, published_dates=published_dates)
    # Overwrite with actual text entropy
    metrics.topic_entropy = topic_entropy
    metrics.composite_score_fj = round(
        0.35 * (1.0 - metrics.avg_suspicion_score / 100.0)
        + 0.25 * metrics.grounding_ratio
        + 0.20 * metrics.topic_entropy
        + 0.20 * metrics.freshness_index,
        3,
    )

    if metrics.topic_entropy < 0.25:
        quarantine_reasons.append(
            "Extreme topic clustering detected (suspected commercial astroturfing or native ad takeover)."
        )
    if metrics.avg_suspicion_score > 60.0:
        quarantine_reasons.append(
            f"High suspicion density detected across sampled coverage (avg score: {metrics.avg_suspicion_score:.1f})."
        )
    if metrics.grounding_ratio < 0.70:
        quarantine_reasons.append("Low citation grounding precision (<70% verifiable quotes).")

    is_recommended = metrics.composite_score_fj >= 0.60 and len(quarantine_reasons) == 0

    return PreflightAuditResult(
        feed_url=feed_url,
        feed_title=parsed.title or "Syndicated Feed",
        metrics=metrics,
        sampled_articles=sampled_metadata,
        is_recommended=is_recommended,
        quarantine_reasons=quarantine_reasons,
    )
