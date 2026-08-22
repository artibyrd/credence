# Agent Guidelines & Scalable Invariant Architecture for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

---

## 1. Tier 0: Universal Core Invariants (Prioritized Cognitive Hierarchy)

### Class α (Alpha): Sovereign Safety, Custody & Human Authority (P0 Non-Negotiables)
- **`inv-mk1-eyeball` — Human Review Gate ("Mk1 Eyeball") Before Push & Deploy & Explicit Target Version**: `git push`, `git tag`, and cloud deploys strictly require explicit human Mk1 Eyeball approval after `just check`. Declare target Semantic Version (e.g. `v2.6.0`) in all plans and walkthroughs.
- **`inv-verbatim-grounding` — Epistemic Verbatim Grounding ($G=1.00$) & Anti-Hallucination Slashing**: Citations must match source DOM text character-for-character. Hallucinations incur an autonomous 50% score slash.
- **`inv-canonical-json-ed25519` — RFC 8785 Canonical JSON & Ed25519 Custody**: Envelopes use RFC 8785 canonical bytes with UTC timestamps; payload alterations invalidate Ed25519 verification.
- **`inv-untrusted-ingestion` — Untrusted Ingestion Boundary & Network Defense**: Block cloud metadata (`169.254.169.254`, `metadata.google.internal`), loopback, and private IPs unless `allow_local=True`. Reject `<!DOCTYPE` / `<!ENTITY>`. Wrap LLM inputs in `<untrusted_source_text>`.
- **`inv-clean-scratch-scripts` — Clean Scratch Script Approvals for User Readability**: Multi-file scripts requiring user approval (`BypassSandbox: true`) must be written to standalone files (`scratch/<name>.py`).

### Class β (Beta): Execution Topology, Lifecycle & Release Architecture (P1 Process Boundaries)
- **`inv-incremental-commits-staging` — Incremental Commits & Branch-PR Staging Architecture**: Work on feature/milestone branches (`feat/...`, `release/...`) with discrete progress saves. PRs deploy to Dev (`credence-dev-495173`); `main` merges require Code Owner review (`.github/CODEOWNERS`) and deploy to Prod (`credence-prod-505902`) and Edge.
- **`inv-4phase-release-learning` — 4-Phase Release & Lean Learning Lifecycle**: 1. Code & Local QA Gate (`just check`) $\rightarrow$ 2. **User Mk1 Eyeball Review (Mandatory Human Sign-Off Gate)** $\rightarrow$ 3. Milestone Release (`vX.Y.0`) $\rightarrow$ 4. `/learn` Retrospective $\rightarrow$ 5. Lean Patch (`vX.Y.1` on `main` via identical Phase 1 QA $\rightarrow$ Phase 2 Mk1 Eyeball Review).
- **`inv-cart-before-horse` — The Cart-Before-the-Horse Order-of-Operations Invariant**: Prerequisite models and scrubbers must precede downstream APIs, UIs, and tests. Verify tests before drafting case studies.
- **`inv-commit-before-deploy` — Commit-Before-Deploy & Push-and-Delegate with CI/CD Verification Gate**: Clean working tree before tags. Never push without human Mk1 sign-off. Post-push, verify GitHub Actions (`gh run watch` / `just pipeline watch`) instead of local deploys.
- **`inv-3plane-governance` — 3-Plane Deployment Governance**: 3 decoupled planes: **Edge Plane** (`web/`, `credence-docs`), **Compute Plane** (`credence-server`), and **Infra Plane** (Terraform).
- **`inv-dual-env-least-privilege-cicd` — Dual-Environment Least-Privilege CI/CD**: Keyless WIF with `permissions: { id-token: write }`, repo assertions, and least-privilege roles.
- **`inv-hermetic-unit-tests` — Hermetic Unit Test Isolation & Zero-Browser CI**: Unit tests (`@pytest.mark.unit`) execute in-memory in <35s with zero browser runtimes or daemons.

### Class γ (Gamma): Interface Symmetry, Epistemic Parity & Governance (P2 Ergonomics & Presentation)
- **`inv-4way-parity-symmetric-web` — Universal 4-Way Feature Parity & Symmetric Web Invariant**: Feature parity across **CLI**, **FastMCP 2.0**, **TUI**, and **Zero-Build Web UI** (`web/`). Vanilla HTML5/ES modules with **zero npm dependencies**. Navigation has 5 invariant links (`Home`, `Docs`, `Reports`, `Nexus`, `Foundation`).
- **`inv-epistemic-lensing` — The Epistemic Lensing & Information Pyramid Invariant**: 3-tier hierarchy: Surface Lens (Glance — score gauge), Focus Lens (Explore — claims, sparklines), and Deep Spectrum Lens (Forensic — signatures, DOM hash).
- **`inv-documentation-expansion` — Session-Driven Documentation Expansion & Anti-Proliferation Rule**: Deepen canonical docs and blueprints over creating shallow standalone files.
- **`inv-living-canon` — Dynamic Invariant Canon ("The Invariant Bible")**: Reference system invariants as **The Invariant Bible** or **Living Canon of System Invariants** without hardcoded numbers.
- **`inv-multi-model-sovereignty` — Multi-Model Sovereignty & Token Budget**: Decoupled LLM adapters (Gemini 3.7 Flash default 4k thinking budget, Claude 3.7, GPT-4o, DeepSeek R1, Ollama) with offline circuit breakers (`QUOTA_PRESERVED`) at 30% headroom.
- **`inv-production-telemetry-boundary` — Production Telemetry vs. Simulation Boundary**: Operator dashboards report genuine live node reality ($N \ge 1$, $f = \lfloor (N-1)/3 \rfloor$, `STANDALONE` when alone) with zero mock datasets; simulators belong exclusively in docs playground.
- **`inv-web-component-isolation` — Web Component Isolation & Zero-Clone Invariant**: Web components must never invoke `cloneNode(true)` on host trees containing custom element instances.
- **`inv-topic-entropy-astroturfing` — Topic Entropy Astroturfing Defense ($H < 0.30$) & Poe's Law Safeguards**: Combine top-token concentration with Shannon entropy. Neutralize satire ($0.00$), invoke `SPJ-1.6` overrides on factual allegations.
- **`inv-fastmcp-serialization` — FastMCP Text Evaluation & Serialization Parity**: Standalone text audits persist complete `Snapshot`, `Audit`, and `Violation` entities to SQLite and serialize `datetime` to ISO-8601 strings.

---

## 2. Tier 1: Progressive Subsystem Skills (`.agents/skills/`)
- ☁️ [`cloudrun-ops`](.agents/skills/cloudrun-ops/SKILL.md): Cloud Run compute plane, WIF, and Scale-to-Zero Container Cold Start Optimization.
- 🧠 [`knowledge-governance`](.agents/skills/knowledge-governance/SKILL.md): Invariant lifecycle, 4-tier knowledge taxonomy (`/remember`), and `AGENTS.md` context economy (<800 tokens).
- 🔍 [`invariant-audit`](.agents/skills/invariant-audit/SKILL.md): Living Canon audit, token budget verification, 4-phase lifecycle enforcement, and 7-manifest parity.
- 🌐 [`mesh-cluster`](.agents/skills/mesh-cluster/SKILL.md): 13-node Watts-Strogatz mesh simulation, HRW feed hashing, and Byzantine Sybil cartel resistance.
- 🏛️ [`white-label-ops`](.agents/skills/white-label-ops/SKILL.md): Sovereign org scaffolding (`credence init-org`), multi-cloud Terraform, and zero-build multi-domain edge routing.
- 🏛️ [`architecture-governance`](.agents/skills/architecture-governance/SKILL.md): 500 LOC Ceiling Law, `compute_*` naming ontology, and modular subpackage decoupling.
- 📊 [`epistemic-benchmark`](.agents/skills/epistemic-benchmark/SKILL.md): Golden 12 benchmark suite, Expertise-Weighted Consensus Medians, and Galileo Rule.

---

## 3. Tier 2: Shift-Left Automated Integrity Test Gates (`tests/test_docs_integrity.py`)
- **Markdown Frontmatter & Syntax**: Validates YAML frontmatters, code fences, and zero unrendered directives.
- **Zero-npm & Parity**: Enforces zero npm dependencies and 7-manifest version parity across repositories.
- **Sitemap & Deep Links**: Validates route registrations, anchor links, and WCAG high-contrast diagrams.
- **Hermetic Unit Tests & Governance Contracts**: Validates hermetic unit markers and agent governance declarations.

---

## 4. Standard Task Commands (`Justfile`)
- `just check`: Complete pre-commit QA gate (`preflight` -> `lint` -> `test unit` -> `test docs` -> `tf validate` -> `agent-check`).
- `just ignite [burst]`: One-command developer onboarding (setup -> preflight -> germinate -> mock test -> doctor).
- `just test [suite]`: Run targeted test suites (`unit`, `all`, `mock`, `live`, `e2e`, `docs`, `docker`).
- `just lint` / `just format`: Run static analysis, type checking, and Ruff auto-formatting.
- `just serve [transport]`: Launch server engine (`sse`, `stdio`, `web`).
- `just audit-invariants`: Run comprehensive token budget, dynamic naming, and parity audit.
- `just release <version> <message>`: Complete atomic ecosystem release sequence.

*For complete mathematical proofs and architectural blueprints, see 📘 [`docs/invariants.md`](docs/invariants.md) and 🏛️ [`docs/blueprints/invariant-scalability-and-knowledge-governance.md`](docs/blueprints/invariant-scalability-and-knowledge-governance.md).*
