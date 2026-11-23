"""Architecture and Code Quality Governance Contract Tests.

Governed by:
- Deep Modules & 1,000-LOC Anti-God-File Safety Rail (~500 LOC soft trigger in architecture-review)
- Dynamic Invariant Canon ("The Invariant Bible")
- Universal 4-Way Feature Parity & compute_* naming ontology
- Zero-Build Web Invariant
- Platform-Agnostic .gemini/ Hygiene & Standalone Skill Overlay Parity
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "credence"
MAX_ANTI_GOD_FILE_LOC = 1000
LOCAL_PATH_PATTERNS = (
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\"),
)
EXPECTED_SKILL_OVERLAYS = (
    "architecture-review.md",
    "bootstrap-approvals.md",
    "domain-modeling.md",
    "knowledge-governance.md",
    "pr-brief.md",
    "release-lifecycle.md",
)


@pytest.mark.unit
def test_500_loc_ceiling_invariant() -> None:
    """Verify no Python or JavaScript source file exceeds the 1,000-LOC anti-god-file safety rail.

    Per D1 (Ousterhout Deep Modules), ~500 LOC is the soft internal decomposition trigger in
    architecture-review, while 1,000 LOC is the hard Tier 2 anti-god-file safety rail.
    """
    violating_files = []

    # Exclude auto-generated or external data assets
    excluded_rel_parts = {"data", ".venv", "node_modules", ".git"}

    # 1. Python source files in credence/
    for py_file in SRC_ROOT.rglob("*.py"):
        rel = py_file.relative_to(SRC_ROOT)
        if any(part in excluded_rel_parts for part in rel.parts):
            continue
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_ANTI_GOD_FILE_LOC:
            violating_files.append((f"credence/{rel}", line_count))

    # 2. JavaScript source files in web/
    web_dir = REPO_ROOT / "web"
    if web_dir.exists():
        for js_file in web_dir.rglob("*.js"):
            rel = js_file.relative_to(web_dir)
            if any(part in excluded_rel_parts for part in rel.parts):
                continue
            line_count = len(js_file.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_ANTI_GOD_FILE_LOC:
                violating_files.append((f"web/{rel}", line_count))

    # 3. JavaScript source files in credence-docs/
    docs_dir = REPO_ROOT.parent / "credence-docs"
    if docs_dir.exists():
        for js_file in docs_dir.rglob("*.js"):
            rel = js_file.relative_to(docs_dir)
            if any(part in excluded_rel_parts for part in rel.parts):
                continue
            line_count = len(js_file.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_ANTI_GOD_FILE_LOC:
                violating_files.append((f"credence-docs/{rel}", line_count))

    assert not violating_files, (
        f"Files exceeding {MAX_ANTI_GOD_FILE_LOC}-LOC anti-god-file safety rail: {violating_files}"
    )


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


@pytest.mark.unit
def test_zero_hardcoded_tenant_domains_in_core_engine() -> None:
    """Verify inv-sovereign-config-decoupling: core engine contains zero hardcoded tenant domains."""
    core_dirs = [
        SRC_ROOT / "db.py",
        SRC_ROOT / "models.py",
        SRC_ROOT / "feeds" / "sentinel.py",
        SRC_ROOT / "server",
        SRC_ROOT / "pipeline",
    ]
    # Proprietary case study / test domains that must NOT be hardcoded as core logic
    forbidden_strings = ["inmaricopa.com", "inmaricopa"]
    violations = []

    for path in core_dirs:
        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = list(path.rglob("*.py"))
        else:
            continue

        for py_file in files:
            content = py_file.read_text(encoding="utf-8")
            for forbidden in forbidden_strings:
                if forbidden in content:
                    violations.append((str(py_file.relative_to(REPO_ROOT)), forbidden))

    assert not violations, (
        f"inv-sovereign-config-decoupling violation: Core engine source files must not contain hardcoded tenant domains: {violations}"
    )


@pytest.mark.unit
def test_5tier_dci_and_monotonic_score_thresholds_parity() -> None:
    """Verify inv-epistemic-lensing: classify_verdict enforces exact monotonic score bands."""
    from credence.pipeline.scoring import classify_verdict

    assert classify_verdict(0.0) == "CLEAN"
    assert classify_verdict(15.0) == "CLEAN"
    assert classify_verdict(15.1) == "LOW_SUSPICION"
    assert classify_verdict(40.0) == "LOW_SUSPICION"
    assert classify_verdict(40.1) == "SUSPICIOUS"
    assert classify_verdict(70.0) == "SUSPICIOUS"
    assert classify_verdict(70.1) == "DECEPTIVE"
    assert classify_verdict(100.0) == "DECEPTIVE"
    assert classify_verdict(50.0, is_satire=True) == "SATIRE_PARODY"


@pytest.mark.unit
def test_workspace_root_scratch_directory_isolation() -> None:
    """Verify inv-clean-scratch-scripts (D2): zero scratch directories inside tracked git repos.

    Temporary scripts must live outside tracked git working trees (e.g., an agent harness's
    session scratch directory or /tmp/), never inside tracked repository directories.
    """
    ecosystem_root = REPO_ROOT.parent
    sub_repos = [REPO_ROOT, ecosystem_root / "credence-docs", ecosystem_root / "credence-agent"]

    violations = [str(repo / "scratch") for repo in sub_repos if (repo / "scratch").exists()]
    assert not violations, (
        f"Scratch directories found inside git repositories: {violations}. "
        "Per inv-clean-scratch-scripts, temporary scratch scripts must live strictly outside "
        "tracked git repositories (e.g., harness session scratch dir or /tmp/)."
    )


@pytest.mark.unit
def test_zero_tracked_vendor_ide_dotfolders() -> None:
    """Verify zero tracked vendor IDE dotfolders (.gemini, .vscode, .cursor, .idea) and .gemini/ ignore rules."""
    ecosystem_root = REPO_ROOT.parent
    repos = [
        REPO_ROOT,
        ecosystem_root / "credence-agent",
        ecosystem_root / "credence-docs",
    ]
    vendor_dirs = [".gemini", ".vscode", ".cursor", ".idea"]
    tracked_violations: list[str] = []
    gitignore_violations: list[str] = []

    for repo in repos:
        if not (repo / ".git").exists():
            continue
        res = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--", *vendor_dirs],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in res.stdout.splitlines():
            if line.strip():
                tracked_violations.append(f"{repo.name}/{line.strip()}")

        gitignore = repo / ".gitignore"
        if not gitignore.is_file():
            gitignore_violations.append(f"{repo.name}/.gitignore is missing")
            continue
        ignore_lines = {
            line.strip()
            for line in gitignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        if ".gemini/" not in ignore_lines and ".gemini" not in ignore_lines:
            gitignore_violations.append(f"{repo.name}/.gitignore does not ignore .gemini/")

    assert not tracked_violations, f"Tracked vendor IDE dotfolder files found: {tracked_violations}"
    assert not gitignore_violations, f"Vendor IDE gitignore hygiene failures: {gitignore_violations}"


@pytest.mark.unit
def test_zero_machine_local_paths_in_governance_files() -> None:
    """Verify zero machine-local paths (/home/<user>/, /Users/<user>/) in governance, plugin, or Justfiles."""
    ecosystem_root = REPO_ROOT.parent
    candidate_files: list[Path] = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "Justfile",
        ecosystem_root / "credence-docs" / "AGENTS.md",
    ]
    just_dir = REPO_ROOT / "just"
    if just_dir.is_dir():
        candidate_files.extend(sorted(just_dir.glob("*.just")))

    agent_dir = ecosystem_root / "credence-agent"
    if agent_dir.is_dir():
        for path in sorted(agent_dir.rglob("*")):
            if not path.is_file():
                continue
            if any(part in {".git", "__pycache__"} for part in path.parts):
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pyc"}:
                continue
            candidate_files.append(path)

    violations: list[str] = []
    for file_path in candidate_files:
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            for pat in LOCAL_PATH_PATTERNS:
                match = pat.search(line)
                if match:
                    rel = file_path.relative_to(ecosystem_root)
                    violations.append(f"{rel}:L{idx} leaks '{match.group(0)}'")

    assert not violations, "Machine-local paths found in tracked governance files:\n" + "\n".join(violations)


@pytest.mark.unit
def test_standalone_skill_overlays_parity() -> None:
    """Verify standalone credence/.agents/overrides/ schema, zero stale .agents/skills/, and SHA-256 parity when credence-agent is present."""
    ecosystem_root = REPO_ROOT.parent
    canonical_dir = ecosystem_root / "credence-agent" / "overrides"
    standalone_dir = REPO_ROOT / ".agents" / "overrides"

    assert standalone_dir.is_dir(), "Standalone overlay directory credence/.agents/overrides/ must exist"

    # Zero stale duplicated .agents/skills/ directories in credence (and sibling repos when present)
    stale_skill_dirs = [
        ecosystem_root / ".agents" / "skills",
        REPO_ROOT / ".agents" / "skills",
        ecosystem_root / "credence-docs" / ".agents" / "skills",
        ecosystem_root / "credence-agent" / ".agents" / "skills",
    ]
    existing_stale = [str(p.relative_to(ecosystem_root)) for p in stale_skill_dirs if p.exists()]
    assert not existing_stale, f"Stale duplicated .agents/skills/ directories must be removed: {existing_stale}"

    # Standalone overlays must never contain SKILL.md
    assert not list(standalone_dir.rglob("SKILL.md")), "credence/.agents/overrides/ must never contain SKILL.md files"

    standalone_files = {p.name: p for p in sorted(standalone_dir.glob("*.md"))}
    missing_standalone = [name for name in EXPECTED_SKILL_OVERLAYS if name not in standalone_files]
    assert not missing_standalone, f"Missing expected overlays in credence/.agents/overrides/: {missing_standalone}"

    required_sections = ("## Overrides", "## Extensions", "## Disabled / Not Applicable")
    schema_errors: list[str] = []

    for name, dst_path in standalone_files.items():
        text = dst_path.read_text(encoding="utf-8")
        for sec in required_sections:
            if sec not in text:
                schema_errors.append(f"credence/.agents/overrides/{name} missing '{sec}'")

    assert not schema_errors, "Standalone overlay schema violations:\n" + "\n".join(schema_errors)

    # When sibling credence-agent repo is checked out, enforce strict SHA-256 parity against canonical overrides
    if not canonical_dir.is_dir():
        return

    assert not list(canonical_dir.rglob("SKILL.md")), "credence-agent/overrides/ must never contain SKILL.md files"

    canonical_files = {p.name: p for p in sorted(canonical_dir.glob("*.md"))}
    missing_canonical = [name for name in EXPECTED_SKILL_OVERLAYS if name not in canonical_files]
    assert not missing_canonical, f"Missing expected overlays in credence-agent/overrides/: {missing_canonical}"

    parity_errors: list[str] = []
    for name, src_path in canonical_files.items():
        text = src_path.read_text(encoding="utf-8")
        for sec in required_sections:
            if sec not in text:
                schema_errors.append(f"credence-agent/overrides/{name} missing '{sec}'")

        dst_path = standalone_dir / name
        if not dst_path.is_file():
            parity_errors.append(f"credence/.agents/overrides/{name} is missing (run 'just sync-overlays')")
            continue
        src_hash = hashlib.sha256(src_path.read_bytes()).hexdigest()
        dst_hash = hashlib.sha256(dst_path.read_bytes()).hexdigest()
        if src_hash != dst_hash:
            parity_errors.append(
                f"credence/.agents/overrides/{name} drifted from credence-agent/overrides/{name} (run 'just sync-overlays')"
            )

    extra_standalone = sorted(set(standalone_files) - set(canonical_files))
    if extra_standalone:
        parity_errors.append(f"Extra stale overlays in credence/.agents/overrides/: {extra_standalone}")

    assert not schema_errors, "Canonical overlay schema violations:\n" + "\n".join(schema_errors)
    assert not parity_errors, "Standalone overlay parity drift:\n" + "\n".join(parity_errors)


TOKENS_PER_WORD = 1.33
MAX_AGENTS_MD_TOKENS = 800


@pytest.mark.unit
def test_agents_md_token_budget_ceiling() -> None:
    """Verify all AGENTS.md files strictly adhere to the < 800 token hard budget ceiling."""
    ecosystem_root = REPO_ROOT.parent
    agents_files = [
        REPO_ROOT / "AGENTS.md",
        ecosystem_root / "AGENTS.md",
        ecosystem_root / "credence-docs" / "AGENTS.md",
        ecosystem_root / "credence-agent" / "rules" / "AGENTS.md",
    ]
    for af in agents_files:
        if not af.exists():
            continue
        content = af.read_text(encoding="utf-8")
        word_count = len(content.split())
        est_tokens = int(word_count * TOKENS_PER_WORD)
        assert est_tokens <= MAX_AGENTS_MD_TOKENS, (
            f"{af.name} is ~{est_tokens} tokens ({word_count} words), exceeding the "
            f"{MAX_AGENTS_MD_TOKENS} token ceiling. Demote test-covered invariants to Tier 2."
        )


@pytest.mark.unit
def test_tier0_invariants_demotion_redundancy() -> None:
    """Verify that Tier 0 in AGENTS.md does not contain invariants already 100% covered by test gates."""
    agents_file = REPO_ROOT / "AGENTS.md"
    content = agents_file.read_text(encoding="utf-8")

    # Demoted invariants that must NOT re-accumulate in Tier 0 prompt context
    demoted_to_test_gates = {
        "inv-living-canon": "test_zero_hardcoded_invariant_counts_in_docs",
        "inv-article-h1-header": "test_all_articles_and_docs_have_leading_h1_title_headers",
        "inv-web-component-isolation": "test_web_component_zero_clone_and_defensive_events",
        "inv-hermetic-unit-tests": "test_hermetic_unit_test_markers_invariant",
        "inv-clean-slug-routing": "test_workstation_and_docs_routing_regression_safeguards",
        "inv-production-telemetry-boundary": "test_zero_mock_production_boundary",
    }

    found_redundant = [slug for slug in demoted_to_test_gates if slug in content]
    assert not found_redundant, (
        f"Redundant test-enforced invariants found in Tier 0: {found_redundant}. "
        f"These rules have 100% mechanical coverage and belong exclusively in Tier 2."
    )
