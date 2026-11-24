# Agent Guidelines & Scalable Invariant Architecture for Credence

> **Heuristics**: 1. Check `Justfile` (`just --list`). 2. Zero inline blobs; keep temp scripts outside tracked repos. 3. Append milestones; never overwrite.
> **Skill Overlays**: Before running any generalized skill, check `.agents/overrides/<skill>.md` for Credence overrides and extensions (also actionable standalone on any harness).

---

## 1. Tier 0: Universal Core Invariants

### Class α (Alpha): Sovereign Safety & Authority (P0)
- **`inv-mk1-eyeball` — 🌐 Human Review Gate**: Tags, PR merges, and prod deploys require Mk1 sign-off; verify live Dev deploy (`deploy-dev.yml`).
- **`inv-clean-scratch-scripts` — 🌐 Clean Scratch Scripts**: Zero inline shell blobs (`python -c`, `bash -c`); write temp scripts outside tracked git repos (harness session scratch dir or `/tmp/`).
- **`inv-untrusted-ingestion` — 🌐 Untrusted Ingestion**: Block metadata (`169.254.169.254`) and private IPs; reject XML entities; wrap external text in `<untrusted_source_text>`.
- **`inv-verbatim-anti-truncation` — 🌐 Anti-Truncation**: Citations, forensic logs, and rules match source character-for-character with zero ellipsis (`...`) masking.
- **`inv-sovereign-config-decoupling` — 🌐 Tenant Decoupling**: Core engine, models, and daemons contain zero hardcoded tenant domains; use env vars (`CREDENCE_SENTINEL_FEEDS`) or manifests.

### Class β (Beta): Topology & Lifecycle (P1)
- **`inv-cart-before-horse` — 🌐 Order-of-Operations**: Shared contracts/schemas precede parallel downstream work, and tests pass before walkthroughs or case studies (vertical-slice TDD compatible).
- **`inv-4phase-release-learning` — 🌐 4-Phase Release & Lean Learning Lifecycle**: Local QA → PR Triad/Dev Deploy → Mk1 Review → Merge/Prod Deploy → retrospective → Patch Deploy.
- **`inv-commit-before-deploy` — 🌐 Commit-Before-Deploy**: Clean tree before tags; never push without sign-off; monitor Actions (`gh run watch`).
- **`inv-incremental-commits-staging` — 🌐 Immediate Branching**: Branch upon plan approval (`just branch feat/...`); commit incrementally (`just commit`); open staged PRs (`just pr-create`).
- **`inv-dual-env-least-privilege-cicd` — 🌐 Dual-Environment Least-Privilege CI/CD**: Cloudflare dev deploys use `--branch=dev` previews; prod deploys require signed release tags and review.

### Class γ (Gamma): Ergonomics & Governance (P2)
- **`inv-artifact-curation` — 🌐 Artifact Archival ("That Belongs in a Museum!")**: Never overwrite `implementation_plan.md` or `walkthrough.md`; append Milestone $M+1$.
- **`inv-documentation-expansion` — 🌐 Documentation Expansion**: Deepen canonical docs over shallow files; systematically audit cards for schema drift.
- **`inv-narrative-plot-fidelity` — 🌐 Narrative Plot Fidelity**: Published studies fulfill title promise via a 4-stage narrative arc with zero boilerplate.

---

## 2. Tier 1: Domain Skills (`credence-agent/skills/`) & Overlays (`.agents/overrides/`)
- ☁️ `cloudrun-ops`: Cloud Run compute, 3-plane topology, and WIF.
- 📊 `epistemic-benchmark`: Golden 12 benchmarks, Gemini 4/3.8 `thinkingLevel`, and `just check-models`.
- 🔬 `forensic-audit`: DOM grounding ($G=1.00$), cluster swarms, and topic entropy ($H < 0.30$).
- 🔍 `invariant-audit`: 7-manifest parity, Ed25519 attestations, The Invariant Bible, and RFC standards.
- 🌐 `mesh-cluster`: Watts-Strogatz mesh, node quality ($Q_i$), and Byzantine Sybil defense.
- 🏛️ `white-label-ops`: Sovereign org scaffolding (`credence init-org`) and Terraform.
- 🧩 **Overlays (`.agents/overrides/`)**: `architecture-review`, `knowledge-governance`, `release-lifecycle`, `pr-brief`, `bootstrap-approvals`, `domain-modeling` (optional companion: `antigravity-customizations`).

---

## 3. Tier 2: Shift-Left Automated Gates (`tests/governance/`)
- **Hygiene & Budget**: `<800`-token `AGENTS.md`, demotion guard, zero tracked IDE dotfolders, zero local paths, 1,000-LOC rail, overlay parity.
- **Attestation, Zero-Build & Freshness**: 7-manifest parity, Ed25519 signatures, zero npm, playground mounts, leading H1s, clean slugs, model sunset gate.

---

## 4. Standard Commands (`Justfile`)
- `just check`: Parallel pre-commit QA (`lint` + `test-unit` + `test-docs` + `tf-validate` + `agent-check`).
- `just check-models` / `just sync-overlays`: Offline model sunset check & standalone overlay sync.
- `just branch <name>` / `just commit` / `just pr-create` / `just pr-merge` / `just release`: VCS & release.

*Blueprint: [`docs/invariants.md`](docs/invariants.md) & [`docs/blueprints/invariant-scalability-and-knowledge-governance.md`](docs/blueprints/invariant-scalability-and-knowledge-governance.md).*
