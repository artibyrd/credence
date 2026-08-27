"""Mathematical Scoring and Calibration Engine for Credence.

Calculates:
- Raw weighted suspicion score based on severity, confidence, and root domain weights.
- Non-linear calibrated suspicion score (0.0 to 100.0).
- Suspicion density (violations per 1,000 words).
- Satire neutralization (Poe's Law safeguard) and cloaked disinformation detection.
- Verdict classification bands.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from credence.pipeline.schemas import SpecialistViolationFinding

# Default domain weight multipliers
DEFAULT_DOMAIN_WEIGHTS: Dict[str, float] = {
    "JOURNALISTIC_ETHICS": 1.2,
    "LOGICAL_FALLACY": 1.0,
    "DECEPTIVE_PATTERN": 1.5,
    "DOMAIN_SPECIFIC": 1.2,
}


def compute_raw_suspicion(
    violations: List[SpecialistViolationFinding],
    domain_weights: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate the linear raw suspicion score from a list of grounded violations.

    Formula: sum(severity * confidence * domain_weight for each violation)
    """
    if not violations:
        return 0.0

    weights = domain_weights or DEFAULT_DOMAIN_WEIGHTS
    raw_total = 0.0

    for v in violations:
        # Ignore non-grounded citations if flagged
        if not v.is_grounded:
            continue

        domain_key = v.domain.upper()
        weight = weights.get(domain_key, 1.0)
        raw_total += float(v.severity) * float(v.confidence) * weight

    return round(raw_total, 3)


def compute_suspicion_density(violation_count: int, word_count: int) -> float:
    """Calculate the suspicion density index (violations per 1,000 words).

    Constrained by a minimum denominator of 50 words to prevent divide-by-zero or distortion.
    """
    effective_words = max(50, word_count)
    density = (violation_count / effective_words) * 1000.0
    return round(density, 2)


def compute_calibrated_score(
    raw_score: float,
    is_satire: bool = False,
    has_cloaked_disinfo: bool = False,
    saturation_constant: float = 12.0,
) -> float:
    """Convert raw suspicion score into a calibrated 0.0 - 100.0 score using exponential saturation.

    - Legitimate satire is neutralized to 0.0.
    - Cloaked disinformation bypasses satire neutralization and is scored fully.
    - Score curve: 100 * (1 - e^(-raw_score / saturation_constant))
    """
    if is_satire and not has_cloaked_disinfo:
        return 0.0

    if raw_score <= 0.0:
        return 0.0

    # Non-linear asymptotic saturation towards 100.0
    calibrated = 100.0 * (1.0 - math.exp(-raw_score / saturation_constant))
    return round(min(100.0, max(0.0, calibrated)), 1)


def classify_verdict(
    suspicion_score: float,
    is_satire: bool = False,
    has_cloaked_disinfo: bool = False,
) -> str:
    """Map calibrated score and satire status to standard classification band."""
    if has_cloaked_disinfo:
        return "CLOAKED_DISINFORMATION"

    if is_satire:
        return "SATIRE_PARODY"

    if suspicion_score <= 15.0:
        return "CLEAN"
    elif suspicion_score <= 40.0:
        return "LOW_SUSPICION"
    elif suspicion_score <= 70.0:
        return "SUSPICIOUS"
    else:
        return "DECEPTIVE"


def compute_aggregate_confidence(violations: List[SpecialistViolationFinding]) -> float:
    """Calculate mean confidence across all discovered violations."""
    if not violations:
        return 1.0

    total_conf = sum(v.confidence for v in violations if v.is_grounded)
    grounded_count = sum(1 for v in violations if v.is_grounded)

    if grounded_count == 0:
        return 1.0

    return round(total_conf / grounded_count, 2)


GENERIC_STAFF_BYLINES = {
    "staff",
    "staff reports",
    "editorial staff",
    "news staff",
    "admin",
    "administrator",
    "news desk",
    "contributor",
    "press release",
    "wire service",
    "anonymous",
}


def compute_sourcing_ratios(
    byline: str,
    content_type: str,
    violations: List[SpecialistViolationFinding],
    suspicion_score: float,
) -> Dict[str, float]:
    """Calculate article-level forensic sourcing ratios.

    - R_byline: 100.0 (named human author) vs 0.0 (anonymous or generic staff handle).
    - R_single: 100.0 if relying exclusively on law enforcement blotter/wire pass-through.
    - R_coi: 100.0 if unrecused governance/business conflict present.
    - ASI: Advertorial Separation Index (100.0 down to 0.0 based on commercial blur).
    """
    byline_clean = (byline or "").strip().lower()
    is_staff_handle = (
        byline_clean in GENERIC_STAFF_BYLINES
        or "staff" in byline_clean
        or "news desk" in byline_clean
        or "press release" in byline_clean
    )
    is_named_author = bool(byline_clean and not is_staff_handle)
    r_byline = 100.0 if is_named_author else 0.0

    # Check for single-source law enforcement blotter reliance
    has_single_source = any(v.rule_id in ("SPJ-1.1", "SPJ-1.3") for v in violations)
    r_single = 100.0 if (has_single_source or content_type == "POLICE_BLOTTER") else 0.0

    # Check for governance conflict of interest
    has_coi = any(v.rule_id in ("SPJ-3.1", "SPJ-3.2") for v in violations)
    r_coi = 100.0 if has_coi else 0.0

    # Advertorial Separation Index
    adv_viols = [
        v
        for v in violations
        if v.rule_id in ("DEC-1.1", "DEC-1.2", "DEC-1.3", "DEC-1.4", "SPJ-3.3", "SPJ-4.1", "AST-1.1", "AST-1.2")
    ]
    asi = max(0.0, min(100.0, 100.0 - (len(adv_viols) * 15.0)))

    return {
        "r_byline": round(r_byline, 1),
        "r_single": round(r_single, 1),
        "r_coi": round(r_coi, 1),
        "asi": round(asi, 1),
    }


def compute_domain_dci(
    mean_suspicion: float,
    mean_density: float = 0.0,
    r_byline_avg: float = 1.0,
) -> float:
    """Calculate the aggregate Domain Credence Index (DCI) across a publisher's cohort.

    Formula: DCI = 100.0 - (0.50 * S_recency + 0.30 * Density + 0.20 * (1 - R_byline) * 100)
    """
    byline_penalty = (1.0 - min(1.0, max(0.0, r_byline_avg))) * 100.0
    deduction = (0.50 * mean_suspicion) + (0.30 * min(50.0, mean_density)) + (0.20 * byline_penalty)
    dci = max(0.0, min(100.0, 100.0 - deduction))
    return round(dci, 1)
