# Credence: Epistemic Trustworthiness Engine & Trust Network

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

**Credence** is an autonomous epistemic evaluation engine, FastMCP server, and decentralized trust network. It captures web snapshots (rendered DOM, visual screenshot, and clean prose) and evaluates them against an **extensible, namespaced taxonomy registry**:

1. **The Society of Professional Journalists (SPJ) Code of Ethics** (`domain: JOURNALISTIC_ETHICS`)
2. **The Internet Encyclopedia of Philosophy (IEP) List of Fallacies** (`domain: LOGICAL_FALLACY`)
3. **Deceptive Patterns Catalog** (`domain: DECEPTIVE_PATTERN`)
4. **Poe's Law Parody & Satire Classification Layer** (`content_type: SATIRE_PARODY` / `is_satire: bool`)
5. **Future Domain Extensions** (`domain: DOMAIN_SPECIFIC`, e.g. medical claims, financial disclosures)

Credence calculates a calibrated **Suspicion Score & Density Index**, eliminates hallucinations via **Grounded Citation Verification**, cryptographically signs evaluations using an **Ed25519 Node Identity**, and protects developer token quotas with an in-database **Token Safety Governor**.

---

## Interactive Textual TUI Workstation

Launch the full-screen terminal workstation with live audit history, interactive grounded citation inspector, reader view, and taxonomy tree:

```bash
just tui
# or
poetry run credence tui
```

### Keybindings in TUI
- **`/`** or **`Ctrl+N`**: Open Audit URL dialog
- **`j` / `k`** or **`↑` / `↓`**: Navigate recent audits and violations table
- **`t`**: Switch to Taxonomy Catalog Explorer tab
- **`k`**: Switch to Token Quota & Headroom tab
- **`i`**: Switch to Node Cryptographic Identity tab
- **`r`**: Refresh data from SQLite database
- **`q`**: Quit

---

## Command-Line Interface (CLI)

```bash
# 1. Audit a webpage live
poetry run credence audit https://example.com/article

# 2. Audit a local fixture file
poetry run credence audit file:///path/to/page.html

# 3. Check live Token Headroom & Safety Budget
poetry run credence quota

# 4. View local Ed25519 node identity and public key
poetry run credence identity show

# 5. Lookup cached audit by URL or content SHA-256
poetry run credence lookup https://example.com/article

# 6. List registered taxonomy catalogs & rule counts
poetry run credence taxonomy list
```

---

## Developer Quickstart

### Prerequisites
- Python 3.12+
- Poetry
- Chromium / Playwright

### Local Setup
```bash
# Install dependencies
poetry install

# Install Playwright browser binaries
poetry run playwright install chromium

# Copy environment template
cp .env.example .env
```

### Task Runner Commands (`Justfile`)
```bash
# Run hermetic unit test suite (49 tests, <2s)
just test

# Run code linters and type checkers (Ruff & Mypy)
just lint

# Autoformat code with Ruff
just format

# Launch interactive Textual TUI
just tui

# Build and test inside Docker container
just docker-build
just docker-test
```

---

## Core Documentation Suite (`/docs`)

- 📘 **[Architecture Overview](docs/architecture.md)**: End-to-end system topology, dual-capture ingestion, multi-agent pipeline, and cryptographic attestation flow.
- 📘 **[Scoring Calibration & Mathematical Rubrics](docs/scoring-calibration.md)**: Mathematical definitions for linear raw suspicion, exponential saturation curves, density indices, and satire neutralization.
- 📘 **[Token Safety Governor & Model Tiering](docs/token-governor.md)**: Token budget safety, Gemini 3.7 Flash thinking token accounting, circuit breaker behavior, and quality gates.
- 📘 **[Agent Invariants & Architectural Rules](docs/agent-invariants.md)**: Strict invariants for human developers and autonomous AI coding agents.

---

## Project Structure

```
├── credence/
│   ├── config.py              # Pydantic Settings & model pricing matrix
│   ├── db.py                  # Async SQLite Engine (WAL Mode)
│   ├── models.py              # SQLModel Schema Definitions & TokenUsageRecord
│   ├── identity.py            # Ed25519 Keypairs & RFC 8785 Canonical JSON Signing
│   ├── taxonomy_loader.py     # Dynamic YAML Taxonomy Discovery & Hash Registry
│   ├── taxonomies/            # Extensible YAML Rule Catalogs
│   │   ├── spj_ethics.yaml
│   │   ├── iep_fallacies.yaml
│   │   └── deceptive_patterns.yaml
│   ├── ingestion/             # Dual-Capture Ingestion & SimHash-64
│   │   ├── extractor.py
│   │   ├── hasher.py
│   │   └── snapshot.py
│   ├── pipeline/              # Multi-Agent Pipeline & Scoring Engine
│   │   ├── governor.py        # TokenBudgetGovernor & Response Quality Gates
│   │   ├── schemas.py         # Pydantic Output Models
│   │   ├── scoring.py         # Calibrated Saturation Scoring
│   │   ├── subagents.py       # Specialist Prompts & Grounded Quote Validator
│   │   └── evaluator.py       # Orchestrator with SQLite Caching
│   ├── cli/                   # Rich Terminal CLI
│   │   └── main.py
│   └── tui/                   # Textual Terminal Workstation
│       └── app.py
├── tests/                     # Hermetic Pytest Suite (49 unit tests)
├── docs/                      # Copious Documentation Suite
├── Dockerfile                 # Multi-stage Container with Python 3.12 + Chromium
├── Justfile                   # Task runner
└── pyproject.toml
```

---

## License
MIT
