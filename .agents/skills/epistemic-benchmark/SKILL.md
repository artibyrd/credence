---
name: epistemic-benchmark
description: Run the Golden 12 cross-profile evaluation benchmark suite, measure cross-entropy, precision/recall, and verify heuristic alignment across FREE, BALANCED, and ULTRA profiles.
---

# Epistemic Benchmark Suite Skill

Use this skill when evaluating epistemic calibration, measuring cost efficiency, or profiling new LLM models.

---

## Core Commands
- `just benchmark`: Execute Golden 12 benchmark suite via CLI.
- `just config-verify`: Probe and validate Dev vs. Prod controlled independent variable configurations.
- `just experiment shadow-audit`: Execute bicameral differential shadow audits calculating $\Delta S$ and FinOps cost curves.
- `just experiment federation-bridge`: Simulate sovereign cross-organization attestation signing, HRW feed partitioning, and $3f+1$ Byzantine isolation.
- `poetry run python -m credence.pipeline.cross_model_benchmark`: Execute live cross-model Pareto benchmark across model tiers and thinking budgets.
- `poetry run pytest tests/test_benchmark.py -v`: Run hermetic benchmark test suite.
- `credence profile list`: Inspect operational token and reasoning limits across profiles.

---

## Bicameral Experimentation & Controlled Independent Variables
When running cross-environment benchmarks or shadow audits, enforce the controlled variable matrix:
- **Dev Tier**: `ECONOMY` / `FREE` profile, $\le 1024$ thinking tokens, SQLite storage, ephemeral keypair.
- **Prod Tier**: `BALANCED` / `ULTRA` profile, $\ge 4096$ thinking tokens, PostgreSQL/S3, sovereign root Ed25519 key.
- **Pre-Flight Invariant**: Always run `just config-verify` before recording official benchmark measurements to ensure zero key collision and verified profile separation.

---

## Empirical Calibration Standards & Pareto Frontier
- **Golden 12 Scenarios**: 3 ground-truth news, 3 logical fallacy op-eds, 3 deceptive pattern checkouts, 3 satire/parody articles.
- **Empirical 4k Thinking Budget Invariant**:
  - `gemini-3.7-flash` with **4,096 thinking tokens** is the optimal Pareto sweet spot ($0.34–$0.68 per 1,000 audits, 2.4s–5.1s latency).
  - Captures 100% citation grounding ($G=1.0$) and Poe's Law satire neutralization ($0.00$ suspicion score).
  - Eliminates the 30x cost overhead ($18.29/1k) and over-analysis penalties ($32.6\text{s}$) of flagship Pro models.
- **Cascaded Bicameral Efficiency**: Filtering benign articles at Dev tier before invoking Prod 4k thinking achieves an **83.3% FinOps cost reduction** ($135/100k $\to$ $22.50/100k).
- **Cost Profiles**:
  - `FREE`: $0.00 daily spend, 0 thinking tokens (offline heuristic baseline).
  - `BALANCED`: $0.50/day cap, 1,024–4,096 thinking tokens (Pareto optimal default).
  - `ULTRA`: $5.00/day cap, 4,096–16,384 thinking tokens for full long-form articles.

