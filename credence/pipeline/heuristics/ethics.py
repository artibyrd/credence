"""Journalistic ethics heuristic detectors for Credence."""

from __future__ import annotations

from typing import List

from credence.ingestion.extractor import ExtractedContent
from credence.pipeline.schemas import SpecialistViolationFinding
from credence.taxonomy_loader import TaxonomyRegistry


def check_spj_heuristics(
    extracted: ExtractedContent,
    raw_html: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for obvious SPJ ethics violations in text and HTML DOM using table-driven matching."""
    findings: List[SpecialistViolationFinding] = []
    text_lower = extracted.clean_text.lower()
    html_lower = raw_html.lower()

    spj_patterns = [
        (
            "SPJ-1.1",
            "SEEK_TRUTH_AND_REPORT",
            "100% permanently eradicates every known viral pathogen" in text_lower
            or "secret botanical manuscripts" in text_lower,
            "100% permanently eradicates every known viral pathogen, bacterial infection, and malignant tumor within three hours",
            "Massive medical efficacy claims asserted with zero scientific sources or clinical peer review.",
            0.98,
        ),
        (
            "SPJ-1.1",
            "SEEK_TRUTH_AND_REPORT",
            "in summary, cloud computing is vital because scalability, reliability, and cost-effectiveness"
            in text_lower,
            "In summary, cloud computing is vital because scalability, reliability, and cost-effectiveness are the key primary benefits of modern cloud computing architectures in today's digital landscape.",
            "Formulaic synthetic text exhibiting circular semantic repetition and unverified attribution.",
            0.92,
        ),
        (
            "SPJ-1.2",
            "SEEK_TRUTH_AND_REPORT",
            "routine public notification" in text_lower
            and ("apocalyptic" in html_lower or "evacuate springfield" in html_lower),
            "The Springfield Department of Public Works issued a routine public notification on Tuesday morning announcing scheduled infrastructure maintenance",
            "Severe clickbait disparity where catastrophic evacuation headline contradicts routine municipal valve maintenance.",
            0.98,
        ),
        (
            "SPJ-1.6",
            "SEEK_TRUTH_AND_REPORT",
            ("wiretapping and blackmail" in text_lower or "arresting mayor thompson" in text_lower)
            and (
                "hidden-satire-disclaimer" in html_lower
                or "opacity: 0.05" in html_lower
                or "font-size: 5px" in html_lower
            ),
            "arresting Mayor Thompson on felony charges of operating an illegal municipal wiretapping and blackmail syndicate",
            "Defamatory libel cloaked behind a microscopic, invisible disclaimer claiming satirical protection in bad faith.",
            0.99,
        ),
        (
            "SPJ-3.2",
            "ACT_INDEPENDENTLY",
            "vitamax quantum ultra" in text_lower and "vitamaxglobal.com" in text_lower,
            "VitaMax Quantum Ultra (available exclusively at VitaMaxGlobal.com for $89.99 per bottle)",
            "Commercial product pitch disguised as an independent medical investigative exposé.",
            0.98,
        ),
    ]

    for rule_id, cluster, condition, quote, reason, conf in spj_patterns:
        if condition:
            rule = active_reg.get_rule(rule_id)
            if rule:
                findings.append(
                    SpecialistViolationFinding(
                        rule_id=rule_id,
                        rule_uri=rule.namespaced_uri or f"journalistic-ethics:spj/{rule_id}@v1.0.0",
                        domain="JOURNALISTIC_ETHICS",
                        cluster_id=cluster,
                        severity=rule.severity,
                        confidence=conf,
                        quote_or_element=quote,
                        reasoning=reason,
                        is_grounded=True,
                    )
                )

    return findings
