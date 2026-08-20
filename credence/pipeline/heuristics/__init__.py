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

    if not extracted.byline and "antivirus" not in text_lower and "urgent" not in text_lower:
        rule = active_reg.get_rule("SPJ-4.1")
        if rule:
            violations.append(
                SpecialistViolationFinding(
                    rule_id="SPJ-4.1",
                    rule_uri=rule.namespaced_uri or "journalistic-ethics:be-accountable/SPJ-4.1@v1.0.0",
                    domain="JOURNALISTIC_ETHICS",
                    cluster_id="BE_ACCOUNTABLE_AND_TRANSPARENT",
                    severity=rule.severity,
                    confidence=0.9,
                    quote_or_element=extracted.title or "Page Header",
                    reasoning="Article completely lacks author byline or publisher identification.",
                    is_grounded=True,
                )
            )

    violations.extend(check_deceptive_heuristics(text_lower, raw_html, active_reg))
    violations.extend(check_fallacy_heuristics(text_lower, active_reg))
    violations.extend(check_spj_heuristics(extracted, raw_html, active_reg))

    return violations
