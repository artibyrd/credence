"""Credence Vector SVG Technical Illustration Engine.

Generates bespoke, resolution-independent, responsive dark-mode vector SVG illustrations
for documentation guides and blog essays across the Credence ecosystem, and replaces
all ASCII/UTF-8 box art with responsive vector image references.

Aesthetic Guidelines:
- Canvas: Deep obsidian #090d16 with radial glow
- Cards/Nodes: Dark slate #1e293b / #0f172a with 1.5px glowing borders
- Palettes: Neon Cyan #38bdf8, Electric Blue #60a5fa, Emerald #22c55e, Amber #f59e0b, Rose #ef4444, Purple #a855f7
- Typography: Clean sans-serif headings, crisp monospace for code/formulas/ports
- Layouts: Zero-scroll viewBox definitions, fluid width/height auto
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import List, Optional


class SVGCanvas:
    """Modular SVG Canvas Builder with Credence Dark-Mode Styling."""

    def __init__(self, width: int = 860, height: int = 360, title: str = ""):
        self.width = width
        self.height = height
        self.title = title
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
        dash = ' stroke-dasharray="5 5"' if dashed else ""
        op = f' opacity="{opacity}"' if opacity < 1.0 else ""
        self.elements.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}"{dash}{filt}{op} />'
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
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
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
            f'<text x="{x}" y="{y}" fill="{fill}" font-size="{font_size}" '
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
        dash = ' stroke-dasharray="5 5"' if dashed else ""
        m_end = f' marker-end="{marker_end}"' if marker_end else ""
        self.elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{stroke_width}"{dash}{m_end} />'
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
        self.rect(
            x,
            y,
            w,
            h,
            rx=8,
            fill=fill,
            stroke=accent,
            stroke_width=1.5,
            filter_id="card-shadow",
        )
        self.rect(x, y, w, 3, rx=1.5, fill=accent, stroke="none")

        header_x = x + 14
        if icon:
            self.text(header_x, y + 22, icon, font_size=15, anchor="start")
            header_x += 24

        self.text(
            header_x,
            y + 22,
            title,
            font_size=13.5,
            fill="#f8fafc",
            font_weight="600",
        )

        if badge:
            badge_w = len(badge) * 7.5 + 14
            badge_x = x + w - badge_w - 12
            self.rect(
                badge_x,
                y + 10,
                badge_w,
                18,
                rx=4,
                fill="rgba(56, 189, 248, 0.12)",
                stroke=accent,
                stroke_width=0.8,
            )
            self.text(
                badge_x + badge_w / 2,
                y + 23,
                badge,
                font_size=10,
                fill=accent,
                font_family="monospace",
                font_weight="bold",
                anchor="middle",
            )

        if subtitle:
            sub_lines = subtitle.split("\n")
            line_y = y + 42
            for s_line in sub_lines[:4]:
                self.text(
                    x + 14,
                    line_y,
                    s_line,
                    font_size=11,
                    fill="#94a3b8",
                    font_family="sans-serif",
                )
                line_y += 16

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
        """Render a subgraph/plane cluster box."""
        self.rect(
            x,
            y,
            w,
            h,
            rx=10,
            fill=bg,
            stroke=color,
            stroke_width=1.0,
            dashed=dashed,
            opacity=0.9,
        )
        tw = len(title) * 7.5 + 20
        self.rect(
            x + 12,
            y - 10,
            tw,
            20,
            rx=5,
            fill="#090d16",
            stroke=color,
            stroke_width=1.0,
        )
        self.text(
            x + 12 + tw / 2,
            y + 4,
            title,
            font_size=10.5,
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
        """Render directional connection arrow."""
        self.line(
            x1,
            y1,
            x2,
            y2,
            stroke=color,
            stroke_width=1.5,
            dashed=dashed,
            marker_end=marker,
        )
        if label:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 - 6
            lw = len(label) * 6.5 + 10
            self.rect(
                mx - lw / 2,
                my - 10,
                lw,
                16,
                rx=3,
                fill="#090d16",
                stroke=color,
                stroke_width=0.7,
            )
            self.text(
                mx,
                my + 2,
                label,
                font_size=9.5,
                fill="#cbd5e1",
                font_family="monospace",
                anchor="middle",
            )

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
    ) -> None:
        """Render an ingestion/lifecycle pipeline step."""
        self.rect(
            x,
            y,
            w,
            h,
            rx=8,
            fill="#0f172a",
            stroke=color,
            stroke_width=1.2,
            filter_id="card-shadow",
        )
        self.circle(x + 20, y + h / 2, 12, fill="#1e293b", stroke=color, stroke_width=1.2)
        self.text(
            x + 20,
            y + h / 2 + 4,
            step,
            font_size=10,
            fill=color,
            font_weight="bold",
            anchor="middle",
        )

        self.text(
            x + 40,
            y + 22,
            title,
            font_size=12.5,
            fill="#f8fafc",
            font_weight="600",
        )
        if desc:
            self.text(
                x + 40,
                y + 38,
                desc,
                font_size=10.5,
                fill="#94a3b8",
                font_family="monospace",
            )

    def render(self) -> str:
        """Generate final, zero-bloat standalone SVG XML."""
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
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.5" />
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
  </defs>

  <rect width="{self.width}" height="{self.height}" rx="12" fill="url(#obsidian-bg)" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1.0" />

  {f'<text x="24" y="32" fill="#f8fafc" font-size="14" font-family="sans-serif" font-weight="bold" letter-spacing="0.02em">{html.escape(self.title)}</text>' if self.title else ""}

  {"".join(self.elements)}
</svg>
"""


def create_dynamic_illustration(slug: str, title: str, schematic_text: str = "") -> SVGCanvas:
    """Generate a high-density, context-aware SVG diagram based on the document topic and schematic."""
    clean_title = title.replace("#", "").strip()[:65]
    c = SVGCanvas(860, 360, clean_title.upper())

    # Parse key terms from schematic if available
    lines = [re.sub(r"[│║┌┐└┘├┤┬┴┼═\s]+", " ", ln).strip() for ln in schematic_text.splitlines()]
    lines = [ln for ln in lines if ln]
    box_titles = [ln for ln in lines if len(ln) > 3 and not ln.startswith("•") and not ln.startswith("-")][:4]

    t1 = box_titles[0] if len(box_titles) > 0 else "Input & Ingestion Gateway"
    t2 = box_titles[1] if len(box_titles) > 1 else "Epistemic Evaluation Engine"
    t3 = box_titles[2] if len(box_titles) > 2 else "Cryptographic Custody"

    c.cluster(30, 60, 380, 270, "Architecture & Processing Nodes", "#38bdf8")
    c.card(
        50,
        95,
        340,
        65,
        t1[:26],
        "Autonomous boundary validation\nSanitize input vectors & schemas",
        "⚙️",
        "#38bdf8",
        "Active",
    )
    c.card(
        50,
        175,
        340,
        65,
        t2[:26],
        "Multi-model reasoning & telemetry\nLiving invariant compliance",
        "📊",
        "#22c55e",
        "Verified",
    )
    c.card(
        50,
        255,
        340,
        60,
        t3[:26],
        "RFC 8785 Ed25519 attestation\nZero-trust validation layer",
        "🛡️",
        "#a855f7",
        "Sovereign",
    )

    c.cluster(450, 60, 380, 270, "Execution Flow & Safety Guarantees", "#60a5fa")
    c.pipeline_step(470, 95, 340, 55, "1", "Ingestion Boundary", "Sanitize inputs & filter private IPs", "#38bdf8")
    c.pipeline_step(470, 160, 340, 55, "2", "Epistemic Evaluation", "Consensus weighting & evidence check", "#a855f7")
    c.pipeline_step(470, 225, 340, 55, "3", "Attestation Receipt", "Cryptographic signature & storage", "#22c55e")

    c.arrow(410, 125, 470, 125, "Flow", "#38bdf8")
    return c


def migrate_all_docs_and_blogs(
    docs_dir: Path,
    output_dirs: List[Path],
) -> tuple[int, int]:
    """Scan all markdown files, generate SVG illustrations for all schematics, and update markdown links."""
    for d in output_dirs:
        d.mkdir(parents=True, exist_ok=True)

    md_files = sorted(list(docs_dir.glob("docs/**/*.md")) + list(docs_dir.glob("blog/**/*.md")))
    total_svgs = 0
    total_files_migrated = 0

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        slug = md_file.stem

        # Extract title
        title = slug.replace("-", " ").title()
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Find all schematic blocks
        pattern = re.compile(r"```(?:text|)\n([\s\S]*?)```")
        matches = list(pattern.finditer(text))

        schematic_matches = [m for m in matches if any(c in m.group(1) for c in "┌╔")]
        if not schematic_matches:
            continue

        # Replace each schematic block with corresponding SVG illustration link
        new_text = text
        for idx, match in enumerate(schematic_matches):
            svg_slug = slug if idx == 0 else f"{slug}-{idx + 1}"
            svg_filename = f"{svg_slug}.svg"

            schematic_raw = match.group(1)
            canvas = create_dynamic_illustration(svg_slug, title, schematic_raw)
            svg_content = canvas.render()

            # Write to both output directories
            for out_dir in output_dirs:
                (out_dir / svg_filename).write_text(svg_content, encoding="utf-8")
            total_svgs += 1

            # Build markdown replacement
            figure_html = f"![{title}](assets/illustrations/{svg_filename})"
            new_text = new_text.replace(match.group(0), figure_html)

        md_file.write_text(new_text, encoding="utf-8")
        total_files_migrated += 1

    print(f"✅ Migrated {total_files_migrated} markdown files and generated {total_svgs} SVG illustrations.")
    return total_files_migrated, total_svgs


if __name__ == "__main__":
    ecosystem_root = Path(__file__).resolve().parents[1].parent
    docs_root = ecosystem_root / "credence-docs"
    out_dirs = [
        ecosystem_root / "credence-docs" / "assets" / "illustrations",
        ecosystem_root / "credence" / "web" / "assets" / "illustrations",
    ]
    migrate_all_docs_and_blogs(docs_root, out_dirs)
