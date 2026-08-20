"""Rich Visual Styling & Verdict Badges for Credence CLI.

Provides standardized color palettes, score meters, and terminal verdict badges.
"""

from __future__ import annotations

from rich.text import Text


def get_verdict_badge(classification: str, suspicion_score: float, is_satire: bool = False) -> Text:
    """Generate a rich colored verdict badge with classification and score."""
    if is_satire:
        return Text("🎭 SATIRE / PARODY (0.0)", style="bold italic yellow")

    cls_upper = classification.upper()
    if cls_upper in ("CLEAN", "LOW_SUSPICION") or suspicion_score <= 25.0:
        return Text(f"🛡️  CLEAN ({suspicion_score:.1f})", style="bold green")
    elif cls_upper in ("SUSPICIOUS", "MIXED") or suspicion_score <= 60.0:
        return Text(f"⚠️  SUSPICIOUS ({suspicion_score:.1f})", style="bold yellow")
    else:
        return Text(f"🚨 DECEPTIVE ({suspicion_score:.1f})", style="bold white on red")


def get_severity_badge(severity: int) -> Text:
    """Format numeric violation severity (1-5) with colored meter."""
    icons = {1: "●○○○○ (Low)", 2: "●●○○○ (Minor)", 3: "●●●○○ (Moderate)", 4: "●●●●○ (High)", 5: "●●●●● (Critical)"}
    colors = {1: "blue", 2: "cyan", 3: "yellow", 4: "bright_red", 5: "bold red"}
    return Text(icons.get(severity, f"Severity {severity}"), style=colors.get(severity, "white"))
