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

Credence calculates a calibrated **Suspicion Score & Density Index**, eliminates hallucinations via **Grounded Citation Verification**, cryptographically signs evaluations using an **Ed25519 Node Identity**, gossips signed attestations across a **13-Node Heterogeneous P2P Mesh Network**, exposes tools over **FastMCP 2.0**, benchmarks against the **"Golden 12" Epistemic Testbed**, and deploys to **Google Cloud Run** via **Terraform** with strict cost controls ($15/mo budget ceiling, scale-to-zero).

---

## Canonical Domain Infrastructure

The Credence network is anchored across 4 dedicated domains:

| Domain | Role & Purpose | Production Endpoints |
|---|---|---|
| **`credence.run`** | **Primary Canonical Website, MCP Service & CLI Hub** | `https://credence.run`<br/>`https://mcp.credence.run/sse`<br/>`curl -fsSL https://credence.run/install \| sh` |
| **`credence.nexus`** | **P2P Mesh Network & Bootstrap Seed Directory** | `https://seeds.credence.nexus/peers.json`<br/>`wss://relay.credence.nexus:8765`<br/>DNS SRV: `seed.credence.nexus` |
| **`credence.foundation`**| **Taxonomy Governance & Root Key Custody** | `https://taxonomies.credence.foundation/v1/...`<br/>`https://keys.credence.foundation/root.pub` |
| **`credence.report`** | **Public Audit Viewer & Shareable Permalinks** | `https://credence.report/a/{content_sha256}` |

---

## The "Golden 12" Epistemic Benchmark Suite

Credence includes an automated cross-profile benchmark suite that evaluates 12 diverse content scenarios across `FREE`, `BALANCED`, and `ULTRA` profiles:

```bash
# Run the Golden 12 Benchmark Suite
just benchmark
# or
poetry run credence benchmark
```

See the full rubric and expected verdict matrix in 📘 **[Golden 12 Benchmark Suite Documentation](docs/benchmark-suite.md)**.

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

## 13-Node Decentralized Credence Mesh Cluster

Run an isolated 13-node heterogeneous P2P mesh cluster with multi-hop gossip routing ($d = 4$), robust median Bayesian consensus, $f = 4$ Byzantine cartel isolation, and hardware safety governance:

```bash
# Start 13-node mesh cluster with hardware pre-flight check
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

# 6. Export formatted Markdown or JSON audit report
poetry run credence export-report https://example.com/article --format markdown
poetry run credence export-report https://example.com/article --format json -o /tmp/attestation.json

# 7. Cryptographically verify an on-disk attestation JSON file
poetry run credence verify-file /tmp/attestation.json

# 8. Inspect P2P Node Quality Leaderboard ($Q_i$)
poetry run credence rank

# 9. Fetch, generate, and verify signed bootstrap seed manifests
poetry run credence seeds fetch --url https://seeds.credence.nexus/peers.json
poetry run credence seeds generate --output /tmp/seeds.json --valid-hours 24
poetry run credence seeds verify --path /tmp/seeds.json

# 10. Prune older token records and optimize SQLite database
poetry run credence db-clean --retention-days 30

# 11. List registered taxonomy catalogs & rule counts
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
# Run hermetic unit test suite (99 tests, <45s)
just test

# Run code linters and type checkers (Ruff & Mypy)
just lint

# Autoformat code with Ruff
just format

# Run Golden 12 benchmark suite
just benchmark

# Launch interactive Textual TUI
just tui

# Build and test inside Docker container
just docker-build
just docker-test
```

---

## Core Documentation Suite (`/docs`)

- 📘 **[Architecture Overview](docs/architecture.md)**: End-to-end system topology, dual-capture ingestion, multi-agent pipeline, and cryptographic attestation flow.
- 📘 **[The "Golden 12" Benchmark Suite](docs/benchmark-suite.md)**: 12 standardized epistemic evaluation fixtures across Free, Balanced, and Ultra operational cost profiles.
- 📘 **[Operational Cost Profiles](docs/cost-profiles.md)**: Detailed comparison matrix for Free, Balanced, and Ultra operational presets.
- 📘 **[Bootstrap Seeds & Node Quality ($Q_i$)](docs/bootstrap-seeds.md)**: 5-factor node quality scoring, RFC 8785 signed seed files (`peers.json`), and 4-tier discovery fallback.
- 📘 **[Cloud Run Deployment & Terraform](docs/deployment-cloudrun.md)**: Step-by-step GCP operator guide with $15/mo budget cap, scale-to-zero, and Cloud Build CI/CD.
- 📘 **[P2P Mesh Protocol & Consensus](docs/mesh-protocol.md)**: Multi-hop gossip routing, 13-node heterogeneous topology, robust median consensus, and Byzantine Sybil cartel isolation ($f = 4$).
- 📘 **[FastMCP Server & Client Integration](docs/mcp-integration.md)**: FastMCP tool catalogs, dynamic resources, prompts, and Claude Desktop / Antigravity configs.
- 📘 **[Scoring Calibration & Mathematical Rubrics](docs/scoring-calibration.md)**: Mathematical definitions for linear raw suspicion, exponential saturation curves, density indices, and satire neutralization.
- 📘 **[Token Safety Governor & Model Tiering](docs/token-governor.md)**: Token budget safety, Gemini 3.7 Flash thinking token accounting, circuit breaker behavior, and quality gates.
- 📘 **[Multi-Cloud Deployment (GCP + Cloudflare)](docs/deployment-multi-domain.md)**: Operator runbook for Cloud Run, Cloudflare WAF, and zero-egress R2 seed hosting.
- 📘 **[White-Label Mesh Federation Guide](docs/federation-whitelabel.md)**: Turnkey guide to scaffolding sovereign, brand-customized mesh organizations via `credence init-org`.
- 📘 **[Web Frontend Architecture & Zero-Build Invariant](docs/frontend-architecture.md)**: Zero-dependency web standards, native in-browser Web Crypto Ed25519 verification, and Cloudflare edge delivery.
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
├── tests/                     # Hermetic Pytest Suite (144 tests across 4 interfaces, red team & gauntlet)
├── .agents/skills/            # Antigravity Progressive Disclosure Skills (Cluster, Benchmark, White-Label)
├── docs/                      # Architectural Specs, 31 Invariants, Threat Model FAQ & Parity Matrix
├── docker-compose.mesh.yml    # 13-Node Local Mesh Cluster Configuration
├── Dockerfile                 # Multi-stage Container with Python 3.12 + Chromium
├── Justfile                   # Task runner
└── pyproject.toml
```

---

## Documentation & Deep References

- 📘 **[Agent Guidelines & Invariants (31 Invariants)](docs/agent-invariants.md)**
- 📘 **[Skeptic's FAQ & Adversarial Threat Model](docs/faq-adversarial-defense.md)**
- 📘 **[Universal Feature Parity Matrix](docs/feature-parity-matrix.md)**
- 📘 **[Decentralized Architecture Specification](docs/architecture.md)**
- 📘 **[White-Label Federation Operator Guide](docs/federation-whitelabel.md)**
- 📘 **[Multi-Cloud Multi-Domain Infrastructure Guide](docs/deployment-multi-domain.md)**

---

## License
MIT

