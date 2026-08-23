#!/usr/bin/env python3
"""Precision SVG Illustration Engine for Credence Ecosystem.

Overhauls all vector SVG illustrations with exact card-to-card geometry,
clean interconnects, tailored archetypes, and zero floating/orphan lines.
"""

import html
import re
from pathlib import Path
from typing import List, Optional


class SVGCanvas:
    """Modular SVG Canvas Builder with Credence Dark-Mode Styling."""

    def __init__(self, width: int = 860, height: int = 360, title: str = "", category: str = "CREDENCE ARCHITECTURE"):
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
        fill: str = "#1e293b",
        stroke: str = "rgba(56, 189, 248, 0.25)",
        stroke_width: float = 1.0,
        filter_id: Optional[str] = None,
        opacity: float = 1.0,
        dashed: bool = False,
    ) -> None:
        filt = f' filter="url(#{filter_id})"' if filter_id else ""
        dash = ' stroke-dasharray="4 4"' if dashed else ""
        op = f' opacity="{opacity}"' if opacity < 1.0 else ""
        self.elements.append(
            f'<rect x="{round(x, 1)}" y="{round(y, 1)}" width="{round(w, 1)}" height="{round(h, 1)}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}{filt}{op} />'
        )

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str = "#1e293b",
        stroke: str = "#38bdf8",
        stroke_width: float = 1.5,
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
        font_size: float = 13,
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

    def card(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str = "",
        icon: str = "",
        accent: str = "#38bdf8",
        badge: str = "",
        fill: str = "#0f172a",
    ) -> None:
        """Render a sleek Credence dark slate card with glowing accent border and metadata."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=accent, stroke_width=1.2, filter_id="card-shadow")
        self.rect(x, y, w, 3, rx=1.5, fill=accent, stroke="none")

        header_x = x + 12
        if icon:
            self.text(header_x, y + 21, icon, font_size=14, anchor="start")
            header_x += 22

        self.text(header_x, y + 21, title[:28], font_size=12.5, fill="#f8fafc", font_weight="600")

        if badge:
            badge_w = min(110, len(badge) * 7.0 + 12)
            badge_x = x + w - badge_w - 10
            self.rect(
                badge_x, y + 8, badge_w, 18, rx=4, fill="rgba(56, 189, 248, 0.12)", stroke=accent, stroke_width=0.8
            )
            self.text(
                badge_x + badge_w / 2,
                y + 20.5,
                badge,
                font_size=9.5,
                fill=accent,
                font_family="monospace",
                font_weight="bold",
                anchor="middle",
            )

        if subtitle:
            sub_lines = subtitle.split("\n")
            line_y = y + 40
            for s_line in sub_lines[:4]:
                self.text(x + 12, line_y, s_line[:48], font_size=10.5, fill="#94a3b8", font_family="sans-serif")
                line_y += 15

    def cluster(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        color: str = "#38bdf8",
        bg: str = "rgba(9, 13, 22, 0.75)",
        dashed: bool = False,
    ) -> None:
        """Render a subgraph/plane cluster boundary."""
        self.rect(x, y, w, h, rx=10, fill=bg, stroke=color, stroke_width=1.0, dashed=dashed, opacity=0.9)
        tw = min(w - 20, len(title) * 7.2 + 18)
        self.rect(x + 12, y - 9, tw, 18, rx=4, fill="#090d16", stroke=color, stroke_width=1.0)
        self.text(
            x + 12 + tw / 2,
            y + 3.5,
            title,
            font_size=9.5,
            fill=color,
            font_family="sans-serif",
            font_weight="bold",
            anchor="middle",
        )

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        color: str = "#38bdf8",
        dashed: bool = False,
        marker: str = "url(#arrow-cyan)",
    ) -> None:
        """Render directional connection arrow with non-overlapping label pill."""
        dx = x2 - x1
        dy = y2 - y1
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 5:
            return

        self.line(x1, y1, x2, y2, stroke=color, stroke_width=1.4, dashed=dashed, marker_end=marker)

        if label and dist >= 45:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            lw = min(dist - 10, len(label) * 6.5 + 12)
            self.rect(mx - lw / 2, my - 8, lw, 16, rx=3, fill="#090d16", stroke=color, stroke_width=0.8)
            self.text(mx, my + 3.5, label, font_size=9, fill="#e2e8f0", font_family="monospace", anchor="middle")

    def pipeline_step(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        step: str,
        title: str,
        desc: str = "",
        color: str = "#38bdf8",
        fill: str = "#0f172a",
    ) -> None:
        """Render an ingestion/lifecycle pipeline card with step badge."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=color, stroke_width=1.2, filter_id="card-shadow")
        self.circle(x + 20, y + h / 2, 11, fill="#1e293b", stroke=color, stroke_width=1.2)
        self.text(x + 20, y + h / 2 + 3.5, step, font_size=9.5, fill=color, font_weight="bold", anchor="middle")

        self.text(x + 38, y + 20, title[:30], font_size=12, fill="#f8fafc", font_weight="600")
        if desc:
            self.text(x + 38, y + 36, desc[:42], font_size=10, fill="#94a3b8", font_family="monospace")

    def render(self) -> str:
        """Generate clean, standalone SVG XML."""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="100%" height="auto" style="background: transparent;">
  <defs>
    <linearGradient id="obsidian-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16" />
      <stop offset="100%" stop-color="#050810" />
    </linearGradient>
    <linearGradient id="cyan-glow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#60a5fa" />
    </linearGradient>
    <filter id="card-shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#000000" flood-opacity="0.6" />
    </filter>
    <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
    </marker>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#60a5fa" />
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

  <!-- Background Base -->
  <rect width="{self.width}" height="{self.height}" rx="12" fill="url(#obsidian-bg)" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1.0" />

  <!-- Top Header Bar -->
  <text x="24" y="28" fill="#38bdf8" font-size="10" font-family="monospace" font-weight="bold" letter-spacing="0.1em">{html.escape(self.category.upper())}</text>
  <text x="24" y="46" fill="#f8fafc" font-size="13.5" font-family="sans-serif" font-weight="bold" letter-spacing="0.01em">{html.escape(self.title.upper())}</text>

  <!-- Elements -->
  {"".join(self.elements)}
</svg>
"""


def build_three_plane_architecture(title: str = "3-PLANE DECOUPLED GOVERNANCE ARCHITECTURE") -> SVGCanvas:
    c = SVGCanvas(860, 360, title, "INFRASTRUCTURE TOPOLOGY")

    c.cluster(25, 65, 255, 275, "EDGE PLANE (Cloudflare)", "#38bdf8")
    c.card(
        40,
        95,
        225,
        65,
        "Zero-Build Web UI",
        "Vanilla HTML5 / ES Modules\nZero npm dependencies",
        "🌐",
        "#38bdf8",
        "Edge",
    )
    c.card(
        40, 175, 225, 65, "Interactive Docs", "docs.credence.run\nZero-latency client search", "📘", "#60a5fa", "Pages"
    )
    c.card(
        40,
        255,
        225,
        65,
        "Edge Router (_worker.js)",
        "Multi-domain routing\nTiered CDN cache headers",
        "⚡",
        "#38bdf8",
        "Worker",
    )

    c.cluster(302, 65, 255, 275, "COMPUTE PLANE (Cloud Run)", "#22c55e")
    c.card(
        317,
        95,
        225,
        65,
        "FastMCP 2.0 Engine",
        "Stdio & SSE Transports\nAutomated tools & resources",
        "⚙️",
        "#22c55e",
        "FastMCP",
    )
    c.card(
        317,
        175,
        225,
        65,
        "Starlette Core Server",
        "Ingestion, Scrubber & API\nRate limiting & Prometheus",
        "🚀",
        "#38bdf8",
        ":8000",
    )
    c.card(
        317,
        255,
        225,
        65,
        "SQLite + Vector Store",
        "Relational audit trails\nVector embeddings (WAL)",
        "💾",
        "#a855f7",
        "Storage",
    )

    c.cluster(580, 65, 255, 275, "INFRASTRUCTURE PLANE", "#a855f7")
    c.card(
        595, 95, 225, 65, "Terraform Multi-Cloud", "GCP Cloud Run + WIF\nCloudflare DNS & Pages", "🏛️", "#a855f7", "HCL"
    )
    c.card(
        595,
        175,
        225,
        65,
        "GitHub Actions CI/CD",
        "Keyless WIF deploy\nAutomated dev staging",
        "🔄",
        "#60a5fa",
        "Actions",
    )
    c.card(
        595,
        255,
        225,
        65,
        "Genesis Key Custody",
        "RFC 8785 Canonical JSON\nEd25519 root authority",
        "🔐",
        "#22c55e",
        "Sovereign",
    )

    c.arrow(265, 127, 317, 127, "API / SSE", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(542, 127, 595, 127, "WIF Auth", "#22c55e", marker="url(#arrow-emerald)")
    return c


def build_pipeline_architecture(
    title: str,
    step1: tuple[str, str],
    step2: tuple[str, str],
    step3: tuple[str, str],
    step4: tuple[str, str],
    footer: tuple[str, str],
    category: str = "SECURITY & PIPELINE",
) -> SVGCanvas:
    c = SVGCanvas(860, 360, title, category)

    s_w = 175
    s_h = 75
    gap = 25
    x_start = 42
    y_top = 75

    steps = [
        ("1", step1[0], step1[1], "#38bdf8", "url(#arrow-cyan)"),
        (
            "2",
            step2[0],
            step2[1],
            "#ef4444" if "ssrf" in step2[0].lower() or "filter" in step2[0].lower() else "#60a5fa",
            "url(#arrow-blue)",
        ),
        ("3", step3[0], step3[1], "#a855f7", "url(#arrow-purple)"),
        ("4", step4[0], step4[1], "#22c55e", "url(#arrow-emerald)"),
    ]

    for idx, (num, s_title, s_desc, col, marker) in enumerate(steps):
        sx = x_start + idx * (s_w + gap)
        c.pipeline_step(sx, y_top, s_w, s_h, num, s_title, s_desc, col)
        if idx < 3:
            next_sx = x_start + (idx + 1) * (s_w + gap)
            c.arrow(sx + s_w, y_top + s_h / 2, next_sx, y_top + s_h / 2, "", col, marker=marker)

    c.card(42, 175, 775, 150, footer[0], footer[1], "🛡️", "#22c55e", "INVARIANT")
    return c


def build_demotion_highway(title: str = "THE DEMOTION HIGHWAY & KNOWLEDGE SCALABILITY MATRIX") -> SVGCanvas:
    c = SVGCanvas(860, 360, title, "KNOWLEDGE GOVERNANCE")

    c.cluster(25, 65, 255, 275, "TIER 0: UNIVERSAL INVARIANTS", "#ef4444")
    c.card(
        40,
        95,
        225,
        65,
        "P0 Sovereign Safety",
        "Always-on LLM prompt\n<800 tokens hard ceiling",
        "🧠",
        "#ef4444",
        "Tier 0",
    )
    c.card(
        40,
        175,
        225,
        145,
        "Cognitive Hierarchy",
        "• Class α: Safety & Authority\n• Class β: Lifecycle Topology\n• Class γ: Interface Symmetry\n• Strict Mk1 Eyeball Gate",
        "⚖️",
        "#f59e0b",
        "Bible",
    )

    c.cluster(302, 65, 255, 275, "TIER 1: PROGRESSIVE SKILLS", "#38bdf8")
    c.card(
        317, 95, 225, 65, "Subsystem Skills", "Loaded dynamically on-demand\n.agents/skills/*", "☁️", "#38bdf8", "Tier 1"
    )
    c.card(
        317,
        175,
        225,
        145,
        "Domain Capabilities",
        "• cloudrun-ops\n• mesh-cluster\n• white-label-ops\n• architecture-governance\n• epistemic-benchmark",
        "🏛️",
        "#60a5fa",
        "On-Demand",
    )

    c.cluster(580, 65, 255, 275, "TIER 2: SHIFT-LEFT TESTS", "#22c55e")
    c.card(
        595,
        95,
        225,
        65,
        "Deterministic Test Gates",
        "Shift-left automated QA\n<0.3s local execution",
        "⚡",
        "#22c55e",
        "Tier 2",
    )
    c.card(
        595,
        175,
        225,
        145,
        "Mechanical Rules",
        "• Zero-npm invariant\n• 7-Manifest parity sync\n• Code fence indentation\n• Sitemap route coverage\n• Tiered cache headers",
        "🛡️",
        "#22c55e",
        "Justfile",
    )

    c.arrow(280, 127, 302, 127, "Graduate", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(557, 127, 580, 127, "Demote", "#22c55e", marker="url(#arrow-emerald)")
    return c


def build_mesh_cluster(title: str = "13-NODE WATTS-STROGATZ PEER-TO-PEER MESH TOPOLOGY") -> SVGCanvas:
    c = SVGCanvas(860, 360, title, "CONSENSUS PROTOCOL")

    c.cluster(25, 65, 395, 275, "High-Merit Peer Ring (M_i >= 0.70)", "#22c55e")
    c.card(40, 95, 170, 60, "Node 0 (Genesis)", "M=0.98 | f=4", "🛡️", "#22c55e", "Root")
    c.card(235, 95, 170, 60, "Node 1 (Relay)", "M=0.92 | f=4", "⚡", "#38bdf8", "Active")
    c.card(40, 175, 170, 60, "Node 2 (Auditor)", "M=0.88 | f=4", "🔬", "#60a5fa", "Active")
    c.card(235, 175, 170, 60, "Node 3 (Sifter)", "M=0.85 | f=4", "🔍", "#38bdf8", "Active")
    c.card(137, 255, 170, 60, "Node 4 (Digest)", "M=0.82 | f=4", "📰", "#a855f7", "Active")

    c.line(210, 125, 235, 125, "#22c55e", 1.2, marker_end=None)
    c.line(210, 205, 235, 205, "#22c55e", 1.2, marker_end=None)
    c.line(125, 155, 125, 175, "#22c55e", 1.2, marker_end=None)
    c.line(320, 155, 320, 175, "#22c55e", 1.2, marker_end=None)
    c.line(125, 235, 170, 255, "#22c55e", 1.2, marker_end=None)
    c.line(320, 235, 275, 255, "#22c55e", 1.2, marker_end=None)

    c.cluster(440, 65, 395, 275, "Byzantine Sybil Cartel Defense (N >= 3f + 1)", "#ef4444")
    c.card(455, 95, 175, 60, "Quarantine Node 9", "Suspicion: 88.4%", "🛑", "#ef4444", "Isolated")
    c.card(645, 95, 175, 60, "Quarantine Node 10", "Suspicion: 92.1%", "🛑", "#ef4444", "Isolated")
    c.card(
        455,
        175,
        365,
        140,
        "Consensus Quarantine & Cartel Isolation",
        "• HRW rendezvous hashing partitions feed topics.\n• Nodes with S_j > 70.0% quarantined autonomously.\n• Cartels cannot achieve 3f+1 threshold to skew scores.\n• Byzantine fault tolerance: f = floor((N-1)/3).",
        "⚖️",
        "#f59e0b",
        "Sybil Shield",
    )

    c.arrow(405, 125, 455, 125, "Gossip", "#60a5fa", marker="url(#arrow-blue)")
    return c


def build_information_pyramid(title: str = "THE EPISTEMIC LENSING & INFORMATION PYRAMID") -> SVGCanvas:
    c = SVGCanvas(860, 360, title, "EPISTEMIC LENSING")

    c.card(
        260,
        65,
        340,
        70,
        "1. SURFACE LENS (Glance)",
        "• Overall Credence score gauge (0-100)\n• Quick verified / suspicious badge",
        "⚡",
        "#22c55e",
        "Tier 1",
    )
    c.card(
        160,
        155,
        540,
        75,
        "2. FOCUS LENS (Explore)",
        "• Deconstructed claims & deceptive pattern tags\n• Verbatim DOM citations (G=1.00) & sparklines",
        "🔍",
        "#38bdf8",
        "Tier 2",
    )
    c.card(
        60,
        250,
        740,
        80,
        "3. DEEP SPECTRUM LENS (Forensic Audit)",
        "• Cryptographic Ed25519 signatures & RFC 8785 canonical envelopes\n• Raw DOM SHA-256 hash & full temporal diff timeline",
        "🔬",
        "#a855f7",
        "Tier 3",
    )

    c.arrow(430, 135, 430, 155, "", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(430, 230, 430, 250, "", "#a855f7", marker="url(#arrow-purple)")
    return c


def build_interface_parity_hub(title: str = "UNIVERSAL 4-WAY FEATURE PARITY & INTERFACE HUB") -> SVGCanvas:
    c = SVGCanvas(860, 360, title, "INTERFACE SYMMETRY")

    c.card(
        310,
        135,
        240,
        90,
        "FastMCP 2.0 Core Engine",
        "Stdio & SSE Transports\nShared Heuristics & Scoring",
        "⚙️",
        "#22c55e",
        "Core Hub",
    )

    c.card(40, 85, 210, 70, "Command Line (CLI)", "credence audit <url>\nFast terminal outputs", "💻", "#38bdf8", "CLI")
    c.card(
        40, 205, 210, 70, "Textual TUI Workstation", "credence-tui\nKeyboard-first dashboard", "📟", "#60a5fa", "TUI"
    )

    c.card(610, 85, 210, 70, "Zero-Build Web UI", "Vanilla HTML5/ES6\n5 invariant nav links", "🌐", "#a855f7", "Web")
    c.card(
        610,
        205,
        210,
        70,
        "Claude / Agent SDK",
        "Automated MCP prompts\nEpistemic brake tool",
        "🤖",
        "#f59e0b",
        "Agents",
    )

    c.arrow(250, 120, 310, 160, "CLI API", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(250, 240, 310, 200, "TUI SSE", "#60a5fa", marker="url(#arrow-blue)")
    c.arrow(550, 160, 610, 120, "Web API", "#a855f7", marker="url(#arrow-purple)")
    c.arrow(550, 200, 610, 240, "FastMCP", "#f59e0b", marker="url(#arrow-amber)")

    c.card(
        40,
        295,
        780,
        45,
        "Class γ Invariant: 100% Feature Parity Across All 4 Interfaces",
        "Every capability available in Web is accessible via CLI, TUI, and FastMCP.",
        "✨",
        "#22c55e",
        "Symmetry",
    )
    return c


def build_generic_topic_illustration(slug: str, title: str, category: str = "ARCHITECTURE") -> SVGCanvas:
    clean_title = title.replace("#", "").strip()[:60]
    c = SVGCanvas(860, 360, clean_title, category)

    c.cluster(25, 65, 255, 205, "INGESTION & SCRUBBING", "#38bdf8")
    c.card(
        40,
        95,
        225,
        70,
        "Input Boundary",
        "Target URLs, text, and feeds\nSSRF & private IP filter",
        "📥",
        "#38bdf8",
        "Boundary",
    )
    c.card(
        40,
        180,
        225,
        75,
        "DOM Extractor & Scrubber",
        "Strip script & XML entities\nGrounding text quarantine",
        "🧹",
        "#60a5fa",
        "Sanitized",
    )
    c.arrow(152, 165, 152, 180, "", "#38bdf8", marker="url(#arrow-cyan)")

    c.cluster(302, 65, 255, 205, "EPISTEMIC EVALUATION", "#22c55e")
    c.card(
        317,
        95,
        225,
        70,
        "Multi-Model Heuristics",
        "Heuristic rules & claim extract\nQuota preserved fallback",
        "🧠",
        "#22c55e",
        "Reasoning",
    )
    c.card(
        317,
        180,
        225,
        75,
        "Consensus Aggregator",
        "Expertise-weighted medians\nShannon entropy astroturf def",
        "⚖️",
        "#f59e0b",
        "Consensus",
    )
    c.arrow(429, 165, 429, 180, "", "#22c55e", marker="url(#arrow-emerald)")

    c.cluster(580, 65, 255, 205, "ATTESTATION & CUSTODY", "#a855f7")
    c.card(
        595,
        95,
        225,
        70,
        "RFC 8785 Canonical JSON",
        "Deterministic UTF-8 serialization\nSorted keys byte stream",
        "📜",
        "#a855f7",
        "Receipt",
    )
    c.card(
        595,
        180,
        225,
        75,
        "Ed25519 Cryptographic Seal",
        "Genesis root authority sign\nTamper-evident verification",
        "🔐",
        "#22c55e",
        "Sovereign",
    )
    c.arrow(707, 165, 707, 180, "", "#a855f7", marker="url(#arrow-purple)")

    c.arrow(280, 130, 302, 130, "Clean Text", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(557, 130, 580, 130, "Attest", "#22c55e", marker="url(#arrow-emerald)")

    c.card(
        25,
        285,
        810,
        55,
        "Living Invariant Compliance",
        "Zero-trust untrusted source isolation • Grounding exactness G=1.00 • Hermetic execution <35s",
        "🛡️",
        "#22c55e",
        "Verified",
    )
    return c


def get_illustration_for_topic(slug: str, title: str, category_path: str) -> SVGCanvas:
    s = slug.lower()
    cat = category_path.split("/")[0].upper() if category_path and category_path != "." else "ECOSYSTEM"

    if any(k in s for k in ["three-plane", "architecture", "cloudrun", "deployment", "single-vs-dual"]):
        return build_three_plane_architecture(title)

    if any(k in s for k in ["demotion", "knowledge", "governance", "invariants", "500-loc", "anti-diploma"]):
        return build_demotion_highway(title)

    if any(k in s for k in ["mesh", "watts-strogatz", "rendezvous", "sybil", "airgapped", "swarm"]):
        return build_mesh_cluster(title)

    if any(k in s for k in ["pyramid", "lensing", "spectrum", "galileo", "satire", "poes-law"]):
        return build_information_pyramid(title)

    if any(k in s for k in ["parity", "tui", "cli", "fastmcp", "browser-extension", "four-way"]):
        return build_interface_parity_hub(title)

    if any(k in s for k in ["ssrf", "scrubber", "security", "threat-model", "grounding", "canonical", "ed25519"]):
        return build_pipeline_architecture(
            title,
            ("Raw Input", "URL / untrusted text"),
            ("SSRF Guard", "Block private IPs & 169.254"),
            ("DOM Extractor", "Strip scripts & entities"),
            ("Attestation", "RFC 8785 Ed25519 sign"),
            (
                "Epistemic Security & Untrusted Ingestion Boundary",
                "Citations match source character-for-character (G=1.00). Private IPs blocked autonomously.",
            ),
            category=cat,
        )

    return build_generic_topic_illustration(slug, title, category=cat)


def regenerate_all_illustrations(
    docs_dir: Path,
    output_dirs: List[Path],
) -> tuple[int, int]:
    for d in output_dirs:
        d.mkdir(parents=True, exist_ok=True)

    md_files = sorted(list(docs_dir.glob("docs/**/*.md")) + list(docs_dir.glob("blog/**/*.md")))
    total_svgs = 0
    total_files = 0

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        slug = md_file.stem
        rel_cat = md_file.parent.relative_to(docs_dir).as_posix()

        title = slug.replace("-", " ").title()
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        matches = re.findall(r"!\[([^\]]*)\]\(assets/illustrations/([^)]+\.svg)\)", text)
        if not matches:
            canvas = get_illustration_for_topic(slug, title, rel_cat)
            svg_content = canvas.render()
            for out_dir in output_dirs:
                (out_dir / f"{slug}.svg").write_text(svg_content, encoding="utf-8")
            total_svgs += 1
            continue

        for alt_title, svg_filename in matches:
            svg_slug = svg_filename.replace(".svg", "")
            use_title = alt_title.strip() if alt_title.strip() else title
            canvas = get_illustration_for_topic(svg_slug, use_title, rel_cat)
            svg_content = canvas.render()

            for out_dir in output_dirs:
                (out_dir / svg_filename).write_text(svg_content, encoding="utf-8")
            total_svgs += 1

        total_files += 1

    print(f"✅ Precision SVG overhaul complete: {total_svgs} SVG illustrations generated across {total_files} files.")
    return total_files, total_svgs


if __name__ == "__main__":
    ecosystem_root = Path("/home/pendragon/Projects/credence-ecosystem")
    docs_root = ecosystem_root / "credence-docs"
    out_dirs = [
        ecosystem_root / "credence-docs" / "assets" / "illustrations",
        ecosystem_root / "credence" / "web" / "assets" / "illustrations",
    ]
    generator_target = ecosystem_root / "credence" / "scripts" / "generate_illustrations.py"
    generator_target.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    regenerate_all_illustrations(docs_root, out_dirs)
