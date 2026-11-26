"""Empirical Domain Expertise and Subject-Weighted Authority Engine.

Calculates mathematical expertise scores E_i(subject) strictly from observed
historical evaluations, concordance with network robust median, and verbatim
citation grounding — completely eliminating reliance on static signed diplomas.
"""

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import DomainMetric, utc_now

RECENT_WINDOW_SIZE = 20
SLASH_STREAK_THRESHOLD = 3


def _parse_recent_deviations(raw_json: Optional[str]) -> list[float]:
    """Parse JSON-serialized recent deviations into a bounded list of finite non-negative floats."""
    if not raw_json:
        return []
    try:
        parsed = json.loads(raw_json)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    cleaned: list[float] = []
    for item in parsed:
        try:
            val = abs(float(item))
        except (TypeError, ValueError):
            continue
        if math.isfinite(val):
            cleaned.append(val)
    return cleaned[-RECENT_WINDOW_SIZE:]


def compute_divergence_acceleration_dampening(
    recent_deviations: list[float],
    baseline_deviation: Optional[float] = None,
) -> float:
    """Compute Galileo protection strength in [0.0, 1.0] from recent deviation acceleration.

    A genuine expert who consistently diverges (beekeeper) has stable deviations (acceleration ≈ 0 -> 1.0).
    A long-con attacker who was concordant and suddenly pivots shows high acceleration (-> 0.0).
    When ``baseline_deviation`` is provided (pre-window lifetime average), acceleration also checks
    drift relative to that historical baseline to block slow-drip ramps and post-migration pivots.
    """
    cleaned: list[float] = []
    for d in recent_deviations:
        val = abs(float(d))
        if not math.isfinite(val):
            return 0.0
        cleaned.append(val)

    baseline: Optional[float] = None
    if baseline_deviation is not None:
        base_val = abs(float(baseline_deviation))
        if not math.isfinite(base_val):
            return 0.0
        baseline = base_val

    if not cleaned:
        return 1.0

    if len(cleaned) < 6:
        if baseline is None or len(cleaned) < 3:
            return 1.0
        mid = len(cleaned) // 2
        recent_avg = sum(cleaned[mid:]) / len(cleaned[mid:])
        acceleration = recent_avg - baseline
    else:
        mid = len(cleaned) // 2
        older_avg = sum(cleaned[:mid]) / mid
        recent_avg = sum(cleaned[mid:]) / len(cleaned[mid:])
        window_avg = sum(cleaned) / len(cleaned)
        acceleration = recent_avg - older_avg
        if baseline is not None:
            acceleration = max(acceleration, recent_avg - baseline, window_avg - baseline)

    if acceleration <= 5.0:
        return 1.0
    if acceleration >= 25.0:
        return 0.0
    return round(1.0 - ((acceleration - 5.0) / 20.0), 4)


def _compute_prior_baseline(
    evaluations_count: int,
    median_deviations_sum: float,
    recent_devs: list[float],
) -> Optional[float]:
    """Compute pre-window lifetime average deviation when enough prior history exists."""
    prior_count = evaluations_count - len(recent_devs)
    if prior_count < 6 or not recent_devs:
        return None
    recent_sum = sum(abs(float(d)) for d in recent_devs if math.isfinite(abs(float(d))))
    prior_sum = max(0.0, abs(float(median_deviations_sum)) - recent_sum)
    return prior_sum / prior_count


@dataclass
class DomainMetrics:
    """Historical evaluation metrics for a node within a specific subject."""

    evaluations_count: int = 0
    median_deviations_sum: float = 0.0
    grounded_quotes_count: int = 0
    total_quotes_count: int = 0
    unique_domains_count: int = 1
    slashing_count: int = 0
    first_evaluated_at: Optional[datetime] = None
    last_evaluated_at: Optional[datetime] = None
    recent_deviations: list[float] = field(default_factory=list)


def compute_subject_expertise(metrics: DomainMetrics) -> float:
    """Calculate empirical subject expertise score E_i(subject) in [0.05, 1.0].

    Formula:
        E_i(subject) = 0.40 * C_{i, sub} + 0.35 * G_{i, sub} + 0.15 * V_{i, sub} + 0.10 * L_{i, sub}
        Adjusted by slashing penalties for hallucinated/erratic findings.
        Includes acceleration-dampened Galileo Rule protection: verified verbatim grounding (G >= 0.85)
        mitigates swarm deviation penalties for stable specialists while collapsing on sudden pivots.
    """
    if metrics.evaluations_count <= 0:
        return 0.05

    # 1. Domain Citation Grounding G (35%): Ratio of verbatim DOM-grounded quotes
    total_q = max(1, metrics.total_quotes_count)
    grounding_ratio = min(1.0, max(0.0, metrics.grounded_quotes_count / total_q))

    # 2. Domain Concordance C (40%): Rolling-window & lifetime deviation with dampened Galileo Protection
    avg_deviation = abs(metrics.median_deviations_sum) / max(1, metrics.evaluations_count)
    lifetime_concordance = max(0.0, 1.0 - (avg_deviation / 25.0))

    recent_devs = metrics.recent_deviations or []
    if recent_devs:
        cleaned_recent = [abs(float(d)) for d in recent_devs]
        if any(not math.isfinite(d) for d in cleaned_recent):
            recent_concordance = 0.0
        else:
            recent_avg = sum(cleaned_recent) / len(cleaned_recent)
            recent_concordance = max(0.0, 1.0 - (recent_avg / 25.0))
        raw_concordance = min(lifetime_concordance, recent_concordance)
    else:
        raw_concordance = lifetime_concordance

    baseline = _compute_prior_baseline(
        metrics.evaluations_count,
        metrics.median_deviations_sum,
        recent_devs,
    )
    dampening = compute_divergence_acceleration_dampening(recent_devs, baseline_deviation=baseline)
    if grounding_ratio >= 0.85 and metrics.grounded_quotes_count >= 5:
        # Acceleration-dampened Galileo Adjustment: Grounded discovery cannot be suppressed
        # for stable experts (dampening == 1.0), but collapses to 0.0 on behavioral pivots.
        galileo_floor = 0.70 * grounding_ratio * dampening
        concordance = max(raw_concordance, galileo_floor)
    else:
        concordance = raw_concordance

    # 3. Domain Volume & Entropy V (15%): Requires >= 25 evaluations across >= 5 distinct domains (Anti-Sybil)
    volume_count_ratio = min(1.0, metrics.evaluations_count / 25.0)
    domain_entropy_ratio = min(1.0, max(0.2, metrics.unique_domains_count / 5.0))
    volume_ratio = volume_count_ratio * domain_entropy_ratio

    # 4. Domain Longevity L (10%): Requires >= 30 days active history for full stability credit
    longevity_ratio = 0.1
    if metrics.first_evaluated_at and metrics.last_evaluated_at:
        first_dt = (
            metrics.first_evaluated_at.replace(tzinfo=timezone.utc)
            if metrics.first_evaluated_at.tzinfo is None
            else metrics.first_evaluated_at
        )
        last_dt = (
            metrics.last_evaluated_at.replace(tzinfo=timezone.utc)
            if metrics.last_evaluated_at.tzinfo is None
            else metrics.last_evaluated_at
        )
        days_active = max(0.0, (last_dt - first_dt).total_seconds() / 86400.0)
        longevity_ratio = min(1.0, max(0.1, days_active / 30.0))

    # Composite unpenalized score
    raw_expertise = 0.40 * concordance + 0.35 * grounding_ratio + 0.15 * volume_ratio + 0.10 * longevity_ratio

    # Apply exponential slashing penalties for disproven / hallucinated findings
    slashing_factor = 0.5 ** min(5, metrics.slashing_count)
    penalized_score = raw_expertise * slashing_factor

    return round(min(1.0, max(0.05, penalized_score)), 4)


def compute_effective_weight(
    node_pubkey: str,
    subject_id: str,
    base_quality: float = 0.5,
    expertise_score: Optional[float] = None,
) -> float:
    """Calculate effective consensus authority weight W_i(subject).

    Formula:
        W_i(subject) = 0.20 * Q_i + 0.80 * E_i(subject)
    """
    exp = expertise_score if expertise_score is not None else 0.05
    effective = (0.20 * base_quality) + (0.80 * exp)
    return round(min(1.0, max(0.01, effective)), 4)


async def get_node_subject_expertise(
    session: AsyncSession,
    node_pubkey: str,
    subject_id: str,
) -> float:
    """Query or compute empirical expertise score for a node in a subject."""
    # Check if exact subject or parent subject exists
    stmt = select(DomainMetric).where(
        DomainMetric.node_pubkey == node_pubkey,
        DomainMetric.subject_id == subject_id,
    )
    result = await session.exec(stmt)
    record = result.first()

    if record:
        return record.expertise_score

    # Check parent subject fallback (e.g. apiculture fallback for apiculture.equipment)
    if "." in subject_id:
        parent_id = subject_id.rsplit(".", 1)[0]
        stmt_parent = select(DomainMetric).where(
            DomainMetric.node_pubkey == node_pubkey,
            DomainMetric.subject_id == parent_id,
        )
        parent_result = await session.exec(stmt_parent)
        parent_record = parent_result.first()
        if parent_record:
            # Discount parent expertise slightly (85% transfer)
            return round(max(0.05, parent_record.expertise_score * 0.85), 4)

    return 0.05


async def record_domain_evaluation(
    session: AsyncSession,
    node_pubkey: str,
    subject_id: str,
    median_deviation: float,
    grounded_quotes: int,
    total_quotes: int,
    origin_fqdn: Optional[str] = None,
    unique_domains: Optional[int] = None,
) -> DomainMetric:
    """Update historical metrics, rolling deviation window, and recalculate expertise for an audit."""
    dev = abs(float(median_deviation))
    if not math.isfinite(dev):
        raise ValueError("median_deviation must be finite")

    stmt = select(DomainMetric).where(
        DomainMetric.node_pubkey == node_pubkey,
        DomainMetric.subject_id == subject_id,
    )
    result = await session.exec(stmt)
    record = result.first()

    now = utc_now()
    if not record:
        initial_domains = unique_domains if unique_domains is not None else 1
        recent_devs = [dev]
        record = DomainMetric(
            node_pubkey=node_pubkey,
            subject_id=subject_id,
            evaluations_count=1,
            median_deviations_sum=dev,
            grounded_quotes_count=grounded_quotes,
            total_quotes_count=total_quotes,
            unique_domains_count=initial_domains,
            slashing_count=0,
            recent_deviations_json=json.dumps(recent_devs),
            consecutive_zero_dampening=0,
            first_evaluated_at=now,
            last_evaluated_at=now,
        )
        session.add(record)
    else:
        record.evaluations_count += 1
        record.median_deviations_sum += dev
        record.grounded_quotes_count += grounded_quotes
        record.total_quotes_count += total_quotes
        if unique_domains is not None:
            record.unique_domains_count = unique_domains
        elif origin_fqdn and record.unique_domains_count < 5:
            record.unique_domains_count = min(5, record.unique_domains_count + 1)
        record.last_evaluated_at = now

        recent_devs = _parse_recent_deviations(record.recent_deviations_json)
        recent_devs = (recent_devs + [dev])[-RECENT_WINDOW_SIZE:]
        record.recent_deviations_json = json.dumps(recent_devs)

    baseline = _compute_prior_baseline(
        record.evaluations_count,
        record.median_deviations_sum,
        recent_devs,
    )
    dampening = compute_divergence_acceleration_dampening(recent_devs, baseline_deviation=baseline)
    if dampening == 0.0:
        record.consecutive_zero_dampening += 1
    else:
        record.consecutive_zero_dampening = 0

    metrics = DomainMetrics(
        evaluations_count=record.evaluations_count,
        median_deviations_sum=record.median_deviations_sum,
        grounded_quotes_count=record.grounded_quotes_count,
        total_quotes_count=record.total_quotes_count,
        unique_domains_count=record.unique_domains_count,
        slashing_count=record.slashing_count,
        first_evaluated_at=record.first_evaluated_at,
        last_evaluated_at=record.last_evaluated_at,
        recent_deviations=recent_devs,
    )
    record.expertise_score = compute_subject_expertise(metrics)

    if record.consecutive_zero_dampening >= SLASH_STREAK_THRESHOLD:
        record.consecutive_zero_dampening = 0
        await session.flush()
        slashed = await slash_domain_expertise(session, node_pubkey, subject_id)
        if slashed is not None:
            return slashed

    await session.commit()
    await session.refresh(record)
    return record


async def slash_domain_expertise(
    session: AsyncSession,
    node_pubkey: str,
    subject_id: str,
) -> Optional[DomainMetric]:
    """Slash domain expertise by 50% upon detecting hallucination or malicious collusion."""
    stmt = select(DomainMetric).where(
        DomainMetric.node_pubkey == node_pubkey,
        DomainMetric.subject_id == subject_id,
    )
    result = await session.exec(stmt)
    record = result.first()

    if not record:
        return None

    record.slashing_count += 1
    metrics = DomainMetrics(
        evaluations_count=record.evaluations_count,
        median_deviations_sum=record.median_deviations_sum,
        grounded_quotes_count=record.grounded_quotes_count,
        total_quotes_count=record.total_quotes_count,
        unique_domains_count=record.unique_domains_count,
        slashing_count=record.slashing_count,
        first_evaluated_at=record.first_evaluated_at,
        last_evaluated_at=record.last_evaluated_at,
        recent_deviations=_parse_recent_deviations(record.recent_deviations_json),
    )
    record.expertise_score = compute_subject_expertise(metrics)
    await session.commit()
    await session.refresh(record)
    return record
