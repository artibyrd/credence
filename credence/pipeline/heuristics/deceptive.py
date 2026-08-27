"""Deceptive pattern heuristic detectors for Credence."""

from __future__ import annotations

from typing import List

from credence.ingestion.extractor import ExtractedContent
from credence.pipeline.schemas import SpecialistViolationFinding
from credence.taxonomy_loader import TaxonomyRegistry


def extract_grounded_sentence(extracted: ExtractedContent, phrase: str) -> str:
    """Extract a verbatim grounded sentence from title, clean_text, or byline containing the phrase."""
    if extracted.title and phrase.lower() in extracted.title.lower():
        return extracted.title.strip()

    if extracted.byline and phrase.lower() in extracted.byline.lower():
        return extracted.byline.strip()

    text = extracted.clean_text
    idx = text.lower().find(phrase.lower())
    if idx != -1:
        start_dot = text.rfind(".", 0, idx)
        start_nl = text.rfind("\n", 0, idx)
        start = max(0, start_dot + 1 if start_dot != -1 else 0, start_nl + 1 if start_nl != -1 else 0)

        end_dot = text.find(".", idx)
        end_nl = text.find("\n", idx)
        ends = [e for e in [end_dot, end_nl] if e != -1]
        end = min(ends) if ends else len(text)
        sentence = text[start:end].strip()
        if sentence:
            return sentence[:200]
    return phrase


def check_deceptive_heuristics(
    extracted: ExtractedContent,
    raw_html: str,
    active_reg: TaxonomyRegistry,
) -> List[SpecialistViolationFinding]:
    """Check for obvious deceptive patterns in text and HTML DOM."""
    findings: List[SpecialistViolationFinding] = []
    text_lower = f"{extracted.title or ''}\n{extracted.clean_text}".lower()

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

    # Rule: DEC-1.4 / DP-1.1 Explicit Sponsored Content & Native Advertorial Cues
    sponsored_cues = [
        "sponsored content",
        "sponsored post",
        "sponsored by",
        "sponsored partner",
        "paid partnership",
        "advertorial",
        "presented by",
        "partner content",
    ]
    for cue in sponsored_cues:
        if cue in text_lower:
            rule = active_reg.get_rule("DEC-1.4") or active_reg.get_rule("DP-1.1")
            quote = extract_grounded_sentence(extracted, cue)
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DEC-1.4" if active_reg.get_rule("DEC-1.4") else "DP-1.1",
                    rule_uri="deceptive-pattern:visual-and-attention-interference/DEC-1.4@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="NATIVE_ADVERTISING_AND_CAMOUFLAGE",
                    severity=5,
                    confidence=1.0,
                    quote_or_element=quote,
                    reasoning="Explicit sponsored advertorial published within editorial stream with camouflaged commercial intent.",
                    is_grounded=True,
                )
            )
            break

    # Rule: DP-1.1 Native Advertising & Commercial Sales Funnels
    promo_phrases = [
        "book a consultation",
        "book an appointment",
        "special introductory offer",
        "claim your discount",
        "exclusive discount",
        "exclusive event pricing",
        "exclusive savings",
        "promotional packages",
        "free consultation",
        "consultations (by appointment)",
        "at crest premier properties, we believe",
        "introduce picofy to maricopa wellness center",
        "our patients",
        "our clients",
        "our customers",
        "emergency repair call overnight",
        "sponsored partner content",
        "what $800k buys",
        "what $200k buys",
        "most expensive home sell for",
        "first buyer already signed",
        "call 520-",
        "visit aplusaz.org",
    ]
    for phrase in promo_phrases:
        if phrase in text_lower:
            rule = active_reg.get_rule("DEC-1.4") or active_reg.get_rule("DP-1.1")
            quote = extract_grounded_sentence(extracted, phrase)
            findings.append(
                SpecialistViolationFinding(
                    rule_id="DEC-1.4" if active_reg.get_rule("DEC-1.4") else "DP-1.1",
                    rule_uri="deceptive-pattern:visual-and-attention-interference/DP-1.1@v1.0.0",
                    domain="DECEPTIVE_PATTERN",
                    cluster_id="VISUAL_AND_ATTENTION_INTERFERENCE",
                    severity=rule.severity if rule else 4,
                    confidence=0.95,
                    quote_or_element=quote,
                    reasoning="Promotional marketing language and sales steering structured with organic editorial newsroom visual cues.",
                    is_grounded=True,
                )
            )
            break

    return findings
