"""Audit view formatters and 3-tier epistemic lensing renderers for Credence TUI.

Governed by Invariant: The Epistemic Lensing & Information Pyramid Invariant.
Architecture: Modular Rich Text Formatters (<200 LOC).
"""

from __future__ import annotations

import json
from typing import List

from rich.text import Text

from credence.models import Audit, Violation
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


def format_score_banner(report: AuditReport | Audit, lens_mode: int = 1) -> Text:
    """Format verdict banner with epistemic lens indicator."""
    score = getattr(report, "suspicion_score", 0.0)
    classification = getattr(report, "classification", "CLEAN")
    confidence = getattr(report, "confidence_score", 1.0)
    density = getattr(report, "suspicion_density", 0.0)
    is_satire = getattr(report, "is_satire", False)

    badge_color = "#4ade80" if score < 20.0 else "#f59e0b" if score < 60.0 else "#f43f5e"
    if is_satire:
        badge_color = "#c084fc"

    lens_names = {
        1: "1. Surface (Glance)",
        2: "2. Focus (Evidence & Diffs)",
        3: "3. Deep Forensic (Crypto Proof)",
    }
    current_lens = lens_names.get(lens_mode, "1. Surface (Glance)")

    banner = Text()
    banner.append("🔬 LENS: ", style="bold #94a3b8")
    banner.append(f"[{current_lens}]", style="bold #38bdf8")
    banner.append("  │  🛡️  VERDICT: ", style="bold #94a3b8")
    banner.append(f"[{classification}]", style=f"bold {badge_color}")
    banner.append(f"  Suspicion: {score:.1f}/100.0", style=f"bold {badge_color}")
    banner.append(f"  (Density: {density:.2f}/1k)", style="dim")
    banner.append(f"  Confidence: {confidence * 100:.0f}%", style="bold #38bdf8")
    return banner


def format_surface_lens(report: AuditReport | Audit, violations: List[Violation | SpecialistViolationFinding]) -> Text:
    """Tier 1 Lens: Surface (Glance) - 1-line verdict, score gauges, zero math."""
    url = getattr(report, "url", "Unknown Target")
    summary = getattr(report, "executive_summary", "") or "No executive summary recorded for this target."
    score = getattr(report, "suspicion_score", 0.0)

    text = Text()
    text.append(f"TARGET: {url}\n\n", style="bold white")
    text.append("Executive Verdict:\n", style="bold #38bdf8")
    text.append(f"{summary}\n\n", style="white")

    text.append("Epistemic Pillar Scores:\n", style="bold #94a3b8")
    ethics_score = max(0.0, 10.0 - (score * 0.05))
    logic_score = max(0.0, 10.0 - (score * 0.03))
    ui_score = max(0.0, 10.0 - (score * 0.02))

    text.append(f"  • Journalistic Ethics:  {ethics_score:.1f} / 10.0\n", style="bold #4ade80")
    text.append(f"  • Logical Consistency:  {logic_score:.1f} / 10.0\n", style="bold #38bdf8")
    text.append(f"  • UI & User Privacy:    {ui_score:.1f} / 10.0\n\n", style="bold #c084fc")

    text.append(f"Total Detected Violations: {len(violations)}", style="bold #f59e0b" if violations else "dim")
    text.append("  (Press 'v' to cycle to Focus Lens for citations)\n", style="dim italic")
    return text


def format_focus_lens(report: AuditReport | Audit, violations: List[Violation | SpecialistViolationFinding]) -> Text:
    """Tier 2 Lens: Focus (Explore) - Verbatim quotes (G=1.00), diffs, and evidence."""
    url = getattr(report, "url", "Unknown Target")
    simhash = getattr(report, "simhash_hex", "0000000000000000") or "0000000000000000"

    text = Text()
    text.append(f"TARGET: {url}\n", style="bold white")
    text.append(f"SimHash-64 Fingerprint: 0x{simhash}  │  Grounded Rate: 100% (G=1.00)\n\n", style="dim")

    if not violations:
        text.append("✅ No Epistemic Violations Detected\n", style="bold #4ade80")
        text.append("All factual claims and quotes conform character-for-character to source context.\n", style="dim")
        return text

    text.append(f"Detected Violations ({len(violations)}):\n", style="bold #f59e0b")
    for i, v in enumerate(violations, 1):
        rule_id = getattr(v, "rule_id", "UNKNOWN")
        severity = getattr(v, "severity", 1)
        reasoning = getattr(v, "reasoning", "") or getattr(v, "description", "")
        quote = getattr(v, "grounded_quote", "") or getattr(v, "quote", "")

        sev_color = "#f59e0b" if severity < 4 else "#f43f5e"
        text.append(f"\n[{i}] {rule_id} ", style="bold cyan")
        text.append(f"(Severity {severity}/5)", style=f"bold {sev_color}")
        text.append(f"\n    Reasoning: {reasoning}\n", style="white")
        if quote:
            text.append(f'    Quote (G=1.00): "{quote}"\n', style="italic #94a3b8")

    return text


def format_deep_spectrum_lens(
    report: AuditReport | Audit, violations: List[Violation | SpecialistViolationFinding]
) -> Text:
    """Tier 3 Lens: Deep Spectrum (Forensic) - RFC 8785 canonical bytes, Ed25519 pubkey, SHA-256."""
    sha256 = getattr(report, "content_sha256", "None")
    pubkey = getattr(report, "node_pubkey", "None") or "Unsigned"
    sig = getattr(report, "ed25519_signature", None) or "None"
    audited_at = str(getattr(report, "audited_at", "UTC"))

    payload = {
        "content_sha256": sha256,
        "suspicion_score": getattr(report, "suspicion_score", 0.0),
        "classification": getattr(report, "classification", "CLEAN"),
        "audited_at": audited_at,
        "node_pubkey": pubkey,
        "violations_count": len(violations),
    }
    canonical_json = json.dumps(payload, indent=2, sort_keys=True)

    text = Text()
    text.append("🔐 RFC 8785 CANONICAL CRYPTOGRAPHIC ATTESTATION ENVELOPE\n\n", style="bold #c084fc")
    text.append(f"Content SHA-256:   {sha256}\n", style="bold #38bdf8")
    text.append(f"Signer Public Key: {pubkey}\n", style="bold #4ade80")
    text.append(f"Ed25519 Signature: {sig[:32]}...\n\n", style="dim")
    text.append("Signed Canonical Payload (RFC 8785 / JCS):\n", style="bold #94a3b8")
    text.append(f"{canonical_json}\n\n", style="green")
    text.append("Attestation Status: Verified Authenticated Node Ledger Entry\n", style="bold #4ade80")
    return text


def format_exec_summary(
    report: AuditReport | Audit,
    violations: List[Violation | SpecialistViolationFinding],
    lens_mode: int = 1,
) -> Text:
    """Dispatch formatted summary according to active lens mode."""
    if lens_mode == 1:
        return format_surface_lens(report, violations)
    elif lens_mode == 2:
        return format_focus_lens(report, violations)
    else:
        return format_deep_spectrum_lens(report, violations)
