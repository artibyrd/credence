# Credence: Epistemic Trustworthiness Engine & Credence Mesh

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

**Credence** is an isolated, autonomous epistemic evaluation engine, FastMCP server, and decentralized trust network (**Credence Mesh**). It takes snapshots of webpages (DOM, visual screenshot, and clean prose) and evaluates them against an **extensible, namespaced taxonomy registry**:

1. **The Society of Professional Journalists (SPJ) Code of Ethics** (`domain: JOURNALISTIC_ETHICS`)
2. **The Internet Encyclopedia of Philosophy (IEP) List of Fallacies** (`domain: LOGICAL_FALLACY`)
3. **Deceptive Patterns Catalog** (`domain: DECEPTIVE_PATTERN`)
4. **Parody & Satire Classification Layer** (`content_type: SATIRE_PARODY` / `is_satire: bool`)
5. **Future Domain Extensions** (`domain: DOMAIN_SPECIFIC`, e.g., medical claims, financial disclosures, AI provenance)

Credence calculates a calibrated **Suspicion Score & Density Index**, cryptographically signs the results using an **Ed25519 Node Identity**, and enables nodes to share and aggregate evaluations across a **peer-to-peer gossip network (Credence Mesh)** using Bayesian consensus.

---

## Quickstart

### Prerequisites
- Python 3.12+
- Poetry
- Chromium / Playwright (`poetry run playwright install chromium`)

### Local Installation
```bash
# Clone and install dependencies
poetry install

# Install Playwright browser binaries
poetry run playwright install chromium

# Copy environment template
cp .env.example .env
```

### Developer Commands (`Justfile`)
```bash
# Run unit test suite
just test

# Run linting and type checks
just lint

# Start local server
just dev
```

---

## Project Structure
```
├── credence/
│   ├── config.py              # Pydantic Settings
│   ├── db.py                  # Async SQLite Engine (WAL Mode)
│   ├── models.py              # SQLModel Schema Definitions
│   ├── taxonomy_loader.py     # Dynamic YAML Taxonomy Registry
│   ├── taxonomies/            # Extensible YAML Rule Catalogs
│   │   ├── spj_ethics.yaml
│   │   ├── iep_fallacies.yaml
│   │   └── deceptive_patterns.yaml
│   └── ingestion/             # Dual-Capture Web Ingestion & Hasher
│       ├── extractor.py
│       ├── hasher.py
│       └── snapshot.py
├── tests/                     # Hermetic Pytest Suite
├── docs/                      # Comprehensive Architecture & Protocol Specs
├── terraform/                 # GCP Infrastructure (Cloud Run / GCE)
├── Dockerfile                 # Multi-stage Container with Playwright
├── Justfile                   # Task runner
└── pyproject.toml
```

---

## License
MIT
