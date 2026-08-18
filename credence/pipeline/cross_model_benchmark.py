"""Cross-Model Epistemic & Economic Pareto Benchmark for Credence.

Compares multiple LLM families and thinking token budgets on identical content fixtures using httpx:
1. gemini-3.7-flash (1k thinking budget)
2. gemini-3.7-flash (4k thinking budget)
3. gemini-3.5-flash-lite (fast triage / low cost)
4. gemini-pro-latest (flagship high-parameter reasoning)
5. offline_structural_heuristic ($0.00 baseline)
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx
from rich.console import Console
from rich.table import Table

from credence.ingestion.extractor import extract_clean_content
from credence.pipeline.evaluator import heuristic_evaluate_content
from credence.pipeline.subagents import (
    build_specialist_prompt,
    parse_specialist_response,
    validate_all_violations,
)
from credence.taxonomy_loader import registry

console = Console()

# Pricing constants per 1M tokens (USD)
MODEL_PRICING = {
    "gemini-3.7-flash-1k": {"input": 0.075, "output": 0.30, "thinking": 0.30},
    "gemini-3.7-flash-4k": {"input": 0.075, "output": 0.30, "thinking": 0.30},
    "gemini-3.5-flash-lite": {"input": 0.0375, "output": 0.15, "thinking": 0.00},
    "gemini-pro-latest": {"input": 1.25, "output": 5.00, "thinking": 5.00},
    "offline-heuristic": {"input": 0.00, "output": 0.00, "thinking": 0.00},
}


@dataclass
class ModelEvaluationMetric:
    model_name: str
    scenario: str
    latency_sec: float
    violations_found: int
    grounded_count: int
    grounding_rate: float
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    cost_per_audit_usd: float
    cost_per_1k_usd: float
    verdict: str
    sample_quote: str


async def call_gemini_rest_api(
    client: httpx.AsyncClient,
    api_key: str,
    model_name: str,
    thinking_budget: int,
    prompt: str,
) -> Tuple[str, int, int, int]:
    """Call Google Gemini v1beta REST API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    gen_config: Dict[str, Any] = {
        "temperature": 0.1,
        "responseMimeType": "application/json"
    }
    if thinking_budget > 0:
        gen_config["thinkingConfig"] = {"thinkingBudget": thinking_budget}

    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config
    }

    resp = await client.post(url, json=payload, timeout=45.0)
    if resp.status_code != 200:
        raise ValueError(f"Gemini API {resp.status_code}: {resp.text[:120]}")

    data = resp.json()
    candidates = data.get("candidates", [])
    text = ""
    if candidates and "content" in candidates[0]:
        parts = candidates[0]["content"].get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

    usage = data.get("usageMetadata", {})
    in_tok = usage.get("promptTokenCount", len(prompt) // 4)
    out_tok = usage.get("candidatesTokenCount", len(text) // 4)
    think_tok = usage.get("thoughtsTokenCount", 0)

    return text, in_tok, out_tok, think_tok


async def run_model_benchmark_fixture(
    fixture_path: Path,
    scenario_label: str,
    api_key: str,
    client: httpx.AsyncClient,
) -> List[ModelEvaluationMetric]:
    """Evaluate a single fixture across all candidate model configurations."""
    raw_html = fixture_path.read_text(encoding="utf-8")
    extracted = extract_clean_content(raw_html, url=f"file://{fixture_path.name}")
    registry.load_all()

    results: List[ModelEvaluationMetric] = []

    configs = [
        ("gemini-3.7-flash", 1024, "gemini-3.7-flash-1k"),
        ("gemini-3.7-flash", 4096, "gemini-3.7-flash-4k"),
        ("gemini-3.5-flash-lite", 0, "gemini-3.5-flash-lite"),
        ("gemini-pro-latest", 0, "gemini-pro-latest"),
    ]

    prompt_spj = build_specialist_prompt("spj_ethics", extracted, reg=registry)

    # 1. Offline Heuristic Baseline
    t0 = time.perf_counter()
    heur_findings = heuristic_evaluate_content(extracted, raw_html, reg=registry)
    heur_val = validate_all_violations(heur_findings, raw_text=extracted.clean_text, raw_html=raw_html)
    t_heur = time.perf_counter() - t0
    grounded_heur = sum(1 for v in heur_val if v.is_grounded)
    g_rate_heur = (grounded_heur / len(heur_val)) * 100 if heur_val else 100.0

    results.append(
        ModelEvaluationMetric(
            model_name="offline-heuristic",
            scenario=scenario_label,
            latency_sec=round(t_heur, 4),
            violations_found=len(heur_val),
            grounded_count=grounded_heur,
            grounding_rate=round(g_rate_heur, 1),
            input_tokens=0,
            output_tokens=0,
            thinking_tokens=0,
            cost_per_audit_usd=0.00,
            cost_per_1k_usd=0.00,
            verdict="HEURISTIC",
            sample_quote=heur_val[0].quote_or_element[:40] if heur_val else "None",
        )
    )

    # 2. LLM Candidate Models
    for base_model, budget, config_label in configs:
        t0 = time.perf_counter()
        try:
            raw_resp, in_tok, out_tok, think_tok = await call_gemini_rest_api(
                client, api_key, base_model, budget, prompt_spj
            )
            elapsed = time.perf_counter() - t0
            report = parse_specialist_response(raw_resp, "spj_ethics", reg=registry)
            validated = validate_all_violations(report.violations, raw_text=extracted.clean_text, raw_html=raw_html)
            
            grounded = sum(1 for v in validated if v.is_grounded)
            g_rate = (grounded / len(validated)) * 100 if validated else 100.0

            pricing = MODEL_PRICING.get(config_label, {"input": 0.075, "output": 0.30, "thinking": 0.30})
            cost_audit = (
                (in_tok / 1_000_000) * pricing["input"]
                + (out_tok / 1_000_000) * pricing["output"]
                + (think_tok / 1_000_000) * pricing["thinking"]
            )

            results.append(
                ModelEvaluationMetric(
                    model_name=config_label,
                    scenario=scenario_label,
                    latency_sec=round(elapsed, 3),
                    violations_found=len(validated),
                    grounded_count=grounded,
                    grounding_rate=round(g_rate, 1),
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    thinking_tokens=think_tok,
                    cost_per_audit_usd=round(cost_audit, 6),
                    cost_per_1k_usd=round(cost_audit * 1000, 4),
                    verdict=f"{len(validated)} findings",
                    sample_quote=validated[0].quote_or_element[:40] if validated else "None",
                )
            )
        except Exception as e:
            results.append(
                ModelEvaluationMetric(
                    model_name=config_label,
                    scenario=scenario_label,
                    latency_sec=0.0,
                    violations_found=0,
                    grounded_count=0,
                    grounding_rate=0.0,
                    input_tokens=0,
                    output_tokens=0,
                    thinking_tokens=0,
                    cost_per_audit_usd=0.0,
                    cost_per_1k_usd=0.0,
                    verdict=f"ERR: {str(e)[:25]}",
                    sample_quote="",
                )
            )

    return results


async def run_full_cross_model_benchmark() -> List[ModelEvaluationMetric]:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required.")

    fixtures_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "html"
    if not fixtures_dir.exists():
        fixtures_dir = Path("/home/pendragon/Projects/credence-ecosystem/credence/tests/fixtures/html")

    target_fixtures = [
        ("clean_article.html", "Ground Truth News"),
        ("fallacious_op_ed.html", "Fallacious Op-Ed"),
        ("deceptive_page.html", "Deceptive UX"),
        ("satire_article.html", "Overt Satire"),
    ]

    all_metrics: List[ModelEvaluationMetric] = []

    async with httpx.AsyncClient(timeout=45.0) as client:
        for fixture_name, label in target_fixtures:
            fixture_file = fixtures_dir / fixture_name
            if fixture_file.exists():
                console.print(f"[bold cyan]Auditing Fixture:[/] {label} ({fixture_name})")
                metrics = await run_model_benchmark_fixture(fixture_file, label, api_key, client)
                all_metrics.extend(metrics)

    # Print Summary Table
    table = Table(title="Credence Cross-Model Price-to-Performance Benchmark Matrix")
    table.add_column("Model / Configuration", style="cyan", no_wrap=True)
    table.add_column("Scenario", style="white")
    table.add_column("Latency (s)", justify="right")
    table.add_column("Violations", justify="right")
    table.add_column("Grounding %", justify="right", style="green")
    table.add_column("Thinking Tok", justify="right")
    table.add_column("Cost / 1k ($)", justify="right", style="yellow")

    for m in all_metrics:
        table.add_row(
            m.model_name,
            m.scenario,
            f"{m.latency_sec:.2f}s",
            str(m.violations_found),
            f"{m.grounding_rate:.1f}%",
            str(m.thinking_tokens),
            f"${m.cost_per_1k_usd:.4f}",
        )

    console.print(table)
    return all_metrics


if __name__ == "__main__":
    asyncio.run(run_full_cross_model_benchmark())
