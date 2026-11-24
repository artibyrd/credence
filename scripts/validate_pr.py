#!/usr/bin/env python3
"""Deterministic PR branch, title, and version-bump parity validator.

Enforces three shift-left Tier 2 invariants on every PR targeting ``main``:
1. Branch naming convention (``release/vX.Y.Z`` or ``(feat|fix|docs|ci|hotfix)/<slug>``).
2. Conventional PR title format (``[vX.Y.Z] <type>(<scope>): <summary>``).
3. Deterministic version-bump parity:
   - Any ``[vX.Y.Z]`` tag in the PR title MUST match ``pyproject.toml``.
   - The branch's ``pyproject.toml`` version MUST be strictly greater than
     ``origin/main``'s version (hard-failing whenever ``branch_version <= main_version``).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

BRANCH_PATTERN = re.compile(r"^(release/v[0-9]+\.[0-9]+\.[0-9]+|(feat|fix|docs|ci|hotfix)/.+)$")
TITLE_PATTERN = re.compile(
    r"^(?:\[v([0-9]+\.[0-9]+\.[0-9]+)\] )?"
    r"(feat|fix|docs|refactor|test|ci|chore|perf)"
    r"(?:\((governance|forensics|mesh|crypto|ui|ops)\))?!?: .+$"
)
SEMVER_PATTERN = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)$")


def parse_semver(version_str: str) -> tuple[int, int, int]:
    """Parse a strict ``X.Y.Z`` (or ``vX.Y.Z``) semantic version string into an integer tuple."""
    match = SEMVER_PATTERN.match(version_str.strip())
    if not match:
        raise ValueError(f"Invalid semantic version: {version_str!r}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def read_pyproject_version(pyproject_text: str) -> str:
    """Extract the package version from ``pyproject.toml`` text."""
    data = tomllib.loads(pyproject_text)
    version = data.get("tool", {}).get("poetry", {}).get("version") or data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Could not locate version in pyproject.toml")
    return version.strip()


def read_git_file(repo_root: Path, git_ref: str, rel_path: str) -> str:
    """Read a file from a git ref via ``git show``."""
    git_bin = shutil.which("git")
    if not git_bin:
        raise RuntimeError("git executable not found on PATH")
    res = subprocess.run(  # noqa: S603
        [git_bin, "show", f"{git_ref}:{rel_path}"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Failed to read {git_ref}:{rel_path}: {res.stderr.strip()}")
    return res.stdout


def validate_pr(
    *,
    branch: str,
    title: str,
    branch_version: str,
    main_version: str,
) -> list[str]:
    """Validate PR branch name, title format, title-to-manifest parity, and version bump.

    Returns a list of human-readable error strings (empty list means valid).
    """
    errors: list[str] = []

    if not BRANCH_PATTERN.match(branch):
        errors.append(
            f'Branch name "{branch}" violates naming conventions. '
            "Allowed formats: release/vX.Y.Z, feat/<slug>, fix/<slug>, docs/<slug>, ci/<slug>, hotfix/<slug>."
        )

    title_match = TITLE_PATTERN.match(title)
    if not title_match:
        errors.append(
            f'PR title "{title}" violates conventional format. '
            "Allowed format: [vX.Y.Z] <type>(<scope>): <imperative summary> "
            "(types: feat, fix, docs, refactor, test, ci, chore, perf; "
            "scopes: governance, forensics, mesh, crypto, ui, ops)."
        )
        title_version: str | None = None
    else:
        title_version = title_match.group(1)

    try:
        branch_tuple = parse_semver(branch_version)
    except ValueError as exc:
        errors.append(f"Branch pyproject.toml version error: {exc}")
        return errors

    try:
        main_tuple = parse_semver(main_version)
    except ValueError as exc:
        errors.append(f"Base main pyproject.toml version error: {exc}")
        return errors

    if title_version is not None and title_version != branch_version:
        errors.append(
            f"PR title declares v{title_version}, but branch pyproject.toml is at v{branch_version}. "
            f"Run 'just sync-version {title_version}' before staging this PR."
        )

    if branch_tuple <= main_tuple:
        errors.append(
            f"Branch version v{branch_version} is not bumped above main release version v{main_version} "
            f"(new work version == current release version). "
            "Run 'just sync-version <next-semver>' and update changelogs before staging this PR."
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Credence PR naming and version-bump parity.")
    parser.add_argument("--branch", default=os.environ.get("HEAD_REF", ""), help="PR head branch name")
    parser.add_argument("--title", default=os.environ.get("PR_TITLE", ""), help="PR title string")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Path to credence repository root")
    parser.add_argument("--main-ref", default="origin/main", help="Git ref for base main branch")
    parser.add_argument("--main-version", default=None, help="Override base main version (for testing)")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    pyproject_path = repo_root / "pyproject.toml"
    branch_version = read_pyproject_version(pyproject_path.read_text(encoding="utf-8"))

    if args.main_version is not None:
        main_version = args.main_version
    else:
        main_pyproject = read_git_file(repo_root, args.main_ref, "pyproject.toml")
        main_version = read_pyproject_version(main_pyproject)

    print(f"Checking branch name    : {args.branch}")
    print(f"Checking PR title       : {args.title}")
    print(f"Branch manifest version : v{branch_version}")
    print(f"Base main version       : v{main_version}")

    errors = validate_pr(
        branch=args.branch,
        title=args.title,
        branch_version=branch_version,
        main_version=main_version,
    )
    if errors:
        for err in errors:
            print(f"❌ Error: {err}", file=sys.stderr)
        return 1

    print("✅ Branch name, PR title, and version-bump parity comply with ecosystem governance standards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
