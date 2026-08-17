---
name: epistemic-benchmark
description: Run the Golden 12 cross-profile evaluation benchmark suite, measure cross-entropy, precision/recall, and verify heuristic alignment across FREE, BALANCED, and ULTRA profiles.
---

# Epistemic Benchmark Suite Skill

Use this skill when evaluating epistemic calibration, measuring cost efficiency, or profiling new LLM models.

## Core Commands
- `just benchmark`: Execute Golden 12 benchmark suite via CLI.
- `poetry run pytest tests/test_benchmark.py -v`: Run hermetic benchmark test suite.
- `credence profile list`: Inspect operational token and reasoning limits across profiles.

## Calibration Standards
- **Golden 12 Scenarios**: 3 ground-truth news, 3 logical fallacy op-eds, 3 deceptive pattern checkouts, 3 satire/parody articles.
- **Cost Profiles**:
  - `FREE`: $0.00 daily spend, 0 thinking tokens, 500-word limit.
  - `BALANCED`: $0.50/day cap, 1,024 thinking tokens, 3,000-word limit.
  - `ULTRA`: $5.00/day cap, 4,096–16,384 thinking tokens, 10,000-word limit.
