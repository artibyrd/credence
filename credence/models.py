"""SQLModel Database Models for Credence.

Defines schemas for:
- SnapshotRecord: Captured webpage metadata, DOM/screenshot paths, and cryptographic hashes.
- AuditRecord: Evaluated suspicion scores, satire flags, and attestation signatures.
- ViolationRecord: Granular rule violations linked to exact cited quotes and evidence.
- TokenUsageRecord: In-database token consumption, thinking tokens, and cost tracking.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class SnapshotRecord(SQLModel, table=True):
    """Stores metadata and content hashes for a dual-captured webpage snapshot."""

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, description="Target canonical URL")
    captured_at: datetime = Field(default_factory=utc_now, description="UTC snapshot timestamp")
    content_sha256: str = Field(index=True, description="Normalized text SHA-256 hash")
    simhash_64: str = Field(index=True, description="Hex representation of 64-bit SimHash")
    dom_file_path: Optional[str] = Field(default=None, description="Relative path to stored HTML DOM dump")
    screenshot_file_path: Optional[str] = Field(
        default=None, description="Relative path to stored visual screenshot PNG"
    )
    clean_text_length: int = Field(default=0, description="Length of cleaned extracted text")
    word_count: int = Field(default=0, description="Extracted text word count")
    title: Optional[str] = Field(default=None, description="Page title")
    byline: Optional[str] = Field(default=None, description="Author byline if detected")
    site_name: Optional[str] = Field(default=None, description="Publisher or site name")
    is_satire_cue: bool = Field(default=False, description="Whether snapshot contained explicit satire metadata cues")

    # Relationships
    audits: List["AuditRecord"] = Relationship(
        back_populates="snapshot",
        cascade_delete=True,
    )


class AuditRecord(SQLModel, table=True):
    """Stores full audit report, suspicion score, satire verdict, and cryptographic signature."""

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: int = Field(foreign_key="snapshotrecord.id", index=True)
    audited_at: datetime = Field(default_factory=utc_now, description="UTC audit timestamp")
    content_sha256: str = Field(index=True, description="SHA-256 of snapshot content")

    # Scoring & Calibration
    suspicion_score: float = Field(default=0.0, description="Calibrated suspicion score from 0.0 to 100.0")
    suspicion_density: float = Field(default=0.0, description="Violations per 1,000 words")
    confidence_score: float = Field(default=1.0, description="Aggregate evaluation confidence (0.0 to 1.0)")
    classification: str = Field(
        default="CLEAN", description="Verdict classification band (e.g. CLEAN, SUSPICIOUS, DECEPTIVE, SATIRE_PARODY)"
    )

    # Satire & Poe's Law Safeguards
    is_satire: bool = Field(default=False, index=True, description="True if content is comedic/satirical parody")
    content_type: str = Field(
        default="NEWS_ARTICLE",
        description="Content type category (e.g. NEWS_ARTICLE, OPINION, SATIRE_PARODY, ADVERTORIAL)",
    )
    satire_notes: Optional[str] = Field(default=None, description="Satire classification explanation or guidance")

    # Mesh & Attestation Signatures
    node_pubkey: Optional[str] = Field(default=None, description="Ed25519 public key of evaluating node")
    node_signature: Optional[str] = Field(
        default=None, description="Ed25519 cryptographic signature of attestation JSON"
    )
    taxonomies_used_json: str = Field(default="{}", description="JSON map of {catalog_id: catalog_hash}")
    quota_preserved: bool = Field(
        default=False, description="True if audit fell back to offline heuristics to preserve token quota"
    )
    evaluation_method: str = Field(
        default="llm_multi_agent",
        description="Method used for evaluation (llm_multi_agent or offline_structural_heuristic)",
    )

    # Relationships
    snapshot: Optional[SnapshotRecord] = Relationship(back_populates="audits")
    violations: List["ViolationRecord"] = Relationship(
        back_populates="audit",
        cascade_delete=True,
    )


class ViolationRecord(SQLModel, table=True):
    """Stores an itemized violation citing specific taxonomy rules and grounded excerpts."""

    id: Optional[int] = Field(default=None, primary_key=True)
    audit_id: int = Field(foreign_key="auditrecord.id", index=True)
    rule_id: str = Field(index=True, description="Rule code (e.g. SPJ-1.1, FALLACY-2.2, DP-1.1)")
    rule_uri: str = Field(index=True, description="Full namespaced rule URI")
    domain: str = Field(index=True, description="Root taxonomy domain (e.g. JOURNALISTIC_ETHICS)")
    cluster_id: str = Field(description="Thematic cluster ID")
    severity: int = Field(ge=1, le=5, description="Rule violation severity (1 to 5)")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0, description="Agent confidence in this violation")
    quote_or_element: str = Field(description="Exact grounded excerpt from text or DOM element")
    reasoning: str = Field(description="Justification connecting the quote to the violated rule")
    line_or_selector: Optional[str] = Field(default=None, description="Source line number or DOM CSS selector")

    # Relationships
    audit: Optional[AuditRecord] = Relationship(back_populates="violations")


class TokenUsageRecord(SQLModel, table=True):
    """Stores token consumption, thinking tokens, and estimated USD cost per subagent call."""

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=utc_now, index=True, description="UTC timestamp of API call")
    model_name: str = Field(index=True, description="Gemini model identifier (e.g. gemini-3.7-flash)")
    prompt_tokens: int = Field(default=0, description="Input prompt token count")
    completion_tokens: int = Field(default=0, description="Output candidate token count")
    thinking_tokens: int = Field(default=0, description="Reasoning/thinking token count")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated cost in USD")
    caller: str = Field(default="specialist", index=True, description="Subagent caller name")
    was_escalated: bool = Field(default=False, description="Whether this call was an escalated evaluation")


class PeerMetricRecord(SQLModel, table=True):
    """Stores observed peer node quality metrics and reputation history."""

    id: Optional[int] = Field(default=None, primary_key=True)
    node_pubkey: str = Field(index=True, unique=True, description="Ed25519 public key hex of the peer node")
    node_alias: str = Field(default="credence-node", description="Human-readable node label")
    ws_url: str = Field(description="WebSocket endpoint URL for the peer")
    last_seen: datetime = Field(
        default_factory=utc_now, index=True, description="Last successful communication timestamp"
    )
    first_seen: datetime = Field(default_factory=utc_now, description="First recorded appearance of node identity")
    total_heartbeats_sent: int = Field(default=0, description="Total ping/heartbeat attempts")
    successful_heartbeats: int = Field(default=0, description="Successful pong/heartbeat responses")
    average_latency_ms: float = Field(default=100.0, description="Exponential moving average latency in milliseconds")
    total_attestations_evaluated: int = Field(default=0, description="Number of consensus rounds participated in")
    median_score_deviations_sum: float = Field(
        default=0.0, description="Accumulated absolute deviation from robust median"
    )
    grounded_citations_count: int = Field(default=0, description="Verified verbatim cited quotes")
    total_citations_count: int = Field(default=0, description="Total cited quotes submitted by peer")
    has_valid_catalog_hashes: bool = Field(default=True, description="True if peer runs matching taxonomy versions")
    quality_score: float = Field(default=0.5, description="Composite calculated quality score (0.0 to 1.0)")
    is_seed_candidate: bool = Field(
        default=False, index=True, description="True if node qualifies as a top seed candidate"
    )


class SubjectRecord(SQLModel, table=True):
    """Stores registered hierarchical subject namespaces and evaluation taxonomy mappings."""

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: str = Field(
        index=True, unique=True, description="Hierarchical namespace ID (e.g. apiculture.equipment)"
    )
    title: str = Field(description="Human-readable subject title")
    description: str = Field(default="", description="Subject scope explanation")
    parent_id: Optional[str] = Field(default=None, index=True, description="Parent subject namespace ID")
    is_active: bool = Field(default=True, index=True, description="Whether subject is active for classification")
    created_at: datetime = Field(default_factory=utc_now, description="UTC registration timestamp")


class DomainMetricRecord(SQLModel, table=True):
    """Stores observed empirical domain expertise metrics for a node within a specific subject."""

    id: Optional[int] = Field(default=None, primary_key=True)
    node_pubkey: str = Field(index=True, description="Ed25519 public key hex of the node")
    subject_id: str = Field(index=True, description="Subject namespace ID (e.g. apiculture.equipment)")
    evaluations_count: int = Field(default=0, description="Total audits completed in this subject")
    median_deviations_sum: float = Field(default=0.0, description="Cumulative deviation from domain robust median")
    grounded_quotes_count: int = Field(default=0, description="Verbatim grounded technical citations")
    total_quotes_count: int = Field(default=0, description="Total citations submitted in this domain")
    unique_domains_count: int = Field(default=1, description="Number of distinct origin FQDNs evaluated in this domain")
    slashing_count: int = Field(default=0, description="Number of times expertise was slashed for hallucinations")
    expertise_score: float = Field(default=0.05, description="Empirical expertise score E_i(subject) from 0.05 to 1.0")
    first_evaluated_at: datetime = Field(default_factory=utc_now, description="First evaluation timestamp in domain")
    last_evaluated_at: datetime = Field(default_factory=utc_now, description="Most recent evaluation timestamp")


class FeedSubscriptionRecord(SQLModel, table=True):
    """Stores syndicated RSS/Atom/JSON feed subscriptions and polling metadata."""

    id: Optional[int] = Field(default=None, primary_key=True)
    feed_url: str = Field(index=True, unique=True, description="Syndicated feed URL (RSS, Atom, or JSON)")
    title: str = Field(default="", description="Human-readable feed title")
    feed_format: str = Field(default="rss", description="Feed format: rss, atom, or json")
    subject_tag: str = Field(default="journalism.news", index=True, description="Default subject namespace tag")
    priority_tier: int = Field(
        default=2, ge=1, le=4, description="Priority tier (1=Breaking/Volatile, 2=News, 3=Blogs, 4=Satire)"
    )
    etag: Optional[str] = Field(default=None, description="HTTP ETag header for conditional requests")
    last_modified: Optional[str] = Field(default=None, description="HTTP Last-Modified header for conditional requests")
    polling_interval_seconds: int = Field(default=900, description="Polling interval in seconds")
    last_polled_at: Optional[datetime] = Field(default=None, description="UTC timestamp of last poll")
    is_active: bool = Field(default=True, index=True, description="Whether feed polling is active")
    is_satire: bool = Field(default=False, description="True if feed is a dedicated satire publication")
    created_at: datetime = Field(default_factory=utc_now, description="Subscription creation timestamp")


class FeedItemRecord(SQLModel, table=True):
    """Stores discovered syndicated feed items, processing status, and mesh adoption records."""

    id: Optional[int] = Field(default=None, primary_key=True)
    item_url: str = Field(index=True, unique=True, description="Target article URL")
    feed_id: Optional[int] = Field(default=None, foreign_key="feedsubscriptionrecord.id", index=True)
    title: str = Field(default="", description="Article headline title")
    subject_id: str = Field(default="journalism.news", index=True, description="Classified subject namespace")
    published_at: Optional[datetime] = Field(default=None, description="Article published timestamp")
    discovered_at: datetime = Field(default_factory=utc_now, description="Feed item discovery timestamp")
    processing_status: str = Field(
        default="pending",
        index=True,
        description="Status: pending, mesh_adopted, evaluated, skipped, failed, specialist_needed",
    )
    adopted_from_node: Optional[str] = Field(
        default=None, description="Node pubkey whose signed attestation was adopted at 0 token cost"
    )
    tokens_saved: int = Field(default=0, description="Estimated LLM tokens saved via zero-token mesh adoption")
