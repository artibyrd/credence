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
