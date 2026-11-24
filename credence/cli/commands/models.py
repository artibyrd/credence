"""CLI Model Catalog Freshness & Lifecycle Command Handlers for Credence."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

from credence.config import settings
from credence.pipeline.adapters_base import resolve_provider_key
from credence.pipeline.model_registry import (
    MODEL_REGISTRY,
    ModelAuditIssue,
    audit_model_catalog,
    compute_live_catalog_drift,
    fetch_live_gemini_models,
)

console = Console()


async def run_models_check_command(
    *,
    live: bool = False,
    horizon_days: int = 30,
    json_output: bool = False,
) -> int:
    """Audit active model presets, sunset horizon, pricing parity, harness alignment, and optional live API drift."""
    report = audit_model_catalog(horizon_days=horizon_days)

    if live:
        api_key = resolve_provider_key(
            None,
            "CREDENCE_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "CREDENCE_MODEL_API_KEY",
            setting_fallbacks=(
                settings.CREDENCE_GEMINI_API_KEY,
                settings.GEMINI_API_KEY,
                settings.CREDENCE_MODEL_API_KEY,
            ),
        )
        if not api_key:
            report.live_error = (
                "No Gemini API key configured (set CREDENCE_GEMINI_API_KEY or GEMINI_API_KEY); "
                "skipping live Gemini API catalog probe."
            )
        else:
            try:
                live_models = await fetch_live_gemini_models(api_key)
                new_models, missing_models = compute_live_catalog_drift(live_models)
                report.live_api_checked = True
                report.live_new_models = new_models
                report.live_missing_models = missing_models
                for missing_id in missing_models:
                    report.issues.append(
                        ModelAuditIssue(
                            severity="error",
                            code="LIVE_MODEL_MISSING",
                            subject="Gemini Live API",
                            model_id=missing_id,
                            message=(
                                f"Active profile model '{missing_id}' was not returned by "
                                "Gemini v1beta/models live catalog."
                            ),
                        )
                    )
                for new_id in new_models:
                    report.issues.append(
                        ModelAuditIssue(
                            severity="warning",
                            code="LIVE_NEW_MODEL",
                            subject="Gemini Live API",
                            model_id=new_id,
                            message=f"Newly available Gemini API model discovered: '{new_id}'.",
                        )
                    )
            except Exception as exc:
                report.live_error = str(exc)

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.passed else 1

    console.print("\n[bold cyan]🧭 Credence Model Catalog Lifecycle & Freshness Audit[/bold cyan]")
    console.print(
        f"[dim]Checked On: {report.checked_on.isoformat()} | Sunset Horizon: {report.horizon_days} days[/dim]\n"
    )

    profile_table = Table(title="Active Cost Profile Model Assignments")
    profile_table.add_column("Profile", style="cyan", no_wrap=True)
    profile_table.add_column("Primary Model", style="white")
    profile_table.add_column("Escalation Model", style="white")
    profile_table.add_column("Triage Model", style="white")

    for prof_name, mapping in report.active_profile_models.items():
        profile_table.add_row(
            prof_name.upper(),
            mapping["primary_model"],
            mapping["escalation_model"],
            mapping["triage_model"],
        )
    console.print(profile_table)

    if report.default_models:
        defaults_table = Table(title="Runtime & CLI Default Models")
        defaults_table.add_column("Setting / Surface", style="cyan")
        defaults_table.add_column("Model ID", style="white")
        for label, model_id in report.default_models.items():
            defaults_table.add_row(label, model_id)
        console.print(defaults_table)

    if report.live_api_checked:
        console.print(
            f"\n[bold]Live Gemini API Check:[/bold] "
            f"{len(report.live_new_models)} new model(s), {len(report.live_missing_models)} missing active model(s)."
        )
        if report.live_new_models:
            console.print(f"  [yellow]New models:[/yellow] {', '.join(report.live_new_models)}")
        if report.live_missing_models:
            console.print(f"  [red]Missing models:[/red] {', '.join(report.live_missing_models)}")
    elif report.live_error:
        console.print(f"\n[yellow]⚠️ Live API probe skipped/failed:[/yellow] {report.live_error}")

    errors = [i for i in report.issues if i.severity == "error"]
    warnings = [i for i in report.issues if i.severity == "warning"]

    if errors:
        console.print(f"\n[bold red]❌ Found {len(errors)} blocking catalog error(s):[/bold red]")
        for issue in errors:
            console.print(f"  • [{issue.code}] {issue.message}")
    else:
        console.print(
            "\n[bold green]✅ All active COST_PROFILES and CLI defaults are active, unexpired, priced, and "
            "Antigravity-harness aligned.[/bold green]"
        )

    if warnings:
        console.print(f"[yellow]ℹ️ {len(warnings)} advisory notice(s) detected.[/yellow]")

    return 0 if report.passed else 1


def run_models_list_command(*, json_output: bool = False) -> int:
    """Display the canonical Credence model registry with lifecycle, thinking mode, surfaces, and pricing."""
    rows: List[Dict[str, Any]] = [
        {
            "model_id": spec.model_id,
            "family": spec.family,
            "status": spec.status,
            "thinking_mode": spec.thinking_mode,
            "supported_surfaces": sorted(spec.supported_surfaces),
            "pricing_per_million": dict(spec.pricing_per_million),
            "sunset_date": spec.sunset_date.isoformat() if spec.sunset_date else None,
            "replacement_model": spec.replacement_model,
        }
        for spec in MODEL_REGISTRY.values()
    ]

    if json_output:
        print(json.dumps(rows, indent=2))
        return 0

    table = Table(title="Credence Canonical Model Registry")
    table.add_column("Model ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Thinking", justify="center")
    table.add_column("Pricing ($/1M in/out)", justify="right")
    table.add_column("Surfaces")
    table.add_column("Sunset / Replacement")

    for spec in MODEL_REGISTRY.values():
        status_color = "green" if spec.status == "active" else "yellow" if spec.status == "deprecated" else "red"
        pricing_str = f"${spec.pricing_per_million['prompt']:.3g} / ${spec.pricing_per_million['completion']:.3g}"
        sunset_parts = []
        if spec.sunset_date:
            sunset_parts.append(spec.sunset_date.isoformat())
        if spec.replacement_model:
            sunset_parts.append(f"→ {spec.replacement_model}")
        table.add_row(
            spec.model_id,
            f"[{status_color}]{spec.status}[/{status_color}]",
            spec.thinking_mode,
            pricing_str,
            ", ".join(sorted(spec.supported_surfaces)),
            " ".join(sunset_parts) or "-",
        )

    console.print(table)
    return 0


__all__ = ["run_models_check_command", "run_models_list_command"]
