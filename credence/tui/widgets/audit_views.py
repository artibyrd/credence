"""Audit view formatters and panel renderers for Credence TUI."""

from __future__ import annotations

from typing import List

from rich.text import Text

from credence.models import Audit, Violation
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


def format_score_banner(report: AuditReport | Audit, view_mode: str = "rich") -> Text:
    """Format verdict banner text."""
    score = getattr(report, "suspicion_score", 0.0)
    classification = getattr(report, "classification", "CLEAN")
    confidence = getattr(report, "confidence_score", 1.0)
    density = getattr(report, "suspicion_density", 0.0)
    is_satire = getattr(report, "is_satire", False)

    badge_color = "green" if score < 20.0 else "yellow" if score < 60.0 else "red"
    if is_satire:
        badge_color = "magenta"

    banner = Text()
    banner.append("🛡️  VERDICT: ", style="bold")
    banner.append(f"[{classification}]", style=f"bold {badge_color}")
    banner.append(f"  Suspicion Score: {score:.1f}/100.0", style="bold")
    banner.append(f"  Density: {density:.2f}/1k words", style="dim")
    banner.append(f"  Confidence: {confidence * 100:.0f}%", style="cyan")
    return banner


def format_exec_summary(report: AuditReport | Audit, violations: List[Violation | SpecialistViolationFinding]) -> Text:
    """Format executive summary narrative panel."""
    url = getattr(report, "url", "Unknown Target")
    sha256 = getattr(report, "content_sha256", "None")[:16] + "..."
    pubkey = getattr(report, "node_pubkey", "None")
    pubkey_str = (pubkey[:16] + "...") if pubkey else "Unsigned"

    text = Text()
    text.append(f"Target: {url}\n", style="bold white")
    text.append(f"Content SHA-256: {sha256} | Signer Pubkey: {pubkey_str}\n", style="dim")
    text.append(f"Total Violations: {len(violations)}\n", style="bold yellow")
    return text
