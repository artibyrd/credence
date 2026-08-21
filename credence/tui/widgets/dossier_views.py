"""Publisher Dossiers and DCI rankings renderers for Credence TUI.

Architecture: Modular Rich Text Formatters (<150 LOC).
"""

from __future__ import annotations

from typing import Any, Dict, List

from rich.text import Text

PUBLISHER_PRESETS: List[Dict[str, Any]] = [
    {
        "domain": "reuters.com",
        "title": "Reuters News Agency",
        "tier": "TIER A (PRISTINE WIRE)",
        "color": "#4ade80",
        "dci": "99.8",
        "audits": 412,
        "grounding": "100% (G=1.00)",
        "syndication": "Active RSS Wire (15m)",
        "desc": "International Wire Service • Syndicated Global Bureau Reporting",
        "stability": "0.998",
    },
    {
        "domain": "nature.com",
        "title": "Nature Scientific Journal",
        "tier": "TIER A (ACADEMIC / PEER-REVIEWED)",
        "color": "#4ade80",
        "dci": "99.4",
        "audits": 184,
        "grounding": "100% (G=1.00)",
        "syndication": "Weekly Ingestion (1h)",
        "desc": "Peer-Reviewed Scientific Research • High-Impact Interdisciplinary Science",
        "stability": "0.994",
    },
    {
        "domain": "apnews.com",
        "title": "Associated Press",
        "tier": "TIER A (NEWS WIRE)",
        "color": "#4ade80",
        "dci": "98.9",
        "audits": 528,
        "grounding": "100% (G=1.00)",
        "syndication": "Active RSS Wire (15m)",
        "desc": "Global Non-profit News Cooperative • Verified Sourced Reporting",
        "stability": "0.989",
    },
    {
        "domain": "theonion.com",
        "title": "The Onion",
        "tier": "SATIRE PROTECTED (0.0)",
        "color": "#c084fc",
        "dci": "100.0",
        "audits": 92,
        "grounding": "100% (G=1.00)",
        "syndication": "Daily RSS Poll (6h)",
        "desc": "Legitimate Satirical Humor • Zero Astroturfing • Poe's Law Safe Harbor",
        "stability": "1.000",
    },
    {
        "domain": "bbc.com",
        "title": "BBC News",
        "tier": "TIER B (ESTABLISHED BROADCASTER)",
        "color": "#38bdf8",
        "dci": "94.2",
        "audits": 340,
        "grounding": "99.1% (G=0.99)",
        "syndication": "Active RSS Wire (30m)",
        "desc": "Public Service Broadcaster • International News Coverage",
        "stability": "0.942",
    },
    {
        "domain": "buzzfeednews.com",
        "title": "BuzzFeed News (Investigative)",
        "tier": "TIER B (INVESTIGATIVE ARCHIVE)",
        "color": "#38bdf8",
        "dci": "91.8",
        "audits": 115,
        "grounding": "98.5% (G=0.98)",
        "syndication": "Static Archive",
        "desc": "Pulitzer Prize-Winning Investigative Reporting • High Topic Entropy",
        "stability": "0.918",
    },
    {
        "domain": "dailycaller.com",
        "title": "Daily Caller",
        "tier": "TIER C (PARTISAN / HIGH VARIANCE)",
        "color": "#f59e0b",
        "dci": "68.4",
        "audits": 210,
        "grounding": "88.2% (G=0.88)",
        "syndication": "Daily RSS Poll (6h)",
        "desc": "Partisan Framing • High Ad Hominem & Selective Omission Variance",
        "stability": "0.684",
    },
    {
        "domain": "inmaricopa.com",
        "title": "InMaricopa Local News",
        "tier": "PROVEN HOAX FABRICATION",
        "color": "#f43f5e",
        "dci": "12.4",
        "audits": 48,
        "grounding": "41.0% (G=0.41)",
        "syndication": "QUARANTINED",
        "desc": "Fabricated Disinformation • Astroturfed Syndicate • SPJ-1.6 Violation",
        "stability": "0.124",
    },
]


def format_publisher_dossier(domain: str) -> Text:
    """Format full longitudinal dossier for a selected publisher."""
    pub = next((p for p in PUBLISHER_PRESETS if p["domain"] == domain), None)
    if not pub:
        text = Text()
        text.append(f"Publisher Dossier: {domain}\n\n", style="bold white")
        text.append("No longitudinal historical data recorded for this domain.\n", style="dim")
        return text

    text = Text()
    text.append(f"🏛️  {pub['title']}\n", style="bold white")
    text.append(f"Domain: {pub['domain']}  │  Status: {pub['tier']}\n", style=f"bold {pub['color']}")
    text.append(f"{pub['desc']}\n\n", style="dim")

    text.append("Longitudinal Epistemic Vitals:\n", style="bold #38bdf8")
    text.append(f"  • Credibility Index (DCI):  {pub['dci']} / 100.0\n", style=f"bold {pub['color']}")
    text.append(f"  • 30-Day Stability Score:    {pub['stability']}\n", style="bold #4ade80")
    text.append(f"  • Verbatim Grounding Rate:  {pub['grounding']}\n", style="bold #38bdf8")
    text.append(f"  • Total Evaluated Audits:   {pub['audits']} Audits\n", style="bold white")
    text.append(f"  • Syndication Feed Status:  {pub['syndication']}\n\n", style="dim")

    text.append("P2P Mesh Consensus Standing:\n", style="bold #94a3b8")
    if float(pub["dci"]) >= 90.0:
        text.append("  ✅ Verified Pristine Network Standing (Zero-Token Adoption Active)\n", style="bold #4ade80")
    elif float(pub["dci"]) >= 60.0:
        text.append("  ⚠️ Elevated Variance Monitored (Standard Inspection Required)\n", style="bold #f59e0b")
    else:
        text.append("  🚫 QUARANTINED BY NETWORK CONSENSUS (Sybil / Hoax Defense)\n", style="bold #f43f5e")

    return text
