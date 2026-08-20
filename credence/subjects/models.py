"""Domain Analytics, Domain Credence Index (DCI), and Epistemic Weather Data Models.

Governed by Theme 2: Optical & Forensic Grounding & Theme 3: Meteorological Epistemics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DomainRanking:
    """Structured ranking metric for publisher domains."""

    rank: int
    domain: str
    total_audited: int
    dci_score: float
    avg_suspicion_score: float
    avg_suspicion_density: float
    trust_band: str
    top_violation_domain: str
    badges: List[str] = field(default_factory=list)
    total_audits: int = 0

    def __post_init__(self) -> None:
        if not self.total_audits and self.total_audited:
            self.total_audits = self.total_audited


@dataclass
class RuleViolationMetric:
    """Statistical metric for a single taxonomy rule violation."""

    rank: int
    rule_id: str
    rule_uri: str
    name: str
    domain: str
    total_violations: int
    percentage_of_all_audits: float
    avg_severity: float
    example_quote: str
    example_reasoning: str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class CategoryWeather:
    """Weather condition metric for a specific content category."""

    category_name: str
    health_score: float
    status_label: str
    total_audited: int = 0
    clean_percentage: float = 0.0


@dataclass
class EpistemicWeatherReport:
    """Macro epistemic weather report across web categories."""

    global_weather_score: float
    weather_condition: str
    total_web_audits: int
    categories: List[CategoryWeather]
    top_flagged_domain: Optional[str] = None
    top_clean_domain: Optional[str] = None
    generated_at: Optional[str] = None


@dataclass
class ForensicSourcingMetrics:
    """Forensic citation and transparency ratios."""

    byline_transparency_ratio: float
    single_source_reliance_ratio: float
    anonymous_sourcing_ratio: float = 0.0
    primary_source_grounding_ratio: float = 1.0
    conflict_disclosure_rate: float = 1.0
    advertorial_separation_index: float = 100.0


@dataclass
class PublisherTrendBucket:
    """Time-series audit bucket for publisher trends."""

    period_label: str
    audits_count: int
    avg_suspicion: float = 0.0
    avg_dci: float = 100.0
    clean_audits_count: int = 0
    violations_count: int = 0
    avg_suspicion_score: float = 0.0
    total_violations_count: int = 0


@dataclass
class PublisherAnalyticsProfile:
    """Deep forensic profile for a news outlet or domain."""

    domain: str
    dci_score: float
    trust_band: str
    byline_transparency_ratio: float = 1.0
    commercial_bias_risk: str = "LOW"
    topic_entropy: float = 1.0
    topic_entropy_score: float = 1.0
    top_token_concentration: float = 0.1
    is_astroturf_flagged: bool = False
    badges: List[str] = field(default_factory=list)
    total_audits: int = 0
    total_audits_count: int = 0
    clean_audits_count: int = 0
    suspicious_audits_count: int = 0
    deceptive_audits_count: int = 0
    satire_audits_count: int = 0
    avg_suspicion: float = 0.0
    average_suspicion_score: float = 0.0
    avg_violation_density: float = 0.0
    average_suspicion_density: float = 0.0
    confidence_score: float = 1.0
    sourcing_metrics: Optional[ForensicSourcingMetrics] = None
    violations_by_domain: Dict[str, int] = field(default_factory=dict)
    top_violated_rules: List[Any] = field(default_factory=list)
    representative_flagged_quotes: List[Any] = field(default_factory=list)
    representative_clean_articles: List[Any] = field(default_factory=list)
    trend_timeline: List[PublisherTrendBucket] = field(default_factory=list)
    first_audited_at: Optional[str] = None
    last_audited_at: Optional[str] = None
    generated_at: Optional[str] = None


@dataclass
class BountyItem:
    """Community bounties for un-audited high-impact news items."""

    bounty_id: str
    title: str
    url: str
    discovered_at: str = ""
    urgency: str = "MEDIUM"
    subject: str = "general"
    bounty_type: str = "VIRAL_VERIFICATION"
    node_audits_count: int = 0
    target_consensus_nodes: int = 3


@dataclass
class CommunityBounty:
    """Alias for BountyItem."""

    bounty_id: str
    title: str
    url: str
    urgency: str = "MEDIUM"


@dataclass
class CommunityBountiesResponse:
    """List response for open community bounties."""

    total_bounties: int
    bounties: List[BountyItem]
