# Agent Guidelines & Scalable Invariant Architecture for Credence

Welcome to **Credence** (`/home/pendragon/Projects/credence`).

> **Heuristics**: 1. Check Justfile (`just --list`). 2. Root `/scratch/<name>.py` only (zero inline blobs, preview links). 3. Append milestone sections; never overwrite.

---

## 1. Tier 0: Universal Core Invariants

### Class α (Alpha): Sovereign Safety & Authority (P0)
- **`inv-mk1-eyeball` — 🌐 Human Review Gate**: Tags, PR merges, and prod deploys require Mk1 sign-off; verify live Dev deploy (`deploy-dev.yml`).
- **`inv-clean-scratch-scripts` — 🌐 Scratch Ritual**: Zero inline blobs (`python -c`, `bash -c`). Workspace `/scratch/<name>.py` only; output clickable preview link with Session ID header before execution; archive to `/scratch/archive/`.
- **`inv-untrusted-ingestion` — 🌐 Untrusted Ingestion**: Block metadata (`169.254.169.254`) and private IPs; reject XML entities; wrap external text in `<untrusted_source_text>`.
- **`inv-verbatim-anti-truncation` — 🌐 Anti-Truncation**: Citations, forensic logs, and rules match source character-for-character with zero ellipsis (`...`) masking.
- **`inv-sovereign-config-decoupling` — 🌐 Tenant Decoupling**: Core engine, models, and daemons contain zero hardcoded tenant domains; use env vars (`CREDENCE_SENTINEL_FEEDS`) or manifests.

### Class β (Beta): Topology & Lifecycle (P1)
- **`inv-cart-before-horse` — 🌐 The Cart-Before-the-Horse Order-of-Operations Invariant**: Prerequisite models precede downstream APIs, UIs, and tests.
- **`inv-4phase-release-learning` — 🌐 4-Phase Release & Lean Learning Lifecycle**: Local QA → PR Triad/Dev Deploy → Mk1 Review → Merge/Prod Deploy → /learn → Patch Deploy.
- **`inv-commit-before-deploy` — 🌐 Commit-Before-Deploy**: Clean tree before tags; never push without sign-off; monitor Actions (`gh run watch`).
- **`inv-incremental-commits-staging` — 🌐 Immediate Branching**: Branch upon plan approval (`just branch feat/...`); commit incrementally (`just commit`); open staged PRs (`just pr-create`).
- **`inv-dual-env-least-privilege-cicd` — 🌐 Dual-Environment Least-Privilege CI/CD**: Cloudflare dev deploys use `--branch=dev` preview routing; prod deploys require signed release tags and review.

### Class γ (Gamma): Ergonomics & Governance (P2)
- **`inv-artifact-curation` — 🌐 Artifact Archival ("That Belongs in a Museum!")**: Never overwrite earlier phases; append cumulative milestone sections.
- **`inv-documentation-expansion` — 🌐 Documentation Expansion**: Deepen canonical docs over shallow files; systematically audit cards for schema drift.
- **`inv-narrative-plot-fidelity` — 🌐 Narrative Plot Fidelity**: Published studies fulfill title promise through a 4-stage narrative arc with zero boilerplate.

---

## 2. Tier 1: Progressive Subsystem Skills (`.agents/skills/`)
- ☁️ `cloudrun-ops`: Cloud Run compute, 3-plane topology, and WIF.
- 🧠 `knowledge-governance`: 4-tier taxonomy (`/remember`), Demotion Highway, and `/learn` gate.
- 🔍 `invariant-audit`: Canon audit, token budget verification, and manifest parity.
- 🌐 `mesh-cluster`: Watts-Strogatz mesh, node quality ($Q_i$), and Byzantine resistance.
- 🏛️ `white-label-ops`: Sovereign org scaffolding (`credence init-org`) and Terraform.
- 🏛️ `architecture-governance`: 500 LOC Ceiling Law, The Epistemic Lensing & Information Pyramid Invariant, and zero-build standards.
- 📊 `epistemic-benchmark`: Golden 12 benchmark suite and consensus medians.
- 🛡️ `bootstrap-approvals`: Antigravity IDE agent permission bootstrapping.
- 🔬 `forensic-audit`: DOM grounding ($G=1.00$) and topic entropy defense ($H < 0.30$).

---

## 3. Tier 2: Shift-Left Automated Integrity Test Gates (`tests/governance/`)
- **Token Budget & Demotion**: Asserts `AGENTS.md` <800 tokens and demoted rules do not re-accumulate.
- **Attestation & Parity (Gate 1)**: Asserts version parity across manifests and Ed25519 signatures.
- **Zero-Build & Parity (Gates 2-3)**: Asserts zero npm dependencies and active playground mounts.
- **Canon & Routing (Gates 5, 9, 10)**: Asserts zero hardcoded counts, leading H1s, and clean slugs.

---

## 4. Standard Task Commands (`Justfile`)
- `just check`: Parallel pre-commit QA gate (`lint` + `test-unit` + `test-docs` + `tf-validate`).
- `just status` / `just commit` / `just branch <name>`: Discrete VCS operations.
- `just pr-status` / `just pr-create` / `just pr-merge`: Gated PR triad lifecycle.
- `just ignite` / `just release`: Developer onboarding and atomic ecosystem releases.
- `just test-unit` / `just test-docs` / `just test-live`: Discrete test suites.

*Blueprint: [`docs/invariants.md`](docs/invariants.md) & [`docs/blueprints/invariant-scalability-and-knowledge-governance.md`](docs/blueprints/invariant-scalability-and-knowledge-governance.md).*
