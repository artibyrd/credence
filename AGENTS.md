# Agent Guidelines & Scalable Invariant Architecture for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

> **Core Operational Heuristics**:
> 1. *When in doubt, check the Justfile (`just --list` or `Justfile`).*
> 2. *The ONLY scratch directory is the workspace root `/scratch/` (zero inline blobs, always output preview links).*
> 3. *Artifacts belong in a museum: never overwrite past phases wholesale; append cumulative milestone sections.*

---

## 1. Tier 0: Universal Core Invariants (Prioritized Cognitive Hierarchy)

### Class α (Alpha): Sovereign Safety, Custody & Human Authority (P0 Non-Negotiables)
- **`inv-mk1-eyeball` — 🌐 Human Review Gate ("Mk1 Eyeball") with Staged PRs & Live Dev Links**: Tags, PR merges, and prod deploys require human Mk1 sign-off. Zero speculative UI additions. Pre-sync version manifests; verify live Dev deployment (`deploy-dev.yml`) and validate routes with automated HTTP probes before requesting review.
- **`inv-clean-scratch-scripts` — 🌐 Workspace Root Scratch Directory & 3-Step Script Ritual**: Zero inline blobs (`python -c`, `bash -c`). The ONLY valid scratch location is workspace root `/scratch/<name>.py` (strictly outside sub-repos, zero in-repo `scratch/` folders). Strictly follow the 3-step ritual: 1. Write script to `/scratch/<name>.py` with Session ID headers $\to$ 2. Output clickable markdown file link in chat $\to$ 3. Run script via `poetry run python scratch/<name>.py`. Archive stale scripts to `/scratch/archive/`.
- **`inv-untrusted-ingestion` — 🌐 Untrusted Ingestion Boundary & Network Defense**: Block cloud metadata (`169.254.169.254`, `metadata.google.internal`), loopback, and private IPs unless `allow_local=True`. Reject `<!DOCTYPE` / `<!ENTITY>`. Wrap LLM inputs in `<untrusted_source_text>`.
- **`inv-verbatim-anti-truncation` — 🌐 Universal Epistemic Verbatim Anti-Truncation UI**: Citations, forensic logs, and system rules must match source character-for-character with zero ellipsis (`...`) masking.
- **`inv-verbatim-grounding` — 🔬 Whitespace-Insensitive Grounding ($G=1.00$)**: Extracted quotes match source DOM character-for-character ($G=1.00$); hallucinations incur an autonomous 50% score slash.
- **`inv-canonical-json-ed25519` — 🔬 RFC 8785 Canonical JSON & Ed25519 Custody**: Envelopes use RFC 8785 canonical bytes with UTC timestamps; payload alterations invalidate Ed25519 verification.
- **`inv-sovereign-config-decoupling` — 🌐 Sovereign Multi-Tenant Decoupling & Zero Hardcoded Tenant Config**: Tenant-specific domains, proprietary feeds, and organization configurations must reside strictly in environment variables (`CREDENCE_SENTINEL_FEEDS`), manifests, or admin APIs. Core engine models, database migrations, scrapers, and daemons must contain zero hardcoded third-party domain favoritism.

### Class β (Beta): Execution Topology, Lifecycle & Release Architecture (P1 Process Boundaries)
- **`inv-cart-before-horse` — 🌐 The Cart-Before-the-Horse Order-of-Operations Invariant**: Prerequisite models and scrubbers must precede downstream APIs, UIs, and tests. Verify tests before drafting case studies.
- **`inv-4phase-release-learning` — 🌐 4-Phase Release & Lean Learning Lifecycle**: 1. Local QA $\rightarrow$ 2. Open PR Triad & Dev Deploy $\rightarrow$ 3. **Mk1 Review (live Dev links)** $\rightarrow$ 4. Merge, Tag (`vX.Y.0`), Prod Deploy $\rightarrow$ 5. `/learn` $\rightarrow$ 6. Autonomous Lean Patch Release (`vX.Y.1`). Must execute patch deploy immediately after learning approval.
- **`inv-commit-before-deploy` — 🌐 Commit-Before-Deploy & Push-and-Delegate CI/CD Gate**: Clean tree before tags. Never push without Mk1 sign-off. Post-push, verify GitHub Actions (`gh run watch`) instead of local deploys.
- **`inv-incremental-commits-staging` — 🌐 Incremental Commits, Immediate Branching & Staging Topology**: Switch to feature branch (`just branch feat/...`) immediately upon plan approval before making changes. Commit incrementally (`just commit <msg>`). Open PRs (`just pr-create`), monitor CI/CD (`gh run watch`), and verify live Dev deployment before updating `walkthrough.md`. Main merges require Code Owner review (`.github/CODEOWNERS`) and deploy to Prod (`credence-prod-505902`).
- **`inv-hermetic-unit-tests` — 🌐 Hermetic Unit Test Isolation & Zero-Browser CI**: Unit tests (`@pytest.mark.unit`) execute in-memory in <35s with zero browser runtimes or daemons.
- **`inv-3plane-governance` — 🌐 3-Plane Deployment Governance**: 3 decoupled planes: **Edge Plane** (`web/`, `credence-docs`), **Compute Plane** (`credence-server`), and **Infra Plane** (Terraform).
- **`inv-dual-env-least-privilege-cicd` — 🌐 Dual-Environment Least-Privilege CI/CD**: Keyless WIF with least-privilege roles. Cloudflare Pages dev deploys use `--branch=dev` (never `main`); dev proxies route to preview endpoints with zero escape to prod.
- **`inv-5factor-node-quality` — 🔬 5-Factor Node Quality ($Q_i$)**: Node reputation evaluates 5 composite factors: $Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$. Bootstrap seeds (`peers.json`) require root Ed25519 verification.

### Class γ (Gamma): Interface Symmetry, Epistemic Parity & Governance (P2 Ergonomics & Presentation)
- **`inv-multi-interface-parity` — 🌐 Universal Multi-Interface Feature Parity**: Feature parity across **CLI**, **FastMCP 2.0**, **TUI**, and **Zero-Build Web UI** (`web/`). Vanilla HTML5/ES modules, **zero npm dependencies**, 5 invariant nav links.
- **`inv-zero-build-standards` — 🌐 Universal Zero-Build Standards (Zero-npm Invariant)**: All public web surfaces use vanilla HTML5, CSS Custom Properties, and native ES Modules with zero npm dependencies and zero build toolchains. Workstations require universal 6px custom scrollbars (`*`, `.tab-panel`) and vertical flex scrolling (`overflow-y: auto; overflow-x: hidden;`).
- **`inv-epistemic-lensing` — 🌐 The Epistemic Lensing & Information Pyramid Invariant**: 3-tier hierarchy: Surface Lens (Glance — zero-jargon score gauge, executive findings & cross-links), Focus Lens (Explore — grounded DOM quotes & diffs), and Deep Spectrum Lens (Forensic — cryptographic signatures, hashes & mathematical formulas). Enforces 5-Tier DCI (A $\ge 90$, B $80-89.9$, C $65-79.9$, D $45-64.9$, E $<45$) and monotonic verdict bands ($\le 15$ Clean, $\le 40$ Low Suspicion, $\le 70$ Suspicious, $> 70$ Deceptive).
- **`inv-artifact-curation` — 🌐 The Artifact Archival & Anti-Wipe Invariant ("That Belongs in a Museum!")**: Artifacts (`implementation_plan.md`, `walkthrough.md`) are permanent historical records. Never overwrite earlier phases or erase previous test tables/proofs wholesale. Append chronological milestone phases (`## Milestone N`) or spawn discrete numbered artifacts (`walkthrough_v2_18_0.md`) to preserve complete session context.
- **`inv-documentation-expansion` — 🌐 Session-Driven Documentation Expansion & Anti-Proliferation Rule**: Deepen canonical docs and blueprints over creating shallow standalone files. Systematically review existing blueprints and invariant cards for schema drift when backend models change.
- **`inv-living-canon` — 🌐 Dynamic Invariant Canon ("The Invariant Bible")**: Reference system invariants as **The Invariant Bible** or **Living Canon of System Invariants** without hardcoded numbers.
- **`inv-multi-model-sovereignty` — 🌐 Multi-Model Sovereignty & Token Budget**: Decoupled LLM adapters (Gemini 3.7 default 4k thinking, Claude 3.7, GPT-4o, DeepSeek R1, Ollama) with offline circuit breakers (`QUOTA_PRESERVED`) at 30% headroom.
- **`inv-production-telemetry-boundary` — 🌐 Production Telemetry vs. Simulation Boundary**: Operator dashboards report genuine node reality ($N \ge 1$, $f = \lfloor (N-1)/3 \rfloor$) with zero mock data; simulators belong exclusively in docs playground.
- **`inv-web-component-isolation` — 🌐 Web Component Isolation & Zero-Clone Invariant**: Web components must never invoke `cloneNode(true)` on host trees containing custom element instances.
- **`inv-topic-entropy-defense` — 🔬 Topic Entropy Astroturfing Defense ($H < 0.30$)**: Combine top-token concentration with Shannon entropy ($H_{\text{penalized}} = H \times (1 - C_{\text{top3}})$). Neutralize satire ($0.00$), invoke `SPJ-1.6` overrides on factual allegations.
- **`inv-fastmcp-datetime-serialization` — 🌐 FastMCP Datetime Serialization**: Standalone text audits persist entities to SQLite and serialize `datetime` to ISO-8601 strings in `.to_dict()`.
- **`inv-clean-slug-routing` — 🌐 Zero-Hash Clean URL Routing & Canonical Slugs**: Slugs reside in pathname with zero `#blog/...` legacy hash cruft; `#hash` is reserved strictly for in-page DOM anchors.
- **`inv-article-h1-header` — 🌐 Anti-Headless Article Invariant**: All articles require leading `# <Title>` matching frontmatter; client parser defensively synthesizes `<h1>` if missing.

---

## 2. Tier 1: Progressive Subsystem Skills (`.agents/skills/`)
- ☁️ [`cloudrun-ops`](.agents/skills/cloudrun-ops/SKILL.md): Cloud Run compute plane, WIF, and Scale-to-Zero Container Cold Start Optimization.
- 🧠 [`knowledge-governance`](.agents/skills/knowledge-governance/SKILL.md): Invariant lifecycle, 4-tier knowledge taxonomy (`/remember`), and `AGENTS.md` context economy (<800 tokens).
- 🔍 [`invariant-audit`](.agents/skills/invariant-audit/SKILL.md): Living Canon audit, token budget verification, 4-phase lifecycle enforcement, and 7-manifest parity.
- 🌐 [`mesh-cluster`](.agents/skills/mesh-cluster/SKILL.md): 13-node Watts-Strogatz mesh simulation, HRW feed hashing, and Byzantine Sybil cartel resistance.
- 🏛️ [`white-label-ops`](.agents/skills/white-label-ops/SKILL.md): Sovereign org scaffolding (`credence init-org`), multi-cloud Terraform, and zero-build multi-domain edge routing.
- 🏛️ [`architecture-governance`](.agents/skills/architecture-governance/SKILL.md): 500 LOC Ceiling Law, `compute_*` naming ontology, and modular subpackage decoupling.
- 📊 [`epistemic-benchmark`](.agents/skills/epistemic-benchmark/SKILL.md): Golden 12 benchmark suite, Expertise-Weighted Consensus Medians, and Galileo Rule.
- 🛡️ [`bootstrap-approvals`](.agents/skills/bootstrap-approvals/SKILL.md): Fresh workspace agent permission bootstrapping, sequential IDE command shape firing, and discrete scope isolation.

---

## 3. Tier 2: Shift-Left Automated Integrity Test Gates (`tests/governance/test_docs_integrity.py`)
- **Attestation & Manifest Parity (Gate 1)**: Asserts all markdown frontmatters match `pyproject.toml` version and verifies all Ed25519 signatures in `attestations.json` over canonical RFC 8785 JSON bytes.
- **Playground DOM Mounts (Gate 2)**: Asserts all 14 interactive playground routes have active DOM mount handlers in `app.js`.
- **CLI Commands & Flags Validity (Gate 3)**: Statically parses documented CLI commands and asserts valid `argparse` registration.
- **Justfile Recipes Parity (Gate 4)**: Statically verifies all documented `just` commands against recipe declarations.
- **Dynamic Living Canon Prohibition (Gate 5)**: Enforces dynamic invariant naming ("The Invariant Bible") with zero hardcoded numbers.
- **Anti-Headless Leading H1 Integrity (Gate 9)**: Asserts all markdown documents begin with an `# <Title>` header matching frontmatter.
- **Invariant Scope & Variable Parity (Gate 10)**: Asserts 100% slug matching, scope classification, and formula variable anatomy across docs, workstation registry, and code.

---

## 4. Standard Task Commands (`Justfile`)
- `just check`: Parallel pre-commit QA gate (<3s: `lint` + `test-unit` + `test-docs` + `tf-validate` + `agent-check`).
- `just status` / `just commit <msg>` / `just branch <name>`: Discrete VCS operations with invariant guardrails.
- `just pr-status` / `just pr-create <title>` / `just pr-merge`: Gated pull request triad lifecycle.
- `just ignite [burst]`: One-command developer onboarding (setup -> preflight -> germinate -> mock test -> doctor).
- `just test-unit` / `just test-docs` / `just test-mock` / `just test-live`: Discrete targeted test suites.
- `just bootstrap-approvals`: Prime fresh workspace command approval cache.
- `just release <version> <message>`: Complete atomic ecosystem release sequence.

*For complete mathematical proofs and architectural blueprints, see 📘 [`docs/invariants.md`](docs/invariants.md) and 🏛️ [`docs/blueprints/invariant-scalability-and-knowledge-governance.md`](docs/blueprints/invariant-scalability-and-knowledge-governance.md).*
