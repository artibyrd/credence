"""Governance unit tests for Tier 2 PR naming & version-bump parity enforcement."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATE_PR_PATH = REPO_ROOT / "scripts" / "validate_pr.py"
MANAGE_PR_PATH = REPO_ROOT.parent / "credence-agent" / "scripts" / "manage_pr.py"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validate_pr_accepts_bumped_feat_and_fix_branches() -> None:
    mod = _load_module("validate_pr", VALIDATE_PR_PATH)

    assert (
        mod.validate_pr(
            branch="feat/gemini-4-support",
            title="[v2.24.0] feat(forensics): add Gemini 4 support",
            branch_version="2.24.0",
            main_version="2.23.0",
        )
        == []
    )
    assert (
        mod.validate_pr(
            branch="fix/v2231-learn-gates",
            title="[v2.23.1] fix(governance): enforce version-bump parity",
            branch_version="2.23.1",
            main_version="2.23.0",
        )
        == []
    )
    assert (
        mod.validate_pr(
            branch="docs/guide-polish",
            title="docs(governance): polish guide 08 prose",
            branch_version="2.23.1",
            main_version="2.23.0",
        )
        == []
    )


@pytest.mark.parametrize(
    ("branch", "title"),
    [
        ("feat/unbumped-feature", "feat(ops): forgot to bump version"),
        ("fix/unbumped-bugfix", "fix(forensics): forgot to bump patch version"),
        ("docs/unbumped-docs", "docs(governance): forgot to bump version"),
        ("ci/unbumped-workflow", "ci(ops): forgot to bump version"),
        ("hotfix/unbumped-hotfix", "fix(ops): urgent hotfix without bump"),
        ("release/v2.23.0", "[v2.23.0] feat(ops): release v2.23.0"),
    ],
)
def test_validate_pr_hard_fails_when_branch_version_equals_main_on_all_branch_types(branch: str, title: str) -> None:
    mod = _load_module("validate_pr", VALIDATE_PR_PATH)

    errors = mod.validate_pr(
        branch=branch,
        title=title,
        branch_version="2.23.0",
        main_version="2.23.0",
    )
    assert any("not bumped above main release version" in err for err in errors)


def test_validate_pr_hard_fails_on_pr_title_manifest_mismatch() -> None:
    mod = _load_module("validate_pr", VALIDATE_PR_PATH)

    errors = mod.validate_pr(
        branch="feat/agy-v234",
        title="[v2.23.0] feat(governance): adopt overlays",
        branch_version="2.22.1",
        main_version="2.22.1",
    )
    assert any("PR title declares v2.23.0, but branch pyproject.toml is at v2.22.1" in err for err in errors)
    assert any("not bumped above main release version" in err for err in errors)


def test_validate_pr_rejects_invalid_branch_and_title_formats() -> None:
    mod = _load_module("validate_pr", VALIDATE_PR_PATH)

    errors = mod.validate_pr(
        branch="random-branch",
        title="wip: bad commit style",
        branch_version="2.23.1",
        main_version="2.23.0",
    )
    assert any("violates naming conventions" in err for err in errors)
    assert any("violates conventional format" in err for err in errors)


def test_validate_pr_cli_main_entrypoint(tmp_path: Path) -> None:
    mod = _load_module("validate_pr", VALIDATE_PR_PATH)
    (tmp_path / "pyproject.toml").write_text('[tool.poetry]\nversion = "2.23.1"\n', encoding="utf-8")

    rc_ok = mod.main(
        [
            "--branch",
            "fix/v2231-learn-gates",
            "--title",
            "[v2.23.1] fix(governance): enforce version-bump parity",
            "--repo-root",
            str(tmp_path),
            "--main-version",
            "2.23.0",
        ]
    )
    assert rc_ok == 0

    rc_fail = mod.main(
        [
            "--branch",
            "fix/v2231-learn-gates",
            "--title",
            "[v2.23.1] fix(governance): enforce version-bump parity",
            "--repo-root",
            str(tmp_path),
            "--main-version",
            "2.23.1",
        ]
    )
    assert rc_fail == 1


def test_manage_pr_triad_version_parity_gate() -> None:
    if not MANAGE_PR_PATH.exists():
        pytest.skip("credence-agent not present in standalone repository CI runner")

    mod = _load_module("manage_pr", MANAGE_PR_PATH)

    # Clean bumped triad passes
    assert (
        mod.validate_triad_version_parity(
            "[v2.23.1] fix(governance): patch gates",
            triad_versions={"credence": "2.23.1", "credence-docs": "2.23.1", "credence-agent": "2.23.1"},
            main_version="2.23.0",
        )
        == []
    )

    # Unbumped triad hard fails
    unbumped = mod.validate_triad_version_parity(
        "fix(governance): forgot bump",
        triad_versions={"credence": "2.23.0", "credence-docs": "2.23.0", "credence-agent": "2.23.0"},
        main_version="2.23.0",
    )
    assert any("not bumped above main release version" in err for err in unbumped)

    # Cross-repo manifest drift hard fails
    drifted = mod.validate_triad_version_parity(
        "[v2.23.1] fix(governance): partial bump",
        triad_versions={"credence": "2.23.1", "credence-docs": "2.23.0", "credence-agent": "2.23.1"},
        main_version="2.23.0",
    )
    assert any("Triad manifest version drift detected" in err for err in drifted)
