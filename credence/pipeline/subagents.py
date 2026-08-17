"""Specialized Subagents and Prompts for Credence Pipeline.

Orchestrates 4 specialist auditors:
1. SPJ Ethics Auditor (Journalistic standards, citations, bylines)
2. Fallacy Auditor (IEP 6 cognitive fallacy clusters)
3. Deceptive Pattern Auditor (Dark UI patterns, fake urgency, disguised ads)
4. Satire & Provenance Auditor (Poe's Law filter, satire detection)

Includes Grounded Quote Validation to filter hallucinated citations.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import normalize_text
from credence.pipeline.schemas import (
    SatireVerdict,
    SpecialistReport,
    SpecialistViolationFinding,
)
from credence.taxonomy_loader import TaxonomyRegistry, registry


def validate_grounded_quote(quote: str, raw_text: str, raw_html: str) -> bool:
    """Verify that a cited quote or DOM selector exists within the ingested snapshot."""
    if not quote or not quote.strip():
        return False

    def _normalize_all_whitespace(s: str) -> str:
        return re.sub(r"\s+", " ", normalize_text(s)).strip().lower()

    clean_quote = _normalize_all_whitespace(quote)
    clean_source_text = _normalize_all_whitespace(raw_text)
    clean_html_text = _normalize_all_whitespace(raw_html)

    # 1. Exact substring match in clean prose
    if clean_quote in clean_source_text:
        return True

    # 2. Check within raw HTML markup
    if clean_quote in clean_html_text:
        return True

    # 3. Check for 80%+ fuzzy token match for slightly trimmed quotes
    quote_tokens = [w for w in re.findall(r"\w+", clean_quote) if len(w) > 3]
    if len(quote_tokens) >= 4:
        matched_tokens = sum(1 for tok in quote_tokens if tok in clean_source_text)
        if (matched_tokens / len(quote_tokens)) >= 0.8:
            return True

    return False


def validate_all_violations(
    violations: List[SpecialistViolationFinding],
    raw_text: str,
    raw_html: str,
) -> List[SpecialistViolationFinding]:
    """Validate grounding of all discovered violations against source text."""
    validated: List[SpecialistViolationFinding] = []
    for v in violations:
        is_grounded = validate_grounded_quote(v.quote_or_element, raw_text, raw_html)
        v.is_grounded = is_grounded
        validated.append(v)
    return validated


def build_satire_provenance_prompt(extracted: ExtractedContent, reg: Optional[TaxonomyRegistry] = None) -> str:
    """Construct prompt for the Satire & Provenance Auditor."""
    cues_str = "\n".join(f"- {r}" for r in extracted.satire_cue_reasons) if extracted.satire_cue_reasons else "None"
    return f"""You are the Credence Satire & Provenance Auditor.
Your objective is to classify whether the provided web content is legitimate comedy/satire (e.g., The Onion, The Babylon Bee, humor op-ed), genuine reporting, or malicious disinformation attempting to cloak itself as a joke.

### Ingested Metadata:
- Title: {extracted.title or "N/A"}
- Author: {extracted.byline or "N/A"}
- Publisher: {extracted.site_name or "N/A"}
- Explicit Satire Cues Detected: {cues_str}

### Article Text:
\"\"\"
{extracted.clean_text[:4000]}
\"\"\"

### Classification Criteria:
1. SATIRE_PARODY: Content uses obvious comedic hyperbole, fictitious quotes, absurd premises, or humor masthead disclaimers for artistic commentary.
2. NEWS_ARTICLE: Serious journalistic or factual reporting.
3. OPINION: Editorial commentary or opinion column.
4. CLOAKED_DISINFORMATION: Malicious disinformation or defamatory claims masquerading as satire without obvious comedic cues or masthead disclosures.

Respond ONLY with valid JSON matching this schema:
{{
  "is_satire": boolean,
  "confidence": float (0.0 to 1.0),
  "classification": "SATIRE_PARODY" | "NEWS_ARTICLE" | "OPINION" | "CLOAKED_DISINFORMATION",
  "satire_cues_found": ["list of specific clues or quotes"],
  "notes": "string explanation"
}}
"""


def build_specialist_prompt(
    catalog_id: str,
    extracted: ExtractedContent,
    reg: Optional[TaxonomyRegistry] = None,
) -> str:
    """Construct prompt for a domain specialist subagent using dynamic taxonomy rules."""
    active_reg = reg or registry
    checklist = active_reg.generate_prompt_checklist(catalog_id)
    catalog = active_reg.get_catalog(catalog_id)
    domain_name = catalog.domain if catalog else "GENERAL"

    return f"""You are a specialized Credence Auditor evaluating web content against formal rubrics.

{checklist}

### Webpage Content to Evaluate:
- Title: {extracted.title or "N/A"}
- Author / Byline: {extracted.byline or "N/A"}
- Publisher: {extracted.site_name or "N/A"}

\"\"\"
{extracted.clean_text[:6000]}
\"\"\"

### Instructions:
1. Scrutinize the content against the checklist above.
2. For EVERY violation found, you MUST provide:
   - rule_id: The exact rule code (e.g., SPJ-1.1, FALLACY-1.1, DP-1.1).
   - quote_or_element: The EXACT substring from the text demonstrating the violation.
   - reasoning: Why this excerpt breaches the specific rule.
   - severity: Integer 1 to 5 as defined in the rule catalog.
   - confidence: Float 0.0 to 1.0.
3. If no violations are found, return an empty violations list.

Respond ONLY with valid JSON matching this schema:
{{
  "specialist_name": "{catalog_id}_auditor",
  "domain": "{domain_name}",
  "violations": [
    {{
      "rule_id": "string",
      "severity": integer (1..5),
      "confidence": float (0.0..1.0),
      "quote_or_element": "exact quote from text",
      "reasoning": "explanation",
      "line_or_selector": null
    }}
  ],
  "summary": "Brief summary of evaluation"
}}
"""


def parse_specialist_response(
    raw_json_or_text: str,
    catalog_id: str,
    reg: Optional[TaxonomyRegistry] = None,
) -> SpecialistReport:
    """Parse and validate JSON response from specialist subagent."""
    active_reg = reg or registry
    catalog = active_reg.get_catalog(catalog_id)
    domain = catalog.domain if catalog else "GENERAL"

    # Extract JSON block if wrapped in markdown code fence
    cleaned = raw_json_or_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        data: Dict[str, Any] = json.loads(cleaned)
    except Exception:
        return SpecialistReport(
            specialist_name=f"{catalog_id}_auditor",
            domain=domain,
            violations=[],
            summary="Failed to parse LLM response.",
        )

    violations_raw = data.get("violations", [])
    parsed_violations: List[SpecialistViolationFinding] = []

    for item in violations_raw:
        rule_id = item.get("rule_id", "")
        rule = active_reg.get_rule(rule_id)

        # Fallback values if rule is dynamically passed
        rule_uri = rule.namespaced_uri if rule and rule.namespaced_uri else f"{domain.lower()}:unknown/{rule_id}@v1.0.0"
        cluster_id = rule_id.split("-")[0] if "-" in rule_id else "GENERAL"
        severity = item.get("severity", rule.severity if rule else 3)
        severity = max(1, min(5, severity))

        parsed_violations.append(
            SpecialistViolationFinding(
                rule_id=rule_id,
                rule_uri=rule_uri,
                domain=domain,
                cluster_id=cluster_id,
                severity=severity,
                confidence=float(item.get("confidence", 1.0)),
                quote_or_element=item.get("quote_or_element", ""),
                reasoning=item.get("reasoning", ""),
                line_or_selector=item.get("line_or_selector"),
                is_grounded=True,
            )
        )

    return SpecialistReport(
        specialist_name=data.get("specialist_name", f"{catalog_id}_auditor"),
        domain=domain,
        violations=parsed_violations,
        summary=data.get("summary", ""),
    )


def parse_satire_response(raw_json_or_text: str) -> SatireVerdict:
    """Parse and validate JSON response from Satire Auditor."""
    cleaned = raw_json_or_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        data: Dict[str, Any] = json.loads(cleaned)
        return SatireVerdict(
            is_satire=bool(data.get("is_satire", False)),
            confidence=float(data.get("confidence", 1.0)),
            classification=str(data.get("classification", "NEWS_ARTICLE")),
            satire_cues_found=data.get("satire_cues_found", []),
            notes=data.get("notes"),
        )
    except Exception:
        return SatireVerdict(
            is_satire=False,
            confidence=0.5,
            classification="NEWS_ARTICLE",
            notes="Could not parse satire response.",
        )
