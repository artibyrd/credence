"""Unit tests for RFC & Standards Governance CLI Commands (Phase 2).

Tests:
- credence rfc list
- credence rfc show
- credence rfc validate
- credence rfc hash
- credence rfc benchmark
- credence rfc vote
"""

from pathlib import Path
import pytest

from credence.cli.commands.rfc import (
    run_rfc_benchmark_command,
    run_rfc_hash_command,
    run_rfc_list_command,
    run_rfc_show_command,
    run_rfc_validate_command,
    run_rfc_vote_command,
)


@pytest.mark.unit
def test_cli_rfc_list_command() -> None:
    """Verify run_rfc_list_command executes without errors."""
    code = run_rfc_list_command()
    assert code == 0

    code_tier = run_rfc_list_command(tier="general")
    assert code_tier == 0

    code_invalid = run_rfc_list_command(tier="invalid_tier")
    assert code_invalid == 1


@pytest.mark.unit
def test_cli_rfc_show_command() -> None:
    """Verify run_rfc_show_command returns 0 for known RFCs and 1 for unknown."""
    code = run_rfc_show_command("RFC-001")
    assert code == 0

    code_unknown = run_rfc_show_command("RFC-999")
    assert code_unknown == 1


@pytest.mark.unit
def test_cli_rfc_validate_and_hash_commands(tmp_path: Path) -> None:
    """Verify run_rfc_validate_command and run_rfc_hash_command on valid and invalid files."""
    valid_file = tmp_path / "valid_catalog.yaml"
    valid_file.write_text("""
catalog_id: "sec_disclosures"
domain: "FINANCIAL_DISCLOSURES"
name: "SEC Disclosures"
version: "1.0.0"
description: "Rules auditing SEC disclosures."
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "SEC-1.1"
        name: "Missing 10-K Reconciliation"
        severity: 4
        description: "Missing reconciliation."
        detection_signals:
          - "Signal 1 here"
          - "Signal 2 here"
        evidence_guidelines: "Must quote verbatim."
""", encoding="utf-8")

    code_val = run_rfc_validate_command(str(valid_file))
    assert code_val == 0

    code_hash = run_rfc_hash_command(str(valid_file))
    assert code_hash == 0

    # Non-existent file
    assert run_rfc_validate_command(str(tmp_path / "missing.yaml")) == 1
    assert run_rfc_hash_command(str(tmp_path / "missing.yaml")) == 1


@pytest.mark.unit
def test_cli_rfc_vote_command() -> None:
    """Verify run_rfc_vote_command signs and registers an attestation vote."""
    code = run_rfc_vote_command("RFC-001", approve=True)
    assert code == 0

    code_unknown = run_rfc_vote_command("RFC-UNKNOWN", approve=False)
    assert code_unknown == 1
