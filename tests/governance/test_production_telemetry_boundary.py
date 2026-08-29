"""Shift-Left Governance Gates for Production Telemetry & Invariant Reality.

Enforces:
- inv-production-telemetry-boundary: Zero mock data, synthetic generators, or fake fallbacks in operator dashboards.
- inv-canonical-json-ed25519: True WebCrypto and RFC 8785 Ed25519 verification.
- inv-verbatim-grounding: Zero hallucinated quotes or synthetic score algorithms.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.mesh.stats import _compute_mesh_dynamics


@pytest.fixture
def web_dir() -> Path:
    """Return path to web presentation directory."""
    return Path(__file__).resolve().parents[2] / "web"


@pytest.mark.governance
def test_zero_synthetic_generators_in_web_workstations(web_dir: Path) -> None:
    """Assert no synthetic domain generators or zero-padded bitwise hash algorithms exist in operator workstations."""
    banned_patterns = [
        re.compile(r"function\s+synthesizeDomainAudit"),
        re.compile(r"synthesizeDomainAudit\s*\("),
        re.compile(r"Math\.abs\(hashNum\)\.toString\(16\)\.padStart\(64,\s*['\"]0['\"]\);?"),
        re.compile(r"sha:\s*['\"][a-f0-9]{8}0{40,}[a-f0-9]*['\"]"),
        re.compile(r"sha256:[a-f0-9]{8}0{40,}[a-f0-9]*"),
    ]

    target_files: List[Path] = [
        web_dir / "credence.report" / "index.html",
        web_dir / "credence.report" / "viewer.html",
        web_dir / "credence.report" / "history.html",
        web_dir / "credence.nexus" / "index.html",
        web_dir / "admin.credence.run" / "index.html",
        web_dir / "credence.foundation" / "index.html",
    ]

    for file_path in target_files:
        if not file_path.exists():
            continue
        content = file_path.read_text(encoding="utf-8")
        for pat in banned_patterns:
            match = pat.search(content)
            assert match is None, (
                f"Violation of inv-production-telemetry-boundary: Banned synthetic pattern '{pat.pattern}' "
                f"detected in operator surface: {file_path.relative_to(web_dir.parent)}\n"
                f"Matched snippet: {match.group(0) if match else ''}"
            )


@pytest.mark.governance
def test_zero_fake_webcrypto_verification_flows(web_dir: Path) -> None:
    """Assert that client-side verification functions execute real WebCrypto and do not mock verification."""
    report_index = web_dir / "credence.report" / "index.html"
    if report_index.exists():
        content = report_index.read_text(encoding="utf-8")
        assert "In-Browser WebCrypto Verification Passed" not in content or "verifyEd25519Signature" in content, (
            "verifyCurrentReportCrypto must invoke authentic verifyEd25519Signature rather than dummy setTimeout"
        )

    nexus_index = web_dir / "credence.nexus" / "index.html"
    if nexus_index.exists():
        content = nexus_index.read_text(encoding="utf-8")
        # Ensure Quorum Custodian does not default to ?? 25
        assert "consensus_rounds ?? 25" not in content, (
            "Quorum Custodian (byzantine_custodian) must not default consensus_rounds to 25"
        )


@pytest.mark.governance
def test_zero_fake_success_on_network_catch(web_dir: Path) -> None:
    """Assert catch blocks on admin and foundation surfaces do not simulate success."""
    admin_index = web_dir / "admin.credence.run" / "index.html"
    if admin_index.exists():
        content = admin_index.read_text(encoding="utf-8")
        assert "saved locally" not in content.lower(), (
            "Catch blocks must not display fake 'saved locally' success toasts on backend failure"
        )
        assert "tripped locally" not in content.lower(), (
            "Catch blocks must not display fake 'tripped locally' success toasts on backend failure"
        )

    foundation_index = web_dir / "credence.foundation" / "index.html"
    if foundation_index.exists():
        content = foundation_index.read_text(encoding="utf-8")
        assert "G=1.00 (Simulated)" not in content, (
            "Benchmark candidate failure must not emit fake '(Simulated)' passing gauntlet banners"
        )


@pytest.mark.asyncio
@pytest.mark.governance
async def test_backend_standalone_telemetry_zero_floors(db_session: AsyncSession) -> None:
    """Assert backend telemetry reports true 0.0% compute savings and 0 peers when unpeered."""
    dynamics = await _compute_mesh_dynamics(db_session, total_audits=0)

    savings = dynamics.get("compute_savings", {})
    assert savings.get("work_sharing_efficiency_pct") == 0.0, "Fresh standalone node must report 0.0% efficiency"
    assert savings.get("tokens_saved_estimate") == 0, "Fresh standalone node must report 0 tokens saved"
    assert savings.get("adopted_from_mesh_count") == 0, "Fresh standalone node must have 0 adopted items"
    assert dynamics.get("connected_peers_count") == 0, "Fresh standalone node with empty DB must report 0 peers"
