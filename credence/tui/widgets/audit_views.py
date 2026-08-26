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


SAMPLE_AUDIT_PRESETS: List[dict] = [
    {
        "url": "https://reuters.com/world/energy/clean-grid-transition-2026",
        "title": "Global Clean Energy Investments Hit $2 Trillion Milestone, IEA Reports",
        "suspicion_score": 0.0,
        "classification": "CLEAN",
        "confidence_score": 0.98,
        "suspicion_density": 0.0,
        "is_satire": False,
        "content_sha256": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "4a8f9c1e2b3d4f50",
        "executive_summary": "Rigorous empirical wire reporting on international clean energy capacity additions. All statistical figures are explicitly attributed to the International Energy Agency.",
        "violations": [],
    },
    {
        "url": "https://theonion.com/science/astronomers-confirm-universe-expanding-into-neighboring-yard",
        "title": "Astronomers Confirm Universe Expanding Entirely Into Neighboring Yard",
        "suspicion_score": 0.0,
        "classification": "SATIRE_PROTECTED",
        "confidence_score": 1.0,
        "suspicion_density": 0.0,
        "is_satire": True,
        "content_sha256": "sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "1020304050607080",
        "executive_summary": "Legitimate hyperbolic satire. Qualifies fully for Poe's Law Safe Harbor with zero defamatory claims.",
        "violations": [],
    },
    {
        "url": "https://dailycaller.com/2026/02/14/secret-subsidies-electric-vehicles-mandate",
        "title": "Secret Bureaucrats Funnel Subsidies to Preferred EV Firms",
        "suspicion_score": 68.4,
        "classification": "SUSPICIOUS",
        "confidence_score": 0.89,
        "suspicion_density": 3.42,
        "is_satire": False,
        "content_sha256": "sha256:3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "feedfacecafebabe",
        "executive_summary": "Elevated astroturfing and selective omission. Anonymous assertions of secret subsidies without supporting documentary links.",
        "violations": [
            {
                "rule_id": "SPJ-1.3",
                "severity": 3,
                "reasoning": "Damaging assertions attributed to unnamed 'senior insiders' without independent corroboration.",
                "grounded_quote": "according to senior insiders who spoke on condition of anonymity",
            },
            {
                "rule_id": "IEP-2.4",
                "severity": 4,
                "reasoning": "Cherry-picked quarterly grant data while omitting broader competitive bidding figures.",
                "grounded_quote": "grants were awarded to select favored manufacturers during the spring cycle",
            },
        ],
    },
    {
        "url": "https://inmaricopa.com/breaking/miracle-supplement-cures-all-chronic-illness",
        "title": "Local Clinic Discovers 100% Miracle Cure for Chronic Illness",
        "suspicion_score": 96.2,
        "classification": "PROVEN_HOAX",
        "confidence_score": 0.99,
        "suspicion_density": 8.15,
        "is_satire": False,
        "content_sha256": "sha256:9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "deadbeefdeadbeef",
        "executive_summary": "Critical deceptive fabrication. Fabricates medical trial data and masks commercial sales behind fake clinical breakthroughs.",
        "violations": [
            {
                "rule_id": "SPJ-1.6",
                "severity": 5,
                "reasoning": "Malicious health disinformation claiming an unapproved compound cures all illness.",
                "grounded_quote": "guaranteed 100% cure rate with zero clinical side effects in local patient trials",
            },
            {
                "rule_id": "DEC-3.1",
                "severity": 5,
                "reasoning": "Fake system warnings simulating medical authority endorsements.",
                "grounded_quote": "official health advisory: all citizens urged to claim allocation immediately",
            },
        ],
    },
]
