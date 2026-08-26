"""Architecture and Code Quality Governance Contract Tests.

Governed by:
- Invariant 1: 500 LOC Ceiling Law
- Invariant 2: Dynamic Invariant Canon
- Invariant 8: Universal 4-Way Feature Parity & compute_* naming ontology
- Invariant 16: Zero-Build Web Invariant
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "credence"


@pytest.mark.unit
def test_500_loc_ceiling_invariant() -> None:
    """Verify that no Python source file in the credence/ package exceeds 500 lines of code."""
    violating_files = []

    # Exclude auto-generated or external data assets
    excluded_rel_paths = {"data"}

    for py_file in SRC_ROOT.rglob("*.py"):
        rel = py_file.relative_to(SRC_ROOT)
        if any(part in excluded_rel_paths for part in rel.parts):
            continue
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        if line_count > 500:
            violating_files.append((str(rel), line_count))

    assert not violating_files, f"Files exceeding 500 LOC ceiling: {violating_files}"


@pytest.mark.unit
def test_compute_naming_ontology_invariant() -> None:
    """Verify that calculation functions adhere strictly to compute_* naming (banning calc_* / calculate_*)."""
    disallowed_prefixes = ("calculate_", "calc_")
    violations = []

    for py_file in SRC_ROOT.rglob("*.py"):
        if "tests" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(node.name.startswith(p) for p in disallowed_prefixes):
                        violations.append((str(py_file.relative_to(SRC_ROOT)), node.name, node.lineno))
        except Exception:
            pass

    assert not violations, f"Functions violating compute_* naming ontology: {violations}"


@pytest.mark.unit
def test_zero_npm_web_surfaces_invariant() -> None:
    """Verify zero npm dependencies or build configurations on web surfaces."""
    web_dir = REPO_ROOT / "web"
    if not web_dir.exists():
        return
    for _root, dirs, files in os.walk(web_dir):
        assert "node_modules" not in dirs, "node_modules directory found in web/"
        assert "package.json" not in files, "package.json found in web/"
        assert "package-lock.json" not in files, "package-lock.json found in web/"


@pytest.mark.unit
def test_workstation_viewport_vertical_bounds_invariant() -> None:
    """Verify that dense workstation card grids use .ws-scroll-pane containers with responsive vertical bounds."""
    report_html_path = REPO_ROOT / "web" / "credence.report" / "index.html"
    if not report_html_path.exists():
        return
    report_html = report_html_path.read_text(encoding="utf-8")
    assert "ws-scroll-pane" in report_html, "Missing .ws-scroll-pane container in credence.report/index.html"
    assert "overflow-y: auto" in report_html or "overflow-y:auto" in report_html
    assert "ws-table-container" in report_html, "Missing .ws-table-container in credence.report/index.html"
