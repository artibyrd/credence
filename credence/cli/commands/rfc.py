"""CLI RFC & Standards Governance Command Handlers for Credence (Phase 2).

Provides:
- credence rfc list
- credence rfc show <rfc_id>
- credence rfc validate <path.yaml>
- credence rfc benchmark <path.yaml> --fixtures <fixtures.json>
- credence rfc shadow <rfc_id>
- credence rfc hash <path.yaml>
- credence rfc vote <rfc_id> --approve|--reject
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from credence.identity import canonical_json_bytes, compute_payload_hash, load_or_create_node_identity
from credence.pipeline.rfc import (
    RFCProposal,
    RFCStage,
    RFCVoteAttestation,
    StandardTier,
    compute_byzantine_quorum,
    rfc_registry,
    run_synthetic_benchmark,
    validate_catalog_yaml,
)

console = Console()


def run_rfc_list_command(
    tier: Optional[str] = None, stage: Optional[str] = None, *args: Any, **kwargs: Any
) -> int:
    """List RFC standard proposals with optional tier and stage filtering."""
    tier_map = {
        "general": StandardTier.UNIVERSAL_GENERAL,
        "universal_general": StandardTier.UNIVERSAL_GENERAL,
        "specialist": StandardTier.DOMAIN_SPECIALIST,
        "domain_specialist": StandardTier.DOMAIN_SPECIALIST,
        "niche": StandardTier.SOVEREIGN_NICHE,
        "sovereign_niche": StandardTier.SOVEREIGN_NICHE,
    }

    tier_enum = None
    if tier:
        clean_tier = tier.strip().lower()
        if clean_tier in tier_map:
            tier_enum = tier_map[clean_tier]
        else:
            try:
                tier_enum = StandardTier(tier.upper())
            except ValueError:
                console.print(f"[bold red]Unknown tier:[/bold red] {tier}. Choose from: general, specialist, niche.")
                return 1

    stage_enum = None
    if stage:
        try:
            stage_enum = RFCStage(stage.upper())
        except ValueError:
            console.print(f"[bold red]Unknown stage:[/bold red] {stage}.")
            return 1

    proposals = rfc_registry.list_proposals(tier=tier_enum, stage=stage_enum)

    table = Table(title="Standards RFC Registry (Universal 4-Way Governance)", box=box.ROUNDED)
    table.add_column("RFC ID", style="bold cyan")
    table.add_column("Title", style="white")
    table.add_column("Tier", style="yellow")
    table.add_column("Stage", style="magenta")
    table.add_column("Domain", style="green")
    table.add_column("Version", justify="right")
    table.add_column("SHA-256", style="dim")

    for p in proposals:
        tier_str = (
            "[cyan]Universal General[/cyan]"
            if p.tier == StandardTier.UNIVERSAL_GENERAL
            else "[yellow]Domain Specialist[/yellow]"
            if p.tier == StandardTier.DOMAIN_SPECIALIST
            else "[magenta]Sovereign Niche[/magenta]"
        )
        stage_str = (
            "[bold green]RATIFIED[/bold green]"
            if p.stage == RFCStage.RATIFIED
            else f"[bold yellow]{p.stage.value}[/bold yellow]"
        )
        h_preview = (p.catalog_sha256[:16] + "...") if p.catalog_sha256 else "None"
        table.add_row(p.rfc_id, p.title, tier_str, stage_str, p.target_domain, f"v{p.version}", h_preview)

    console.print(table)
    return 0


def run_rfc_show_command(rfc_id: str, *args: Any, **kwargs: Any) -> int:
    """Display deep details, rules, and vote status of an RFC proposal."""
    clean_id = rfc_id.strip().upper()
    proposal = rfc_registry.get_proposal(clean_id)
    if not proposal:
        console.print(f"[bold red]Error:[/bold red] RFC proposal '{clean_id}' not found in registry.")
        return 1

    console.print(
        Panel(
            f"[bold white]{proposal.title}[/bold white]\n"
            f"[dim]ID:[/dim] {proposal.rfc_id} | [dim]Tier:[/dim] {proposal.tier.value} | [dim]Stage:[/dim] {proposal.stage.value} | [dim]Version:[/dim] v{proposal.version}\n"
            f"[dim]Domain:[/dim] {proposal.target_domain} | [dim]Author:[/dim] {proposal.author}\n"
            f"[dim]SHA-256 Digest:[/dim] [cyan]{proposal.catalog_sha256}[/cyan]\n\n"
            f"[bold]Motivation & Rationale:[/bold]\n{proposal.motivation}",
            title=f"📜 Standard Specification: {proposal.rfc_id}",
            border_style="cyan",
        )
    )

    is_valid, errors, catalog = validate_catalog_yaml(proposal.catalog_yaml)
    if catalog:
        for cluster in catalog.clusters:
            c_table = Table(title=f"Cluster: {cluster.name} ({cluster.cluster_id})", box=box.SIMPLE)
            c_table.add_column("Rule ID", style="bold cyan")
            c_table.add_column("Name", style="white")
            c_table.add_column("Severity", justify="center")
            c_table.add_column("Detection Signals", style="dim")

            for r in cluster.rules:
                signals = "; ".join(r.detection_signals[:2])
                c_table.add_row(r.rule_id, r.name, f"{r.severity}/5", signals)
            console.print(c_table)

    votes = rfc_registry.get_votes(clean_id)
    if votes:
        v_table = Table(title="Recorded Node Attestation Votes", box=box.SIMPLE)
        v_table.add_column("Node Public Key", style="dim")
        v_table.add_column("Vote", style="bold")
        v_table.add_column("Timestamp", style="white")

        for v in votes:
            vote_style = "[green]APPROVE[/green]" if v.vote == "APPROVE" else "[red]REJECT[/red]"
            v_table.add_row(v.node_pubkey[:24] + "...", vote_style, v.timestamp)
        console.print(v_table)

    return 0


def run_rfc_validate_command(yaml_path: str, *args: Any, **kwargs: Any) -> int:
    """Validate a candidate YAML taxonomy catalog file (<0.3s gate)."""
    p = Path(yaml_path)
    if not p.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {yaml_path}")
        return 1

    content = p.read_text(encoding="utf-8")
    is_valid, errors, catalog = validate_catalog_yaml(content)

    if not is_valid or not catalog:
        console.print("[bold red]❌ Validation Failed:[/bold red]")
        for err in errors:
            console.print(f"  • {err}")
        return 1

    total_rules = sum(len(c.rules) for c in catalog.clusters)
    console.print(f"[bold green]✓ Validation Passed ({total_rules} rules across {len(catalog.clusters)} clusters)[/bold green]")
    console.print(f"  [dim]Domain:[/dim] {catalog.domain} | [dim]Version:[/dim] v{catalog.version}")
    console.print(f"  [dim]Catalog SHA-256:[/dim] [cyan]{catalog.catalog_hash}[/cyan]")
    return 0


def run_rfc_hash_command(yaml_path: str, *args: Any, **kwargs: Any) -> int:
    """Compute deterministic RFC 8785 canonical SHA-256 digest of catalog YAML."""
    p = Path(yaml_path)
    if not p.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {yaml_path}")
        return 1

    content = p.read_text(encoding="utf-8")
    is_valid, errors, catalog = validate_catalog_yaml(content)
    if not is_valid or not catalog:
        console.print("[bold red]Cannot hash invalid catalog.[/bold red]")
        for err in errors:
            console.print(f"  • {err}")
        return 1

    console.print(catalog.catalog_hash)
    return 0


def run_rfc_benchmark_command(yaml_path: str, fixtures_path: Optional[str] = None, *args: Any, **kwargs: Any) -> int:
    """Execute the Synthetic Benchmark Gauntlet against test fixtures and Golden Baseline."""
    p = Path(yaml_path)
    if not p.exists():
        console.print(f"[bold red]Error:[/bold red] YAML file not found: {yaml_path}")
        return 1

    content = p.read_text(encoding="utf-8")
    is_valid, errors, catalog = validate_catalog_yaml(content)
    if not is_valid or not catalog:
        console.print("[bold red]Cannot benchmark invalid catalog.[/bold red]")
        return 1

    fixtures = []
    if fixtures_path:
        fp = Path(fixtures_path)
        if fp.exists():
            try:
                fixtures = json.loads(fp.read_text(encoding="utf-8"))
            except Exception as e:
                console.print(f"[bold red]Failed to parse fixtures JSON:[/bold red] {e}")
                return 1

    report = run_synthetic_benchmark(catalog, fixtures)

    table = Table(title="Synthetic Benchmark Gauntlet Scorecard", box=box.ROUNDED)
    table.add_column("Metric", style="white")
    table.add_column("Observed Value", style="bold")
    table.add_column("Required Threshold", style="dim")
    table.add_column("Status", style="bold")

    f1_status = "[green]PASS[/green]" if report.f1_score >= 0.87 else "[red]FAIL[/red]"
    table.add_row("F1 Score", f"{report.f1_score:.4f}", ">= 0.8700", f1_status)

    prec_status = "[green]PASS[/green]" if report.precision >= 0.90 else "[red]FAIL[/red]"
    table.add_row("Precision", f"{report.precision:.4f}", ">= 0.9000", prec_status)

    rec_status = "[green]PASS[/green]" if report.recall >= 0.85 else "[red]FAIL[/red]"
    table.add_row("Recall", f"{report.recall:.4f}", ">= 0.8500", rec_status)

    fpr_status = "[green]PASS[/green]" if report.golden_baseline_fpr == 0.00 else "[red]FAIL[/red]"
    table.add_row("Golden Control FPR", f"{report.golden_baseline_fpr:.4f}", "== 0.0000", fpr_status)

    g_status = "[green]PASS[/green]" if report.grounding_quotient >= 1.00 else "[red]FAIL[/red]"
    table.add_row("Verbatim Grounding (G)", f"{report.grounding_quotient:.2f}", "== 1.00", g_status)

    console.print(table)

    if report.passed_gate:
        console.print("[bold green]✓ Standard Passed Synthetic Benchmark Gauntlet[/bold green]")
        return 0
    else:
        console.print("[bold red]❌ Standard Failed Acceptance Gates[/bold red]")
        return 1


def run_rfc_vote_command(
    rfc_id: str,
    approve: bool = True,
    key_path: Optional[str] = None,
    *args: Any,
    **kwargs: Any,
) -> int:
    """Sign and submit an Ed25519 vote attestation envelope for a candidate RFC."""
    clean_id = rfc_id.strip().upper()
    proposal = rfc_registry.get_proposal(clean_id)
    if not proposal:
        console.print(f"[bold red]Error:[/bold red] RFC proposal '{clean_id}' not found.")
        return 1

    identity = load_or_create_node_identity()
    vote_verdict = "APPROVE" if approve else "REJECT"

    attestation = RFCVoteAttestation(
        rfc_id=clean_id,
        catalog_sha256=proposal.catalog_sha256 or "",
        node_pubkey=identity.public_key_hex,
        vote=vote_verdict,
        metrics={"status": "manual_or_autonomous_node_eval"},
    )

    canonical_bytes = canonical_json_bytes(attestation.get_signable_payload())
    sig_bytes = identity.private_key.sign(canonical_bytes)
    attestation.signature = sig_bytes.hex()

    rfc_registry.record_vote(attestation)
    console.print(f"[bold green]✓ Signed {vote_verdict} attestation envelope for {clean_id}[/bold green]")
    console.print(f"  [dim]Signer Pubkey:[/dim] {identity.public_key_hex[:32]}...")
    console.print(f"  [dim]Signature:[/dim] {attestation.signature[:32]}...")
    return 0
