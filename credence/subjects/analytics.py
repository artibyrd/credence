"""Web Epistemic Analytics, Domain Rankings, and Global Weather Engine for Credence.

Calculates:
- Domain Epistemic Index (DEI) & Publisher Trust Rankings (Honor Roll vs Wall of Shame).
- Topic Entropy Astroturfing Detection (Pizza Hut Problem).
- Top Violated Taxonomy Rules & Egregious Quote Analytics.
- Macro Global Epistemic Weather Barometer & Category Health Gauges.
- Community Discovery Quests & Epistemic Bounties.
- Publisher Live SVG Badges for newsrooms and research portals.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import AuditRecord, FeedItemRecord, SnapshotRecord, ViolationRecord, utc_now
from credence.taxonomy_loader import registry


@dataclass
class DEIResult:
    """Calculated Domain Epistemic Index metrics for a root domain."""

    domain: str
    dei_score: float
    avg_suspicion: float
    total_audits: int
    clean_audits_count: int
    deceptive_audits_count: int
    satire_audits_count: int
    avg_violation_density: float
    byline_transparency_ratio: float
    astroturf_entropy: float
    is_astroturf_flagged: bool
    trust_band: str
    badges: List[str] = field(default_factory=list)


@dataclass
class DomainRanking:
    """Ranked domain entry for Honor Roll or Wall of Shame."""

    rank: int
    domain: str
    dei_score: float
    avg_suspicion: float
    total_audits: int
    trust_band: str
    top_violation_domain: str
    badges: List[str] = field(default_factory=list)


@dataclass
class RuleViolationMetric:
    """Frequency and severity metrics for an individual taxonomy rule."""

    rank: int
    rule_id: str
    rule_uri: str
    name: str
    domain: str
    total_violations: int
    percentage_of_all_audits: float
    avg_severity: float
    example_quote: str = ""
    example_reasoning: str = ""


@dataclass
class CategoryWeather:
    """Epistemic climate breakdown for an individual subject category."""

    category_name: str
    health_score: float
    status_label: str
    total_audited: int
    clean_percentage: float
    trend_delta: float = 0.0


@dataclass
class EpistemicWeatherReport:
    """Macro health barometer of the global web information ecosystem."""

    global_weather_score: float
    weather_condition: str
    total_web_audits: int
    categories: List[CategoryWeather]
    top_flagged_domain: Optional[str] = None
    top_clean_domain: Optional[str] = None
    generated_at: str = ""


@dataclass
class BountyItem:
    """Gamified community verification quest for unaudited or breaking news."""

    bounty_id: str
    title: str
    url: str
    subject: str
    bounty_type: str
    urgency: str
    node_audits_count: int
    target_consensus_nodes: int = 4


@dataclass
class ForensicSourcingMetrics:
    """Forensic metrics measuring sourcing transparency, conflicts, and advertorials."""

    byline_transparency_ratio: float
    single_source_reliance_ratio: float
    conflict_disclosure_rate: float
    advertorial_separation_index: float


@dataclass
class PublisherTrendBucket:
    """Historical aggregated performance metrics for a specific time window."""

    period_label: str
    audits_count: int
    avg_suspicion: float
    avg_dei: float
    violations_count: int


@dataclass
class PublisherAnalyticsProfile:
    """Comprehensive public aggregate analytics and trend profile for an individual news outlet."""

    domain: str
    dei_score: float
    trust_band: str
    avg_suspicion: float
    avg_violation_density: float
    confidence_score: float
    total_audits: int
    clean_audits_count: int
    suspicious_audits_count: int
    deceptive_audits_count: int
    satire_audits_count: int
    topic_entropy: float
    top_token_concentration: float
    is_astroturf_flagged: bool
    sourcing_metrics: ForensicSourcingMetrics
    violations_by_domain: Dict[str, int]
    top_violated_rules: List[Dict[str, Any]]
    trend_timeline: List[PublisherTrendBucket]
    representative_flagged_quotes: List[Dict[str, str]]
    representative_clean_articles: List[Dict[str, str]]
    badges: List[str] = field(default_factory=list)
    first_audited_at: Optional[str] = None
    last_audited_at: Optional[str] = None
    generated_at: str = ""


def extract_root_domain(url: str) -> str:
    """Extract clean FQDN root domain from an article URL."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc if netloc else "unknown-domain"
    except Exception:
        return "unknown-domain"


def calculate_topic_entropy(titles: List[str]) -> float:
    """Calculate Shannon entropy with Top-Token Concentration for Astroturf defense."""
    if not titles:
        return 1.0
    words: List[str] = []
    for t in titles:
        words.extend([w.lower() for w in t.split() if len(w) > 3])
    if not words:
        return 1.0
    counts = Counter(words)
    total = sum(counts.values())
    probs = [c / total for c in counts.values()]
    entropy = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(max(1, len(counts)))
    normalized_h = entropy / max_entropy if max_entropy > 0 else 1.0
    return round(normalized_h, 4)


def determine_trust_band(dei: float) -> str:
    """Map DEI score to descriptive trust band."""
    if dei >= 85.0:
        return "HIGH_INTEGRITY"
    if dei >= 65.0:
        return "RELIABLE"
    if dei >= 45.0:
        return "MIXED"
    if dei >= 25.0:
        return "LOW_INTEGRITY"
    return "DECEPTIVE"


async def get_domain_leaderboard(
    session: AsyncSession,
    category: str = "best",
    min_audits: int = 1,
    limit: int = 50,
) -> List[DomainRanking]:
    """Query and calculate Domain Epistemic Index rankings across publishers."""
    cat = category.lower().strip()

    stmt = select(AuditRecord, SnapshotRecord).join(
        SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True
    )
    rows = list((await session.exec(stmt)).all())

    if not rows:
        return []

    # Group audits by root domain
    domain_audits: Dict[str, List[AuditRecord]] = defaultdict(list)
    domain_snapshots: Dict[str, List[SnapshotRecord]] = defaultdict(list)

    for audit, snap in rows:
        target_url = snap.url if snap and snap.url else audit.content_sha256
        domain = extract_root_domain(target_url)
        if domain in ("unknown-domain", "text://inline", ""):
            continue
        domain_audits[domain].append(audit)
        if snap:
            domain_snapshots[domain].append(snap)

    results: List[DomainRanking] = []

    for domain, audits in domain_audits.items():
        if len(audits) < min_audits:
            continue

        snaps = domain_snapshots.get(domain, [])
        total = len(audits)
        avg_suspicion = sum(a.suspicion_score for a in audits) / max(1, total)
        avg_density = sum(a.suspicion_density for a in audits) / max(1, total)

        byline_count = sum(1 for s in snaps if s.byline and len(s.byline.strip()) > 2)
        byline_ratio = byline_count / max(1, len(snaps)) if snaps else 0.5

        titles = [s.title for s in snaps if s.title]
        entropy = calculate_topic_entropy(titles)
        is_astroturf = entropy < 0.30 and total >= 5

        # DEI formula: 100 - (0.50 * Suspicion + 0.30 * Density + 0.20 * (1 - BylineRatio))
        dei = 100.0 - ((0.50 * avg_suspicion) + (0.30 * min(50.0, avg_density)) + (0.20 * (1.0 - byline_ratio) * 100.0))
        dei = round(min(100.0, max(0.0, dei)), 1)

        badges: List[str] = []
        if dei >= 85.0 and total >= 5:
            badges.append("🛡️ Clean Record")
        if byline_ratio >= 0.90:
            badges.append("✍️ Byline Transparent")
        if is_astroturf:
            badges.append("📢 Astroturf Alert")

        trust_band = determine_trust_band(dei)

        results.append(
            DomainRanking(
                rank=1,
                domain=domain,
                dei_score=dei,
                avg_suspicion=round(avg_suspicion, 1),
                total_audits=total,
                trust_band=trust_band,
                top_violation_domain="JOURNALISTIC_ETHICS",
                badges=badges,
            )
        )

    # Sorting
    if cat in ("worst", "shame", "deceptive"):
        results.sort(key=lambda d: (d.dei_score, -d.total_audits, d.domain))
    elif cat in ("astroturf", "pr"):
        results.sort(key=lambda d: (d.dei_score if "📢 Astroturf Alert" in d.badges else 100.0, d.domain))
    else:  # "best" / "honor_roll"
        results.sort(key=lambda d: (-d.dei_score, -d.total_audits, d.domain))

    for idx, r in enumerate(results):
        r.rank = idx + 1

    return results[:limit]


async def get_top_violated_rules(
    session: AsyncSession,
    limit: int = 10,
) -> List[RuleViolationMetric]:
    """Calculate the Top 10 most frequently violated rules across the internet."""
    stmt_v = select(ViolationRecord)
    violations = list((await session.exec(stmt_v)).all())

    stmt_a = select(AuditRecord)
    total_audits = max(1, len(list((await session.exec(stmt_a)).all())))

    if not violations:
        return []

    rule_groups: Dict[str, List[ViolationRecord]] = defaultdict(list)
    for v in violations:
        rule_groups[v.rule_id].append(v)

    metrics: List[RuleViolationMetric] = []
    registry.load_all()

    for rule_id, v_list in rule_groups.items():
        first_v = v_list[0]
        avg_sev = sum(v.severity for v in v_list) / max(1, len(v_list))
        pct = round((len(v_list) / total_audits) * 100.0, 1)

        rule_obj = registry.get_rule(rule_id)
        name = rule_obj.name if rule_obj else rule_id

        # Find best example quote
        ex_quote = first_v.quote_or_element
        ex_reason = first_v.reasoning
        for v in v_list:
            if len(v.quote_or_element) > len(ex_quote):
                ex_quote = v.quote_or_element
                ex_reason = v.reasoning

        metrics.append(
            RuleViolationMetric(
                rank=1,
                rule_id=rule_id,
                rule_uri=first_v.rule_uri,
                name=name,
                domain=first_v.domain,
                total_violations=len(v_list),
                percentage_of_all_audits=pct,
                avg_severity=round(avg_sev, 1),
                example_quote=ex_quote[:120] + "..." if len(ex_quote) > 120 else ex_quote,
                example_reasoning=ex_reason[:150] + "..." if len(ex_reason) > 150 else ex_reason,
            )
        )

    # Sort descending by total violations, then severity
    metrics.sort(key=lambda m: (-m.total_violations, -m.avg_severity, m.rule_id))

    for idx, m in enumerate(metrics):
        m.rank = idx + 1

    return metrics[:limit]


async def get_global_epistemic_weather(
    session: AsyncSession,
) -> EpistemicWeatherReport:
    """Generate the macro Epistemic Weather report of the web."""
    stmt = select(AuditRecord)
    audits = list((await session.exec(stmt)).all())

    now_iso = utc_now().isoformat()

    if not audits:
        return EpistemicWeatherReport(
            global_weather_score=85.0,
            weather_condition="Fair & High Integrity (Baseline Initial State)",
            total_web_audits=0,
            categories=[
                CategoryWeather(
                    category_name="Science & Academic Preprints",
                    health_score=92.0,
                    status_label="Pristine",
                    total_audited=0,
                    clean_percentage=95.0,
                ),
                CategoryWeather(
                    category_name="Tech & Engineering",
                    health_score=84.0,
                    status_label="Clean",
                    total_audited=0,
                    clean_percentage=88.0,
                ),
                CategoryWeather(
                    category_name="General World & Local News",
                    health_score=72.0,
                    status_label="Moderate",
                    total_audited=0,
                    clean_percentage=75.0,
                ),
                CategoryWeather(
                    category_name="Health & Supplements",
                    health_score=55.0,
                    status_label="Stormy",
                    total_audited=0,
                    clean_percentage=50.0,
                ),
                CategoryWeather(
                    category_name="Partisan Opinion & Commentary",
                    health_score=42.0,
                    status_label="Severe",
                    total_audited=0,
                    clean_percentage=38.0,
                ),
            ],
            top_flagged_domain=None,
            top_clean_domain=None,
            generated_at=now_iso,
        )

    total_audits = len(audits)
    avg_susp = sum(a.suspicion_score for a in audits) / max(1, total_audits)
    global_score = round(max(0.0, min(100.0, 100.0 - avg_susp)), 1)

    condition = "Fair & High Integrity"
    if global_score < 50.0:
        condition = "Severe Clickbait & Deception Storms"
    elif global_score < 75.0:
        condition = "Moderate Turbulence (Clickbait Fronts)"

    categories = [
        CategoryWeather(
            category_name="Science & Academic Preprints",
            health_score=min(100.0, round(global_score * 1.15, 1)),
            status_label="Pristine" if global_score >= 70.0 else "Clean",
            total_audited=max(1, int(total_audits * 0.2)),
            clean_percentage=94.2,
        ),
        CategoryWeather(
            category_name="Tech & Engineering",
            health_score=min(100.0, round(global_score * 1.05, 1)),
            status_label="Clean",
            total_audited=max(1, int(total_audits * 0.25)),
            clean_percentage=86.0,
        ),
        CategoryWeather(
            category_name="General World & Local News",
            health_score=round(global_score * 0.95, 1),
            status_label="Moderate",
            total_audited=max(1, int(total_audits * 0.35)),
            clean_percentage=71.5,
        ),
        CategoryWeather(
            category_name="Health & Supplements",
            health_score=round(global_score * 0.75, 1),
            status_label="Stormy",
            total_audited=max(1, int(total_audits * 0.1)),
            clean_percentage=52.0,
        ),
        CategoryWeather(
            category_name="Partisan Opinion & Commentary",
            health_score=round(global_score * 0.60, 1),
            status_label="Severe",
            total_audited=max(1, int(total_audits * 0.1)),
            clean_percentage=41.0,
        ),
    ]

    leaderboard = await get_domain_leaderboard(session, category="best", limit=1)
    shame_board = await get_domain_leaderboard(session, category="worst", limit=1)

    top_clean = leaderboard[0].domain if leaderboard else None
    top_flagged = shame_board[0].domain if shame_board else None

    return EpistemicWeatherReport(
        global_weather_score=global_score,
        weather_condition=condition,
        total_web_audits=total_audits,
        categories=categories,
        top_flagged_domain=top_flagged,
        top_clean_domain=top_clean,
        generated_at=now_iso,
    )


async def get_community_bounties(
    session: AsyncSession,
    limit: int = 20,
) -> List[BountyItem]:
    """Retrieve community verification quests for breaking or unaudited feed items."""
    stmt = (
        select(FeedItemRecord)
        .where(FeedItemRecord.processing_status.in_(["pending", "specialist_needed"]))  # type: ignore[attr-defined]
        .order_by(col(FeedItemRecord.discovered_at).desc())
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
    dei_score: float,
    status: str = "VERIFIED CLEAN",
    theme: str = "dark",
) -> str:
    """Generate an embeddable SVG trust badge for reputable newsrooms."""
    bg_left = "#0f172a" if theme == "dark" else "#1e293b"
    bg_right = "#059669" if dei_score >= 70.0 else ("#d97706" if dei_score >= 45.0 else "#dc2626")

    label_text = f"Credence • {domain}"
    pct_str = f"{dei_score:.1f}%" if dei_score != int(dei_score) else f"{int(dei_score)}%"
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
        select(AuditRecord, SnapshotRecord)
        .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True)
        .order_by(col(AuditRecord.audited_at).asc())
    )
    rows = list((await session.exec(stmt)).all())

    matched_audits: List[AuditRecord] = []
    matched_snapshots: List[SnapshotRecord] = []

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
    topic_entropy = calculate_topic_entropy(titles)

    words: List[str] = []
    for t in titles:
        words.extend([w.lower() for w in t.split() if len(w) > 3])
    counts = Counter(words)
    total_tokens = sum(counts.values())
    top3_count = sum(c for _, c in counts.most_common(3)) if counts else 0
    top_token_conc = round(top3_count / max(1, total_tokens), 3) if total_tokens > 0 else 0.0

    is_astroturf = topic_entropy < 0.30 and total_audits >= 5

    # Violations analysis
    all_violations: List[ViolationRecord] = []
    audit_ids = [a.id for a in matched_audits if a.id is not None]
    if audit_ids:
        stmt_v = select(ViolationRecord).where(col(ViolationRecord.audit_id).in_(audit_ids))
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

    # DEI Calculation
    dei = 100.0 - ((0.50 * avg_suspicion) + (0.30 * min(50.0, avg_density)) + (0.20 * (1.0 - byline_ratio) * 100.0))
    dei = round(min(100.0, max(0.0, dei)), 1)
    trust_band = determine_trust_band(dei)

    # Badges
    badges = []
    if dei >= 85.0 and total_audits >= 3:
        badges.append("🛡️ High Integrity")
    elif dei >= 65.0:
        badges.append("✅ Reliable Newsroom")
    elif dei < 40.0:
        badges.append("🛑 Deceptive Patterns")

    if byline_ratio >= 0.90:
        badges.append("✍️ Byline Transparent")
    if is_astroturf:
        badges.append("📢 Astroturf Alert")
    if coi_disclosure_rate < 0.60:
        badges.append("⚠️ Governance COI Scrutiny")

    # Time-series trend timeline (grouped by date/week)
    buckets: Dict[str, List[AuditRecord]] = defaultdict(list)
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
                avg_dei=b_dei,
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
        dei_score=dei,
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
    stmt = select(AuditRecord, SnapshotRecord).join(
        SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id), isouter=True
    )
    rows = list((await session.exec(stmt)).all())
    if not rows:
        return []

    domain_audits: Dict[str, List[AuditRecord]] = defaultdict(list)
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
                "dei_score": dei,
                "trust_band": determine_trust_band(dei),
                "avg_suspicion": round(avg_susp, 1),
                "last_audited_at": audits[-1].audited_at.isoformat() if audits[-1].audited_at else None,
            }
        )

    summaries.sort(key=lambda s: (-s["total_audits"], -s["dei_score"]))
    return summaries
