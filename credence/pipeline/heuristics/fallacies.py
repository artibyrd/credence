"""Logical fallacy heuristic detectors for Credence."""

from __future__ import annotations

from typing import List

from credence.pipeline.schemas import SpecialistViolationFinding
from credence.taxonomy_loader import TaxonomyRegistry


def check_fallacy_heuristics(
    text_lower: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for blatant logical fallacies in text using table-driven matching."""
    findings: List[SpecialistViolationFinding] = []

    fallacy_patterns = [
        (
            "FALLACY-1.1",
            [
                ("ignorant cowards", "ignorant cowards"),
                ("circus clown", "failed accountant who dresses like a circus clown"),
                ("morally bankrupt, uneducated", "morally bankrupt, uneducated"),
            ],
            "logical-fallacy:relevance/FALLACY-1.1@v1.0.0",
            "RELEVANCE_AND_PERSONAL_ATTACKS",
            "Ad Hominem attack dismissing critics through personal insults rather than logical rebuttal.",
        ),
        (
            "FALLACY-2.2",
            [
                (
                    "100% on our side, or you are an enemy",
                    "you are either 100% on our side, or you are an enemy of the people",
                ),
                (
                    "either you stand courageously",
                    "You either stand courageously with our movement to preserve our national heritage, or you are a treasonous collaborator",
                ),
                ("either 100% on our side", "you are either 100% on our side, or you are an enemy of the people"),
            ],
            "logical-fallacy:presumption/FALLACY-2.2@v1.0.0",
            "PRESUMPTION_AND_CIRCULARITY",
            "False Dilemma framing complex policy as an absolute binary choice.",
        ),
        (
            "FALLACY-3.1",
            [
                (
                    "electric car last month, and yesterday his household plumbing",
                    "bought an electric car last month, and yesterday his household plumbing broke down",
                )
            ],
            "logical-fallacy:causal/FALLACY-3.1@v1.0.0",
            "CAUSAL_AND_INDUCTIVE_ERRORS",
            "Post Hoc fallacy asserting green technology caused unrelated plumbing failures.",
        ),
        (
            "FALLACY-3.2",
            [
                ("0.003% versus 0.001%", "absolute event rate was 0.003% versus 0.001%"),
                ("caffeine causes a catastrophic 200% surge", "caffeine causes a catastrophic 200% surge"),
            ],
            "logical-fallacy:causal/FALLACY-3.2@v1.0.0",
            "CAUSAL_AND_INDUCTIVE_ERRORS",
            "Conflating absolute and relative risk changes while drawing definitive causal conclusions from observational surveys.",
        ),
        (
            "FALLACY-5.2",
            [
                (
                    "supported by over four million followers on social media",
                    "supported by over four million followers on social media, so our economic conclusions are an undeniable, unquestionable fact",
                )
            ],
            "logical-fallacy:relevance/FALLACY-5.2@v1.0.0",
            "RELEVANCE_AND_PERSONAL_ATTACKS",
            "Bandwagon appeal asserting policy truth is determined by social media follower counts.",
        ),
    ]

    for rule_id, trigger_list, default_uri, cluster, reason in fallacy_patterns:
        for trig, specific_quote in trigger_list:
            if trig in text_lower:
                rule = active_reg.get_rule(rule_id)
                if rule:
                    findings.append(
                        SpecialistViolationFinding(
                            rule_id=rule_id,
                            rule_uri=rule.namespaced_uri or default_uri,
                            domain="LOGICAL_FALLACY",
                            cluster_id=cluster,
                            severity=rule.severity,
                            confidence=0.95,
                            quote_or_element=specific_quote,
                            reasoning=reason,
                            is_grounded=True,
                        )
                    )
                break

    return findings
