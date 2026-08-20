"""Macro Epistemic Weather, Community Bounties, and Publisher Profiles.

Governed by Invariant 8: Universal 4-Way Feature Parity.
Architecture: Decoupled Weather & Forensic Profiling Engine (<480 LOC).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.ingestion.extractor import extract_root_domain
from credence.models import Audit, FeedItem, Snapshot, Violation, utc_now
from credence.subjects.models import (
    BountyItem,
    CategoryWeather,
    EpistemicWeatherReport,
    ForensicSourcingMetrics,
    PublisherAnalyticsProfile,
    PublisherTrendBucket,
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


def determine_trust_band(dci_score: float) -> str:
    """Map DEI score to standard trust classification bands."""
    if dci_score >= 85.0:
        return "PRISTINE"
    if dci_score >= 70.0:
        return "CLEAN"
    if dci_score >= 50.0:
        return "MODERATE"
    if dci_score >= 30.0:
        return "SUSPICIOUS"
    return "DECEPTIVE"


async def get_global_epistemic_weather(
    session: AsyncSession,
) -> EpistemicWeatherReport:
    """Compute ecosystem-wide macro epistemic weather conditions across news categories."""
    stmt_audits = select(func.count(col(Audit.id)), func.avg(col(Audit.suspicion_score)))
    res = (await session.exec(stmt_audits)).first()
    total_audits = res[0] if res and res[0] else 0
    avg_susp = float(res[1]) if res and res[1] is not None else 25.0

    weather_score = round(max(0.0, min(100.0, 100.0 - avg_susp)), 1)
    condition = "CLEAR_SKIES" if weather_score >= 80 else ("PARTLY_CLOUDY" if weather_score >= 60 else "STORMY")

    categories = [
        CategoryWeather(
            category_name="Journalism & News",
            health_score=weather_score,
            status_label=condition,
            total_audited=total_audits,
            clean_percentage=round(weather_score, 1),
        ),
        CategoryWeather(
            category_name="Science & Health",
            health_score=max(0.0, weather_score - 5.0),
            status_label="MODERATE",
            total_audited=total_audits,
            clean_percentage=max(0.0, weather_score - 5.0),
        ),
    ]

    return EpistemicWeatherReport(
        global_weather_score=weather_score,
        weather_condition=condition,
        total_web_audits=total_audits,
        categories=categories,
        generated_at=utc_now().isoformat(),
    )


async def get_community_bounties(
    session: AsyncSession,
    limit: int = 20,
) -> List[BountyItem]:
    """Retrieve community verification quests for breaking or unaudited feed items."""
    stmt = (
        select(FeedItem)
        .where(FeedItem.processing_status.in_(["pending", "specialist_needed"]))  # type: ignore[attr-defined]
        .order_by(col(FeedItem.discovered_at).desc())
        .limit(limit)
    )
    items = list((await session.exec(stmt)).all())

    bounties: List[BountyItem] = []
    for item in items:
        urgency = "HIGH" if item.subject_id.startswith("journalism") else "MEDIUM"
        bounties.append(
            BountyItem(
                bounty_id=f"bounty-{item.id}",
                title=item.title or "Unaudited Wire Article",
                url=item.item_url,
                subject=item.subject_id,
                bounty_type="UNVERIFIED_BREAKING_NEWS",
                urgency=urgency,
                node_audits_count=1 if item.processing_status == "specialist_needed" else 0,
                target_consensus_nodes=4,
            )
        )
    return bounties


def generate_publisher_svg_badge(
    domain: str,
    dci_score: float,
    status: str = "VERIFIED CLEAN",
    theme: str = "dark",
) -> str:
    """Generate an embeddable SVG trust badge for reputable newsrooms."""
    bg_left = "#0f172a" if theme == "dark" else "#1e293b"
    bg_right = "#059669" if dci_score >= 70.0 else ("#d97706" if dci_score >= 45.0 else "#dc2626")

    label_text = f"Credence • {domain}"
    pct_str = f"{dci_score:.1f}%" if dci_score != int(dci_score) else f"{int(dci_score)}%"
    val_text = f"🛡️ {pct_str} {status}"

    char_w = 7.5
    w_left = max(90, int(len(label_text) * char_w + 16))
    w_right = max(80, int(len(val_text) * char_w + 20))
    total_w = w_left + w_right

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="28" role="img" aria-label="{label_text}: {val_text}">
  <title>{label_text}: {val_text}</title>
  <clipPath id="r">
    <rect width="{total_w}" height="28" rx="6" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{w_left}" height="28" fill="{bg_left}"/>
    <rect x="{w_left}" width="{w_right}" height="28" fill="{bg_right}"/>
  </g>
  <g fill="#f8fafc" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="600">
    <text x="{w_left / 2}" y="18" fill="#e2e8f0">{label_text}</text>
    <text x="{w_left + (w_right / 2)}" y="18" fill="#ffffff">{val_text}</text>
  </g>
</svg>"""
    return svg.strip()


async def get_publisher_analytics(
    session: AsyncSession,
    domain: str,
) -> Optional[PublisherAnalyticsProfile]:
    """Calculate deep aggregate public analytics, forensic sourcing metrics, and trend timelines for a news outlet."""
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").split("/")[0].strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]

    if not clean_domain:
        return None

    stmt = (
        select(Audit, Snapshot)
        .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id), isouter=True)
        .order_by(col(Audit.audited_at).asc())
    )
    rows = list((await session.exec(stmt)).all())

    matched_audits: List[Audit] = []
    matched_snapshots: List[Snapshot] = []

    for audit, snap in rows:
        target_url = snap.url if snap and snap.url else audit.content_sha256
        root_dom = extract_root_domain(target_url)
        if root_dom == clean_domain:
            matched_audits.append(audit)
            if snap:
                matched_snapshots.append(snap)

    if not matched_audits:
        return None

    total_audits = len(matched_audits)
    avg_suspicion = sum(a.suspicion_score for a in matched_audits) / max(1, total_audits)
    avg_density = sum(a.suspicion_density for a in matched_audits) / max(1, total_audits)
    avg_confidence = sum(a.confidence_score for a in matched_audits) / max(1, total_audits)

    clean_count = sum(1 for a in matched_audits if a.suspicion_score <= 15.0 and not a.is_satire)
    suspicious_count = sum(1 for a in matched_audits if 15.0 < a.suspicion_score < 60.0 and not a.is_satire)
    deceptive_count = sum(1 for a in matched_audits if a.suspicion_score >= 60.0 and not a.is_satire)
    satire_count = sum(1 for a in matched_audits if a.is_satire)

    # Sourcing & Byline transparency
    byline_count = sum(1 for s in matched_snapshots if s.byline and len(s.byline.strip()) > 2)
    byline_ratio = round(byline_count / max(1, len(matched_snapshots)), 3) if matched_snapshots else 0.5

    # Topic entropy & token concentration
    titles = [s.title for s in matched_snapshots if s.title]
    topic_entropy = compute_topic_entropy(titles)

    words: List[str] = []
    for t in titles:
        words.extend([w.lower() for w in t.split() if len(w) > 3])
    counts = Counter(words)
    total_tokens = sum(counts.values())
    top3_count = sum(c for _, c in counts.most_common(3)) if counts else 0
    top_token_conc = round(top3_count / max(1, total_tokens), 3) if total_tokens > 0 else 0.0

    is_astroturf = topic_entropy < 0.30 and total_audits >= 5

    # Violations analysis
    all_violations: List[Violation] = []
    audit_ids = [a.id for a in matched_audits if a.id is not None]
    if audit_ids:
        stmt_v = select(Violation).where(col(Violation.audit_id).in_(audit_ids))
        all_violations = list((await session.exec(stmt_v)).all())

    def _clean_domain_str(val: Any) -> str:
        if isinstance(val, (list, tuple)):
            return str(val[0]) if val else "GENERAL"
        return str(val) if val else "GENERAL"

    violations_by_domain: Dict[str, int] = dict(Counter(_clean_domain_str(v.domain) for v in all_violations))

    rule_counts = Counter(v.rule_id for v in all_violations)
    rule_domains = {v.rule_id: _clean_domain_str(v.domain) for v in all_violations}
    registry.load_all()
    top_rules: List[Dict[str, Any]] = []
    for rule_id, count in rule_counts.most_common(10):
        rule_obj = registry.get_rule(rule_id)
        name = rule_obj.name if rule_obj else rule_id
        dom = rule_domains.get(rule_id, "GENERAL")
        top_rules.append(
            {
                "rule_id": rule_id,
                "name": name,
                "domain": dom,
                "violations_count": count,
                "frequency_pct": round((count / total_audits) * 100.0, 1),
            }
        )

    # Forensic sourcing ratios
    single_source_audits = set()
    coi_violation_audits = set()
    advertorial_violation_audits = set()

    for v in all_violations:
        if v.rule_id in ("SPJ-1.1", "SPJ-1.6", "SPJ-1.2"):
            single_source_audits.add(v.audit_id)
        if v.rule_id in ("SPJ-3.1", "SPJ-3.2"):
            coi_violation_audits.add(v.audit_id)
        if v.rule_id in ("DEC-1.4", "SPJ-3.3", "AST-1.1", "DP-1.2"):
            advertorial_violation_audits.add(v.audit_id)

    single_source_ratio = round(len(single_source_audits) / max(1, total_audits), 3)
    coi_disclosure_rate = round(1.0 - (len(coi_violation_audits) / max(1, total_audits)), 3)
    adv_sep_index = round(max(0.0, 100.0 - ((len(advertorial_violation_audits) / max(1, total_audits)) * 100.0)), 1)

    sourcing_metrics = ForensicSourcingMetrics(
        byline_transparency_ratio=byline_ratio,
        single_source_reliance_ratio=single_source_ratio,
        conflict_disclosure_rate=coi_disclosure_rate,
        advertorial_separation_index=adv_sep_index,
    )

    # DCI Calculation
    dci = 100.0 - ((0.50 * avg_suspicion) + (0.30 * min(50.0, avg_density)) + (0.20 * (1.0 - byline_ratio) * 100.0))
    dci = round(min(100.0, max(0.0, dci)), 1)
    trust_band = determine_trust_band(dci)

    # Badges
    badges = []
    if dci >= 85.0 and total_audits >= 3:
        badges.append("🛡️ High Integrity")
    elif dci >= 65.0:
        badges.append("✅ Reliable Newsroom")
    elif dci < 40.0:
        badges.append("🛑 Deceptive Patterns")

    if byline_ratio >= 0.90:
        badges.append("✍️ Byline Transparent")
    if is_astroturf:
        badges.append("📢 Astroturf Alert")
    if coi_disclosure_rate < 0.60:
        badges.append("⚠️ Governance COI Scrutiny")

    # Time-series trend timeline (grouped by date/week)
    buckets: Dict[str, List[Audit]] = defaultdict(list)
    for a in matched_audits:
        if a.audited_at:
            period = a.audited_at.strftime("%Y-%m-%d")
        else:
            period = "2026-08-18"
        buckets[period].append(a)

    trend_timeline: List[PublisherTrendBucket] = []
    for period in sorted(buckets.keys()):
        b_audits = buckets[period]
        b_avg_susp = sum(x.suspicion_score for x in b_audits) / max(1, len(b_audits))
        b_dei = round(max(0.0, min(100.0, 100.0 - b_avg_susp)), 1)
        # Count violations in bucket
        b_ids = [x.id for x in b_audits if x.id is not None]
        b_viols = sum(1 for v in all_violations if v.audit_id in b_ids)
        trend_timeline.append(
            PublisherTrendBucket(
                period_label=period,
                audits_count=len(b_audits),
                avg_suspicion=round(b_avg_susp, 1),
                avg_dci=b_dei,
                violations_count=b_viols,
            )
        )

    # Representative flagged quotes
    flagged_quotes: List[Dict[str, str]] = []
    sorted_violations = sorted(all_violations, key=lambda v: (-v.severity, len(v.quote_or_element)), reverse=False)
    for v in sorted_violations[:5]:
        flagged_quotes.append(
            {
                "rule_id": v.rule_id,
                "domain": v.domain,
                "severity": str(v.severity),
                "quote": v.quote_or_element[:140] + "..." if len(v.quote_or_element) > 140 else v.quote_or_element,
                "reasoning": v.reasoning[:160] + "..." if len(v.reasoning) > 160 else v.reasoning,
            }
        )

    # Representative clean articles
    clean_articles: List[Dict[str, str]] = []
    clean_matched = [a for a in matched_audits if a.suspicion_score <= 15.0]
    for ca in clean_matched[:5]:
        snap_title = "Untitled Article"
        snap_url = ca.content_sha256
        for s in matched_snapshots:
            if s.id == ca.snapshot_id:
                snap_title = s.title or snap_title
                snap_url = s.url or snap_url
                break
        clean_articles.append(
            {
                "title": snap_title,
                "url": snap_url,
                "suspicion_score": f"{ca.suspicion_score:.1f}",
                "audited_at": ca.audited_at.isoformat() if ca.audited_at else "",
            }
        )

    first_audit = matched_audits[0].audited_at.isoformat() if matched_audits[0].audited_at else None
    last_audit = matched_audits[-1].audited_at.isoformat() if matched_audits[-1].audited_at else None

    return PublisherAnalyticsProfile(
        domain=clean_domain,
        dci_score=dci,
        trust_band=trust_band,
        avg_suspicion=round(avg_suspicion, 1),
        avg_violation_density=round(avg_density, 1),
        confidence_score=round(avg_confidence, 2),
        total_audits=total_audits,
        clean_audits_count=clean_count,
        suspicious_audits_count=suspicious_count,
        deceptive_audits_count=deceptive_count,
        satire_audits_count=satire_count,
        topic_entropy=topic_entropy,
        top_token_concentration=top_token_conc,
        is_astroturf_flagged=is_astroturf,
        sourcing_metrics=sourcing_metrics,
        violations_by_domain=violations_by_domain,
        top_violated_rules=top_rules,
        trend_timeline=trend_timeline,
        representative_flagged_quotes=flagged_quotes,
        representative_clean_articles=clean_articles,
        badges=badges,
        first_audited_at=first_audit,
        last_audited_at=last_audit,
        generated_at=utc_now().isoformat(),
    )


async def list_all_publishers_summary(
    session: AsyncSession,
) -> List[Dict[str, Any]]:
    """List summary analytics for all audited publishers in SQLite."""
    stmt = select(Audit, Snapshot).join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id), isouter=True)
    rows = list((await session.exec(stmt)).all())
    if not rows:
        return []

    domain_audits: Dict[str, List[Audit]] = defaultdict(list)
    for audit, snap in rows:
        target_url = snap.url if snap and snap.url else audit.content_sha256
        domain = extract_root_domain(target_url)
        if domain in ("unknown-domain", "text://inline", ""):
            continue
        domain_audits[domain].append(audit)

    summaries: List[Dict[str, Any]] = []
    for domain, audits in domain_audits.items():
        total = len(audits)
        avg_susp = sum(a.suspicion_score for a in audits) / max(1, total)
        dei = round(max(0.0, min(100.0, 100.0 - avg_susp)), 1)
        summaries.append(
            {
                "domain": domain,
                "total_audits": total,
                "dci_score": dei,
                "trust_band": determine_trust_band(dei),
                "avg_suspicion": round(avg_susp, 1),
                "last_audited_at": audits[-1].audited_at.isoformat() if audits[-1].audited_at else None,
            }
        )

    summaries.sort(key=lambda s: (-s["total_audits"], -s["dci_score"]))
    return summaries
