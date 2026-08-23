#!/usr/bin/env python3
"""Credence Clean Vector SVG Technical Illustration Engine (Zero-Overlap Precision).

Design Principles:
- Zero decorative pill/badge clutter
- Exact line heights and generous card padding to prevent text overflow
- Clean, directional card-to-card connectors with non-overlapping labels
- Contextual, topic-specific technical diagrams
- 860x360 responsive viewBox with obsidian #090d16 background
"""

import html
import re
from pathlib import Path
from typing import List, Optional


class CleanSVGCanvas:
    """Spacious, pill-free SVG Canvas with Credence Dark-Mode Styling."""

    def __init__(self, width: int = 860, height: int = 360, title: str = "", category: str = "CREDENCE ECOSYSTEM"):
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
        fill: str = "#0f172a",
    ) -> None:
        """Render a clean card with generous padding, accent border, and zero decorative pills."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=accent, stroke_width=1.2, filter_id="card-shadow")
        self.rect(x, y, w, 3, rx=1.5, fill=accent, stroke="none")

        header_x = x + 14
        if icon:
            self.text(header_x, y + 22, icon, font_size=14, anchor="start")
            header_x += 22

        self.text(header_x, y + 22, title, font_size=12, fill="#f8fafc", font_weight="600")

        if subtitle:
            sub_lines = subtitle.split("\n")
            line_y = y + 42
            for s_line in sub_lines:
                self.text(x + 14, line_y, s_line, font_size=10.5, fill="#94a3b8", font_family="sans-serif")
                line_y += 17

    def container(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str = "",
        color: str = "rgba(56, 189, 248, 0.3)",
        bg: str = "rgba(15, 23, 42, 0.5)",
    ) -> None:
        """Render a clean grouping container without overlapping header pills."""
        self.rect(x, y, w, h, rx=10, fill=bg, stroke=color, stroke_width=1.0)
        if title:
            self.text(
                x + 14, y + 18, title.upper(), font_size=9.5, fill=color, font_family="monospace", font_weight="bold"
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
        """Render clean directional connection arrow."""
        dx = x2 - x1
        dy = y2 - y1
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 8:
            return

        self.line(x1, y1, x2, y2, stroke=color, stroke_width=1.4, dashed=dashed, marker_end=marker)

        if label:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 - 6
            self.text(mx, my, label, font_size=9, fill="#94a3b8", font_family="monospace", anchor="middle")

    def pipeline_step(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        step_num: str,
        title: str,
        desc: str = "",
        color: str = "#38bdf8",
        fill: str = "#0f172a",
    ) -> None:
        """Render a clean horizontal pipeline card."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=color, stroke_width=1.2, filter_id="card-shadow")
        self.rect(x, y, w, 3, rx=1.5, fill=color, stroke="none")

        self.circle(x + 20, y + 24, 10, fill="#1e293b", stroke=color, stroke_width=1.2)
        self.text(x + 20, y + 27.5, step_num, font_size=9.5, fill=color, font_weight="bold", anchor="middle")

        self.text(x + 38, y + 27.5, title, font_size=12, fill="#f8fafc", font_weight="600")
        if desc:
            desc_lines = desc.split("\n")
            dy = y + 48
            for d in desc_lines:
                self.text(x + 14, dy, d, font_size=10, fill="#94a3b8", font_family="sans-serif")
                dy += 16

    def render(self) -> str:
        """Generate final clean SVG XML."""
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

  <!-- Top Header -->
  <text x="28" y="28" fill="#38bdf8" font-size="10" font-family="monospace" font-weight="bold" letter-spacing="0.1em">{html.escape(self.category.upper())}</text>
  <text x="28" y="48" fill="#f8fafc" font-size="13.5" font-family="sans-serif" font-weight="bold">{html.escape(self.title.upper())}</text>

  <!-- Elements -->
  {"".join(self.elements)}
</svg>
"""


def build_three_plane_architecture(title: str = "3-PLANE DECOUPLED GOVERNANCE ARCHITECTURE") -> CleanSVGCanvas:
    c = CleanSVGCanvas(860, 360, title, "INFRASTRUCTURE PLANE TOPOLOGY")

    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "Edge Plane (Cloudflare)", "#38bdf8")
    c.card(
        x1 + 12,
        94,
        col_w - 24,
        70,
        "Zero-Build Web UI",
        "• Vanilla HTML5 / ES Modules\n• Zero npm dependencies",
        "🌐",
        "#38bdf8",
    )
    c.card(
        x1 + 12,
        174,
        col_w - 24,
        70,
        "Interactive Docs",
        "• docs.credence.run\n• Fast client search index",
        "📘",
        "#60a5fa",
    )
    c.card(
        x1 + 12,
        254,
        col_w - 24,
        70,
        "Edge Router (_worker.js)",
        "• Multi-domain routing\n• Tiered CDN cache headers",
        "⚡",
        "#38bdf8",
    )

    c.container(x2, 68, col_w, 266, "Compute Plane (Cloud Run)", "#22c55e")
    c.card(
        x2 + 12,
        94,
        col_w - 24,
        70,
        "FastMCP 2.0 Engine",
        "• Stdio & SSE Transports\n• Automated tools & resources",
        "⚙️",
        "#22c55e",
    )
    c.card(
        x2 + 12,
        174,
        col_w - 24,
        70,
        "Starlette Core Server",
        "• Ingestion & Scrubber API\n• Rate limiting & Prometheus",
        "🚀",
        "#38bdf8",
    )
    c.card(
        x2 + 12,
        254,
        col_w - 24,
        70,
        "SQLite + Vector Store",
        "• Relational audit logs\n• Vector embeddings (WAL)",
        "💾",
        "#a855f7",
    )

    c.container(x3, 68, col_w, 266, "Infra Plane (Multi-Cloud)", "#a855f7")
    c.card(
        x3 + 12, 94, col_w - 24, 70, "Terraform HCL", "• GCP Cloud Run + WIF\n• Cloudflare DNS & Pages", "🏛️", "#a855f7"
    )
    c.card(
        x3 + 12,
        174,
        col_w - 24,
        70,
        "GitHub Actions CI/CD",
        "• Keyless WIF deploy\n• Automated dev staging",
        "🔄",
        "#60a5fa",
    )
    c.card(
        x3 + 12,
        254,
        col_w - 24,
        70,
        "Genesis Key Custody",
        "• RFC 8785 Canonical JSON\n• Ed25519 root authority",
        "🔐",
        "#22c55e",
    )

    c.arrow(x1 + col_w, 129, x2, 129, "API / SSE", "#38bdf8")
    c.arrow(x2 + col_w, 129, x3, 129, "WIF Auth", "#22c55e", marker="url(#arrow-emerald)")
    return c


def build_satire_and_entropy_defense(
    title: str = "TOPIC ENTROPY ASTROTURFING & SATIRE CLOAK DEFENSE",
) -> CleanSVGCanvas:
    c = CleanSVGCanvas(860, 360, title, "DEFENSIVE REASONING & POE'S LAW")

    w = 384
    c.container(28, 68, w, 266, "Satire Detection (Poe's Law)", "#38bdf8")
    c.card(
        42,
        94,
        w - 28,
        102,
        "Humor & Parody Surface",
        "• Satirical cues, irony, or farce detected\n• Score safely neutralized (0.00)\n• Zero false-positive misinformation flags",
        "🎭",
        "#38bdf8",
    )
    c.card(
        42,
        208,
        w - 28,
        114,
        "Invariant Guardrail",
        "• Protects legitimate comedy and satire from AI censorship\n• Avoids over-enforcement and algorithmic bias\n• Grounding exactness preserved character-for-character",
        "🛡️",
        "#60a5fa",
    )

    c.container(448, 68, w, 266, "Factual Allegation Override (SPJ-1.6)", "#ef4444")
    c.card(
        462,
        94,
        w - 28,
        102,
        "Factual Defamation / Claims",
        "• Specific named entities & financial allegations\n• Verified real-world harm potential\n• SPJ-1.6 mandatory override active",
        "⚖️",
        "#ef4444",
    )
    c.card(
        462,
        208,
        w - 28,
        114,
        "Shannon Entropy Defense (H < 0.30)",
        "• Low-entropy astroturfing campaigns detected\n• Forensic audit applied when satire cloaks real attacks\n• Cryptographic Ed25519 tamper-evident attestation",
        "🔬",
        "#f59e0b",
    )

    c.arrow(412, 145, 448, 145, "Override", "#ef4444", marker="url(#arrow-rose)")
    return c


def build_four_stage_pipeline(
    title: str,
    step1: tuple[str, str],
    step2: tuple[str, str],
    step3: tuple[str, str],
    step4: tuple[str, str],
    banner_title: str = "Security & Epistemic Invariant",
    banner_desc: str = "Zero-trust ingestion boundary • Epistemic verbatim grounding (G=1.00) • Deterministic verification",
    category: str = "PROCESSING PIPELINE",
) -> CleanSVGCanvas:
    c = CleanSVGCanvas(860, 360, title, category)

    s_w = 180
    s_h = 100
    gap = 28
    x_start = 28
    y_top = 70

    steps = [
        ("1", step1[0], step1[1], "#38bdf8", "url(#arrow-cyan)"),
        ("2", step2[0], step2[1], "#60a5fa", "url(#arrow-blue)"),
        ("3", step3[0], step3[1], "#a855f7", "url(#arrow-purple)"),
        ("4", step4[0], step4[1], "#22c55e", "url(#arrow-emerald)"),
    ]

    for idx, (num, s_title, s_desc, col, marker) in enumerate(steps):
        sx = x_start + idx * (s_w + gap)
        c.pipeline_step(sx, y_top, s_w, s_h, num, s_title, s_desc, col)
        if idx < 3:
            next_sx = x_start + (idx + 1) * (s_w + gap)
            c.arrow(sx + s_w, y_top + s_h / 2, next_sx, y_top + s_h / 2, "", col, marker=marker)

    c.card(28, 188, 804, 146, banner_title, banner_desc, "🛡️", "#22c55e")
    return c


def build_mesh_cluster(title: str = "13-NODE WATTS-STROGATZ PEER-TO-PEER MESH TOPOLOGY") -> CleanSVGCanvas:
    c = CleanSVGCanvas(860, 360, title, "CONSENSUS & BYZANTINE DEFENSE")

    w = 384
    c.container(28, 68, w, 266, "High-Merit Peer Ring (M_i >= 0.70)", "#22c55e")
    c.card(42, 94, 164, 66, "Node 0 (Genesis)", "• M=0.98 | Root Seed\n• Sovereign Authority", "🛡️", "#22c55e")
    c.card(234, 94, 164, 66, "Node 1 (Relay)", "• M=0.92 | Active\n• Feed Rendezvous", "⚡", "#38bdf8")
    c.card(42, 172, 164, 66, "Node 2 (Auditor)", "• M=0.88 | Active\n• Heuristic Verifier", "🔬", "#60a5fa")
    c.card(234, 172, 164, 66, "Node 3 (Sifter)", "• M=0.85 | Active\n• Boredom Sifter", "🔍", "#38bdf8")
    c.card(138, 250, 164, 66, "Node 4 (Digest)", "• M=0.82 | Active\n• Briefing Generator", "📰", "#a855f7")

    c.line(206, 127, 234, 127, "#22c55e", 1.2, marker_end=None)
    c.line(206, 205, 234, 205, "#22c55e", 1.2, marker_end=None)
    c.line(124, 160, 124, 172, "#22c55e", 1.2, marker_end=None)
    c.line(316, 160, 316, 172, "#22c55e", 1.2, marker_end=None)

    c.container(448, 68, w, 266, "Byzantine Sybil Cartel Defense", "#ef4444")
    c.card(462, 94, 164, 66, "Quarantine Node 9", "• Suspicion: 88.4%\n• Cartel Isolated", "🛑", "#ef4444")
    c.card(654, 94, 164, 66, "Quarantine Node 10", "• Suspicion: 92.1%\n• Score Slash 50%", "🛑", "#ef4444")
    c.card(
        462,
        172,
        356,
        144,
        "Consensus Quarantine Isolation",
        "• Watts-Strogatz HRW hashing routes feeds\n• Nodes with S_j > 70.0% isolated autonomously\n• Cartels cannot skew consensus medians\n• Byzantine tolerance: f = floor((N-1)/3)",
        "⚖️",
        "#f59e0b",
    )

    c.arrow(412, 127, 448, 127, "Gossip", "#60a5fa", marker="url(#arrow-blue)")
    return c


def build_information_pyramid(title: str = "THE EPISTEMIC LENSING & INFORMATION PYRAMID") -> CleanSVGCanvas:
    c = CleanSVGCanvas(860, 360, title, "EPISTEMIC LENSING")

    c.card(
        250,
        70,
        360,
        70,
        "1. Surface Lens (Glance)",
        "• Overall Credence score gauge (0-100)\n• Quick verified / suspicious badge",
        "⚡",
        "#22c55e",
    )
    c.card(
        150,
        156,
        560,
        74,
        "2. Focus Lens (Explore)",
        "• Deconstructed claims & deceptive pattern tags\n• Verbatim DOM citations (G=1.00) & sparklines",
        "🔍",
        "#38bdf8",
    )
    c.card(
        50,
        246,
        760,
        84,
        "3. Deep Spectrum Lens (Forensic Audit)",
        "• Cryptographic Ed25519 signatures & RFC 8785 canonical envelopes\n• Raw DOM SHA-256 hash & full temporal diff timeline",
        "🔬",
        "#a855f7",
    )

    c.arrow(430, 140, 430, 156, "", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(430, 230, 430, 246, "", "#a855f7", marker="url(#arrow-purple)")
    return c


def build_demotion_highway(title: str = "THE DEMOTION HIGHWAY & KNOWLEDGE SCALABILITY MATRIX") -> CleanSVGCanvas:
    c = CleanSVGCanvas(860, 360, title, "KNOWLEDGE GOVERNANCE")

    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "Tier 0: Universal Invariants", "#ef4444")
    c.card(
        x1 + 12,
        94,
        col_w - 24,
        76,
        "P0 Sovereign Safety",
        "• Always-on LLM prompt context\n• <800 tokens hard ceiling\n• Zero speculative code",
        "🧠",
        "#ef4444",
    )
    c.card(
        x1 + 12,
        180,
        col_w - 24,
        136,
        "Cognitive Canon",
        "• Class α: Safety & Authority\n• Class β: Lifecycle Topology\n• Class γ: Interface Symmetry\n• Strict Mk1 Human Gate",
        "⚖️",
        "#f59e0b",
    )

    c.container(x2, 68, col_w, 266, "Tier 1: Progressive Skills", "#38bdf8")
    c.card(
        x2 + 12,
        94,
        col_w - 24,
        76,
        "Subsystem Skills",
        "• Loaded dynamically on demand\n• .agents/skills/*\n• Context economy preserved",
        "☁️",
        "#38bdf8",
    )
    c.card(
        x2 + 12,
        180,
        col_w - 24,
        136,
        "Specialized Domains",
        "• cloudrun-ops\n• mesh-cluster\n• white-label-ops\n• architecture-governance\n• epistemic-benchmark",
        "🏛️",
        "#60a5fa",
    )

    c.container(x3, 68, col_w, 266, "Tier 2: Shift-Left Tests", "#22c55e")
    c.card(
        x3 + 12,
        94,
        col_w - 24,
        76,
        "Deterministic Tests",
        "• Shift-left automated QA\n• <0.3s local execution\n• Immediate feedback loop",
        "⚡",
        "#22c55e",
    )
    c.card(
        x3 + 12,
        180,
        col_w - 24,
        136,
        "Mechanical Invariants",
        "• Zero-npm invariant\n• 7-Manifest parity sync\n• Code fence validation\n• Sitemap route coverage\n• Tiered edge caching",
        "🛡️",
        "#22c55e",
    )

    c.arrow(x1 + col_w, 132, x2, 132, "Graduate", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(x2 + col_w, 132, x3, 132, "Demote", "#22c55e", marker="url(#arrow-emerald)")
    return c


def build_generic_clean_illustration(slug: str, title: str, category: str = "ARCHITECTURE") -> CleanSVGCanvas:
    clean_title = title.replace("#", "").strip()[:65]
    c = CleanSVGCanvas(860, 360, clean_title, category)

    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "Ingestion & Security", "#38bdf8")
    c.card(
        x1 + 12,
        94,
        col_w - 24,
        104,
        "Network Boundary",
        "• Target URLs, text & feeds\n• SSRF & metadata IP filter\n• XML entity injection defense\n• Private subnets blocked",
        "📥",
        "#38bdf8",
    )
    c.card(
        x1 + 12,
        210,
        col_w - 24,
        106,
        "DOM Extractor",
        "• Strips scripts & styling\n• Sanitizes HTML elements\n• Isolates untrusted text\n• Verbatim ground G=1.00",
        "🧹",
        "#60a5fa",
    )

    c.container(x2, 68, col_w, 266, "Epistemic Evaluation", "#22c55e")
    c.card(
        x2 + 12,
        94,
        col_w - 24,
        104,
        "Multi-Model Consensus",
        "• Heuristic rules & claim check\n• Circuit breaker headroom\n• Verbatim citation matching\n• Multi-model Pareto scoring",
        "🧠",
        "#22c55e",
    )
    c.card(
        x2 + 12,
        210,
        col_w - 24,
        106,
        "Entropy Defense",
        "• Shannon entropy astroturf def\n• Expertise-weighted medians\n• Galileo minority rule override\n• Poe's law satire balance",
        "⚖️",
        "#f59e0b",
    )

    c.container(x3, 68, col_w, 266, "Attestation & Storage", "#a855f7")
    c.card(
        x3 + 12,
        94,
        col_w - 24,
        104,
        "RFC 8785 Canonical JSON",
        "• Deterministic serialization\n• UTF-8 sorted key envelope\n• Tamper-evident byte stream\n• UTC ISO-8601 timestamps",
        "📜",
        "#a855f7",
    )
    c.card(
        x3 + 12,
        210,
        col_w - 24,
        106,
        "Ed25519 Signature",
        "• Genesis root authority sign\n• SQLite + vector persistence\n• Zero-trust verification\n• Sovereign key custody",
        "🔐",
        "#22c55e",
    )

    c.arrow(x1 + col_w, 146, x2, 146, "Sanitized", "#38bdf8", marker="url(#arrow-cyan)")
    c.arrow(x2 + col_w, 146, x3, 146, "Attest", "#22c55e", marker="url(#arrow-emerald)")
    return c


def get_clean_illustration(slug: str, title: str, category_path: str) -> CleanSVGCanvas:
    s = slug.lower()
    cat = category_path.split("/")[0].upper() if category_path and category_path != "." else "ECOSYSTEM"

    if any(k in s for k in ["pun-terest", "satire", "poe", "astroturf", "pizza-hut", "conflict"]):
        return build_satire_and_entropy_defense(title)

    if any(k in s for k in ["three-plane", "architecture", "cloudrun", "deployment", "single-vs-dual"]):
        return build_three_plane_architecture(title)

    if any(k in s for k in ["demotion", "knowledge", "governance", "invariants", "500-loc", "anti-diploma"]):
        return build_demotion_highway(title)

    if any(k in s for k in ["mesh", "watts-strogatz", "rendezvous", "sybil", "airgapped", "swarm"]):
        return build_mesh_cluster(title)

    if any(k in s for k in ["pyramid", "lensing", "spectrum", "galileo"]):
        return build_information_pyramid(title)

    if any(k in s for k in ["ssrf", "scrubber", "security", "threat-model", "grounding", "canonical", "ed25519"]):
        return build_four_stage_pipeline(
            title,
            ("Raw Input", "Target URL / untrusted payload"),
            ("SSRF Guard", "Block private IPs & 169.254"),
            ("DOM Scrubber", "Strip scripts & entities"),
            ("Attestation", "RFC 8785 Ed25519 sign"),
            banner_title="Epistemic Security & Untrusted Ingestion Boundary",
            banner_desc="Citations match source text character-for-character (G=1.00). Cloud metadata and private IPs blocked autonomously.",
            category=cat,
        )

    return build_generic_clean_illustration(slug, title, category=cat)


def regenerate_all_illustrations(docs_dir: Path, output_dirs: List[Path]) -> tuple[int, int]:
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
            canvas = get_clean_illustration(slug, title, rel_cat)
            svg_content = canvas.render()
            for out_dir in output_dirs:
                (out_dir / f"{slug}.svg").write_text(svg_content, encoding="utf-8")
            total_svgs += 1
            continue

        for alt_title, svg_filename in matches:
            svg_slug = svg_filename.replace(".svg", "")
            use_title = alt_title.strip() if alt_title.strip() else title
            canvas = get_clean_illustration(svg_slug, use_title, rel_cat)
            svg_content = canvas.render()

            for out_dir in output_dirs:
                (out_dir / svg_filename).write_text(svg_content, encoding="utf-8")
            total_svgs += 1

        total_files += 1

    print(f"✅ Clean SVG generation complete: {total_svgs} SVG illustrations generated across {total_files} files.")
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
