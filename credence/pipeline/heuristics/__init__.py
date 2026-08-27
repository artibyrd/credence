"""Heuristic analysis detectors for hermetic validation and fast-path triage."""

from __future__ import annotations

from typing import List, Optional

from credence.ingestion.extractor import ExtractedContent
from credence.pipeline.heuristics.deceptive import check_deceptive_heuristics
from credence.pipeline.heuristics.ethics import check_spj_heuristics
from credence.pipeline.heuristics.fallacies import check_fallacy_heuristics
from credence.pipeline.schemas import SpecialistViolationFinding
from credence.taxonomy_loader import TaxonomyRegistry, registry

# Backward compatibility aliases
_check_deceptive_heuristics = check_deceptive_heuristics
_check_fallacy_heuristics = check_fallacy_heuristics
_check_spj_heuristics = check_spj_heuristics


def heuristic_evaluate_content(
    extracted: ExtractedContent,
    raw_html: str,
    reg: Optional[TaxonomyRegistry] = None,
) -> List[SpecialistViolationFinding]:
    """Offline heuristic rule evaluator used for hermetic testing and fallback analysis."""
    active_reg = reg or registry
    violations: List[SpecialistViolationFinding] = []
    text_lower = extracted.clean_text.lower()

    violations.extend(check_deceptive_heuristics(text_lower, raw_html, active_reg))
    violations.extend(check_fallacy_heuristics(text_lower, active_reg))
    violations.extend(check_spj_heuristics(extracted, raw_html, active_reg))

    return violations
