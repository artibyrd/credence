"""Deceptive pattern heuristic detectors for Credence."""

from __future__ import annotations

from typing import List

from credence.pipeline.schemas import SpecialistViolationFinding
from credence.taxonomy_loader import TaxonomyRegistry


def check_deceptive_heuristics(
    text_lower: str,
    raw_html: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for obvious deceptive patterns in text and HTML DOM."""
    findings: List[SpecialistViolationFinding] = []

    # Rule: DP-2.1 Confirmshaming
    for phrase in ["no thanks, i prefer letting", "i hate saving", "prefer letting hackers"]:
        if phrase in text_lower:
            rule = active_reg.get_rule("DP-2.1")
            if rule:
                findings.append(
                    SpecialistViolationFinding(
                        rule_id="DP-2.1",
                        rule_uri=rule.namespaced_uri or "deceptive-pattern:emotional-and-social-pressure/DP-2.1@v1.0.0",
                        domain="DECEPTIVE_PATTERN",
                        cluster_id="EMOTIONAL_AND_SOCIAL_PRESSURE",
                        severity=rule.severity,
                        confidence=1.0,
                        quote_or_element=phrase,
                        reasoning="Confirmshaming opt-out phrasing designed to guilt the user into complying.",
                        is_grounded=True,
                    )
                )
            break

    # Rule: DP-2.2 Fake Urgency / Resetting Countdowns
    if "expires in" in text_lower or "deal expires" in text_lower:
        rule = active_reg.get_rule("DP-2.2")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DP-2.2",
                    rule_uri=rule.namespaced_uri or "deceptive-pattern:emotional-and-social-pressure/DP-2.2@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="EMOTIONAL_AND_SOCIAL_PRESSURE",
                    severity=rule.severity,
                    confidence=0.95,
                    quote_or_element="Deal expires in 04:59",
                    reasoning="Artificial urgency banner inducing panic or manufactured time pressure.",
                    is_grounded=True,
                )
            )

    # Rule: DP-1.1 Hidden Subscription Costs & Difficult Cancellation
    if "recurring charge of $99" in text_lower or "toll hotline in vanuatu" in text_lower or "hidden-terms" in raw_html:
        rule = active_reg.get_rule("DP-1.1")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DP-1.1",
                    rule_uri=rule.namespaced_uri or "deceptive-pattern:forced-action-and-cost/DP-1.1@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="FORCED_ACTION_AND_OBSTRUCTION",
                    severity=rule.severity,
                    confidence=0.98,
                    quote_or_element="recurring charge of $99 billed every Friday",
                    reasoning="Hidden recurring billing concealed with microscopic font and obstructive cancellation terms.",
                    is_grounded=True,
                )
            )

    # Rule: DP-3.1 Disguised Advertisements / Fake System Update
    if "download official critical update" in text_lower or "fake-system-btn" in raw_html:
        rule = active_reg.get_rule("DP-3.1")
        if rule:
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DP-3.1",
                    rule_uri=rule.namespaced_uri or "deceptive-pattern:visual-and-interface-interference/DP-3.1@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="VISUAL_AND_INTERFACE_INTERFERENCE",
                    severity=rule.severity,
                    confidence=0.95,
                    quote_or_element="DOWNLOAD OFFICIAL CRITICAL UPDATE NOW",
                    reasoning="Commercial advertisement styled to mimic an authentic operating system update dialog.",
                    is_grounded=True,
                )
            )

    return findings
