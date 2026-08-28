"""Subject domain analytics, Domain Credence Index (DCI) calculation, and publisher leaderboards.

Governed by Invariant 8: Universal 4-Way Feature Parity & compute_* naming ontology.
Architecture: Modular Analytics Engine (<400 LOC).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, List

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.ingestion.extractor import extract_root_domain
from credence.models import Audit, Snapshot, Violation
from credence.subjects.models import (
    DomainRanking,
    RuleViolationMetric,
)
from credence.subjects.weather import (
    generate_publisher_svg_badge,
    get_community_bounties,
    get_global_epistemic_weather,
    get_publisher_analytics,
    list_all_publishers_summary,
)
from credence.taxonomy_loader import registry


def compute_topic_entropy(titles: List[str]) -> float:
    """Calculate normalized Shannon entropy H in [0.0, 1.0] across word token distributions."""
    if not titles:
        return 1.0

    words: List[str] = []
    for t in titles:
        for w in t.lower().split():
            clean_w = "".join(c for c in w if c.isalnum())
            if len(clean_w) > 3:
                words.append(clean_w)

    if not words:
        return 1.0

    counts = Counter(words)
    total = len(words)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)

    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    normalized_entropy = entropy / max(1e-9, max_entropy)
    return round(max(0.0, min(1.0, normalized_entropy)), 3)


def compute_dci_score(avg_suspicion: float, avg_density: float) -> float:
    """Compute the Domain Credence Index (DCI) in [0.0, 100.0] from suspicion score and density.

    Governed by Theme 2: Optical & Forensic Grounding.
    Formula: DCI = max(0.0, min(100.0, 100.0 - (0.60 * S_avg + 0.40 * min(50.0, V_density))))
    """
    dci = 100.0 - ((0.60 * avg_suspicion) + (0.40 * min(50.0, avg_density)))
    return round(min(100.0, max(0.0, dci)), 1)


def determine_trust_band(dci_score: float) -> str:
    """Map Domain Credence Index (DCI) score to standard 5-tier Trust Bands."""
    if dci_score >= 90.0:
        return "HIGH_INTEGRITY"
    if dci_score >= 80.0:
        return "RELIABLE"
    if dci_score >= 65.0:
        return "MONITORED"
    if dci_score >= 45.0:
        return "WATCHLIST"
    return "DECEPTIVE"


async def get_domain_leaderboard(
    session: AsyncSession,
    category: str = "best",
    limit: int = 50,
    min_audits: int = 1,
) -> List[DomainRanking]:
    """Retrieve ranked publisher domain leaderboards based on DEI scores."""
    stmt = select(Audit, Snapshot).join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id), isouter=True)
    rows = list((await session.exec(stmt)).all())

    if not rows:
        return []
    # filter min_audits if needed

    domain_audits: Dict[str, List[Audit]] = defaultdict(list)
    for audit, snap in rows:
        target_url = snap.url if snap and snap.url else audit.content_sha256
        domain = extract_root_domain(target_url)
        if domain in ("unknown-domain", "text://inline", ""):
            continue
        domain_audits[domain].append(audit)

    rankings: List[DomainRanking] = []
    for domain, audits in domain_audits.items():
        total = len(audits)
        avg_susp = sum(a.suspicion_score for a in audits) / max(1, total)
        avg_density = sum(a.suspicion_density for a in audits) / max(1, total)

        dci = compute_dci_score(avg_susp, avg_density)
        trust_band = determine_trust_band(dci)

        badges: List[str] = []
        if dci >= 85.0 and total >= 5:
            badges.append("HIGH_INTEGRITY")
        if total >= 20:
            badges.append("DEEPLY_AUDITED")

        rankings.append(
            DomainRanking(
                rank=1,
                domain=domain,
                total_audited=total,
                dci_score=dci,
                avg_suspicion_score=round(avg_susp, 1),
                avg_suspicion_density=round(avg_density, 2),
                trust_band=trust_band,
                top_violation_domain="JOURNALISTIC_ETHICS",
                badges=badges,
            )
        )

    cat = category.lower()
    if cat in ("worst", "shame", "deceptive"):
        rankings.sort(key=lambda r: (r.dci_score, -r.total_audited, r.domain))
    else:
        rankings.sort(key=lambda r: (-r.dci_score, -r.total_audited, r.domain))

    for idx, r in enumerate(rankings):
        r.rank = idx + 1

    return rankings[:limit]


async def get_top_violated_rules(
    session: AsyncSession,
    limit: int = 10,
) -> List[RuleViolationMetric]:
    """Calculate the most frequently breached taxonomy rules across all stored audits using SQL aggregates."""
    from sqlalchemy import func

    stmt_count = select(func.count(col(Audit.id)))
    total_audits_res = (await session.exec(stmt_count)).one_or_none()
    total_audits = max(1, total_audits_res or 1)

    stmt_agg = (
        select(
            Violation.rule_id,
            func.count(col(Violation.id)).label("v_count"),
            func.avg(col(Violation.severity)).label("v_avg_sev"),
        )
        .group_by(Violation.rule_id)
        .order_by(func.count(col(Violation.id)).desc(), func.avg(col(Violation.severity)).desc())
        .limit(limit)
    )
    agg_rows = (await session.exec(stmt_agg)).all()
    if not agg_rows:
        return []

    registry.load_all()
    metrics: List[RuleViolationMetric] = []

    for idx, (rule_id, count_val, avg_sev_val) in enumerate(agg_rows):
        rule_obj = registry.get_rule(rule_id)
        name = rule_obj.name if rule_obj else rule_id
        pct = round((count_val / total_audits) * 100.0, 1)

        # Retrieve a representative sample violation for quote and reasoning
        sample_stmt = select(Violation).where(Violation.rule_id == rule_id).limit(1)
        sample_v = (await session.exec(sample_stmt)).first()

        ex_quote = sample_v.quote_or_element if sample_v else ""
        ex_reason = sample_v.reasoning if sample_v else ""
        rule_uri = sample_v.rule_uri if sample_v else f"credence://taxonomy/rules/{rule_id}"
        domain_name = sample_v.domain if sample_v else "unknown"

        metrics.append(
            RuleViolationMetric(
                rank=idx + 1,
                rule_id=rule_id,
                rule_uri=rule_uri,
                name=name,
                domain=domain_name,
                total_violations=int(count_val),
                percentage_of_all_audits=pct,
                avg_severity=round(float(avg_sev_val or 0.0), 1),
                example_quote=ex_quote[:120] + "..." if len(ex_quote) > 120 else ex_quote,
                example_reasoning=ex_reason[:150] + "..." if len(ex_reason) > 150 else ex_reason,
            )
        )

    return metrics


__all__ = [
    "get_publisher_analytics",
    "list_all_publishers_summary",
    "compute_topic_entropy",
    "determine_trust_band",
    "get_domain_leaderboard",
    "get_top_violated_rules",
    "get_global_epistemic_weather",
    "generate_publisher_svg_badge",
    "get_community_bounties",
]
