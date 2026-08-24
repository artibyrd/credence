r"""Canonical Golden Control Corpus for Synthetic Benchmark Calibration (Invariant 10).

Provides a verified baseline of diverse, clean, non-violating articles across:
1. Neutral Journalistic Reporting (AP, Reuters style factual dispatches)
2. Peer-Reviewed Scientific Abstracts & Findings
3. Canonical Neutral Encyclopedia Summaries (Wikipedia style)
4. Clearly Labeled Opinion & Editorial Commentary (Properly attributed)
5. Standard Corporate SEC / Financial Statements (Proper GAAP reconciliations)
6. Clearly Disclosed Parody & Satire (The Onion / Babylon Bee style)

Used to enforce the $FPR = 0.00\%$ control gate in the Synthetic Benchmark Gauntlet,
preventing Goodhart's Law benchmark gaming by rule authors.
"""

from __future__ import annotations

from typing import Any, Dict, List

GOLDEN_CONTROL_ARTICLES: List[Dict[str, Any]] = [
    {
        "id": "golden_001_reuters_climate_factual",
        "domain": "reuters.com",
        "title": "NOAA Reports Global Sea Surface Temperatures Set Record High in July",
        "text": "WASHINGTON (Reuters) - Global average sea surface temperatures reached 20.96 degrees Celsius in July, exceeding the previous record set in 2016, according to official data released by the National Oceanic and Atmospheric Administration on Thursday. Scientists noted that El Niño conditions combined with long-term anthropogenic climate trends contributed to the observed anomaly across the North Atlantic and Pacific basins.",
        "expected_violations": [],
        "article_type": "factual_news",
    },
    {
        "id": "golden_002_ap_city_council_zoning",
        "domain": "apnews.com",
        "title": "City Council Approves New Mixed-Use Zoning Ordinance Following Public Hearing",
        "text": "MARICOPA, Ariz. (AP) — The City Council voted 5-2 on Tuesday evening to approve a rezoning amendment for the Heritage District, permitting commercial ground floors with residential apartments above. Over two dozen residents spoke during a three-hour public comment period regarding traffic impact studies and water infrastructure capacity. Councilmember Jane Smith, who voted against the measure, stated that infrastructure assessments required further review.",
        "expected_violations": [],
        "article_type": "local_government",
    },
    {
        "id": "golden_003_nature_clinical_trial",
        "domain": "nature.com",
        "title": "Phase III Double-Blind Trial Demonstrates Efficacy of Novel Monoclonal Antibody in Alzheimer's Cohort",
        "text": "In a randomized, placebo-controlled trial encompassing 1,795 participants with early symptomatic Alzheimer's disease, intravenous administration of lecanemab reduced clinical decline on the CDR-SB scale by 27% at 18 months relative to placebo (p < 0.001). Amyloid-related imaging abnormalities with edema (ARIA-E) occurred in 12.6% of the treatment group versus 1.7% of the placebo group, necessitating routine MRI monitoring.",
        "expected_violations": [],
        "article_type": "peer_reviewed_science",
    },
    {
        "id": "golden_004_sec_10k_financial_gaap",
        "domain": "sec.gov",
        "title": "Acme Industrial Corp 10-K Consolidated Statements of Operations & Non-GAAP Reconciliations",
        "text": "For the fiscal year ended December 31, 2025, Net Income determined in accordance with U.S. GAAP was $412.5 million, compared to $385.0 million in 2024. Adjusted EBITDA, a non-GAAP financial metric, was $620.0 million. Below is a full reconciliation of Net Income to Adjusted EBITDA: Net Income ($412.5M) plus Provision for Income Taxes ($98.0M), plus Interest Expense ($35.5M), plus Depreciation and Amortization ($74.0M) equals Adjusted EBITDA ($620.0M). Forward-looking projections are subject to material market risks described in Item 1A.",
        "expected_violations": [],
        "article_type": "financial_filing",
    },
    {
        "id": "golden_005_satire_onion_defense",
        "domain": "theonion.com",
        "title": "Department of Transportation Announces Potholes Now Deemed Protected Historic Landmarks",
        "text": "WASHINGTON — Citing their rich cultural heritage and decades of continuous presence in American commuter life, the Federal Highway Administration declared all interstate potholes measuring greater than four inches in depth to be protected national historic landmarks on Friday. 'We must preserve these storied asphalt craters for future generations,' remarked administrator Dave Higgins with a straight face.",
        "expected_violations": [],
        "article_type": "satire_parody",
        "is_satire": True,
    },
    {
        "id": "golden_006_wikipedia_encyclopedia_neutral",
        "domain": "en.wikipedia.org",
        "title": "Photosynthesis — Overview of Light-Dependent Reactions",
        "text": "Photosynthesis is a biological process utilized by plants, algae, and certain bacteria to synthesize organic compounds from atmospheric carbon dioxide and water using radiant energy captured from sunlight. Oxygenic photosynthesis produces molecular oxygen as a byproduct through the photolysis of water molecules inside the thylakoid membranes of chloroplasts.",
        "expected_violations": [],
        "article_type": "encyclopedia_neutral",
    },
]


def get_golden_control_corpus() -> List[Dict[str, Any]]:
    """Return the canonical immutable Golden Control Corpus for synthetic benchmark validation."""
    return [dict(a) for a in GOLDEN_CONTROL_ARTICLES]
