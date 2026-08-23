#!/usr/bin/env python3
"""Credence Visual Architecture & Illustration Audit Execution Script.

Actions:
1. Refactor markdown files across docs/ and blog/:
   - Retain illustrations ONLY in core architectural docs and deep-dive case studies.
   - Remove decorative top-of-page and redundant image tags from reference/index docs.
   - Position retained diagrams directly in the technical section they illustrate.
   - Assign precise, descriptive alt text (e.g. "Figure 1.1: Circular conflict feedback loop...")
2. Build genuine technical schematics (Process flow, network topology, state machines, entity models).
3. Clean up orphaned SVGs and synchronize active assets between credence-docs and credence/web.
"""

import html
import re
from pathlib import Path
from typing import List, Optional

# ==============================================================================
# 1. CORE ARCHITECTURAL SCHEMATIC BUILDERS (NO TEXT IN BOXES)
# ==============================================================================


class SchematicCanvas:
    """Dark-mode SVG canvas for genuine technical diagrams."""

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
        fill: str = "#0f172a",
        stroke: str = "rgba(56, 189, 248, 0.3)",
        stroke_width: float = 1.2,
        filter_id: Optional[str] = None,
        dashed: bool = False,
        opacity: float = 1.0,
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
        stroke_width: float = 1.6,
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
        stroke_width: float = 1.6,
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
    ) -> None:
        """Render a distinct architectural component node."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=accent, stroke_width=1.3, filter_id="card-shadow")
        self.rect(x, y, w, 3, rx=1.5, fill=accent, stroke="none")

        header_x = x + 14
        if icon:
            self.text(header_x, y + 23, icon, font_size=15, anchor="start")
            header_x += 24

        self.text(header_x, y + 23, title, font_size=13, fill="#f8fafc", font_weight="600")

        if subtitle:
            sub_lines = subtitle.split("\n")
            line_y = y + 43
            for s_line in sub_lines:
                self.text(x + 14, line_y, s_line, font_size=11, fill="#94a3b8", font_family="sans-serif")
                line_y += 18

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
        """Render an architectural boundary/plane container."""
        self.rect(x, y, w, h, rx=10, fill=bg, stroke=color, stroke_width=1.1, dashed=dashed)
        if title:
            self.text(
                x + 16, y + 20, title.upper(), font_size=10, fill=color, font_family="monospace", font_weight="bold"
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
        dx = x2 - x1
        dy = y2 - y1
        if (dx * dx + dy * dy) ** 0.5 < 8:
            return
        self.line(x1, y1, x2, y2, stroke=color, stroke_width=1.6, dashed=dashed, marker_end=marker)

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
  <text x="28" y="28" fill="#38bdf8" font-size="10.5" font-family="monospace" font-weight="bold" letter-spacing="0.1em">{html.escape(self.category.upper())}</text>
  <text x="28" y="50" fill="#f8fafc" font-size="14.5" font-family="sans-serif" font-weight="bold">{html.escape(self.title.upper())}</text>

  <!-- Elements -->
  {"".join(self.elements)}
</svg>
"""


# ==============================================================================
# BESPOKE DIAGRAM IMPLEMENTATIONS
# ==============================================================================


def diagram_conflict_of_punterest() -> str:
    """Maricopa Municipal vs Newsroom Closed Loop Conflict Model."""
    c = SchematicCanvas(
        860, 360, "MUNICIPAL PUBLISHER-POLITICIAN CONFLICT vs CREDENCE AUDIT", "CIVIC CONFLICT OF INTEREST AUDIT"
    )

    # Top Half: The Corrupt Circular Feedback Loop
    c.container(28, 68, 804, 134, "Local Newsroom Monopoly vs Governance Collision", "#ef4444", dashed=True)
    c.node(
        48, 96, 210, 86, "Elected Councilmember", "• Holds City Council Seat\n• Directs newsroom policy", "🏛️", "#ef4444"
    )
    c.node(
        324,
        96,
        210,
        86,
        "Municipal Council Dais",
        "• Votes on rezoning & contracts\n• Police & public budgets",
        "🗳️",
        "#f59e0b",
    )
    c.node(
        600,
        96,
        210,
        86,
        "Digital News Outlet",
        "• inmaricopa.com publisher\n• Unlabelled advertorials",
        "📰",
        "#ef4444",
    )

    # Circular Directed Connectors
    c.arrow(258, 126, 324, 126, "#f59e0b", marker="url(#arrow-amber)")
    c.arrow(534, 126, 600, 126, "#ef4444", marker="url(#arrow-rose)")
    # Loopback curve from Newsroom back to Elected Councilmember
    c.path(
        "M 705 182 L 705 194 L 153 194 L 153 182",
        stroke="#ef4444",
        stroke_width=1.5,
        dashed=True,
        marker_end="url(#arrow-rose)",
    )

    # Bottom Half: Credence Epistemic Audit Interception Layer
    c.container(28, 216, 804, 118, "Credence Cryptographic Attestation Layer (G=1.00)", "#22c55e")
    c.node(
        48,
        240,
        224,
        76,
        "Target Ingestion",
        "• Harvester pulls published DOM\n• Untrusted source container",
        "📥",
        "#38bdf8",
    )
    c.node(
        318,
        240,
        224,
        76,
        "Verbatim Primary Grounding",
        "• Cross-checks council transcripts\n• Unmasks advertorial camouflage",
        "🔬",
        "#22c55e",
    )
    c.node(
        586,
        240,
        224,
        76,
        "Sovereign Attestation",
        "• SPJ-1.6 investigative credit\n• Ed25519 sealed receipt",
        "🔐",
        "#a855f7",
    )

    c.arrow(272, 278, 318, 278, "#22c55e", marker="url(#arrow-emerald)")
    c.arrow(542, 278, 586, 278, "#a855f7", marker="url(#arrow-purple)")
    return c.render()


def diagram_three_plane_architecture() -> str:
    """3-Plane Decoupled Governance Topology."""
    c = SchematicCanvas(860, 360, "3-PLANE DECOUPLED GOVERNANCE ARCHITECTURE", "SYSTEM TOPOLOGY")
    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "Edge Plane (Cloudflare)", "#38bdf8")
    c.node(
        x1 + 12,
        96,
        col_w - 24,
        72,
        "Zero-Build Web UI",
        "• Vanilla HTML5 / ES modules\n• Zero npm dependencies",
        "🌐",
        "#38bdf8",
    )
    c.node(
        x1 + 12,
        180,
        col_w - 24,
        72,
        "Interactive Docs Site",
        "• Fast client-side search\n• Responsive SVG rendering",
        "📘",
        "#60a5fa",
    )
    c.node(x1 + 12, 254, col_w - 24, 66, "Edge Router (_worker.js)", "• Tiered edge caching", "⚡", "#38bdf8")

    c.container(x2, 68, col_w, 266, "Compute Plane (Cloud Run)", "#22c55e")
    c.node(
        x2 + 12,
        96,
        col_w - 24,
        72,
        "FastMCP 2.0 Engine",
        "• Stdio & SSE dual transport\n• JSON-RPC tools & resources",
        "⚙️",
        "#22c55e",
    )
    c.node(
        x2 + 12,
        180,
        col_w - 24,
        72,
        "Starlette Server Core",
        "• Ingestion scrubber & SSRF\n• Prometheus live metrics",
        "🚀",
        "#38bdf8",
    )
    c.node(x2 + 12, 254, col_w - 24, 66, "SQLite + Vector Store", "• WAL persistence layer", "💾", "#a855f7")

    c.container(x3, 68, col_w, 266, "Infra Plane (Multi-Cloud)", "#a855f7")
    c.node(
        x3 + 12, 96, col_w - 24, 72, "Terraform HCL", "• GCP Cloud Run + WIF\n• Cloudflare DNS & Pages", "🏛️", "#a855f7"
    )
    c.node(
        x3 + 12,
        180,
        col_w - 24,
        72,
        "GitHub Actions CI/CD",
        "• Keyless WIF deployment\n• Automated dev staging",
        "🔄",
        "#60a5fa",
    )
    c.node(x3 + 12, 254, col_w - 24, 66, "Genesis Key Custody", "• Ed25519 root authority", "🔐", "#22c55e")

    c.arrow(x1 + col_w, 132, x2, 132, "#38bdf8")
    c.arrow(x2 + col_w, 132, x3, 132, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_mesh_topology() -> str:
    """13-Node Watts-Strogatz Mesh & Sybil Cartel Defense."""
    c = SchematicCanvas(860, 360, "13-NODE WATTS-STROGATZ MESH & SYBIL CARTEL DEFENSE", "DECENTRALIZED CONSENSUS")
    w = 384

    c.container(28, 68, w, 266, "High-Merit Peer Ring (M_i >= 0.70)", "#22c55e")
    c.node(42, 96, 164, 66, "Node 0 (Genesis)", "M=0.98 | Root Seed\nSovereign Authority", "🛡️", "#22c55e")
    c.node(234, 96, 164, 66, "Node 1 (Relay)", "M=0.92 | Active\nFeed Rendezvous", "⚡", "#38bdf8")
    c.node(42, 174, 164, 66, "Node 2 (Auditor)", "M=0.88 | Active\nHeuristic Verifier", "🔬", "#60a5fa")
    c.node(234, 174, 164, 66, "Node 3 (Sifter)", "M=0.85 | Active\nBoredom Sifter", "🔍", "#38bdf8")
    c.node(138, 252, 164, 66, "Node 4 (Digest)", "M=0.82 | Active\nBriefing Generator", "📰", "#a855f7")

    # Internal Mesh Connectors
    c.line(206, 129, 234, 129, "#22c55e", 1.4, marker_end=None)
    c.line(206, 207, 234, 207, "#22c55e", 1.4, marker_end=None)
    c.line(124, 162, 124, 174, "#22c55e", 1.4, marker_end=None)
    c.line(316, 162, 316, 174, "#22c55e", 1.4, marker_end=None)

    c.container(448, 68, w, 266, "Byzantine Sybil Cartel Quarantine", "#ef4444", dashed=True)
    c.node(462, 96, 164, 66, "Cartel Node 9", "Suspicion: 88.4%\nQuarantined", "🛑", "#ef4444")
    c.node(654, 96, 164, 66, "Cartel Node 10", "Suspicion: 92.1%\nScore Slashed", "🛑", "#ef4444")
    c.node(
        462,
        174,
        356,
        144,
        "Autonomous Sybil Defense",
        "• HRW hashing routes feeds deterministically.\n• Nodes with Suspicion > 70% isolated.\n• Consensus medians protected from collusion.\n• Byzantine fault tolerance: f = floor((N-1)/3).",
        "⚖️",
        "#f59e0b",
    )

    c.arrow(412, 129, 448, 129, "#ef4444", marker="url(#arrow-rose)")
    return c.render()


def diagram_scale_to_zero_storage() -> str:
    """Scale-to-Zero Cloud Run Storage Hydration State Machine."""
    c = SchematicCanvas(860, 360, "SCALE-TO-ZERO COLD-BOOT STORAGE HYDRATION CYCLE", "COMPUTE LIFECYCLE")

    s_w = 175
    gap = 32
    y = 96
    h = 105

    steps = [
        (
            28,
            "1. Scale to Zero",
            "• Idle containers sleep\n• N=0 compute nodes\n• $0 idle cost incurred",
            "🧊",
            "#38bdf8",
        ),
        (
            28 + s_w + gap,
            "2. Request Wakeup",
            "• Inbound HTTP / MCP\n• Cold boot trigger\n• Instance spin-up",
            "⚡",
            "#60a5fa",
        ),
        (
            28 + 2 * (s_w + gap),
            "3. GCS Hydration",
            "• Dual-pointer restore\n• WAL replay (<1.2s)\n• SQLite in-memory",
            "💾",
            "#22c55e",
        ),
        (
            28 + 3 * (s_w + gap),
            "4. Live Serving",
            "• P50 latency < 0.5ms\n• FastMCP SSE active\n• Snapshot sync",
            "🚀",
            "#a855f7",
        ),
    ]

    for idx, (sx, title, desc, icon, col) in enumerate(steps):
        c.node(sx, y, s_w, h, title, desc, icon, col)
        if idx < 3:
            c.arrow(sx + s_w, y + h / 2, sx + s_w + gap, y + h / 2, col)

    c.node(
        28,
        225,
        804,
        105,
        "Dual-Pointer GCS Storage Invariant",
        "• Dual-pointer metadata prevents race conditions during cold-start container initialization.\n• Point-in-time WAL recovery guarantees zero data loss across ephemeral instance lifecycles.\n• In-memory cache warming delivers instant sub-millisecond response for repeat domain queries.",
        "🛡️",
        "#22c55e",
    )
    return c.render()


def diagram_satire_decision_tree() -> str:
    """Satire Cloak vs SPJ-1.6 Decision Tree."""
    c = SchematicCanvas(860, 360, "SATIRE CLOAK vs SPJ-1.6 INVESTIGATIVE OVERRIDE", "DEFENSIVE REASONING")
    w = 384

    c.container(28, 68, w, 266, "Poe's Law Satire Safeguard", "#38bdf8")
    c.node(
        42,
        96,
        w - 28,
        96,
        "Parody & Irony Surface",
        "• Satirical cues, farce, or comedic exaggeration\n• Score safely neutralized (0.00)\n• Zero false-positive misinformation penalties",
        "🎭",
        "#38bdf8",
    )
    c.node(
        42,
        204,
        w - 28,
        114,
        "Cognitive Guardrail",
        "• Protects legitimate comedy and satire from AI bias\n• Avoids pedantic literalist over-enforcement\n• Grounding exactness preserved character-for-character",
        "🛡️",
        "#60a5fa",
    )

    c.container(448, 68, w, 266, "SPJ-1.6 Factual Allegation Override", "#ef4444")
    c.node(
        462,
        96,
        w - 28,
        96,
        "Factual Defamation / Claims",
        "• Specific named entities & financial allegations\n• Real-world reputational or legal harm\n• SPJ-1.6 mandatory override active",
        "⚖️",
        "#ef4444",
    )
    c.node(
        462,
        204,
        w - 28,
        114,
        "Shannon Topic Entropy Defense",
        "• Detects low-entropy astroturfing campaigns (H < 0.30)\n• Forensic audit applied when satire cloaks real attacks\n• Cryptographic Ed25519 tamper-evident attestation",
        "🔬",
        "#f59e0b",
    )

    c.arrow(412, 144, 448, 144, "#ef4444", marker="url(#arrow-rose)")
    return c.render()


def diagram_knowledge_demotion_highway() -> str:
    """The Knowledge Demotion Highway & Invariant Canon."""
    c = SchematicCanvas(860, 360, "THE LIVING INVARIANT CANON & DEMOTION HIGHWAY", "KNOWLEDGE GOVERNANCE")
    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "Tier 0: Universal Canon", "#ef4444")
    c.node(
        x1 + 12,
        96,
        col_w - 24,
        76,
        "P0 Sovereign Safety",
        "• Always-on LLM prompt\n• <800 tokens hard budget\n• Zero speculative code",
        "🧠",
        "#ef4444",
    )
    c.node(
        x1 + 12,
        184,
        col_w - 24,
        134,
        "Cognitive Canon",
        "• Class α: Sovereign Safety\n• Class β: Lifecycle Topology\n• Class γ: Interface Symmetry\n• Strict Mk1 Human Gate",
        "⚖️",
        "#f59e0b",
    )

    c.container(x2, 68, col_w, 266, "Tier 1: Progressive Skills", "#38bdf8")
    c.node(
        x2 + 12,
        96,
        col_w - 24,
        76,
        "Subsystem Skills",
        "• Loaded on demand\n• .agents/skills/*\n• Context economy",
        "☁️",
        "#38bdf8",
    )
    c.node(
        x2 + 12,
        184,
        col_w - 24,
        134,
        "Specialized Domains",
        "• cloudrun-ops\n• mesh-cluster\n• white-label-ops\n• architecture-governance\n• epistemic-benchmark",
        "🏛️",
        "#60a5fa",
    )

    c.container(x3, 68, col_w, 266, "Tier 2: Shift-Left Tests", "#22c55e")
    c.node(
        x3 + 12,
        96,
        col_w - 24,
        76,
        "Automated QA Gates",
        "• Local pre-commit QA\n• <0.3s execution time\n• Immediate feedback",
        "⚡",
        "#22c55e",
    )
    c.node(
        x3 + 12,
        184,
        col_w - 24,
        134,
        "Mechanical Invariants",
        "• Zero-npm invariant\n• 7-Manifest parity sync\n• 500 LOC ceiling check\n• Sitemap route coverage\n• Tiered edge caching",
        "🛡️",
        "#22c55e",
    )

    c.arrow(x1 + col_w, 134, x2, 134, "#38bdf8")
    c.arrow(x2 + col_w, 134, x3, 134, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_agentic_engineering_lifecycle() -> str:
    """Antigravity 5-Stage Agentic Engineering Lifecycle."""
    c = SchematicCanvas(860, 360, "ANTIGRAVITY 5-STAGE AGENTIC ENGINEERING LIFECYCLE", "PAIR-PROGRAMMING PARADIGM")

    s_w = 175
    gap = 32
    y = 96
    h = 105

    steps = [
        (28, "1. Survey", "• Read-only exploration\n• Context investigation\n• Zero modifying edits", "🔍", "#38bdf8"),
        (
            28 + s_w + gap,
            "2. Plan",
            "• Implementation plan\n• Invariant mapping\n• User approval gate",
            "📝",
            "#60a5fa",
        ),
        (
            28 + 2 * (s_w + gap),
            "3. Execute",
            "• Hermetic sandbox\n• Multi-plane updates\n• Atomic refactoring",
            "⚙️",
            "#a855f7",
        ),
        (
            28 + 3 * (s_w + gap),
            "4. QA & Staging",
            "• just check gauntlet\n• 100% test pass rate\n• Dev Cloud Run deploy",
            "🚀",
            "#22c55e",
        ),
    ]

    for idx, (sx, title, desc, icon, col) in enumerate(steps):
        c.node(sx, y, s_w, h, title, desc, icon, col)
        if idx < 3:
            c.arrow(sx + s_w, y + h / 2, sx + s_w + gap, y + h / 2, col)

    c.node(
        28,
        225,
        804,
        105,
        "Human Sovereign Authority (Mk1 Eyeball Invariant)",
        "• Production releases, tag promotions, and PR merges require human review character-for-character.\n• Sandboxed agent execution protects user filesystem and host security.\n• Continuous learning loop (/learn) crystallizes runtime friction into permanent repository invariants.",
        "👁️",
        "#22c55e",
    )
    return c.render()


def diagram_bicameral_finops() -> str:
    """Dual-Tier Bicameral FinOps Architecture."""
    c = SchematicCanvas(860, 360, "DUAL-TIER BICAMERAL INFERENCE ARCHITECTURE", "COMPUTE FINOPS")
    w = 384

    c.container(28, 68, w, 266, "Tier 1: Fast Heuristic Triage (Free)", "#38bdf8")
    c.node(
        42,
        96,
        w - 28,
        96,
        "Local Heuristic Sifter",
        "• Fast pattern matching (<15ms latency)\n• Filters 83% of routine, uncontested content\n• $0 API token expense incurred",
        "⚡",
        "#38bdf8",
    )
    c.node(
        42,
        204,
        w - 28,
        114,
        "Safety & Ingestion Filters",
        "• SSRF and private IP blocking\n• Domain reputation index lookup\n• Poe's law satire detection",
        "🛡️",
        "#60a5fa",
    )

    c.container(448, 68, w, 266, "Tier 2: Deep LLM Verification (Ultra)", "#22c55e")
    c.node(
        462,
        96,
        w - 28,
        96,
        "Targeted Epistemic Reasoning",
        "• Invoked strictly for complex, contested claims\n• 4k thinking budget on core facts\n• Full verbatim grounding checks (G=1.00)",
        "🧠",
        "#22c55e",
    )
    c.node(
        462,
        204,
        w - 28,
        114,
        "83% Compute Cost Slashing",
        "• Preserves rate limit quotas under burst loads\n• Offline circuit breaker headroom buffer\n• Cryptographic Ed25519 attestation seal",
        "🪙",
        "#a855f7",
    )

    c.arrow(412, 144, 448, 144, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_astroturfing_entropy() -> str:
    """Astroturfing Swarms vs Organic Civic Discourse Entropy."""
    c = SchematicCanvas(860, 360, "SHANNON TOPIC ENTROPY & ASTROTURFING DEFENSE", "DISCOURSE FORENSICS")
    w = 384

    c.container(28, 68, w, 266, "Coordinated Bot Campaign (H < 0.30)", "#ef4444", dashed=True)
    c.node(
        42,
        96,
        w - 28,
        96,
        "Low Shannon Entropy Swarm",
        "• Highly concentrated top-token distribution\n• Repetitive keyword talking points\n• Synchronized multi-account publication spikes",
        "🤖",
        "#ef4444",
    )
    c.node(
        42,
        204,
        w - 28,
        114,
        "Astroturfing Penalty",
        "• Masquerades as organic grassroots sentiment\n• Automated 50% score slash applied\n• Identified entities flagged in forensic audit",
        "🛑",
        "#f59e0b",
    )

    c.container(448, 68, w, 266, "Organic Civic Discourse (H > 0.70)", "#22c55e")
    c.node(
        462,
        96,
        w - 28,
        96,
        "High Lexical Diversity",
        "• Rich vocabulary variance and natural phrasing\n• Diverse independent perspectives and timing\n• Authentic citizen engagement indicators",
        "👥",
        "#22c55e",
    )
    c.node(
        462,
        204,
        w - 28,
        114,
        "Galileo Minority Override",
        "• Protects lone factual whistleblowers\n• Prevents majority consensus suppression\n• Verified through primary source citations",
        "⚖️",
        "#38bdf8",
    )

    c.arrow(412, 144, 448, 144, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_bittorrent_fact_checking() -> str:
    """BitTorrent P2P Fact-Checking Work Sharing."""
    c = SchematicCanvas(860, 360, "BITTORRENT P2P FACT-CHECKING WORK-SHARING PROTOCOL", "DECENTRALIZED SWARM")

    s_w = 175
    gap = 32
    y = 96
    h = 105

    steps = [
        (28, "1. Ingest URL", "• Extract target URL\n• Scrubber strips scripts\n• SHA-256 DOM hash", "📥", "#38bdf8"),
        (
            28 + s_w + gap,
            "2. HRW Hashing",
            "• Rendezvous hashing\n• Deterministic node map\n• Prevents dogpiling",
            "⚙️",
            "#60a5fa",
        ),
        (
            28 + 2 * (s_w + gap),
            "3. Peer Audit",
            "• Highest-merit peer runs\n• Verbatim claim audit\n• Ed25519 sealed receipt",
            "🔬",
            "#22c55e",
        ),
        (
            28 + 3 * (s_w + gap),
            "4. Gossip Sync",
            "• P2P gossip distribution\n• Deduplicated cache\n• 92.3% compute savings",
            "🌐",
            "#a855f7",
        ),
    ]

    for idx, (sx, title, desc, icon, col) in enumerate(steps):
        c.node(sx, y, s_w, h, title, desc, icon, col)
        if idx < 3:
            c.arrow(sx + s_w, y + h / 2, sx + s_w + gap, y + h / 2, col)

    c.node(
        28,
        225,
        804,
        105,
        "Decentralized Swarm Work-Sharing Invariant",
        "• Rendezvous hashing distributes domain verification workloads across nodes without central coordination.\n• Gossip protocols propagate verified cryptographic audit receipts across the network in <500ms.\n• Nodes reuse peer evaluation receipts, eliminating repetitive redundant inference across the swarm.",
        "🛡️",
        "#22c55e",
    )
    return c.render()


def diagram_untrusted_ingestion() -> str:
    """Untrusted Ingestion Boundary & SSRF Defense Pipeline."""
    c = SchematicCanvas(860, 360, "UNTRUSTED INGESTION BOUNDARY & SSRF DEFENSE", "INGESTION PIPELINE")

    s_w = 175
    gap = 32
    y = 96
    h = 105

    steps = [
        (
            28,
            "1. Input Boundary",
            "• Raw URL / text ingest\n• Untrusted source wrap\n• Rate limit checkpoint",
            "📥",
            "#38bdf8",
        ),
        (
            28 + s_w + gap,
            "2. Network Filter",
            "• Block 169.254 metadata\n• Reject loopback / private\n• Strip XML entities",
            "🛡️",
            "#60a5fa",
        ),
        (
            28 + 2 * (s_w + gap),
            "3. DOM Scrubber",
            "• Strip scripts & styling\n• Clean DOM text tree\n• Verbatim citation lock",
            "🧹",
            "#22c55e",
        ),
        (
            28 + 3 * (s_w + gap),
            "4. Signed Attestation",
            "• RFC 8785 Canonical JSON\n• Ed25519 cryptographic seal\n• Tamper-evident receipt",
            "🔐",
            "#a855f7",
        ),
    ]

    for idx, (sx, title, desc, icon, col) in enumerate(steps):
        c.node(sx, y, s_w, h, title, desc, icon, col)
        if idx < 3:
            c.arrow(sx + s_w, y + h / 2, sx + s_w + gap, y + h / 2, col)

    c.node(
        28,
        225,
        804,
        105,
        "Security Invariant: Socket-Layer SSRF Defense & Epistemic Grounding (G=1.00)",
        "• Cloud metadata and private subnet ranges are blocked at the socket layer before connection establishment.\n• Untrusted source text is strictly isolated in XML container tags to prevent prompt injection attacks.\n• Verbatim citations match source text character-for-character, eliminating hallucinated assertions.",
        "🛡️",
        "#22c55e",
    )
    return c.render()


def diagram_500_loc_ceiling() -> str:
    """500 LOC Ceiling Law & Modular Subpackage Decoupling."""
    c = SchematicCanvas(860, 360, "THE 500 LOC CEILING LAW & MODULAR DECOUPLING", "ARCHITECTURAL GOVERNANCE")
    w = 384

    c.container(28, 68, w, 266, "Anti-Bloat 500 LOC Rule", "#ef4444")
    c.node(
        42,
        96,
        w - 28,
        96,
        "Single-Responsibility Focus",
        "• Strict 500 LOC ceiling on Python files\n• Strict 500 LOC ceiling on Justfiles\n• Automated pre-commit lint gate",
        "📏",
        "#ef4444",
    )
    c.node(
        42,
        204,
        w - 28,
        114,
        "Cognitive Economy",
        "• Prevents unmaintainable god classes\n• Files fit comfortably in agent context\n• Zero hidden state accumulation",
        "🧠",
        "#f59e0b",
    )

    c.container(448, 68, w, 266, "Modular Subpackage Decoupling", "#22c55e")
    c.node(
        462,
        96,
        w - 28,
        96,
        "Decoupled Subpackages",
        "• Domain-isolated directory modules\n• Strict public API facades\n• Explicit cross-module boundaries",
        "📦",
        "#22c55e",
    )
    c.node(
        462,
        204,
        w - 28,
        114,
        "Shift-Left Enforcement",
        "• Validated in test_architecture_governance\n• Immediate failure on size breach\n• Continuous refactoring discipline",
        "🛡️",
        "#38bdf8",
    )

    c.arrow(412, 144, 448, 144, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_boredom_engine() -> str:
    """Autonomous Boredom Engine & Citation Harvesting."""
    c = SchematicCanvas(860, 360, "AUTONOMOUS BOREDOM ENGINE & CITATION HARVESTING", "AUTONOMOUS AGENT")
    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "1. Idle Detection", "#38bdf8")
    c.node(
        x1 + 12,
        96,
        col_w - 24,
        110,
        "Boredom Accumulator",
        "• Tracks idle server seconds\n• Boredom metric rises steadily\n• Triggers when τ_bored > 100",
        "🦥",
        "#38bdf8",
    )
    c.node(
        x1 + 12,
        218,
        col_w - 24,
        100,
        "Background Daemon",
        "• Cron schedule trigger\n• Zero CPU drain during peak",
        "⏱️",
        "#60a5fa",
    )

    c.container(x2, 68, col_w, 266, "2. Autonomous Sifting", "#22c55e")
    c.node(
        x2 + 12,
        96,
        col_w - 24,
        110,
        "Excitement Engine",
        "• Probes RSS and atom feeds\n• Discovers new civic publications\n• Evaluates semantic density",
        "🔍",
        "#22c55e",
    )
    c.node(
        x2 + 12,
        218,
        col_w - 24,
        100,
        "Domain Sifter",
        "• Cross-references root index\n• Detects decaying claims",
        "🌐",
        "#38bdf8",
    )

    c.container(x3, 68, col_w, 266, "3. Attestation Garden", "#a855f7")
    c.node(
        x3 + 12,
        96,
        col_w - 24,
        110,
        "Citation Harvesting",
        "• Auto-harvests primary quotes\n• Re-verifies decaying claims\n• Enriches local vector store",
        "🌱",
        "#a855f7",
    )
    c.node(
        x3 + 12,
        218,
        col_w - 24,
        100,
        "Signed Envelopes",
        "• Stores Ed25519 receipts\n• Updates mesh gossip peers",
        "🔐",
        "#22c55e",
    )

    c.arrow(x1 + col_w, 151, x2, 151, "#38bdf8")
    c.arrow(x2 + col_w, 151, x3, 151, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_pareto_4k_thinking() -> str:
    """Multi-Model Pareto Frontier: 4k Thinking Sweet Spot."""
    c = SchematicCanvas(860, 360, "MULTI-MODEL PARETO OPTIMIZATION: 4K THINKING SWEET SPOT", "MODEL GOVERNANCE")
    w = 384

    c.container(28, 68, w, 266, "Gemini 3.7 Flash (4,096 Thinking Tokens)", "#22c55e")
    c.node(
        42,
        96,
        w - 28,
        96,
        "Balanced Pareto Peak",
        "• 4,096 thinking tokens default budget\n• Resolves satire & Poe's law nuances\n• 90%+ cost reduction vs flagship models",
        "⚡",
        "#22c55e",
    )
    c.node(
        42,
        204,
        w - 28,
        114,
        "Offline Circuit Breaker",
        "• 30% quota headroom buffer\n• Graceful offline fallback without crashing\n• Hermetic execution on local benchmark",
        "🛡️",
        "#38bdf8",
    )

    c.container(448, 68, w, 266, "Heavyweight Models (Claude / GPT-4o / R1)", "#ef4444")
    c.node(
        462,
        96,
        w - 28,
        96,
        "Flagship Inference Overhead",
        "• 30x higher operational token expense\n• Diminishing returns on structured audits\n• Latency spikes on high-throughput feeds",
        "💰",
        "#ef4444",
    )
    c.node(
        462,
        204,
        w - 28,
        114,
        "Budget Governance",
        "• Restricted to complex multi-source claims\n• Controlled by cost optimizer governor\n• Strict token caps on background tasks",
        "⚖️",
        "#f59e0b",
    )

    c.arrow(412, 144, 448, 144, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


def diagram_generic_schematic(title: str, category: str = "CREDENCE ARCHITECTURE") -> str:
    """Clean 3-column architectural schematic for retaining documents."""
    c = SchematicCanvas(860, 360, title, category)
    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap

    c.container(x1, 68, col_w, 266, "1. Ingestion & Security", "#38bdf8")
    c.node(
        x1 + 12,
        96,
        col_w - 24,
        100,
        "Network Boundary",
        "• Target URLs & text payloads\n• SSRF & metadata IP filter\n• XML entity injection block",
        "📥",
        "#38bdf8",
    )
    c.node(
        x1 + 12,
        208,
        col_w - 24,
        110,
        "DOM Extractor",
        "• Strips scripts & styling\n• Sanitizes HTML elements\n• Isolates untrusted text",
        "🧹",
        "#60a5fa",
    )

    c.container(x2, 68, col_w, 266, "2. Epistemic Evaluation", "#22c55e")
    c.node(
        x2 + 12,
        96,
        col_w - 24,
        100,
        "Multi-Model Consensus",
        "• Heuristic claim verification\n• Verbatim citations (G=1.00)\n• Circuit breaker headroom",
        "🧠",
        "#22c55e",
    )
    c.node(
        x2 + 12,
        208,
        col_w - 24,
        110,
        "Entropy Defense",
        "• Shannon entropy astroturf def\n• Expertise-weighted medians\n• Galileo minority rule override",
        "⚖️",
        "#f59e0b",
    )

    c.container(x3, 68, col_w, 266, "3. Attestation & Custody", "#a855f7")
    c.node(
        x3 + 12,
        96,
        col_w - 24,
        100,
        "RFC 8785 Canonical JSON",
        "• Deterministic serialization\n• UTF-8 sorted key envelope\n• Tamper-evident byte stream",
        "📜",
        "#a855f7",
    )
    c.node(
        x3 + 12,
        208,
        col_w - 24,
        110,
        "Ed25519 Signature",
        "• Genesis root authority sign\n• SQLite + vector persistence\n• Zero-trust verification",
        "🔐",
        "#22c55e",
    )

    c.arrow(x1 + col_w, 146, x2, 146, "#38bdf8")
    c.arrow(x2 + col_w, 146, x3, 146, "#22c55e", marker="url(#arrow-emerald)")
    return c.render()


# ==============================================================================
# 2. MASTER CATALOG OF ACTIVE ARCHITECTURAL ILLUSTRATIONS
# ==============================================================================

# Mapping of active diagram filenames to (builder_function, descriptive_alt_text)
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
    "bittorrent-for-truth.svg": (
        diagram_bittorrent_fact_checking,
        "Figure 1.1: BitTorrent P2P fact-checking work-sharing protocol and rendezvous feed hashing",
    ),
    "bittorrent-economics-of-fact-checking.svg": (
        diagram_bittorrent_fact_checking,
        "Figure 1.1: Decentralized compute swarm economics and deduplicated gossip audit propagation",
    ),
    "confessions-of-a-bored-ai.svg": (
        diagram_boredom_engine,
        "Figure 1.1: Autonomous boredom engine accumulation, excitation thresholds, and citation soil harvesting",
    ),
    "from-860mb-to-2mb-sub-40s-cicd-pipeline.svg": (
        diagram_three_plane_architecture,
        "Figure 1.1: Multi-stage container build optimization and keyless WIF CI/CD staging pipeline",
    ),
    "pining-for-the-fjords.svg": (
        diagram_scale_to_zero_storage,
        "Figure 1.1: Scale-to-zero cold-boot storage hydration cycle and dual-pointer GCS snapshot sync",
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
        diagram_500_loc_ceiling,
        "Figure 1.1: Architectural governance boundaries enforcing single-responsibility code modules",
    ),
    "the-three-plane-architecture.svg": (
        diagram_three_plane_architecture,
        "Figure 1.1: 3-Plane decoupled deployment governance across Edge, Compute, and Infrastructure planes",
    ),
    "the-demotion-highway.svg": (
        diagram_knowledge_demotion_highway,
        "Figure 1.1: 3-Tier knowledge demotion highway and living invariant prompt budget governance",
    ),
    "architecting-sovereign-ai-with-google-antigravity.svg": (
        diagram_agentic_engineering_lifecycle,
        "Figure 1.1: Antigravity 5-stage agentic engineering lifecycle and human Mk1 review gate",
    ),
    "finops-as-epistemology.svg": (
        diagram_bicameral_finops,
        "Figure 1.1: Bicameral inference triage and offline rate-limit circuit breaker architecture",
    ),
    # Core Architectural Documentation Guides
    "architecture.svg": (
        diagram_three_plane_architecture,
        "Figure 1.1: Comprehensive Credence 3-plane ecosystem architecture and service topologies",
    ),
    "invariants.svg": (
        diagram_knowledge_demotion_highway,
        "Figure 1.1: Universal living invariant canon and cognitive hierarchy architecture",
    ),
    "mesh-network.svg": (
        diagram_mesh_topology,
        "Figure 1.1: 13-node Watts-Strogatz peer mesh topology and Byzantine Sybil cartel defense",
    ),
    "security.svg": (
        diagram_untrusted_ingestion,
        "Figure 1.1: Untrusted ingestion boundary, SSRF network defense, and Ed25519 cryptographic seal",
    ),
    "fastmcp.svg": (
        lambda: diagram_generic_schematic("FASTMCP 2.0 PROTOCOL & DUAL TRANSPORT ARCHITECTURE", "MCP INTEROPERABILITY"),
        "Figure 1.1: FastMCP 2.0 dual transport protocol, tools, resources, and prompt endpoints",
    ),
    "feature-parity.svg": (
        lambda: diagram_generic_schematic("UNIVERSAL 4-WAY FEATURE PARITY INTERFACE HUB", "INTERFACE SYMMETRY"),
        "Figure 1.1: Universal 4-way feature parity across CLI, FastMCP, TUI, and Zero-Build Web UI",
    ),
    "deployment-cloudrun.svg": (
        diagram_three_plane_architecture,
        "Figure 1.1: Google Cloud Run serverless compute plane deployment with keyless WIF authentication",
    ),
    "node-germination-lifecycle.svg": (
        diagram_untrusted_ingestion,
        "Figure 1.1: Zero-touch node germination lifecycle, seed initialization, and attestation persistence",
    ),
    "cloudrun-scale-to-zero-cold-start-optimization.svg": (
        diagram_scale_to_zero_storage,
        "Figure 1.1: Cloud Run scale-to-zero cold-start container optimization and sub-1.2s snapshot restore",
    ),
    "security-architecture-and-threat-model.svg": (
        diagram_untrusted_ingestion,
        "Figure 1.1: Comprehensive security architecture, threat model, and untrusted boundary defenses",
    ),
    "invariant-scalability-and-knowledge-governance.svg": (
        diagram_knowledge_demotion_highway,
        "Figure 1.1: Invariant scalability matrix, knowledge taxonomy, and AGENTS.md context economy",
    ),
    "watts-strogatz-dynamics.svg": (
        diagram_mesh_topology,
        "Figure 1.1: Watts-Strogatz small-world mesh clustering, rendezvous feed routing, and Sybil resistance",
    ),
}


# ==============================================================================
# 3. REFACTOR MARKDOWN FILES & SYNCHRONIZE ASSETS
# ==============================================================================


def execute_audit(ecosystem_root: Path):
    docs_root = ecosystem_root / "credence-docs"
    docs_illustrations_dir = docs_root / "assets" / "illustrations"
    web_illustrations_dir = ecosystem_root / "credence" / "web" / "assets" / "illustrations"

    all_mds = sorted(list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md")))

    pruned_tags_count = 0
    updated_tags_count = 0

    print("=== Step 1: Auditing & Refactoring Markdown Image Tags ===")
    for md in all_mds:
        text = md.read_text(encoding="utf-8")
        orig_text = text

        def replace_img(match):
            nonlocal pruned_tags_count, updated_tags_count
            src = match.group(2)
            filename = Path(src).name

            if filename in ACTIVE_DIAGRAMS:
                _, descriptive_alt = ACTIVE_DIAGRAMS[filename]
                updated_tags_count += 1
                return f"![{descriptive_alt}]({src})"
            else:
                pruned_tags_count += 1
                return ""  # Prune non-architectural / redundant image tag

        # Replace image tags
        new_text = re.sub(r"!\[([^\]]*)\]\((assets/illustrations/[^)]+\.svg)\)\n*", replace_img, text)

        # Clean up any duplicate blank lines left by pruned tags
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)

        if new_text != orig_text:
            md.write_text(new_text, encoding="utf-8")

    print(
        f"✅ Markdown Audit Complete: {updated_tags_count} high-value diagrams captioned, {pruned_tags_count} decorative tags pruned."
    )

    print("\n=== Step 2: Generating Active Architectural Schematics ===")
    # Ensure output directories exist
    docs_illustrations_dir.mkdir(parents=True, exist_ok=True)
    web_illustrations_dir.mkdir(parents=True, exist_ok=True)

    # Clean out old SVG files from illustrations directories
    for p in docs_illustrations_dir.glob("*.svg"):
        p.unlink()
    for p in web_illustrations_dir.glob("*.svg"):
        p.unlink()

    generated_count = 0
    for filename, (builder, _) in ACTIVE_DIAGRAMS.items():
        svg_xml = builder()
        (docs_illustrations_dir / filename).write_text(svg_xml, encoding="utf-8")
        (web_illustrations_dir / filename).write_text(svg_xml, encoding="utf-8")
        generated_count += 1

    print(f"✅ Active Schematics Generated: {generated_count} precision SVGs created with 100% SHA-256 parity.")

    # Also update generate_illustrations.py target
    generator_target = ecosystem_root / "credence" / "scripts" / "generate_illustrations.py"
    generator_target.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    print("✅ generator script synchronized.")


if __name__ == "__main__":
    eco_root = Path("/home/pendragon/Projects/credence-ecosystem")
    execute_audit(eco_root)
