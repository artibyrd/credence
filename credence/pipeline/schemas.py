"""Pydantic schemas for the Credence multi-agent pipeline.

Defines schemas for:
- SpecialistViolationFinding: A concrete rule violation with grounded quote and reasoning.
- SatireVerdict: Satire/parody vs genuine news vs cloaked disinformation classification.
- SpecialistReport: Output from an individual domain specialist subagent.
- AuditReport: Consolidated, calibrated audit report with cryptographic attestation readiness.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class SpecialistViolationFinding(BaseModel):
    """A granular rule violation discovered by a specialist subagent."""

    rule_id: str = Field(..., description="Unique rule code (e.g. SPJ-1.1, FALLACY-2.2, DP-1.1)")
    rule_uri: str = Field(..., description="Canonical namespaced rule URI")
    domain: str = Field(..., description="Root taxonomy domain (e.g. JOURNALISTIC_ETHICS)")
    cluster_id: str = Field(..., description="Thematic cluster ID")
    severity: int = Field(..., ge=1, le=5, description="Violation severity from 1 (minor) to 5 (critical)")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Evaluator confidence in this violation (0.0 to 1.0)"
    )
    quote_or_element: str = Field(..., description="Exact cited excerpt or DOM selector from the snapshot")
    reasoning: str = Field(..., description="Detailed justification connecting quote to violated rule")
    line_or_selector: Optional[str] = Field(default=None, description="Source line number or DOM selector")
    is_grounded: bool = Field(default=True, description="Whether the quote was verified against raw text")


class SatireVerdict(BaseModel):
    """Verdict from the Satire & Provenance Auditor."""

    is_satire: bool = Field(default=False, description="True if content is comedic/satirical parody")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in satire classification")
    classification: str = Field(
        default="NEWS_ARTICLE",
        description="Content classification (NEWS_ARTICLE, OPINION, SATIRE_PARODY, CLOAKED_DISINFORMATION)",
    )
    satire_cues_found: List[str] = Field(default_factory=list, description="Specific satire indicators detected")
    notes: Optional[str] = Field(default=None, description="Explanation for satire or provenance verdict")


class SpecialistReport(BaseModel):
    """Output from an individual domain specialist subagent."""

    specialist_name: str = Field(..., description="Name of the specialist auditor")
    domain: str = Field(..., description="Taxonomy domain evaluated")
    violations: List[SpecialistViolationFinding] = Field(default_factory=list, description="Discovered rule violations")
    summary: str = Field(default="", description="Executive summary of specialist evaluation")


class AuditReport(BaseModel):
    """Consolidated, calibrated audit report for a webpage snapshot."""

    url: str = Field(..., description="Evaluated target URL")
    content_sha256: str = Field(..., description="SHA-256 hash of normalized text")
    simhash_64: str = Field(..., description="64-bit SimHash hex string")
    audited_at: datetime = Field(default_factory=utc_now, description="UTC evaluation timestamp")

    # Scoring & Calibration
    suspicion_score: float = Field(..., ge=0.0, le=100.0, description="Calibrated suspicion score (0.0 to 100.0)")
    suspicion_density: float = Field(..., ge=0.0, description="Violations per 1,000 words")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall evaluation confidence")
    classification: str = Field(
        ..., description="Verdict band (CLEAN, LOW_SUSPICION, SUSPICIOUS, DECEPTIVE, SATIRE_PARODY)"
    )

    # Satire & Poe's Law Safeguards
    is_satire: bool = Field(default=False, description="Whether content was classified as parody/satire")
    content_type: str = Field(default="NEWS_ARTICLE", description="Evaluated content type")
    satire_notes: Optional[str] = Field(default=None, description="Satire contextual explanation")

    # Granular Evidence
    violations: List[SpecialistViolationFinding] = Field(default_factory=list, description="Itemized violations")
    taxonomies_used: Dict[str, str] = Field(default_factory=dict, description="Map of {catalog_id: catalog_hash}")

    # Cryptographic Attestation Fields (Optional until signed)
    node_pubkey: Optional[str] = Field(default=None, description="Ed25519 public key hex of evaluating node")
    node_signature: Optional[str] = Field(default=None, description="Ed25519 signature hex of canonical JSON")
