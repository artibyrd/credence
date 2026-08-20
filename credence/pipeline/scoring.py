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
