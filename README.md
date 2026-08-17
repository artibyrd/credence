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

Credence calculates a calibrated **Suspicion Score & Density Index**, eliminates hallucinations via **Grounded Citation Verification**, cryptographically signs evaluations using an **Ed25519 Node Identity**, gossips signed attestations across a **7-Node P2P Mesh Network**, exposes tools over **FastMCP 2.0**, and deploys to **Google Cloud Run** via **Terraform** with strict cost controls ($15/mo budget ceiling, scale-to-zero).

---

## Operational Cost Profiles Mapped to Gemini Tiers

Credence provides 3 preconfigured **Cost Profiles** that dynamically adjust model selection, thinking token budgets, article word limits, and spending caps:

| Feature / Metric | `FREE` (Zero-Cost / Free Tier) | `BALANCED` (Pay-As-You-Go Dev) *(Default)* | `ULTRA` (Gemini Ultra / High Fidelity) |
|---|---|---|---|
| **Target Audience** | Gemini Free Tier (15 RPM / 1M TPM) | Standard Pay-As-You-Go ($0.10/$0.40 per 1M) | Gemini Advanced / Newsroom Desks |
| **Primary Model** | `gemini-2.0-flash-lite` | `gemini-3.7-flash` | `gemini-3.7-flash` + `gemini-1.5-pro` |
| **Thinking Budget** | $0$ tokens | $1,024$ tokens | $4,096$ tokens |
| **Escalation Thinking** | $0$ tokens | $4,096$ tokens | $16,384$ tokens |
| **Daily Spend Cap** | **$0.00 USD** (Strict Zero Spend) | **$0.50 USD/day** | **$15.00 USD/day** |
| **Hourly Token Limit** | 50,000 tokens/hr | 100,000 tokens/hr | 2,000,000 tokens/hr |
| **Daily Token Limit** | 250,000 tokens/day | 1,000,000 tokens/day | 20,000,000 tokens/day |
| **Max Article Words** | 1,500 words | 3,000 words | 10,000 words (deep long-form) |
| **Cloud Run Sizing** | `min=0, max=1, 384Mi` RAM | `min=0, max=2, 512Mi` RAM | `min=0 (or 1), max=5, 1024Mi` RAM |

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

## Model Context Protocol (FastMCP 2.0) Server

Credence natively exposes its multi-agent evaluation pipeline and dynamic taxonomy catalogs over standard MCP transports:

```bash
# 1. Start FastMCP Server on stdio (Antigravity & Claude Desktop)
just serve-stdio
# or
poetry run credence serve --transport stdio

# 2. Start FastMCP Server on SSE / HTTP (Port 8000)
just serve-sse
# or
poetry run credence serve --transport sse --host 0.0.0.0 --port 8000 --profile=balanced
```

### Registered FastMCP Tools
- `credence_check_url`: Audits target webpage, calculates suspicion score, and signs Ed25519 attestation (supports `profile="ultra"`).
- `credence_evaluate_text`: Audits raw prose text directly without web scraping (zero network overhead).
- `credence_get_audit`: Queries cached audits by URL or content SHA-256 in $0$ LLM tokens.
- `credence_verify_attestation`: Cryptographically verifies signed audit reports.
- `credence_get_quota_status`: Returns token headroom %, active cost profile, daily spend, and circuit breaker status.
- `credence_get_consensus`: Calculates Bayesian multi-node consensus across peer attestations.

---

## 7-Node Decentralized Credence Mesh Cluster

Run an isolated 7-node P2P mesh cluster with multi-hop gossip routing and Byzantine Sybil fault tolerance:

```bash
# Start 7-node mesh cluster
just mesh-cluster-up

# View live P2P gossip logs
just mesh-cluster-logs

# Stop cluster
just mesh-cluster-down
```

---

## Command-Line Interface (CLI)

```bash
# 1. Audit a webpage live with a specific profile
poetry run credence audit https://example.com/article --profile=ultra

# 2. List and inspect operational cost profiles
poetry run credence profile list
poetry run credence profile show ultra

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
- Terraform $\ge 1.5.0$ (for Cloud Run deployment)

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
# Run hermetic unit test suite (67 tests, <2s)
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
- 📘 **[Operational Cost Profiles](docs/cost-profiles.md)**: Detailed comparison matrix for Free, Balanced, and Ultra operational presets.
- 📘 **[Cloud Run Deployment & Terraform](docs/deployment-cloudrun.md)**: Step-by-step GCP operator guide with $15/mo budget cap, scale-to-zero, and Cloud Build CI/CD.
- 📘 **[P2P Mesh Protocol & Consensus](docs/mesh-protocol.md)**: Multi-hop gossip routing, 7-node topology, LRU storm suppression, and Byzantine Sybil collusion isolation.
- 📘 **[FastMCP Server & Client Integration](docs/mcp-integration.md)**: FastMCP tool catalogs, dynamic resources, prompts, and Claude Desktop / Antigravity configs.
- 📘 **[Scoring Calibration & Mathematical Rubrics](docs/scoring-calibration.md)**: Mathematical definitions for linear raw suspicion, exponential saturation curves, density indices, and satire neutralization.
- 📘 **[Token Safety Governor & Model Tiering](docs/token-governor.md)**: Token budget safety, Gemini 3.7 Flash thinking token accounting, circuit breaker behavior, and quality gates.
- 📘 **[Agent Invariants & Architectural Rules](docs/agent-invariants.md)**: Strict invariants for human developers and autonomous AI coding agents.

---

## Project Structure

```
├── credence/
│   ├── config.py              # CostProfile presets, Pydantic Settings & pricing matrix
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
│   │   ├── governor.py        # Profile-aware TokenBudgetGovernor & Quality Gates
│   │   ├── schemas.py         # Pydantic Output Models
│   │   ├── scoring.py         # Calibrated Saturation Scoring
│   │   ├── subagents.py       # Specialist Prompts & Grounded Quote Validator
│   │   └── evaluator.py       # Orchestrator with SQLite Caching
│   ├── server/                # FastMCP 2.0 Server (Stdio & SSE)
│   │   └── app.py
│   ├── mesh/                  # P2P Mesh Protocol & Bayesian Consensus
│   │   ├── protocol.py
│   │   ├── relay.py
│   │   └── consensus.py
│   ├── cli/                   # Rich Terminal CLI (Audit, Profile, Quota, Serve, Mesh)
│   │   └── main.py
│   └── tui/                   # Textual Terminal Workstation
│       └── app.py
├── terraform/                 # GCP Cloud Run Infrastructure Suite ($15/mo Cap)
│   ├── main.tf
│   ├── variables.tf
│   ├── cloud_run.tf
│   ├── secret_manager.tf
│   ├── budget.tf
│   ├── monitoring.tf
│   └── outputs.tf
├── cloudbuild.yaml            # Cloud Build CI/CD (Lint -> Test Gate -> Build -> Deploy)
├── tests/                     # Hermetic Pytest Suite (67 unit tests)
├── docs/                      # Copious Documentation Suite
├── docker-compose.mesh.yml    # 7-Node Local Mesh Cluster Configuration
├── Dockerfile                 # Multi-stage Container with Python 3.12 + Chromium
├── Justfile                   # Task runner
└── pyproject.toml
```

---

## License
MIT
