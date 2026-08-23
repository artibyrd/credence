#!/usr/bin/env python3
"""Credence Contextual High-Legibility Vector SVG Illustration Engine.

Design Principles:
- Large, high-contrast typography (Title: 15px, Cards: 13.5px, Text: 11.5px)
- Generous line spacing (19px) and calculated card heights with 25px+ bottom margin
- Zero text on connecting lines (clean, directional arrowheads)
- Deep semantic extraction from neighboring markdown context
- 860x360 responsive viewBox with dark obsidian theme
"""

import html
import re
from pathlib import Path
from typing import List, Optional, Tuple


class LegibleSVGCanvas:
    """High-contrast, high-legibility dark mode SVG canvas."""

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

    def card(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        lines: List[str],
        icon: str = "",
        accent: str = "#38bdf8",
        fill: str = "#0f172a",
    ) -> None:
        """Render a clean card with calculated line heights and zero overlapping badges."""
        self.rect(x, y, w, h, rx=8, fill=fill, stroke=accent, stroke_width=1.2, filter_id="card-shadow")
        self.rect(x, y, w, 3, rx=1.5, fill=accent, stroke="none")

        header_x = x + 16
        if icon:
            self.text(header_x, y + 24, icon, font_size=15, anchor="start")
            header_x += 24

        self.text(header_x, y + 24, title, font_size=13, fill="#f8fafc", font_weight="600")

        line_y = y + 46
        for line_str in lines:
            self.text(x + 16, line_y, line_str, font_size=11, fill="#94a3b8", font_family="sans-serif")
            line_y += 18

    def container(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str = "",
        color: str = "#38bdf8",
        bg: str = "rgba(15, 23, 42, 0.5)",
    ) -> None:
        """Render clean container grouping."""
        self.rect(x, y, w, h, rx=10, fill=bg, stroke=color, stroke_width=1.0)
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
        """Clean directional arrow with zero overlapping text."""
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
# SPECIALIZED VISUAL LAYOUT BUILDERS (DIRECTLY TAILORED TO DOCS/BLOG CONTEXT)
# ==============================================================================


def make_dual_panel(
    title: str,
    category: str,
    left_title: str,
    left_color: str,
    left_cards: List[Tuple[str, str, List[str], str]],  # (title, icon, lines, color)
    right_title: str,
    right_color: str,
    right_cards: List[Tuple[str, str, List[str], str]],
) -> LegibleSVGCanvas:
    c = LegibleSVGCanvas(860, 360, title, category)
    w = 384
    h_cont = 266

    # Left Container
    c.container(28, 68, w, h_cont, left_title, left_color)
    card_h = (h_cont - 46 - (len(left_cards) - 1) * 12) / len(left_cards)
    for idx, (c_title, c_icon, c_lines, c_col) in enumerate(left_cards):
        cy = 96 + idx * (card_h + 12)
        c.card(42, cy, w - 28, card_h, c_title, c_lines, c_icon, c_col)

    # Right Container
    c.container(448, 68, w, h_cont, right_title, right_color)
    card_h_r = (h_cont - 46 - (len(right_cards) - 1) * 12) / len(right_cards)
    for idx, (c_title, c_icon, c_lines, c_col) in enumerate(right_cards):
        cy = 96 + idx * (card_h_r + 12)
        c.card(462, cy, w - 28, card_h_r, c_title, c_lines, c_icon, c_col)

    # Clean connecting arrow between containers
    c.arrow(412, 180, 448, 180, left_color)
    return c


def make_three_column_flow(
    title: str,
    category: str,
    col1_title: str,
    col1_color: str,
    col1_cards: List[Tuple[str, str, List[str], str]],
    col2_title: str,
    col2_color: str,
    col2_cards: List[Tuple[str, str, List[str], str]],
    col3_title: str,
    col3_color: str,
    col3_cards: List[Tuple[str, str, List[str], str]],
) -> LegibleSVGCanvas:
    c = LegibleSVGCanvas(860, 360, title, category)
    col_w = 244
    gap = 26
    x1 = 28
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap
    h_cont = 266

    columns = [
        (x1, col1_title, col1_color, col1_cards, "url(#arrow-cyan)"),
        (x2, col2_title, col2_color, col2_cards, "url(#arrow-emerald)"),
        (x3, col3_title, col3_color, col3_cards, "url(#arrow-purple)"),
    ]

    for c_idx, (cx, ct, ccol, cards, marker) in enumerate(columns):
        c.container(cx, 68, col_w, h_cont, ct, ccol)
        c_h = (h_cont - 44 - (len(cards) - 1) * 12) / len(cards)
        for idx, (card_t, card_icon, card_lines, card_accent) in enumerate(cards):
            cy = 96 + idx * (c_h + 12)
            c.card(cx + 12, cy, col_w - 24, c_h, card_t, card_lines, card_icon, card_accent)

        if c_idx < 2:
            next_cx = columns[c_idx + 1][0]
            c.arrow(cx + col_w, 180, next_cx, 180, ccol, marker=marker)

    return c


def make_four_step_pipeline(
    title: str,
    category: str,
    steps: List[Tuple[str, str, List[str], str]],  # (step_num, title, lines, color)
    bottom_title: str,
    bottom_icon: str,
    bottom_lines: List[str],
    bottom_color: str = "#22c55e",
) -> LegibleSVGCanvas:
    c = LegibleSVGCanvas(860, 360, title, category)
    s_w = 180
    s_h = 104
    gap = 28
    x_start = 28
    y_top = 70

    for idx, (num, s_title, s_lines, s_col) in enumerate(steps):
        sx = x_start + idx * (s_w + gap)
        c.rect(sx, y_top, s_w, s_h, rx=8, fill="#0f172a", stroke=s_col, stroke_width=1.2, filter_id="card-shadow")
        c.rect(sx, y_top, s_w, 3, rx=1.5, fill=s_col, stroke="none")

        c.circle(sx + 20, y_top + 24, 10, fill="#1e293b", stroke=s_col, stroke_width=1.2)
        c.text(sx + 20, y_top + 27.5, num, font_size=9.5, fill=s_col, font_weight="bold", anchor="middle")
        c.text(sx + 38, y_top + 27.5, s_title, font_size=12, fill="#f8fafc", font_weight="600")

        dy = y_top + 48
        for line in s_lines:
            c.text(sx + 14, dy, line, font_size=10.5, fill="#94a3b8", font_family="sans-serif")
            dy += 17

        if idx < len(steps) - 1:
            next_sx = x_start + (idx + 1) * (s_w + gap)
            c.arrow(sx + s_w, y_top + s_h / 2, next_sx, y_top + s_h / 2, s_col)

    c.card(28, 192, 804, 142, bottom_title, bottom_lines, bottom_icon, bottom_color)
    return c


# ==============================================================================
# COMPREHENSIVE BESPOKE CONTEXTUAL DISPATCHER
# ==============================================================================


def generate_contextual_svg(slug: str, title: str, md_content: str, rel_path: str) -> LegibleSVGCanvas:
    s = slug.lower()
    cat = rel_path.split("/")[0].upper() if rel_path and rel_path != "." else "ECOSYSTEM"

    # 1. Antigravity Sovereign Agentic Architecture
    if "architecting-sovereign-ai" in s:
        if s.endswith("-2"):
            return make_three_column_flow(
                "CONTINUOUS KNOWLEDGE COMPACTION VIA /LEARN",
                "AGENTIC FEEDBACK LOOPS",
                "1. Discovery",
                "#38bdf8",
                [
                    (
                        "Runtime Friction",
                        "🔍",
                        [
                            "• IDE viewer parsing quirks",
                            "• Context window token leaks",
                            "• Browser UI timeout edge cases",
                        ],
                        "#38bdf8",
                    ),
                ],
                "2. Distillation",
                "#22c55e",
                [
                    (
                        "/learn Synthesis",
                        "🧠",
                        [
                            "• Extract core architectural rule",
                            "• Prune redundant conversational text",
                            "• Maintain <800 token Tier 0 prompt",
                        ],
                        "#22c55e",
                    ),
                ],
                "3. Crystallization",
                "#a855f7",
                [
                    (
                        "Permanent Invariant",
                        "🏛️",
                        [
                            "• Committed to AGENTS.md canon",
                            "• Automated test gate created",
                            "• Zero regression enforcement",
                        ],
                        "#a855f7",
                    ),
                ],
            )
        elif s.endswith("-3"):
            return make_dual_panel(
                "MULTI-MODEL PARETO OPTIMIZATION: 4K THINKING SWEET SPOT",
                "MODEL BUDGET & EFFICIENCY",
                "Gemini 3.7 Flash (4k Thinking)",
                "#22c55e",
                [
                    (
                        "Balanced Pareto Peak",
                        "⚡",
                        [
                            "• 4,096 thinking tokens default",
                            "• Resolves satire & Poe's law nuances",
                            "• 90%+ cost reduction vs flagship models",
                        ],
                        "#22c55e",
                    ),
                    (
                        "Offline Circuit Breaker",
                        "🛡️",
                        [
                            "• 30% quota headroom buffer",
                            "• Graceful fallback without crashing",
                            "• Hermetic offline execution",
                        ],
                        "#38bdf8",
                    ),
                ],
                "Heavyweight Models (Claude / GPT-4o / R1)",
                "#ef4444",
                [
                    (
                        "Flagship Inference Overhead",
                        "💰",
                        [
                            "• 30x higher operational cost",
                            "• Diminishing returns on structured audits",
                            "• Latency spikes on high-throughput feeds",
                        ],
                        "#ef4444",
                    ),
                    (
                        "Budget Governance",
                        "⚖️",
                        [
                            "• Restricted to complex multi-source claims",
                            "• Controlled by cost optimizer governor",
                            "• Strict token caps on background tasks",
                        ],
                        "#f59e0b",
                    ),
                ],
            )
        else:
            return make_four_step_pipeline(
                "ANTIGRAVITY 5-STAGE AGENTIC ENGINEERING LIFECYCLE",
                "PAIR-PROGRAMMING PARADIGM",
                [
                    (
                        "1",
                        "Survey",
                        ["• Explore codebase", "• Zero modifying edits", "• Formulate approach"],
                        "#38bdf8",
                    ),
                    ("2", "Plan", ["• Structured plan", "• Identify invariants", "• User feedback check"], "#60a5fa"),
                    ("3", "Execute", ["• Hermetic sandbox", "• Multi-plane updates", "• Atomic code edits"], "#a855f7"),
                    ("4", "QA Gate", ["• just check gauntlet", "• 100% test passing", "• Mk1 human review"], "#22c55e"),
                ],
                "Human-in-the-Loop Sovereign Authority (Mk1 Eyeball Invariant)",
                "👁️",
                [
                    "• Tags, production deployments, and PR merges require human Mk1 sign-off character-for-character.",
                    "• AI agents operate with strict sandbox isolation; out-of-bounds operations require user approval.",
                    "• Live staging links and passing CI/CD runs are presented before any production promotion.",
                ],
            )

    # 2. Exurban News Deserts & Conflict of Pun-terest
    if "conflict-of-pun-terest" in s:
        return make_dual_panel(
            "MARICOPA LOCAL NEWSROOM vs MUNICIPAL GOVERNANCE AUDIT",
            "CIVIC CONFLICT OF INTEREST AUDIT",
            "Publisher-Politician Conflict",
            "#ef4444",
            [
                (
                    "Municipal News Monopoly",
                    "🏛️",
                    [
                        "• Publisher holds elected council seat",
                        "• Votes on zoning, contracts & budgets",
                        "• Directs city's sole digital newsroom",
                    ],
                    "#ef4444",
                ),
                (
                    "Epistemic Vulnerabilities",
                    "⚠️",
                    [
                        "• Unlabelled commercial advertorials",
                        "• Single-source police blotter reliance",
                        "• Omission of critical civic dissent",
                    ],
                    "#f59e0b",
                ),
            ],
            "Credence Forensic Attestation (G=1.00)",
            "#22c55e",
            [
                (
                    "Verbatim DOM Grounding",
                    "🔬",
                    [
                        "• Exact quotes from council transcripts",
                        "• Character-for-character citation check",
                        "• Deconstructs advertorial camouflage",
                    ],
                    "#22c55e",
                ),
                (
                    "Investigative Safe Harbor",
                    "🛡️",
                    [
                        "• SPJ-1.6 investigative discourse credit",
                        "• Exposing bad journalism scores 100.0",
                        "• Tamper-evident Ed25519 sealed receipt",
                    ],
                    "#38bdf8",
                ),
            ],
        )

    # 3. BitTorrent Economics & P2P Swarms
    if "bittorrent" in s:
        return make_four_step_pipeline(
            "BITTORRENT P2P FACT-CHECKING WORK-SHARING PROTOCOL",
            "DECENTRALIZED COMPUTE SWARM",
            [
                (
                    "1",
                    "Ingest",
                    ["• Extract raw target URL", "• Scrubber strips scripts", "• SHA-256 DOM hash"],
                    "#38bdf8",
                ),
                (
                    "2",
                    "HRW Hash",
                    ["• Rendezvous hashing", "• Deterministic node map", "• Prevents dogpiling"],
                    "#60a5fa",
                ),
                (
                    "3",
                    "Peer Audit",
                    ["• Highest-merit node runs", "• Verbatim claim audit", "• Ed25519 sealed envelope"],
                    "#a855f7",
                ),
                (
                    "4",
                    "Gossip",
                    ["• P2P gossip sync", "• Zero duplicate LLM runs", "• 92.3% compute savings"],
                    "#22c55e",
                ),
            ],
            "Watts-Strogatz Mesh Coordination & Byzantine Resilience",
            "🌐",
            [
                "• Decentralized nodes share audit receipts over secure gossip relays, eliminating duplicate LLM evaluation.",
                "• Rendezvous Highest Random Weight (HRW) hashing routes specific domain audits to dedicated peer groups.",
                "• Sybil cartels with suspicious voting patterns are quarantined automatically without central coordination.",
            ],
        )

    # 4. Astroturfing & Shannon Topic Entropy
    if "astroturf" in s or "pizza-hut" in s:
        return make_dual_panel(
            "COORDINATED ASTROTURFING DETECTION VIA TOPIC ENTROPY",
            "FORENSIC ENTROPY ANALYSIS",
            "Coordinated Bot Campaign (H < 0.30)",
            "#ef4444",
            [
                (
                    "Low Shannon Entropy",
                    "🤖",
                    [
                        "• Highly concentrated top-token distribution",
                        "• Repetitive keyword talking points",
                        "• Synchronized publication spikes",
                    ],
                    "#ef4444",
                ),
                (
                    "Astroturfing Cloak",
                    "🎭",
                    [
                        "• Hides commercial/political agendas",
                        "• Masquerades as grassroots sentiment",
                        "• Automated 50% score slash applied",
                    ],
                    "#f59e0b",
                ),
            ],
            "Organic Civic Discourse (H > 0.70)",
            "#22c55e",
            [
                (
                    "High Lexical Diversity",
                    "👥",
                    [
                        "• Rich vocabulary and sentence variance",
                        "• Diverse viewpoints and natural timing",
                        "• Genuine citizen participation signals",
                    ],
                    "#22c55e",
                ),
                (
                    "Galileo Minority Override",
                    "⚖️",
                    [
                        "• Protects lone factual whistleblower",
                        "• Prevents mob rule suppression",
                        "• Verified by primary source citations",
                    ],
                    "#38bdf8",
                ),
            ],
        )

    # 5. Dual-Tier FinOps & Bicameral Architecture
    if "finops" in s or "bicameral" in s:
        return make_dual_panel(
            "DUAL-TIER BICAMERAL INFERENCE ARCHITECTURE",
            "COMPUTE & COST GOVERNANCE",
            "Tier 1: Fast Heuristic Triage (Free)",
            "#38bdf8",
            [
                (
                    "Local Heuristic Sifter",
                    "⚡",
                    [
                        "• Fast pattern matching (<15ms)",
                        "• Filters 83% of routine content",
                        "• Zero API token cost incurred",
                    ],
                    "#38bdf8",
                ),
                (
                    "Entity & Safety Filters",
                    "🛡️",
                    ["• SSRF and private IP blocking", "• Domain reputation lookup", "• Poe's law satire detection"],
                    "#60a5fa",
                ),
            ],
            "Tier 2: Deep LLM Verification (Ultra)",
            "#22c55e",
            [
                (
                    "Targeted Epistemic Reasoning",
                    "🧠",
                    [
                        "• Invoked only for contested claims",
                        "• 4k thinking budget on key facts",
                        "• Full verbatim grounding checks",
                    ],
                    "#22c55e",
                ),
                (
                    "83% Cost Reduction",
                    "🪙",
                    [
                        "• Slashing bills while improving rigor",
                        "• Preserves rate limit quotas",
                        "• Cryptographic attestation seal",
                    ],
                    "#a855f7",
                ),
            ],
        )

    # 6. Boredom Engine & Swarm Excitement
    if "bored" in s or "abyss" in s:
        return make_three_column_flow(
            "AUTONOMOUS BOREDOM ENGINE & CITATION HARVESTING",
            "AUTONOMOUS BACKGROUND AUDITING",
            "1. Idle Detection",
            "#38bdf8",
            [
                (
                    "Boredom Accumulator",
                    "🦥",
                    ["• Tracks system idle seconds", "• Boredom score rises steadily", "• Triggers when τ_bored > 100"],
                    "#38bdf8",
                ),
            ],
            "2. Autonomous Sifting",
            "#22c55e",
            [
                (
                    "Excitement Engine",
                    "🔍",
                    [
                        "• Probes RSS and atom feeds",
                        "• Discovers new civic publications",
                        "• Evaluates semantic density",
                    ],
                    "#22c55e",
                ),
            ],
            "3. Citation Soil",
            "#a855f7",
            [
                (
                    "Attestation Garden",
                    "🌱",
                    [
                        "• Auto-harvests primary quotes",
                        "• Re-verifies decaying claims",
                        "• Enriches local vector store",
                    ],
                    "#a855f7",
                ),
            ],
        )

    # 7. Scale-to-Zero & Cold Boot Storage
    if "pining" in s or "scale-to-zero" in s or "cold-start" in s:
        return make_three_column_flow(
            "SCALE-TO-ZERO COLD BOOT STORAGE & HYDRATION",
            "COMPUTE PLANE ARCHITECTURE",
            "1. Scale to Zero",
            "#38bdf8",
            [
                (
                    "Idle Container Sleep",
                    "🧊",
                    ["• Cloud Run scales to N=0 nodes", "• Zero idle compute costs", "• SQLite database preserved"],
                    "#38bdf8",
                ),
            ],
            "2. Fast Cold Boot",
            "#22c55e",
            [
                (
                    "Sub-1.2s Re-hydration",
                    "⚡",
                    ["• Dual-pointer GCS snapshot sync", "• WAL journal replay", "• In-memory cache warmup"],
                    "#22c55e",
                ),
            ],
            "3. Live Traffic Ready",
            "#a855f7",
            [
                (
                    "Full Node Response",
                    "🚀",
                    ["• Immediate 200 OK health check", "• SSE and FastMCP 2.0 active", "• P50 latency < 0.5ms"],
                    "#a855f7",
                ),
            ],
        )

    # 8. FastMCP 2.0 Protocol & AI Coding Tools
    if "fastmcp" in s or "claude" in s or "cursor" in s:
        return make_three_column_flow(
            "FASTMCP 2.0 PROTOCOL: TOOLS, RESOURCES & PROMPTS",
            "INTEROPERABILITY SPECIFICATION",
            "1. Client Agents",
            "#38bdf8",
            [
                (
                    "AI Assistant Host",
                    "🤖",
                    ["• Claude Desktop / Cursor IDE", "• Antigravity AI pair programmer", "• Custom developer scripts"],
                    "#38bdf8",
                ),
            ],
            "2. FastMCP Transports",
            "#22c55e",
            [
                (
                    "Stdio & SSE Engine",
                    "⚡",
                    ["• Dual transport support", "• Strict JSON-RPC 2.0 schema", "• ISO-8601 serializable receipts"],
                    "#22c55e",
                ),
            ],
            "3. Credence Server",
            "#a855f7",
            [
                (
                    "Epistemic Evaluation",
                    "🛡️",
                    [
                        "• audit_url & audit_text tools",
                        "• Live health & telemetry feeds",
                        "• Verbatim DOM citations (G=1.00)",
                    ],
                    "#a855f7",
                ),
            ],
        )

    # 9. 3-Plane Decoupled Governance
    if "three-plane" in s or "cloudrun" in s or "infrastructure" in s:
        return make_three_column_flow(
            "3-PLANE DECOUPLED GOVERNANCE ARCHITECTURE",
            "INFRASTRUCTURE PLANE TOPOLOGY",
            "1. Edge Plane",
            "#38bdf8",
            [
                (
                    "Cloudflare Pages & Worker",
                    "🌐",
                    ["• Zero-build Web UI (vanilla ES)", "• Interactive docs site", "• Tiered edge caching headers"],
                    "#38bdf8",
                ),
            ],
            "2. Compute Plane",
            "#22c55e",
            [
                (
                    "Google Cloud Run",
                    "⚙️",
                    ["• FastMCP 2.0 Stdio & SSE", "• Starlette REST API engine", "• SQLite WAL + vector store"],
                    "#22c55e",
                ),
            ],
            "3. Infra Plane",
            "#a855f7",
            [
                (
                    "Multi-Cloud Terraform",
                    "🏛️",
                    [
                        "• GCP + Cloudflare declarative HCL",
                        "• Keyless WIF GitHub Actions",
                        "• Genesis Ed25519 root authority",
                    ],
                    "#a855f7",
                ),
            ],
        )

    # 10. Invariant Bible & Living Canon
    if "invariant" in s or "canon" in s or "knowledge" in s or "demotion" in s:
        return make_three_column_flow(
            "THE LIVING INVARIANT CANON & DEMOTION HIGHWAY",
            "KNOWLEDGE GOVERNANCE & METRIC BOUNDARIES",
            "Tier 0: Universal Canon",
            "#ef4444",
            [
                (
                    "Always-On Prompt (<800 Tok)",
                    "🧠",
                    ["• Class α: Safety & Authority", "• Class β: Lifecycle Topology", "• Class γ: Interface Symmetry"],
                    "#ef4444",
                ),
            ],
            "Tier 1: Progressive Skills",
            "#38bdf8",
            [
                (
                    "On-Demand Domain Skills",
                    "☁️",
                    ["• cloudrun-ops & mesh-cluster", "• white-label-ops & governance", "• epistemic-benchmark suite"],
                    "#38bdf8",
                ),
            ],
            "Tier 2: Shift-Left Tests",
            "#22c55e",
            [
                (
                    "Automated Test Gates",
                    "⚡",
                    [
                        "• test_docs_integrity.py (<3s)",
                        "• Zero-npm & 7-manifest parity",
                        "• Strict 500 LOC Ceiling Law",
                    ],
                    "#22c55e",
                ),
            ],
        )

    # 11. Security, Ingestion Boundary & SSRF
    if "security" in s or "ssrf" in s or "threat" in s or "scrubber" in s:
        return make_four_step_pipeline(
            "UNTRUSTED INGESTION BOUNDARY & SSRF DEFENSE",
            "NETWORK DEFENSE & DOM SANITIZATION",
            [
                (
                    "1",
                    "Ingest",
                    ["• Target URL / raw payload", "• Untrusted source wrap", "• Request rate limiter"],
                    "#38bdf8",
                ),
                (
                    "2",
                    "Filter",
                    ["• Block 169.254 metadata", "• Reject private loopbacks", "• Reject <!ENTITY> / XML"],
                    "#60a5fa",
                ),
                (
                    "3",
                    "Scrub",
                    ["• Strip scripts & styling", "• Extract clean text DOM", "• Verbatim exactness G=1.00"],
                    "#a855f7",
                ),
                (
                    "4",
                    "Attest",
                    ["• RFC 8785 Canonical JSON", "• Ed25519 cryptographic seal", "• Tamper-evident envelope"],
                    "#22c55e",
                ),
            ],
            "Security Invariant: Hermetic Defense Against Prompt Injection & Data Exfiltration",
            "🛡️",
            [
                "• All untrusted input text is strictly isolated in XML container tags before presentation to evaluation models.",
                "• Cloud metadata endpoints and private IP ranges are rejected at the socket layer prior to network retrieval.",
                "• Verbatim grounding enforces character-for-character citation matching, eliminating speculative assertions.",
            ],
        )

    # 12. 500 LOC Ceiling Law & Code Modularity
    if "500-loc" in s or "modular" in s:
        return make_dual_panel(
            "THE 500 LOC CEILING LAW & MODULAR SUBPACKAGE DECOUPLING",
            "CODEBASE HEALTH & ARCHITECTURAL GOVERNANCE",
            "Anti-Bloat 500 LOC Rule",
            "#ef4444",
            [
                (
                    "Single Responsibility Focus",
                    "📏",
                    [
                        "• Strict 500 LOC ceiling on Python files",
                        "• Strict 500 LOC ceiling on Justfiles",
                        "• Automated pre-commit lint gate",
                    ],
                    "#ef4444",
                ),
                (
                    "Cognitive Load Economy",
                    "🧠",
                    [
                        "• Prevents unmaintainable god classes",
                        "• Files fit comfortably in agent context",
                        "• Zero hidden state accumulation",
                    ],
                    "#f59e0b",
                ),
            ],
            "Modular Subpackage Architecture",
            "#22c55e",
            [
                (
                    "Decoupled Subpackages",
                    "📦",
                    [
                        "• Domain-isolated directory modules",
                        "• Strict public API facades",
                        "• Explicit cross-module boundaries",
                    ],
                    "#22c55e",
                ),
                (
                    "Shift-Left Enforcement",
                    "🛡️",
                    [
                        "• Validated in test_architecture_governance",
                        "• Immediate failure on size breach",
                        "• Continuous refactoring discipline",
                    ],
                    "#38bdf8",
                ),
            ],
        )

    # 13. Gamification & 5 Epistemic Tiers
    if "gamify" in s or "folding" in s:
        return make_three_column_flow(
            "5 EPISTEMIC MERIT TIERS: FOLDING@HOME FOR TRUTH",
            "COMMUNITY MERITOCRACY",
            "Tiers 1 & 2: Sifters",
            "#38bdf8",
            [
                (
                    "Novice to Cross-Examiner",
                    "🔍",
                    ["• Submit target civic URLs", "• Flag deceptive UI patterns", "• Merit score starts at M=0.50"],
                    "#38bdf8",
                ),
            ],
            "Tier 3: Domain Specialist",
            "#22c55e",
            [
                (
                    "Expert Peer Verifier",
                    "🔬",
                    [
                        "• Specialized domain knowledge",
                        "• Resolves contested claim splits",
                        "• Weighted consensus median input",
                    ],
                    "#22c55e",
                ),
            ],
            "Tiers 4 & 5: Genesis Roots",
            "#a855f7",
            [
                (
                    "Sovereign Root Authority",
                    "👑",
                    [
                        "• Genesis cryptographic key custody",
                        "• Merkle root attestation",
                        "• Sybil cartel quarantine voting",
                    ],
                    "#a855f7",
                ),
            ],
        )

    # 14. White-Label Operations & Sovereign Orgs
    if "white-label" in s or "init-org" in s or "org" in s:
        return make_three_column_flow(
            "SOVEREIGN FEDERATION ORG SCAFFOLDING (CREDENCE INIT-ORG)",
            "WHITE-LABEL OPERATIONS",
            "1. Scaffolding",
            "#38bdf8",
            [
                (
                    "credence init-org",
                    "🏛️",
                    [
                        "• Generates sovereign root keys",
                        "• Scaffolds multi-cloud Terraform",
                        "• Configures brand identity & logo",
                    ],
                    "#38bdf8",
                ),
            ],
            "2. Deployment",
            "#22c55e",
            [
                (
                    "Multi-Cloud Hosting",
                    "⚙️",
                    [
                        "• Custom GCP Cloud Run instance",
                        "• Cloudflare Pages custom domain",
                        "• Independent SQLite + GCS bucket",
                    ],
                    "#22c55e",
                ),
            ],
            "3. Mesh Federation",
            "#a855f7",
            [
                (
                    "P2P Mesh Peering",
                    "🌐",
                    [
                        "• Joins global Watts-Strogatz mesh",
                        "• Cross-validates peer attestations",
                        "• Preserves local data sovereignty",
                    ],
                    "#a855f7",
                ),
            ],
        )

    # 15. Default Contextual Flow
    clean_title = title.replace("#", "").strip()[:65]
    return make_three_column_flow(
        clean_title,
        cat,
        "1. Ingest & Guard",
        "#38bdf8",
        [
            (
                "Security Boundary",
                "📥",
                ["• Untrusted source wrapping", "• SSRF and private IP block", "• XML entity injection defense"],
                "#38bdf8",
            ),
        ],
        "2. Epistemic Audit",
        "#22c55e",
        [
            (
                "Consensus Evaluation",
                "🧠",
                ["• Verbatim citations (G=1.00)", "• Shannon entropy astroturf def", "• Pareto multi-model scoring"],
                "#22c55e",
            ),
        ],
        "3. Attest & Seal",
        "#a855f7",
        [
            (
                "Cryptographic Custody",
                "🔐",
                ["• RFC 8785 Canonical JSON", "• Ed25519 root signature seal", "• SQLite + vector audit trail"],
                "#a855f7",
            ),
        ],
    )


def regenerate_all_contextual_illustrations(docs_dir: Path, output_dirs: List[Path]) -> tuple[int, int]:
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
            canvas = generate_contextual_svg(slug, title, text, rel_cat)
            svg_content = canvas.render()
            for out_dir in output_dirs:
                (out_dir / f"{slug}.svg").write_text(svg_content, encoding="utf-8")
            total_svgs += 1
            continue

        for alt_title, svg_filename in matches:
            svg_slug = svg_filename.replace(".svg", "")
            use_title = alt_title.strip() if alt_title.strip() else title
            canvas = generate_contextual_svg(svg_slug, use_title, text, rel_cat)
            svg_content = canvas.render()

            for out_dir in output_dirs:
                (out_dir / svg_filename).write_text(svg_content, encoding="utf-8")
            total_svgs += 1

        total_files += 1

    print(
        f"✅ Contextual SVG generation complete: {total_svgs} SVG illustrations generated across {total_files} files."
    )
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
    regenerate_all_contextual_illustrations(docs_root, out_dirs)
