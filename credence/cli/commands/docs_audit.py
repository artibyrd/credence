"""Documentation Self-Auditing and Attestation Engine for Credence.

Command: `credence audit-docs`
Practices what Credence preaches by evaluating and cryptographically signing
its own documentation portal and blog articles.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, List, Optional

from rich.console import Console
from rich.table import Table

from credence.identity import canonical_json_bytes, load_or_create_node_identity
from credence.ingestion.hasher import compute_content_sha256, compute_simhash, normalize_text

console = Console()

CURRENT_VERSION = "v2.1.1"
_HARDCODED_INVARIANT_COUNT_PATTERN = re.compile(r"\b(36|38|39|40)\s+core\s+invariants\b", re.IGNORECASE)


def parse_markdown_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown file content."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1].strip()
    body = parts[2].strip()

    frontmatter = {}
    for line in frontmatter_str.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, val = line.split(":", 1)
            frontmatter[key.strip()] = val.strip().strip("'\"")

    return frontmatter, body


def update_markdown_frontmatter(content: str, updates: dict) -> str:
    """Update or inject YAML frontmatter keys into markdown content."""
    today_str = datetime.date.today().isoformat()
    default_updates = {
        "verified_version": CURRENT_VERSION,
        "last_verified": today_str,
    }
    merged_updates = {**default_updates, **updates}

    if not content.startswith("---"):
        # Prepend new frontmatter
        lines = ["---"]
        for k, v in merged_updates.items():
            lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(content)
        return "\n".join(lines)

    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    fm_lines = parts[1].strip().splitlines()
    existing_keys = set()
    new_fm_lines = []

    for line in fm_lines:
        s_line = line.strip()
        if ":" in s_line and not s_line.startswith("#"):
            key = s_line.split(":", 1)[0].strip()
            existing_keys.add(key)
            if key in merged_updates:
                new_fm_lines.append(f"{key}: {merged_updates[key]}")
            else:
                new_fm_lines.append(line)
        else:
            new_fm_lines.append(line)

    for k, v in merged_updates.items():
        if k not in existing_keys:
            new_fm_lines.append(f"{k}: {v}")

    return "---\n" + "\n".join(new_fm_lines) + "\n---\n\n" + parts[2].lstrip("\r\n")


def audit_single_doc(
    file_path: Path,
    identity: Any,
    update_frontmatter: bool = False,
) -> dict:
    """Audit, score, and sign attestation for a single markdown documentation file."""
    content = file_path.read_text(encoding="utf-8")
    fm, body = parse_markdown_frontmatter(content)

    clean_text = normalize_text(body)
    content_sha = compute_content_sha256(clean_text)
    simhash = compute_simhash(clean_text)

    # Documentation Self-Evaluation Heuristics
    issues: list[str] = []
    title = fm.get("title") or file_path.stem.replace("-", " ").title()

    # 1. Verification of Dynamic Invariant Canon Naming
    for match in _HARDCODED_INVARIANT_COUNT_PATTERN.finditer(body):
        matched_str = match.group(0)
        issues.append(f"Hardcoded invariant count violation: '{matched_str}'. Must reference 'The Invariant Bible'.")

    # 2. Check for missing required frontmatter
    if not fm.get("title"):
        issues.append("Missing required 'title' in frontmatter.")
    if not fm.get("description"):
        issues.append("Missing required 'description' in frontmatter.")

    # 3. Calculate metrics
    content_sha = compute_content_sha256(body)
    simhash = compute_simhash(body)

    suspicion_score = 0.0 if not issues else min(len(issues) * 25.0, 100.0)
    classification = (
        "PRISTINE" if suspicion_score == 0.0 else ("NOTABLE_FLAGS" if suspicion_score <= 50.0 else "SUSPICIOUS")
    )

    doc_url = f"https://docs.credence.run#{file_path.stem}"

    audited_at_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    receipt_signable = {
        "origin_url": doc_url,
        "content_sha256": content_sha,
        "simhash_64": simhash,
        "audited_at": audited_at_iso,
        "suspicion_score": suspicion_score,
        "classification": classification,
    }
    canonical_bytes = canonical_json_bytes(receipt_signable)
    sig_bytes = identity.private_key.sign(canonical_bytes)

    if update_frontmatter:
        new_content = update_markdown_frontmatter(content, {"verified_version": CURRENT_VERSION})
        file_path.write_text(new_content, encoding="utf-8")

    return {
        "file": str(file_path),
        "url": doc_url,
        "title": title,
        "content_sha256": content_sha,
        "simhash_64": simhash,
        "suspicion_score": suspicion_score,
        "classification": classification,
        "issues": issues,
        "receipt": {
            "origin_url": doc_url,
            "content_sha256": content_sha,
            "simhash_64": simhash,
            "audited_at": audited_at_iso,
            "suspicion_score": suspicion_score,
            "classification": classification,
            "node_pubkey": identity.public_key_hex,
            "node_signature": sig_bytes.hex(),
            "verified_version": CURRENT_VERSION,
        },
    }


def cli_audit_docs(
    docs_root: Optional[str] = None,
    files: Optional[List[str]] = None,
    check_only: bool = False,
    update: bool = False,
    lens: str = "surface",
) -> int:
    """Scan documentation files, evaluate epistemic integrity, and mint attestations."""
    root = Path(docs_root) if docs_root else Path("/home/pendragon/Projects/credence-ecosystem/credence-docs")
    if not root.exists():
        # Fallback to local repo docs
        root = Path("docs")

    identity = load_or_create_node_identity()
    target_files: List[Path] = []

    if files:
        for f in files:
            p = Path(f) if Path(f).is_absolute() else (root / f if (root / f).exists() else Path(f))
            if p.exists() and p.suffix == ".md":
                target_files.append(p)
    else:
        # Scan docs and blog directories
        for sub in ["docs", "blog"]:
            sub_dir = root / sub
            if sub_dir.exists():
                target_files.extend(sorted(sub_dir.rglob("*.md")))

    if not target_files:
        console.print("[yellow]No markdown files found to audit.[/yellow]")
        return 0

    results = []
    attestations_manifest = {}
    has_errors = False

    for file_path in target_files:
        res = audit_single_doc(file_path, identity, update_frontmatter=update)
        results.append(res)
        rel_key = str(file_path.relative_to(root)) if file_path.is_relative_to(root) else file_path.name
        attestations_manifest[rel_key] = res["receipt"]
        if res["issues"]:
            has_errors = True

    # Output attestations manifest to assets/attestations.json
    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = assets_dir / "attestations.json"
    manifest_path.write_text(json.dumps(attestations_manifest, indent=2), encoding="utf-8")

    # Render results with 3-Tier Lensing
    if lens == "surface":
        table = Table(title=f"Credence Self-Auditing Dogfood Engine ({CURRENT_VERSION})")
        table.add_column("Document", style="cyan")
        table.add_column("Verdict", style="bold")
        table.add_column("Score", justify="right")
        table.add_column("Status", style="green")

        for r in results:
            verdict_color = "green" if r["suspicion_score"] == 0.0 else "yellow"
            table.add_row(
                r["title"][:40],
                f"[{verdict_color}]{r['classification']}[/{verdict_color}]",
                f"{100.0 - r['suspicion_score']:.1f}",
                "Signed Ed25519",
            )
        console.print(table)
        console.print(
            f"\n[bold green]✓ Scored & signed {len(results)} docs. Attestations saved to {manifest_path}.[/bold green]"
        )
    elif lens == "focus":
        for r in results:
            issues_str = "; ".join(r["issues"]) if r["issues"] else "Clean"
            console.print(
                f"[bold cyan]{r['title']}[/bold cyan] | Score: [green]{100.0 - r['suspicion_score']:.1f}[/green] | Issues: {issues_str}"
            )
    else:  # forensic
        console.print(json.dumps(results, indent=2))

    if check_only and has_errors:
        return 1
    return 0
