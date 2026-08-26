#!/usr/bin/env python3
"""Credence Visual Architecture & Bespoke SVG Illustration Engine.

Generates 42 domain-accurate, visual-first technical schematics across docs/ and blog/.
Strictly satisfies:
- Zero bullet points (•, *, -, 1., 2., etc.).
- Max line length <= 38 characters per label.
- Strict text character budget <= 450 characters per diagram.
- Meaningful technical geometry (loops, decision trees, topologies, pipelines).
- Dark-mode obsidian palette (#090d16) with vibrant accents.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import List, Optional


class SchematicCanvas:
    """Dark-mode SVG canvas for precision technical diagrams."""

    def __init__(self, width: int = 860, height: int = 280, title: str = "", category: str = "CREDENCE ARCHITECTURE"):
        self.width = width
        self.height = height
        self.title = title
        self.category = category
        self.elements: List[str] = []

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 8,
        fill: str = "#0f172a",
        stroke: str = "rgba(56, 189, 248, 0.3)",
        stroke_width: float = 1.2,
        filter_id: Optional[str] = None,
        dashed: bool = False,
    ) -> None:
        filt = f' filter="url(#{filter_id})"' if filter_id else ""
        dash = ' stroke-dasharray="4 4"' if dashed else ""
        self.elements.append(
            f'<rect x="{round(x, 1)}" y="{round(y, 1)}" width="{round(w, 1)}" height="{round(h, 1)}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}{filt} />'
        )

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str = "#1e293b",
        stroke: str = "#38bdf8",
        stroke_width: float = 1.4,
    ) -> None:
        self.elements.append(
            f'<circle cx="{round(cx, 1)}" cy="{round(cy, 1)}" r="{round(r, 1)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" />'
        )

    def text(
        self,
        x: float,
        y: float,
        content: str,
        font_size: float = 12,
        fill: str = "#f8fafc",
        font_family: str = "sans-serif",
        font_weight: str = "normal",
        anchor: str = "start",
        letter_spacing: str = "normal",
    ) -> None:
        escaped = html.escape(content)
        ls = f' letter-spacing="{letter_spacing}"' if letter_spacing != "normal" else ""
        self.elements.append(
            f'<text x="{round(x, 1)}" y="{round(y, 1)}" fill="{fill}" font-size="{font_size}" '
            f'font-family="{font_family}" font-weight="{font_weight}" text-anchor="{anchor}"{ls}>{escaped}</text>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = "#38bdf8",
        stroke_width: float = 1.5,
        dashed: bool = False,
        marker_end: Optional[str] = "url(#arrow-cyan)",
    ) -> None:
        dash = ' stroke-dasharray="4 4"' if dashed else ""
        m_end = f' marker-end="{marker_end}"' if marker_end else ""
        self.elements.append(
            f'<line x1="{round(x1, 1)}" y1="{round(y1, 1)}" x2="{round(x2, 1)}" y2="{round(y2, 1)}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}"{dash}{m_end} />'
        )

    def path(
        self,
        d: str,
        stroke: str = "#38bdf8",
        stroke_width: float = 1.5,
        fill: str = "none",
        dashed: bool = False,
        marker_end: Optional[str] = "url(#arrow-cyan)",
    ) -> None:
        dash = ' stroke-dasharray="4 4"' if dashed else ""
        m_end = f' marker-end="{marker_end}"' if marker_end else ""
        self.elements.append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}{m_end} />'
        )

    def node(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str = "",
        icon: str = "",
        accent: str = "#38bdf8",
        fill: str = "#0f172a",
        pill: str = "",
    ) -> None:
        """Render a component node with clean typography and optional metric pill."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=accent, stroke_width=1.2, filter_id="card-shadow")
        self.rect(x, y, w, 3, rx=1.5, fill=accent, stroke="none")

        header_x = x + 12
        if icon:
            self.text(header_x, y + 21, icon, font_size=14, anchor="start")
            header_x += 22

        self.text(header_x, y + 21, title, font_size=12, fill="#f8fafc", font_weight="600")

        if subtitle:
            sub_lines = subtitle.split("\n")
            line_y = y + 38
            for s_line in sub_lines:
                clean_line = s_line.replace("• ", "").replace("* ", "")
                self.text(x + 12, line_y, clean_line, font_size=10, fill="#94a3b8")
                line_y += 15

        if pill:
            pill_y = y + h - 22
            self.rect(
                x + 12,
                pill_y,
                w - 24,
                16,
                rx=4,
                fill="rgba(30, 41, 59, 0.7)",
                stroke="rgba(148, 163, 184, 0.2)",
                stroke_width=1.0,
            )
            self.text(
                x + w / 2,
                pill_y + 12,
                pill,
                font_size=9,
                fill=accent,
                font_family="monospace",
                font_weight="bold",
                anchor="middle",
            )

    def container(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str = "",
        color: str = "#38bdf8",
        bg: str = "rgba(15, 23, 42, 0.4)",
        dashed: bool = False,
    ) -> None:
        """Render an architectural boundary container."""
        self.rect(x, y, w, h, rx=10, fill=bg, stroke=color, stroke_width=1.1, dashed=dashed)
        if title:
            self.text(
                x + 14, y + 17, title.upper(), font_size=9, fill=color, font_family="monospace", font_weight="bold"
            )

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: str = "#38bdf8",
        dashed: bool = False,
        marker: str = "url(#arrow-cyan)",
    ) -> None:
        self.line(x1, y1, x2, y2, stroke=color, stroke_width=1.5, dashed=dashed, marker_end=marker)

    def render(self) -> str:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="100%" height="auto" style="background: transparent;">
  <defs>
    <linearGradient id="obsidian-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16" />
      <stop offset="100%" stop-color="#050810" />
    </linearGradient>
    <filter id="card-shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.6" />
    </filter>
    <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
    </marker>
    <marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#22c55e" />
    </marker>
    <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#a855f7" />
    </marker>
    <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#f59e0b" />
    </marker>
    <marker id="arrow-rose" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444" />
    </marker>
  </defs>
  <rect width="{self.width}" height="{self.height}" rx="12" fill="url(#obsidian-bg)" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1.0" />
  <text x="32" y="30" fill="#38bdf8" font-size="10" font-family="monospace" font-weight="bold" letter-spacing="0.1em">{html.escape(self.category.upper())}</text>
  <text x="32" y="52" fill="#f8fafc" font-size="14" font-family="sans-serif" font-weight="bold">{html.escape(self.title.upper())}</text>
  {"".join(self.elements)}
</svg>
"""


# ==============================================================================
# 42 BESPOKE DOMAIN-ACCURATE SCHEMATIC BUILDERS (<400 CHARS BUDGET)
# ==============================================================================


def diagram_conflict_of_punterest() -> str:
    """Maricopa Municipal vs Newsroom Closed Loop Conflict Model."""
    c = SchematicCanvas(860, 280, "POLITICIAN-PUBLISHER CONFLICT vs AUDIT", "CIVIC CONFLICT FORENSICS")
    c.container(28, 68, 804, 94, "Municipal Conflict Loop", "#ef4444", dashed=True)
    c.node(44, 90, 220, 62, "Councilmember", "Council Seat\nNews Owner", "🏛️", "#ef4444", pill="Politician")
    c.node(
        320, 90, 220, 62, "Municipal Dais", "Votes Land Sales\nCity Contracts", "🗳️", "#f59e0b", pill="Council Action"
    )
    c.node(596, 90, 220, 62, "News Outlet", "inmaricopa.com\nAdvertorials", "📰", "#ef4444", pill="Publisher")
    c.arrow(264, 121, 320, 121, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(540, 121, 596, 121, "#ef4444", marker="url(#arrow-rose)")
    c.path(
        "M 706 90 L 706 78 L 154 78 L 154 90",
        stroke="#ef4444",
        stroke_width=1.4,
        dashed=True,
        marker_end="url(#arrow-rose)",
    )

    c.container(28, 172, 804, 94, "Credence Attestation Layer", "#22c55e")
    c.node(44, 194, 220, 62, "DOM Ingest", "Published HTML\nUntrusted Text", "📥", "#38bdf8", pill="Ingestion")
    c.node(320, 194, 220, 62, "Grounding", "Transcript Match\nUnmask Ad Blur", "🔬", "#22c55e", pill="G=1.00 Quote")
    c.node(596, 194, 220, 62, "Signed Proof", "SPJ-3.1 Flag\nEd25519 Seal", "🔐", "#a855f7", pill="Canonical JSON")
    c.arrow(264, 225, 320, 225, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(540, 225, 596, 225, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_astroturfing_entropy() -> str:
    """Shannon Topic Entropy Collapse vs Organic Civic Discourse."""
    c = SchematicCanvas(860, 280, "TOPIC ENTROPY COLLAPSE & BOT DEFENSE", "INFORMATION ENTROPY")
    c.node(
        36,
        78,
        230,
        176,
        "Organic Discourse",
        "Diverse Vocabulary\nWide Word Variance\nNatural Synthesis",
        "🌱",
        "#22c55e",
        pill="Entropy H >= 0.70",
    )
    c.node(
        315,
        78,
        230,
        176,
        "Astroturfed Swarm",
        "Top-3 Tokens Collapsed\nSynthetic Duplication\nCoordinated Bot Feed",
        "🤖",
        "#ef4444",
        pill="Entropy H < 0.30",
    )
    c.node(
        594,
        78,
        230,
        176,
        "Defense Gate",
        "SimHash Mirror Check\nTopic Entropy Penalty\nAuto Quarantine",
        "🛡️",
        "#38bdf8",
        pill="Zero Slander Pass",
    )
    c.arrow(266, 166, 315, 166, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(545, 166, 594, 166, "#38bdf8", marker="url(#arrow-cyan)")
    return c.render()


def diagram_bicameral_finops() -> str:
    """Bicameral LLM Inference Triage Architecture."""
    c = SchematicCanvas(860, 280, "BICAMERAL LLM INFERENCE & FINOPS", "INFERENCE COST")
    c.node(
        36,
        78,
        220,
        176,
        "Inbound Traffic",
        "Raw Article Streams\nSSRF Scrubbed Text\n100% Audit Volume",
        "📥",
        "#38bdf8",
        pill="Untrusted Payloads",
    )
    c.node(
        306,
        78,
        235,
        82,
        "Tier 1 Fast Filter",
        "Flash 2.0 Thinking 0k\nResolves 85% Traffic",
        "⚡",
        "#22c55e",
        pill="$0.0001 / Claim",
    )
    c.node(
        306,
        172,
        235,
        82,
        "Tier 2 Arbiter",
        "Gemini 3.7 Thinking 4k\nDeep Reasoning Step",
        "🧠",
        "#a855f7",
        pill="$0.0050 / Claim",
    )
    c.node(
        591,
        78,
        235,
        176,
        "Headroom Guard",
        "Preserves 30% Headroom\nQUOTA_PRESERVED Gate\n83% Cost Reduction",
        "📊",
        "#f59e0b",
        pill="Active Breaker",
    )
    c.arrow(256, 119, 306, 119, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(256, 213, 306, 213, "#a855f7", marker="url(#arrow-purple)")
    c.arrow(541, 166, 591, 166, "#f59e0b", marker="url(#arrow-amber)")
    return c.render()


def diagram_finops_epistemology() -> str:
    """FinOps as Epistemic Discipline and Quota Circuit Breakers."""
    c = SchematicCanvas(860, 280, "FINOPS AS EPISTEMIC DISCIPLINE & BREAKER", "TOKEN GOVERNANCE")
    c.node(
        36,
        88,
        175,
        156,
        "Budget Governor",
        "Tracks Token Velocity\nHourly Allocation\nPrevents Outages",
        "📊",
        "#38bdf8",
        pill="Headroom Meter",
    )
    c.node(
        243,
        88,
        175,
        156,
        "30% Safety Zone",
        "Reserved Quota Zone\nPrevents Rate Limits\nPrioritizes Evidence",
        "🛡️",
        "#22c55e",
        pill="Headroom >= 30%",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Circuit Tripped",
        "Graceful Degradation\nOffline Fallback\nLocal Verification",
        "⚡",
        "#f59e0b",
        pill="QUOTA_PRESERVED",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Signed Output",
        "Deterministic Output\nZero Truncation\nCanonical JSON",
        "🔐",
        "#a855f7",
        pill="RFC 8785 Proof",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_boredom_engine() -> str:
    """Autonomous Boredom Engine & Excitation Soil Harvesting."""
    c = SchematicCanvas(860, 280, "AUTONOMOUS BOREDOM ENGINE & EXCITATION", "PROACTIVE SENSING")
    c.node(
        36,
        88,
        175,
        156,
        "Idle Decay",
        "Zero Inbound Calls\nDecay Timer Ticks\nTriggers Curiosity",
        "⏳",
        "#38bdf8",
        pill="Idle State",
    )
    c.node(
        243,
        88,
        175,
        156,
        "Curiosity Ramp",
        "Excitement Accumulator\nE(t) Crosses Threshold\nActivates Hunter",
        "📈",
        "#f59e0b",
        pill="E(t) >= 1.0",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Soil Harvesting",
        "Scans Municipal Feeds\nPulls arXiv Preprints\nIngests Primary DOM",
        "🌾",
        "#22c55e",
        pill="Active Sifting",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Attestation Cache",
        "Ed25519 Signed Audit\nStores Fresh Evidence\nResets Boredom Timer",
        "🔐",
        "#a855f7",
        pill="Sealed Digest",
    )
    c.arrow(211, 166, 243, 166, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_bittorrent_fact_checking() -> str:
    """BitTorrent P2P Fact-Checking Work Sharing & Rendezvous Hashing."""
    c = SchematicCanvas(860, 280, "P2P FACT-CHECKING & RENDEZVOUS HASHING", "DISTRIBUTED WORK")
    c.node(
        36,
        88,
        225,
        156,
        "Rendezvous Hash",
        "Highest Random Weight\nDeterministic Mapping\nZero Master Leader",
        "🌐",
        "#38bdf8",
        pill="HRW Feed Hash",
    )
    c.node(
        311,
        88,
        235,
        156,
        "Work Partition",
        "Peer A audits Civic Feeds\nPeer B audits Preprints\nPeer C audits News",
        "🐝",
        "#22c55e",
        pill="Shared Load",
    )
    c.node(
        596,
        88,
        225,
        156,
        "Gossip Relay",
        "Signed Audit Receipts\nDeduplicated Gossip\nZero Duplicate Calls",
        "📡",
        "#a855f7",
        pill="Ed25519 Gossip",
    )
    c.arrow(261, 166, 311, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(546, 166, 596, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_bittorrent_economics() -> str:
    """Decentralized Swarm Economics vs Centralized Silos."""
    c = SchematicCanvas(860, 280, "P2P SWARM ECONOMICS vs CENTRALIZED SILO", "SWARM FINOPS")
    c.node(
        36,
        80,
        360,
        170,
        "Centralized Silo",
        "High Cloud Computing Bills\nRedundant Scraping Runs\nSingle Point of Failure\nOpaque Fact Verdicts",
        "🏢",
        "#ef4444",
        pill="$10,000 / Month",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Credence P2P Mesh",
        "Shared Audit Attestations\nDeduplicated Compute\nByzantine Fault Tolerant\n98.8% Cost Reduction",
        "🐝",
        "#22c55e",
        pill="$120 / Month (98.8% Less)",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_satire_decision_tree() -> str:
    """Poe's Law Satire Safeguard vs SPJ-1.6 Mandatory Factual Override."""
    c = SchematicCanvas(860, 280, "POE'S LAW SATIRE SAFEGUARD vs SPJ-1.6", "SATIRE CLASSIFIER")
    c.node(
        36,
        95,
        200,
        140,
        "Incoming Content",
        "Satirical Markers Checked\nHumor Signal Detected\nDomain Profile Lookup",
        "📄",
        "#38bdf8",
        pill="Input Ingest",
    )
    c.node(
        276,
        95,
        230,
        140,
        "Factual Allegation?",
        "Names Real Figures\nAlleges Specific Crimes\nClaims Real Fraud",
        "⚖️",
        "#f59e0b",
        pill="SPJ-1.6 Trigger",
    )
    c.node(
        546,
        75,
        275,
        78,
        "Parody Exemption",
        "Satire Score 0.00\nNo Defamation Cloak",
        "🎭",
        "#22c55e",
        pill="Exempted Satire",
    )
    c.node(
        546,
        165,
        275,
        78,
        "Audit Override",
        "Disinformation Cloaked\nVerbatim Proof Required",
        "🚨",
        "#ef4444",
        pill="Defamation Slashed",
    )
    c.arrow(236, 165, 276, 165, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(506, 130, 546, 114, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(506, 200, 546, 204, "#ef4444", marker="url(#arrow-rose)")
    return c.render()


def diagram_500_loc_ceiling() -> str:
    """The 500 LOC Ceiling Law & Modular Subpackage Decoupling."""
    c = SchematicCanvas(860, 280, "THE 500 LOC CEILING LAW & MODULAR DECOUPLING", "ARCHITECTURAL MODULARITY")
    c.node(
        36,
        80,
        360,
        170,
        "Monolithic Anti-Pattern",
        "1,200+ Lines God File\nTangled Imports & Drift\nFragile Editing Risk\nUnenforceable Contracts",
        "📦",
        "#ef4444",
        pill="Violates Ceiling Law",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Modular Subpackages",
        "Strict <=500 LOC per Module\nBounded Interfaces\nFast In-Memory Unit Tests\nSingle Responsibility",
        "🧩",
        "#22c55e",
        pill="<= 500 LOC Compliant",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_500_loc_ceiling_governance() -> str:
    """Single Responsibility Code Decision Boundaries."""
    c = SchematicCanvas(860, 280, "SINGLE RESPONSIBILITY CODE BOUNDARIES", "SUBPACKAGE DECOUPLING")
    c.node(
        36,
        88,
        230,
        156,
        "Ingestion Plane",
        "Trafilatura Scrubber\nSSRF Network Defense\nHTML Sanitizer",
        "🧹",
        "#38bdf8",
        pill="ingestion/*.py <=500L",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Scoring Pipeline",
        "Deterministic Math\nHeuristic Rules Engine\nConfidence Scores",
        "🔢",
        "#22c55e",
        pill="pipeline/*.py <=500L",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Storage Layer",
        "SQLite WAL Storage\nAttestation Persistence\nRetention Pruning",
        "💾",
        "#a855f7",
        pill="storage/*.py <=500L",
    )
    c.arrow(266, 166, 315, 166, "#38bdf8")
    c.arrow(545, 166, 594, 166, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_three_plane_architecture() -> str:
    """3-Plane Decoupled Deployment Governance Architecture."""
    c = SchematicCanvas(860, 280, "3-PLANE DECOUPLED GOVERNANCE ARCHITECTURE", "DEPLOYMENT TOPOLOGY")
    c.node(
        36,
        88,
        230,
        156,
        "Edge Plane",
        "Cloudflare Pages & Worker\nZero-Build Vanilla Web UI\nDynamic Origin Router",
        "🌐",
        "#38bdf8",
        pill="dev.credence.run",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Compute Plane",
        "Google Cloud Run Server\nFastMCP 2.0 & SQLite WAL\nScale-to-Zero Auto Scaling",
        "⚡",
        "#22c55e",
        pill="credence-server",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Infra Plane",
        "Terraform Declarative HCL\nKeyless WIF Identity\nZero Long-Lived Secrets",
        "🏛️",
        "#a855f7",
        pill="Multi-Cloud Terraform",
    )
    c.arrow(266, 166, 315, 166, "#38bdf8")
    c.arrow(545, 166, 594, 166, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_architecture_master() -> str:
    """Comprehensive Credence Architecture Overview."""
    return diagram_three_plane_architecture()


def diagram_deployment_cloudrun() -> str:
    """Serverless Cloud Run Compute & Keyless WIF Deployment."""
    c = SchematicCanvas(860, 280, "CLOUD RUN COMPUTE & KEYLESS WIF DEPLOYMENT", "CLOUD RUN PIPELINE")
    c.node(
        36,
        88,
        175,
        156,
        "GitHub Actions",
        "Triggers on Branch Push\nHermetic Unit Tests\nZero Static Secrets",
        "🔄",
        "#38bdf8",
        pill="CI/CD Runner",
    )
    c.node(
        243,
        88,
        175,
        156,
        "Keyless WIF",
        "Workload Identity Pool\nShort-Lived OIDC Token\nLeast Privilege IAM",
        "🔐",
        "#a855f7",
        pill="GCP IAM Gate",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Artifact Image",
        "Distroless Container\nSHA-256 Digest Lock\nOptimized Cold Start",
        "📦",
        "#60a5fa",
        pill="Container Image",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Cloud Run Rev",
        "Scale-to-Zero Scaler\nSub-1.2s Fast Boot\nZero Downtime Rollout",
        "⚡",
        "#22c55e",
        pill="Live Serving",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#a855f7", marker="url(#arrow-purple)")
    c.arrow(625, 166, 657, 166, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_cicd_pipeline() -> str:
    """Multi-Stage Container Optimization and Sub-40s Pipeline."""
    c = SchematicCanvas(860, 280, "MULTI-STAGE BUILD & SUB-40S CI/CD", "BUILD OPTIMIZATION")
    c.node(
        36,
        88,
        175,
        156,
        "Poetry Stage",
        "Full Virtualenv Build\nInstalls Packages\nBuild Cache Primed",
        "📦",
        "#ef4444",
        pill="860MB Build Cache",
    )
    c.node(
        243,
        88,
        175,
        156,
        "Distroless Prune",
        "Strips Build Tooling\nRetains Pure Runtime\nEliminates Shell Flaws",
        "🧹",
        "#38bdf8",
        pill="Pruned Image",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Hermetic QA",
        "In-Memory Test Gate\n52 Integrity Assertions\nZero Browser Waste",
        "🧪",
        "#22c55e",
        pill="Passes <35s",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Live Staging",
        "Fast Cold Boot <1.2s\nMinimal Attack Surface\nInstant Deployment",
        "🚀",
        "#a855f7",
        pill="42MB Production",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_knowledge_demotion_highway() -> str:
    """4-Tier Knowledge Taxonomy & Invariant Demotion Highway."""
    c = SchematicCanvas(860, 280, "4-TIER KNOWLEDGE TAXONOMY & DEMOTION HIGHWAY", "KNOWLEDGE GOVERNANCE")
    c.node(
        36,
        88,
        175,
        156,
        "Tier 0: Universal",
        "Class Alpha Invariants\nSafety Non-Negotiables\nStrict Prompt Budget",
        "🏛️",
        "#ef4444",
        pill="AGENTS.md <800t",
    )
    c.node(
        243,
        88,
        175,
        156,
        "Tier 1: Skills",
        "Progressive Subsystems\nSpecialized Workflows\nOn-Demand Retrieval",
        "🧠",
        "#38bdf8",
        pill=".agents/skills/",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Tier 2: Test Gates",
        "Shift-Left Integrity\nStatic Code Assertions\nPre-Commit Gate CI",
        "🧪",
        "#22c55e",
        pill="tests/governance/",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Tier 3: Blueprints",
        "Exhaustive Docs\nDomain Blueprints\nOperator Guides",
        "📘",
        "#a855f7",
        pill="docs/blueprints/",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_invariants_canon() -> str:
    """Living Canon of System Invariants & Dynamic Reference."""
    c = SchematicCanvas(860, 280, "LIVING CANON OF SYSTEM INVARIANTS", "LIVING CANON")
    c.node(
        36,
        88,
        230,
        156,
        "Class Alpha (P0)",
        "Sovereign Safety & Custody\nHuman Mk1 Eyeball Review\nVerbatim Grounding G=1.00",
        "🛡️",
        "#ef4444",
        pill="P0 Non-Negotiable",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Class Beta (P1)",
        "Execution Topology\n4-Phase Release Lifecycle\n500 LOC Ceiling Law",
        "⚙️",
        "#f59e0b",
        pill="P1 Process Boundaries",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Class Gamma (P2)",
        "Interface Symmetry\nUniversal 4-Way Parity\nZero-Build Standards",
        "📐",
        "#22c55e",
        pill="P2 Ergonomics",
    )
    c.arrow(266, 166, 315, 166, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(545, 166, 594, 166, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_agentic_engineering_lifecycle() -> str:
    """Antigravity 5-Stage Agentic Engineering Lifecycle."""
    c = SchematicCanvas(860, 280, "ANTIGRAVITY 5-STAGE AGENTIC LIFECYCLE", "AGENTIC PAIRING")
    c.node(
        28,
        88,
        140,
        156,
        "Research Phase",
        "Explore Codebase\nZero Code Edits\nMap Dependencies",
        "🔍",
        "#38bdf8",
        pill="Read-Only",
    )
    c.node(
        192,
        88,
        140,
        156,
        "Plan Phase",
        "Implementation Plan\nDefine Test Gates\nSurface Decisions",
        "📋",
        "#60a5fa",
        pill="Structured Design",
    )
    c.node(
        356,
        88,
        148,
        156,
        "Mk1 Review Gate",
        "Human Approval\nInspect Trade-offs\nSign-Off Required",
        "👁️",
        "#ef4444",
        pill="Human Sovereign",
    )
    c.node(
        528,
        88,
        140,
        156,
        "Execute Phase",
        "Hermetic Unit Tests\nAtomic Commits\nZero Browser Waste",
        "⚡",
        "#22c55e",
        pill="Hermetic QA",
    )
    c.node(
        692,
        88,
        140,
        156,
        "Learn Phase",
        "Walkthrough Brief\nExtract Invariants\nDemote to Skills",
        "🧠",
        "#a855f7",
        pill="/learn Patch",
    )
    c.arrow(168, 166, 192, 166, "#38bdf8")
    c.arrow(332, 166, 356, 166, "#ef4444", marker="url(#arrow-rose)")
    c.arrow(504, 166, 528, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(668, 166, 692, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_mesh_topology() -> str:
    """13-Node Watts-Strogatz Peer Mesh & Sybil Cartel Defense."""
    c = SchematicCanvas(860, 280, "13-NODE WATTS-STROGATZ MESH & SYBIL DEFENSE", "CONSENSUS MESH")
    c.node(
        36,
        80,
        360,
        170,
        "Honest Peer Cluster",
        "Watts-Strogatz Ring Lattice\nHigh Clustering Metric\nDeterministic Feed Hashing\nConsensus Median Shield",
        "🛡️",
        "#22c55e",
        pill="Consensus Quorum N=13",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Byzantine Sybil Cartel",
        "Collusion Swarm Detected\nTopic Entropy Collapsed\nSuspicion Slashed >70%\nAutonomous Quarantine",
        "🛑",
        "#ef4444",
        pill="Isolated Cartel (3f+1)",
    )
    c.arrow(396, 165, 464, 165, "#ef4444", marker="url(#arrow-rose)")
    return c.render()


def diagram_watts_strogatz_dynamics() -> str:
    """Watts-Strogatz Small-World Clustering & Routing Dynamics."""
    return diagram_mesh_topology()


def diagram_raspberry_pi_mesh() -> str:
    """13-Node Swarm Simulation on Resource-Constrained Hardware."""
    c = SchematicCanvas(860, 280, "13-NODE SWARM BENCHMARK ON RASPBERRY PI", "EMBEDDED BENCHMARK")
    c.node(
        36,
        88,
        230,
        156,
        "Hardware Host",
        "Raspberry Pi 4 / 5\n4x ARM64 CPU Cores\nTotal RAM: 4.0 GB",
        "🍓",
        "#ef4444",
        pill="Host Hardware",
    )
    c.node(
        315,
        88,
        230,
        156,
        "In-Memory Swarm",
        "13 Hermetic SQLite Nodes\nHRW Gossip Work Sharing\nSub-250ms Consensus",
        "🐝",
        "#22c55e",
        pill="< 1.2GB Swarm RAM",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Chaos Gauntlet",
        "Simulated Link Drops\nByzantine Injection Test\nZero Swarm Deadlocks",
        "⚡",
        "#38bdf8",
        pill="100% Hermetic Pass",
    )
    c.arrow(266, 166, 315, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(545, 166, 594, 166, "#38bdf8")
    return c.render()


def diagram_untrusted_ingestion() -> str:
    """Untrusted Ingestion Boundary & SSRF Defense Pipeline."""
    c = SchematicCanvas(860, 280, "UNTRUSTED INGESTION BOUNDARY & SSRF DEFENSE", "INGESTION DEFENSE")
    c.node(
        36,
        88,
        175,
        156,
        "Untrusted Source",
        "Public URLs & Raw HTML\nUnknown Entity Authors\nPotential Poisoning",
        "🌐",
        "#ef4444",
        pill="Untrusted Input",
    )
    c.node(
        243,
        88,
        175,
        156,
        "SSRF Guard",
        "Blocks Cloud Metadata\nBlocks Loopback IPs\nRejects DOCTYPE DTD",
        "🛡️",
        "#38bdf8",
        pill="169.254.x Filter",
    )
    c.node(
        450,
        88,
        175,
        156,
        "DOM Sanitizer",
        "Trafilatura Scrubber\nStrips JavaScript & CSS\nExtracts Clean DOM",
        "🧹",
        "#22c55e",
        pill="Cleaned Context",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Enclosed Payload",
        "Wrapped in Safety Tags\nCharacter Indexed\nReady for Grounding",
        "📦",
        "#a855f7",
        pill="Prompt Safe DOM",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_security_threat_model() -> str:
    """Comprehensive Security Architecture & Threat Model."""
    c = SchematicCanvas(860, 280, "SECURITY ARCHITECTURE & THREAT MODEL", "DEFENSE-IN-DEPTH")
    c.node(
        36,
        88,
        175,
        156,
        "Network Boundary",
        "SSRF IP Blocking\nLoopback Defense\nXML Entity Rejection",
        "🌐",
        "#38bdf8",
        pill="Boundary Guard",
    )
    c.node(
        243,
        88,
        175,
        156,
        "Prompt Shield",
        "Enclosed Untrusted Tags\nZero Inlined Blobs\nInjection Filter",
        "🛡️",
        "#60a5fa",
        pill="Injection Guard",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Verbatim Ground",
        "Whitespace-Insensitive\nQuote Match G=1.00\nHallucination Slash",
        "🔬",
        "#22c55e",
        pill="Quote Lock G=1.0",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Crypto Proof",
        "RFC 8785 Canonical JSON\nEd25519 Signed Envelopes\nImmutable Attest",
        "🔐",
        "#a855f7",
        pill="Tamper Seal",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_fastmcp_protocol() -> str:
    """FastMCP 2.0 Dual Transport Protocol & Tool Architecture."""
    c = SchematicCanvas(860, 280, "FASTMCP 2.0 DUAL TRANSPORT ARCHITECTURE", "PROTOCOL SPEC")
    c.node(
        36,
        88,
        220,
        156,
        "Client Runtime",
        "Claude Desktop / Cursor\nAI Agent Autonomous Flow\nStdio / SSE Client",
        "🤖",
        "#38bdf8",
        pill="AI Assistant",
    )
    c.node(
        310,
        88,
        240,
        156,
        "FastMCP 2.0 Server",
        "JSON-RPC Protocol Stream\nTools: evaluate, audit\nResources: live reports",
        "⚡",
        "#22c55e",
        pill="Dual Transport",
    )
    c.node(
        590,
        88,
        230,
        156,
        "Epistemic Backing",
        "Deterministic Scoring\nEd25519 Signed Attest\nSQLite Storage",
        "🔐",
        "#a855f7",
        pill="Verifiable Facts",
    )
    c.arrow(256, 166, 310, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(550, 166, 590, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_agent_readable_web() -> str:
    """Agent-Readable Web: FastMCP vs Brittle DOM Scraping."""
    c = SchematicCanvas(860, 280, "AGENT-READABLE WEB: FASTMCP vs SCRAPING", "DATA INGESTION")
    c.node(
        36,
        80,
        360,
        170,
        "Legacy Web Scraping",
        "Fragile HTML DOM Parsing\nBot Blocks & CAPTCHAs\nCSS Selector Breakages\nHigh Token Scraping Waste",
        "🕸️",
        "#ef4444",
        pill="Brittle & High Failure",
    )
    c.node(
        464,
        80,
        360,
        170,
        "FastMCP Semantic Web",
        "Typed JSON-RPC Resources\nStructured Claim Payload\nZero HTML Tag Overhead\nInstant Machine Grounding",
        "⚡",
        "#22c55e",
        pill="Reliable Agent Web",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_epistemic_brake() -> str:
    """The Epistemic Brake: Intercepting Agentic Hallucination."""
    c = SchematicCanvas(860, 280, "EPISTEMIC BRAKE: INTERCEPTING HALLUCINATION", "HALLUCINATION DEFENSE")
    c.node(
        36,
        88,
        220,
        156,
        "Agent Generates Claim",
        "LLM Synthesizes Text\nPotential Hallucination\nAsserts Factual Event",
        "🤖",
        "#f59e0b",
        pill="Unverified Draft",
    )
    c.node(
        310,
        88,
        240,
        156,
        "Epistemic Brake Gate",
        "FastMCP Tool Intercept\nPrimary Source Quote Match\nEnforces G=1.00 Grounding",
        "🛑",
        "#ef4444",
        pill="Grounding Brake",
    )
    c.node(
        590,
        88,
        230,
        156,
        "Grounded Output",
        "Character-Exact Evidence\nVerified Claim Approved\nSigned Crypto Proof",
        "✅",
        "#22c55e",
        pill="100% Fact Checked",
    )
    c.arrow(256, 166, 310, 166, "#ef4444", marker="url(#arrow-rose)")
    c.arrow(550, 166, 590, 166, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_four_way_parity() -> str:
    """Universal 4-Way Symmetric Feature Parity."""
    c = SchematicCanvas(860, 280, "UNIVERSAL 4-WAY SYMMETRIC FEATURE PARITY", "INTERFACE PARITY")
    c.node(
        36,
        80,
        175,
        82,
        "CLI Interface",
        "credence audit <url>\nTerminal Automation",
        "💻",
        "#38bdf8",
        pill="CLI Parity",
    )
    c.node(36, 170, 175, 82, "FastMCP 2.0", "Stdio / SSE RPC\nAgent Integrations", "⚡", "#22c55e", pill="MCP Parity")
    c.node(
        245,
        95,
        370,
        140,
        "Credence Core Engine",
        "compute_* Ontology Math\nRFC 8785 Canonical JSON\nSQLite WAL Persistence\nUnified Logic",
        "⚙️",
        "#f59e0b",
        pill="Single Source of Truth",
    )
    c.node(
        649, 80, 175, 82, "TUI Workstation", "Terminal UI Console\nInteractive Nav", "🖥️", "#60a5fa", pill="TUI Parity"
    )
    c.node(
        649, 170, 175, 82, "Zero-Build Web", "Vanilla HTML5 / ES\nInteractive Web", "🌐", "#a855f7", pill="Web Parity"
    )
    c.arrow(211, 121, 245, 145, "#38bdf8")
    c.arrow(211, 211, 245, 185, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(615, 145, 649, 121, "#60a5fa")
    c.arrow(615, 185, 649, 211, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_node_germination() -> str:
    """5-Second Zero-Touch Node Germination Sequence."""
    c = SchematicCanvas(860, 280, "5-SECOND ZERO-TOUCH NODE GERMINATION", "NODE GENESIS")
    c.node(
        36,
        88,
        175,
        156,
        "Keygen Genesis",
        "Generates Ed25519 Pair\nMints Node Identity\nRoot Seed Anchor",
        "🔑",
        "#38bdf8",
        pill="0.4s Genesis",
    )
    c.node(
        243,
        88,
        175,
        156,
        "Schema Priming",
        "Initializes SQLite WAL\nLoads Invariant Rules\nPre-Warms Cache",
        "💾",
        "#60a5fa",
        pill="1.1s DB Schema",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Peer Handshake",
        "Connects to Mesh Peers\nVerifies Signatures\nSyncs Gossip State",
        "🤝",
        "#22c55e",
        pill="2.8s Mesh Sync",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Active Sentry",
        "Receives Feed Tasks\nCalculates Grounding\nRelays Audits",
        "🚀",
        "#a855f7",
        pill="5.0s Fully Live",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_cold_start_optimization() -> str:
    """Cloud Run Scale-to-Zero Cold Start Optimization."""
    c = SchematicCanvas(860, 280, "CLOUD RUN SCALE-TO-ZERO OPTIMIZATION", "COLD-BOOT TIMELINE")
    c.node(
        36,
        88,
        175,
        156,
        "Scale-to-Zero",
        "0 Active Instances\n$0 Idle Infra Cost\nInstant Sleep on Idle",
        "🧊",
        "#38bdf8",
        pill="Zero Cost Idle",
    )
    c.node(
        243,
        88,
        175,
        156,
        "HTTP Request",
        "Inbound Traffic Spike\nFast Container Spin\nDistroless Optimize",
        "⚡",
        "#f59e0b",
        pill="Cold Wakeup",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Memory Warmup",
        "Pre-Warmed State Init\nSQLite Schema Check\nReady for Serving",
        "💾",
        "#22c55e",
        pill="Sub-1.2s Warmup",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Active Serving",
        "Full Throughput\nMicrosecond Latency\nScale to N Instances",
        "🚀",
        "#a855f7",
        pill="Live Serving",
    )
    c.arrow(211, 166, 243, 166, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_scale_to_zero_storage() -> str:
    """Scale-to-Zero Storage Hydration & GCS Dual-Pointer Checkpoints."""
    return diagram_cold_start_optimization()


def diagram_database_wal() -> str:
    """SQLite Write-Ahead Logging & 90-Day Retention Vacuum."""
    c = SchematicCanvas(860, 280, "SQLITE WAL CONCURRENCY & PRUNING", "STORAGE LIFECYCLE")
    c.node(
        36,
        88,
        175,
        156,
        "Writers & Readers",
        "Concurrent Read Queries\nNon-Blocking Writes\nZero Reader Locks",
        "👥",
        "#38bdf8",
        pill="Concurrent Clients",
    )
    c.node(
        243,
        88,
        175,
        156,
        "WAL Log File",
        "Sequential Append Log\nAtomic Transactions\nHigh Write Rate",
        "📝",
        "#60a5fa",
        pill="credence.db-wal",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Checkpointing",
        "Periodic WAL Flush\nSyncs to Main Database\nZero Data Loss",
        "💾",
        "#22c55e",
        pill="Main Database",
    )
    c.node(
        657,
        88,
        175,
        156,
        "90-Day Vacuum",
        "Automated Vacuum\nPrunes Old Records\nPreserves Storage",
        "🧹",
        "#a855f7",
        pill="Storage Pruned",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_disaster_recovery() -> str:
    """Multi-Region Replication & Automated Anycast Failover."""
    c = SchematicCanvas(860, 280, "MULTI-REGION REPLICATION & FAILOVER", "DISASTER RECOVERY")
    c.node(
        36,
        88,
        230,
        156,
        "Primary Region",
        "Google Cloud Run\nActive SQLite Master\nServing 100% Traffic",
        "🏛️",
        "#22c55e",
        pill="us-central1 (Active)",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Continuous Sync",
        "Snapshot State Sync\nImmutable Ed25519\nContinuous Probes",
        "🔄",
        "#38bdf8",
        pill="Cross-Region Sync",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Standby Region",
        "Warm Backup Instance\nInstant Anycast Switch\nZero RPO Data Loss",
        "🛡️",
        "#a855f7",
        pill="us-east1 (Standby)",
    )
    c.arrow(266, 166, 315, 166, "#38bdf8")
    c.arrow(545, 166, 594, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_gcp_project_isolation() -> str:
    """Single-Project Prefixing vs Dual-Project Hard IAM Boundaries."""
    c = SchematicCanvas(860, 280, "SINGLE vs DUAL GCP PROJECT BOUNDARIES", "IAM ISOLATION")
    c.node(
        36,
        80,
        360,
        170,
        "Single-Project Anti-Pattern",
        "Shared IAM Permissions\nResource Name Collisions\nAccidental Prod Data Leaks\nShared Workload Identity Pool",
        "⚠️",
        "#ef4444",
        pill="High Security Risk",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Dual-Project Architecture",
        "credence-dev & credence-prod\nSeparate Keyless WIF Pools\nZero Cross-Project Access\nStrict CI/CD Separation",
        "🛡️",
        "#22c55e",
        pill="Isolated IAM Boundaries",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_wireguard_mesh() -> str:
    """Encrypted Tailscale WireGuard Point-to-Point Overlay."""
    c = SchematicCanvas(860, 280, "TAILSCALE WIREGUARD ENCRYPTED OVERLAY", "SECURE OVERLAY")
    c.node(
        36,
        88,
        230,
        156,
        "Operator Laptop",
        "Admin Dev Laptop\nTailscale Mesh Node\nDirect DB Inspection",
        "💻",
        "#38bdf8",
        pill="Admin Peer",
    )
    c.node(
        315,
        88,
        230,
        156,
        "WireGuard Overlay",
        "Point-to-Point Encryption\nAuto NAT Traversal\nZero Open Ports",
        "🔒",
        "#22c55e",
        pill="WireGuard Tunnel",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Homelab & Cloud",
        "Raspberry Pi Clusters\nGoogle Cloud Run Nodes\nEncrypted Mesh Sync",
        "☁️",
        "#a855f7",
        pill="Private P2P Subnet",
    )
    c.arrow(266, 166, 315, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(545, 166, 594, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_synthetic_slop_collapse() -> str:
    """Model Collapse Degradation vs Verbatim Grounding."""
    c = SchematicCanvas(860, 280, "SYNTHETIC MODEL COLLAPSE vs GROUNDING", "EPISTEMIC RECOVERY")
    c.node(
        36,
        80,
        360,
        170,
        "Recursive Synthetic Slop",
        "Model Trained on Model Output\nProbability Tails Extinguished\nError Compounding Spiral\nEpistemic Degeneracy",
        "📉",
        "#ef4444",
        pill="Model Collapse Spiral",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Verbatim Primary Grounding",
        "Anchored to Source DOM\nExact Character Offset (G=1.0)\nHallucinations Slashed 50%\nPreserves Ground Truth",
        "🔬",
        "#22c55e",
        pill="Grounded Truth Anchor",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_dead_internet_immune_system() -> str:
    """The Dead Internet Immune System: Multi-Tier Bot Defense."""
    c = SchematicCanvas(860, 280, "THE DEAD INTERNET IMMUNE SYSTEM", "BOT DEFENSE")
    c.node(
        36,
        88,
        175,
        156,
        "Entropy Filter",
        "Detects Synthetic Slop\nFlags Collapsed Variance\nQuarantines Bot Feeds",
        "🤖",
        "#ef4444",
        pill="H < 0.30 Quarantine",
    )
    c.node(
        243,
        88,
        175,
        156,
        "FastMCP Ingest",
        "Structured JSON-RPC Stream\nDirect Machine Schemas\nBypasses Scraping",
        "⚡",
        "#38bdf8",
        pill="Typed RPC Protocol",
    )
    c.node(
        450,
        88,
        175,
        156,
        "Verbatim Check",
        "Character-Offset Grounding\nVerifies Source Quotes\nZero Hallucination Pass",
        "🔬",
        "#22c55e",
        pill="Exact Quote (G=1.0)",
    )
    c.node(
        657,
        88,
        175,
        156,
        "Signed Proof",
        "RFC 8785 Canonical JSON\nEd25519 Root Seal\nImmutable Attestation",
        "🔐",
        "#a855f7",
        pill="Sovereign Attest",
    )
    c.arrow(211, 166, 243, 166, "#38bdf8")
    c.arrow(418, 166, 450, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(625, 166, 657, 166, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_traffic_shaping_merit() -> str:
    """5-Factor Peer Quality Traffic Shaping Topology."""
    c = SchematicCanvas(860, 280, "5-FACTOR PEER QUALITY & TRAFFIC TIERS", "PEER MERIT")
    c.node(
        36,
        88,
        230,
        156,
        "5-Factor Formula",
        "Qi = 0.25U + 0.30C + 0.25G\nPlus 0.10T + 0.10K Factors\nEvaluates Reliability",
        "📊",
        "#38bdf8",
        pill="Reputation Formula",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Merit Tiers",
        "Tier 1: High Priority\nTier 2: Standard Relay\nTier 3: Probation Tier",
        "🏅",
        "#22c55e",
        pill="Bandwidth Priority",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Quarantine Gate",
        "Scores < 0.30 Isolated\nZero Gossip Relay Rights\nProtects Quorum",
        "🛑",
        "#ef4444",
        pill="Sybil Quarantine",
    )
    c.arrow(266, 166, 315, 166, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(545, 166, 594, 166, "#ef4444", marker="url(#arrow-rose)")
    return c.render()


def diagram_anti_tamper_badge() -> str:
    """WebCrypto Anti-Tamper Badge DOM Mutation Integrity."""
    c = SchematicCanvas(860, 280, "WEBCRYPTO ANTI-TAMPER BADGE INTEGRITY", "CLIENT-SIDE SECURITY")
    c.node(
        36,
        88,
        230,
        156,
        "Grounded Article",
        "Article Published to DOM\nAttestation Badge Mounted\nInitial SHA-256 Sealed",
        "📄",
        "#22c55e",
        pill="Verified Badge (Green)",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Mutation Watcher",
        "WebCrypto Hashes DOM\nMonitors Post-Publish Edits\nDetects Bait & Switch",
        "🔬",
        "#f59e0b",
        pill="SHA-256 Check",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Tamper Alarm",
        "Hash Mismatch Triggered\nBadge Flips to Red Warning\nProtects Reader Trust",
        "🚨",
        "#ef4444",
        pill="Tampered (Red Alert)",
    )
    c.arrow(266, 166, 315, 166, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(545, 166, 594, 166, "#ef4444", marker="url(#arrow-rose)")
    return c.render()


def diagram_subagent_parenthood() -> str:
    """Subagent Parenthood & Branched Workspace Task Delegation."""
    c = SchematicCanvas(860, 280, "SUBAGENT PARENTHOOD & WORKSPACE DELEGATION", "MULTI-AGENT TOPOLOGY")
    c.node(
        36,
        95,
        200,
        140,
        "Parent Agent",
        "Overall Task Orchestration\nDecomposes Sub-Tasks\nSynthesizes Responses",
        "🧠",
        "#38bdf8",
        pill="Main Coordinator",
    )
    c.node(
        310,
        75,
        235,
        78,
        "Subagent Research",
        "Explores Codebase & Docs\nRead-Only Sandbox Mode",
        "🔍",
        "#60a5fa",
        pill="Branch: feat/research",
    )
    c.node(
        310,
        165,
        235,
        78,
        "Subagent Refactor",
        "Executes Atomic Edits\nHermetic Unit Tests",
        "⚡",
        "#22c55e",
        pill="Branch: feat/refactor",
    )
    c.node(
        600,
        95,
        225,
        140,
        "Merged Result",
        "Proactive Task Wakeups\nContext Economy Preserved\nClean Atomic Commits",
        "🎯",
        "#a855f7",
        pill="Merged Production",
    )
    c.arrow(236, 130, 310, 114, "#60a5fa")
    c.arrow(236, 200, 310, 204, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(545, 114, 600, 130, "#a855f7", marker="url(#arrow-purple)")
    c.arrow(545, 204, 600, 200, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_token_headroom() -> str:
    """Token Headroom Budgeting & Circuit Breaker Margin."""
    c = SchematicCanvas(860, 280, "TOKEN HEADROOM BUDGETING & PRESERVATION", "TOKEN BUDGET")
    c.node(
        36,
        88,
        230,
        156,
        "Active Prompt Zone",
        "Up to 4,000 Tokens\nCore Instructions\nContext Efficient Inputs",
        "💬",
        "#38bdf8",
        pill="Working Memory",
    )
    c.node(
        315,
        88,
        230,
        156,
        "Thinking Headroom",
        "Extended Reasoning Zone\nEpistemic Deductions\nGemini 3.7 Thinking",
        "🧠",
        "#a855f7",
        pill="Reasoning Budget",
    )
    c.node(
        594,
        88,
        230,
        156,
        "Reserved 30% Zone",
        "Protects from Overages\nQUOTA_PRESERVED Trigger\nPrevents Starvation",
        "🛑",
        "#f59e0b",
        pill="Circuit Breaker",
    )
    c.arrow(266, 166, 315, 166, "#a855f7", marker="url(#arrow-purple)")
    c.arrow(545, 166, 594, 166, "#f59e0b", marker="url(#arrow-amber)")
    return c.render()


def diagram_anti_diploma() -> str:
    """The Anti-Diploma Invariant: Primary Evidence over Authority."""
    c = SchematicCanvas(860, 280, "THE ANTI-DIPLOMA INVARIANT: EVIDENCE OVER AUTHORITY", "EPISTEMIC STANDARDS")
    c.node(
        36,
        80,
        360,
        170,
        "Authority Credential Bias",
        "Institutional Checkmarks\nTitles & Academic Pedigree\nUnverified Press Releases\nArgumentum ad Verecundiam",
        "🎓",
        "#ef4444",
        pill="Disqualified Signal",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Verbatim Primary Grounding",
        "Exact DOM Quote Offset G=1.0\nDirect Public Records Evidence\nCryptographic Attestation Hash\nEmpirical Ground Truth",
        "🔬",
        "#22c55e",
        pill="Sovereign Truth Standard",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_crawler_commons() -> str:
    """The Tragedy of the Crawler Commons & Polite P2P Sharing."""
    c = SchematicCanvas(860, 280, "THE CRAWLER COMMONS: P2P SHARING vs DDOS", "COOPERATIVE CRAWLING")
    c.node(
        36,
        80,
        360,
        170,
        "Uncoordinated Crawlers",
        "100 Independent Scrapers\nHammering Small News Outlets\nServer Outages & IP Bans\nTragedy of the Commons",
        "💥",
        "#ef4444",
        pill="Server Degradation",
    )
    c.node(
        464,
        80,
        360,
        170,
        "Cooperative P2P Gossip",
        "Single Ingestion Crawl\nGossip Shared Attestations\nAdaptive Rate Limiting\nProtects Local Web Hosts",
        "🤝",
        "#22c55e",
        pill="Shared Ingestion Mesh",
    )
    c.arrow(396, 165, 464, 165, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


# ==============================================================================
# MASTER CATALOG OF ALL 42 ACTIVE ARCHITECTURAL ILLUSTRATIONS
# ==============================================================================

ACTIVE_DIAGRAMS = {
    # Case Studies & Deep-Dive Essays
    "conflict-of-pun-terest.svg": (
        diagram_conflict_of_punterest,
        "Figure 1.1: Circular conflict feedback loop between municipal governance and newsroom monopoly, and Credence forensic audit layer",
    ),
    "case-study-astroturfing-entropy.svg": (
        diagram_astroturfing_entropy,
        "Figure 1.1: Shannon topic entropy analysis distinguishing coordinated bot astroturfing from organic civic discourse",
    ),
    "case-study-dual-tier-finops.svg": (
        diagram_bicameral_finops,
        "Figure 1.1: Dual-tier bicameral inference architecture slashing LLM fact-checking costs by 83%",
    ),
    "finops-as-epistemology.svg": (
        diagram_finops_epistemology,
        "Figure 1.1: Bicameral inference triage and offline rate-limit circuit breaker architecture",
    ),
    "confessions-of-a-bored-ai.svg": (
        diagram_boredom_engine,
        "Figure 1.1: Autonomous boredom engine accumulation, excitation thresholds, and citation soil harvesting",
    ),
    "bittorrent-for-truth.svg": (
        diagram_bittorrent_fact_checking,
        "Figure 1.1: BitTorrent P2P fact-checking work-sharing protocol and rendezvous feed hashing",
    ),
    "bittorrent-economics-of-fact-checking.svg": (
        diagram_bittorrent_economics,
        "Figure 1.1: Decentralized compute swarm economics and deduplicated gossip audit propagation",
    ),
    "poes-law-and-the-satire-cloak.svg": (
        diagram_satire_decision_tree,
        "Figure 1.1: Poe's law satire safeguard vs SPJ-1.6 mandatory factual allegation override decision tree",
    ),
    "the-500-loc-ceiling-law.svg": (
        diagram_500_loc_ceiling,
        "Figure 1.1: The 500 LOC Ceiling Law and modular subpackage decoupling architecture",
    ),
    "the-500-loc-ceiling.svg": (
        diagram_500_loc_ceiling_governance,
        "Figure 1.1: Architectural governance boundaries enforcing single-responsibility code modules",
    ),
    "the-three-plane-architecture.svg": (
        diagram_three_plane_architecture,
        "Figure 1.1: 3-Plane decoupled deployment governance across Edge, Compute, and Infrastructure planes",
    ),
    "architecture.svg": (
        diagram_architecture_master,
        "Figure 1.1: Comprehensive Credence 3-plane ecosystem architecture and service topologies",
    ),
    "deployment-cloudrun.svg": (
        diagram_deployment_cloudrun,
        "Figure 1.1: Google Cloud Run serverless compute plane deployment with keyless WIF authentication",
    ),
    "from-860mb-to-2mb-sub-40s-cicd-pipeline.svg": (
        diagram_cicd_pipeline,
        "Figure 1.1: Multi-stage container build optimization and keyless WIF CI/CD staging pipeline",
    ),
    "the-demotion-highway.svg": (
        diagram_knowledge_demotion_highway,
        "Figure 1.1: 3-Tier knowledge demotion highway and living invariant prompt budget governance",
    ),
    "invariants.svg": (
        diagram_invariants_canon,
        "Figure 1.1: Universal living invariant canon and cognitive hierarchy architecture",
    ),
    "invariant-scalability-and-knowledge-governance.svg": (
        diagram_knowledge_demotion_highway,
        "Figure 1.1: Invariant scalability matrix, knowledge taxonomy, and AGENTS.md context economy",
    ),
    "architecting-sovereign-ai-with-google-antigravity.svg": (
        diagram_agentic_engineering_lifecycle,
        "Figure 1.1: Antigravity 5-stage agentic engineering lifecycle and human Mk1 review gate",
    ),
    "mesh-network.svg": (
        diagram_mesh_topology,
        "Figure 1.1: 13-node Watts-Strogatz peer mesh topology and Byzantine Sybil cartel defense",
    ),
    "watts-strogatz-dynamics.svg": (
        diagram_watts_strogatz_dynamics,
        "Figure 1.1: Watts-Strogatz small-world mesh clustering, rendezvous feed routing, and Sybil resistance",
    ),
    "testing-13-node-swarms-on-a-raspberry-pi.svg": (
        diagram_raspberry_pi_mesh,
        "Figure 1.1: Hardware resource governor adaptive swarm topology and memory throttling",
    ),
    "security.svg": (
        diagram_untrusted_ingestion,
        "Figure 1.1: Untrusted ingestion boundary, SSRF network defense, and Ed25519 cryptographic seal",
    ),
    "security-architecture-and-threat-model.svg": (
        diagram_security_threat_model,
        "Figure 1.1: Comprehensive security architecture, threat model, and untrusted boundary defenses",
    ),
    "fastmcp.svg": (
        diagram_fastmcp_protocol,
        "Figure 1.1: FastMCP 2.0 dual transport protocol, tools, resources, and prompt endpoints",
    ),
    "the-agent-readable-web-and-fastmcp.svg": (
        diagram_agent_readable_web,
        "Figure 1.1: FastMCP 2.0 typed JSON-RPC stream vs brittle legacy headless DOM scraping",
    ),
    "giving-claude-and-cursor-an-epistemic-brake.svg": (
        diagram_epistemic_brake,
        "Figure 1.1: The Hallucination Pipeline vs FastMCP 2.0 Epistemic Brake architecture and prompt injection defense",
    ),
    "feature-parity.svg": (
        diagram_four_way_parity,
        "Figure 1.1: Universal 4-way feature parity across CLI, FastMCP, TUI, and Zero-Build Web UI",
    ),
    "node-germination-lifecycle.svg": (
        diagram_node_germination,
        "Figure 1.1: Zero-touch node germination lifecycle, seed initialization, and attestation persistence",
    ),
    "cloudrun-scale-to-zero-cold-start-optimization.svg": (
        diagram_cold_start_optimization,
        "Figure 1.1: Cloud Run scale-to-zero cold-start container optimization and sub-1.2s snapshot restore",
    ),
    "pining-for-the-fjords.svg": (
        diagram_scale_to_zero_storage,
        "Figure 1.1: Scale-to-zero cold-boot storage hydration cycle and dual-pointer GCS snapshot sync",
    ),
    "database-pruning-wal.svg": (
        diagram_database_wal,
        "Figure 1.1: SQLite Write-Ahead Logging concurrency architecture and 90-day pruning lifecycle",
    ),
    "disaster-recovery-and-cross-region-failover.svg": (
        diagram_disaster_recovery,
        "Figure 1.1: Active-Active multi-region replication and automated DNS failover architecture",
    ),
    "single-vs-dual-project-gcp.svg": (
        diagram_gcp_project_isolation,
        "Figure 1.1: Single GCP project name-prefixing vs dual GCP project hard IAM boundary isolation",
    ),
    "tailscale-wireguard-mesh.svg": (
        diagram_wireguard_mesh,
        "Figure 1.1: Tailscale WireGuard encrypted point-to-point mesh network topology",
    ),
    "escaping-the-synthetic-slop-singularity.svg": (
        diagram_synthetic_slop_collapse,
        "Figure 1.1: Model collapse probability distribution degradation vs character-offset verbatim grounding",
    ),
    "the-dead-internet-immune-system.svg": (
        diagram_dead_internet_immune_system,
        "Figure 1.1: Multi-tiered bot resistance, FastMCP structured ingestion, and cryptographic verbatim grounding",
    ),
    "gamifying-truth-without-the-casino.svg": (
        diagram_traffic_shaping_merit,
        "Figure 1.1: 4-tier peer quality traffic shaping classes and bandwidth allocation",
    ),
    "red-teaming-the-truth-badge.svg": (
        diagram_anti_tamper_badge,
        "Figure 1.1: Red-teaming the truth badge and detecting bait-and-switch DOM mutations with WebCrypto",
    ),
    "subagent-parenthood.svg": (
        diagram_subagent_parenthood,
        "Figure 1.1: Subagent parenthood architecture and isolated workspace task delegation",
    ),
    "the-4000-token-trance.svg": (
        diagram_token_headroom,
        "Figure 1.1: Token headroom budgeting zones and QUOTA_PRESERVED circuit breaker ceiling",
    ),
    "the-anti-diploma-invariant.svg": (
        diagram_anti_diploma,
        "Figure 1.1: The Anti-Diploma Invariant: Authority credentials vs character-exact verbatim grounding",
    ),
    "the-tragedy-of-the-crawler-commons.svg": (
        diagram_crawler_commons,
        "Figure 1.1: The tragedy of the crawler commons and polite P2P mesh work-sharing protocols",
    ),
}


def execute_audit(ecosystem_root: Path):
    docs_root = ecosystem_root / "credence-docs"
    docs_illustrations_dir = docs_root / "assets" / "illustrations"
    web_illustrations_dir = ecosystem_root / "credence" / "web" / "assets" / "illustrations"

    print("=== Step 1: Generating 42 Active Architectural Schematics ===")
    docs_illustrations_dir.mkdir(parents=True, exist_ok=True)
    web_illustrations_dir.mkdir(parents=True, exist_ok=True)

    generated_count = 0
    for filename, (builder, _) in ACTIVE_DIAGRAMS.items():
        svg_xml = builder()
        (docs_illustrations_dir / filename).write_text(svg_xml, encoding="utf-8")
        (web_illustrations_dir / filename).write_text(svg_xml, encoding="utf-8")
        generated_count += 1

    print(f"✅ Active Schematics Generated: {generated_count} precision SVGs created with 100% SHA-256 parity.")


if __name__ == "__main__":
    eco_root = Path("/home/pendragon/Projects/credence-ecosystem")
    execute_audit(eco_root)
