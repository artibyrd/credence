"""Empirical Domain Expertise and Subject-Weighted Authority Engine.

Calculates mathematical expertise scores E_i(subject) strictly from observed
historical evaluations, concordance with network robust median, and verbatim
citation grounding — completely eliminating reliance on static signed diplomas.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import DomainMetric, utc_now


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


def compute_subject_expertise(metrics: DomainMetrics) -> float:
    """Calculate empirical subject expertise score E_i(subject) in [0.05, 1.0].

    Formula:
        E_i(subject) = 0.40 * C_{i, sub} + 0.35 * G_{i, sub} + 0.15 * V_{i, sub} + 0.10 * L_{i, sub}
        Adjusted by slashing penalties for hallucinated/erratic findings.
        Includes Galileo Rule protection: verified verbatim grounding (G >= 0.85)
        mitigates swarm deviation penalties to allow whistleblowers to build authority.
    """
    if metrics.evaluations_count <= 0:
        return 0.05

    # 1. Domain Citation Grounding G (35%): Ratio of verbatim DOM-grounded quotes
    total_q = max(1, metrics.total_quotes_count)
    grounding_ratio = min(1.0, max(0.0, metrics.grounded_quotes_count / total_q))

    # 2. Domain Concordance C (40%): Deviation from Robust Median with Galileo Protection
    avg_deviation = metrics.median_deviations_sum / max(1, metrics.evaluations_count)
    raw_concordance = max(0.0, 1.0 - (avg_deviation / 25.0))

    if grounding_ratio >= 0.85 and metrics.grounded_quotes_count >= 5:
        # Galileo Adjustment: Grounded discovery cannot be suppressed by swarm divergence
        concordance = max(raw_concordance, 0.70 * grounding_ratio)
    else:
        concordance = raw_concordance

    # 3. Domain Volume & Entropy V (15%): Requires >= 25 evaluations across >= 5 distinct domains (Anti-Sybil)
    volume_count_ratio = min(1.0, metrics.evaluations_count / 25.0)
    domain_entropy_ratio = min(1.0, max(0.2, metrics.unique_domains_count / 5.0))
    volume_ratio = volume_count_ratio * domain_entropy_ratio

    # 4. Domain Longevity L (10%): Requires >= 30 days active history for full stability credit
    longevity_ratio = 0.1
    if metrics.first_evaluated_at and metrics.last_evaluated_at:
        days_active = max(0.0, (metrics.last_evaluated_at - metrics.first_evaluated_at).total_seconds() / 86400.0)
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
    """Update historical metrics and recalculate expertise for an observed audit."""
    stmt = select(DomainMetric).where(
        DomainMetric.node_pubkey == node_pubkey,
        DomainMetric.subject_id == subject_id,
    )
    result = await session.exec(stmt)
    record = result.first()

    now = utc_now()
    if not record:
        initial_domains = unique_domains if unique_domains is not None else 1
        record = DomainMetric(
            node_pubkey=node_pubkey,
            subject_id=subject_id,
            evaluations_count=1,
            median_deviations_sum=median_deviation,
            grounded_quotes_count=grounded_quotes,
            total_quotes_count=total_quotes,
            unique_domains_count=initial_domains,
            slashing_count=0,
            first_evaluated_at=now,
            last_evaluated_at=now,
        )
        session.add(record)
    else:
        record.evaluations_count += 1
        record.median_deviations_sum += median_deviation
        record.grounded_quotes_count += grounded_quotes
        record.total_quotes_count += total_quotes
        if unique_domains is not None:
            record.unique_domains_count = unique_domains
        elif origin_fqdn and record.unique_domains_count < 5:
            record.unique_domains_count = min(5, record.unique_domains_count + 1)
        record.last_evaluated_at = now

    metrics = DomainMetrics(
        evaluations_count=record.evaluations_count,
        median_deviations_sum=record.median_deviations_sum,
        grounded_quotes_count=record.grounded_quotes_count,
        total_quotes_count=record.total_quotes_count,
        unique_domains_count=record.unique_domains_count,
        slashing_count=record.slashing_count,
        first_evaluated_at=record.first_evaluated_at,
        last_evaluated_at=record.last_evaluated_at,
    )
    record.expertise_score = compute_subject_expertise(metrics)
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
    )
    record.expertise_score = compute_subject_expertise(metrics)
    await session.commit()
    await session.refresh(record)
    return record
