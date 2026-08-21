# Agent Guidelines & Scalable Invariant Architecture for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

---

## 1. Tier 0: Universal Core Invariants (Prioritized Cognitive Hierarchy)
*Strict, zero-tolerance guardrails categorized by failure severity and cognitive criticality.*

### Class α (Alpha): Sovereign Safety, Custody & Human Authority (P0 Non-Negotiables)
- **`inv-mk1-eyeball` — Human Review Before Commits ("Mk1 Eyeball") & Explicit Target Version in Plans/Walkthroughs**: Never execute `git commit` automatically. Always present changes, live verification results, and explicitly declare the target Semantic Version (e.g. `v2.3.0`) in all implementation plans, task outlines, and walkthrough documents.
- **`inv-verbatim-grounding` — Epistemic Verbatim Grounding ($G=1.00$) & Anti-Hallucination Slashing**: Citations must match source DOM text character-for-character after whitespace collapse. Hallucinations incur an autonomous 50% reputation score slash.
- **`inv-canonical-json-ed25519` — RFC 8785 Canonical JSON & Ed25519 Custody**: Cryptographic envelopes must use RFC 8785 canonical bytes with UTC timestamps. Any alteration to signed payload fields (`suspicion_score`, `classification`, `content_sha256`) immediately invalidates Ed25519 verification.
- **`inv-untrusted-ingestion` — Untrusted Ingestion Boundary & Network Defense**: Reject cloud metadata (`169.254.169.254`, `metadata.google.internal`), loopback (`127.0.0.1`), and RFC 1918 private subnets unless running hermetic local fixtures (`allow_local=True`). XML parsers must reject `<!DOCTYPE` / `<!ENTITY>` declarations (Billion Laughs defense). External LLM inputs must be enclosed in `<untrusted_source_text>` containers.
- **`inv-clean-scratch-scripts` — Clean Scratch Script Approvals for User Readability**: When executing programmatic multi-file edits or complex scripts requiring user approval (`BypassSandbox: true`), never pass dense, unreadable inline scripts (`python3 -c "..."`) with escaped quotes or multiline strings in approval dialogs. Always write clean, well-formatted standalone python scripts to `scratch/<script_name>.py` and execute `python3 <scratch_script_path>` to ensure immediate, effortless user readability and Mk1 eyeball review.

### Class β (Beta): Execution Topology, Lifecycle & Release Architecture (P1 Process Boundaries)
- **`inv-incremental-commits-staging` — Incremental Commits & Branch-PR Staging Architecture**: All active development executes on feature/milestone branches (`feat/...`, `release/...`). Changes must be committed incrementally as discrete, tested units throughout sessions with Mk1 Eyeball approval, eliminating massive session-end release commits. Opening or pushing to a Pull Request automatically deploys to Cloud Run Dev (`credence-dev-495173`); merging to `main` is strictly gated by authorized Code Owner reviews (`.github/CODEOWNERS`) and triggers automated Cloud Run Prod (`credence-prod-505902`) and Cloudflare Edge deployments.
- **`inv-4phase-release-learning` — 4-Phase Release & Learning Lifecycle**: Ecosystem delivery strictly follows the sequential progression: 1. Code & Local QA Gate $\rightarrow$ 2. User Mk1 Eyeball Review $\rightarrow$ 3. Feature Version Release $\rightarrow$ 4. `/learn` Retrospective $\rightarrow$ 5. Apply Lessons as Immediate Patch Release (e.g. `vX.Y.0` $\rightarrow$ `vX.Y.1`).
- **`inv-cart-before-horse` — The Cart-Before-the-Horse Order-of-Operations Invariant**: Every implementation plan, task breakdown, and execution sequence must undergo a strict dependency analysis and topological order verification before being presented for human review ("Mk1 Eyeball"). Prerequisite ingestion scrubbers, data models, and cryptographic primitives must strictly precede downstream APIs, UI components, CLI commands, and test suites. Furthermore, empirical tests, red team exercises, and benchmark gauntlets must strictly be executed and verified before drafting corresponding case studies, lab documentation, or walkthroughs.
- **`inv-commit-before-deploy` — Commit-Before-Deploy & Push-and-Delegate with CI/CD Verification Gate**: Never execute cloud deployments or create git tags when unstaged or uncommitted modifications exist in the working tree (`git diff --quiet && git diff --cached --quiet`). In automated release lifecycles, once clean commits and version tags are pushed to GitHub (`just git-sync push` / PR merge), agents must **NEVER** execute redundant local deploy commands (`just deploy`, `wrangler deploy`, `gcloud run deploy`), but **MUST actively verify that the GitHub Actions CI/CD workflow completes with success (`gh run watch` / `just pipeline watch`) before announcing release completion**. Local production deployments are strictly gated troubleshooting overrides requiring explicit human `DEPLOY-PROD` confirmation.
- **`inv-3plane-governance` — 3-Plane Deployment Governance**: Ecosystem pipelines operate across 3 decoupled planes: **Edge Plane** (`web/` and `credence-docs` via Cloudflare & `just deploy edge`), **Compute Plane** (`credence-server` on Cloud Run via `just deploy backend`), and **Infra Plane** (Terraform via `just tf apply`).
- **`inv-dual-env-least-privilege-cicd` — Dual-Environment Least-Privilege CI/CD**: Automated GitHub Actions deployments across Dev (`credence-dev-495173`) and Prod (`credence-prod-505902`) strictly use keyless Workload Identity Federation with `permissions: { id-token: write }`, repository attribute conditions (`assertion.repository == 'artibyrd/credence'`), granular least-privilege roles (`roles/run.developer`, `roles/cloudbuild.builds.builder`), and resource-scoped `serviceAccountUser` bindings, verified via shift-left contract tests (`tests/test_ci_cd_workflows.py`).
- **`inv-hermetic-unit-tests` — Hermetic Unit Test Isolation & Zero-Browser CI**: Unit tests (`@pytest.mark.unit`) must execute purely in-memory in <35s with zero browser runtimes (Playwright), background daemons, or network calls. Never inject OS package managers (`apt-get`, `playwright install --with-deps`) into CI/CD workflows to satisfy unit tests. All tests requiring browsers belong strictly in `@pytest.mark.integration` or `@pytest.mark.e2e`.

### Class γ (Gamma): Interface Symmetry, Epistemic Parity & Governance (P2 Ergonomics & Presentation)
- **`inv-4way-parity-symmetric-web` — Universal 4-Way Feature Parity & Symmetric Web Invariant**: Maintain simultaneous feature parity across **CLI** (`credence`), **FastMCP 2.0** (`credence_` tools & `credence://` resources), **Textual TUI** (`credence tui`), and **Zero-Build Web UI** (`web/`). All public web surfaces strictly use vanilla HTML5, CSS Custom Properties, and native ES Modules with **zero npm dependencies, zero package.json, and zero build toolchains**. Header navigation is strictly 5 invariant links (`Home`, `Docs`, `Reports`, `Nexus`, `Foundation`) across all pages. Footer architecture strictly uses 4 balanced pillars (4 links each); docs reading panes use centered 2x2 card modules (`max-width: 760px; margin: 0 auto;`) with centered copyright and zero redundant secondary bottom links (`.footer-bottom-links`). Local link normalizers must preserve live `https://docs.credence.run` and `https://blog.credence.run` HTTPS targets (`target="_blank"`), and interactive state mutations must maintain bidirectional synchronization across sidebars and cards. All 18 apex/subdomain routes must be explicitly bound in `wrangler.toml` with zero-cache headers (`Cache-Control: public, max-age=0, must-revalidate` for static assets, `no-cache, no-store, must-revalidate` for docs/blog).
- **`inv-epistemic-lensing` — The Epistemic Lensing & Information Pyramid Invariant**: All interfaces (Web, CLI, TUI, FastMCP) strictly structure content into a 3-tier cognitive hierarchy: Surface Lens (Glance — above fold: score gauge, 1-line verdict, 0 math), Focus Lens (Explore — mid-page: claims, grounded quotes, trajectory sparklines), and Deep Spectrum Lens (Forensic — base: Ed25519 signatures, RFC 8785 canonical bytes, live WebCrypto DOM hash match).
- **`inv-documentation-expansion` — Session-Driven Documentation Expansion & Anti-Proliferation Rule**: Always prioritize expanding, deepening, and enriching existing canonical documentation, technical blueprints, and sovereign essays over creating shallow new standalone documents. Avoid document proliferation and redundant variations on a theme; every piece of documentation must provide distinct, substantive epistemic depth.
- **`inv-living-canon` — Dynamic Invariant Canon ("The Invariant Bible")**: Never hardcode invariant numerical counts (e.g., "36 Core", "38 Invariants") in user-facing web surfaces, navigation, sitemaps, hero pills, or marketing prose. The living canon must always be referenced dynamically as **The Invariant Bible** or **Living Canon of System Invariants**.
- **`inv-multi-model-sovereignty` — Multi-Model Sovereignty & Token Budget**: Abstract inference via decoupled adapters (Gemini 3.7 Flash default reference engine with 4k thinking budget Pareto sweet spot, Claude 3.7 Sonnet, GPT-4o, DeepSeek R1, Ollama/vLLM) with automatic offline circuit breakers (`QUOTA_PRESERVED`) at 30% headroom.
- **`inv-production-telemetry-boundary` — Production Telemetry vs. Simulation Boundary**: Live operator dashboards (`credence.nexus/mesh.html`, TUI, CLI, FastMCP) must strictly report genuine live node reality ($N \ge 1$, dynamic $f = \lfloor (N-1)/3 \rfloor$, `STANDALONE` mode when alone) with zero mock dataset generation or scenario simulation buttons; rich chaos attack simulators belong exclusively in the zero-build documentation playground (`docs.credence.run#docs/playground`).
- **`inv-web-component-isolation` — Web Component Isolation & Zero-Clone Invariant**: Custom elements and embeddable Web Components (`HTMLElement` subclasses) must never invoke `cloneNode(true)` on host DOM trees containing custom element instances to prevent recursive constructor cascades (`Maximum call stack size exceeded`). Attribute observers (`attributeChangedCallback`) must be purely synchronous state transitions with zero asynchronous execution loops. All clientside parsers must guard against null/empty frontmatters and nested directives.
- **`inv-topic-entropy-astroturfing` — Topic Entropy Astroturfing Defense ($H < 0.30$) & Poe's Law Safeguards**: Diversity calculators must combine Top-Token Concentration ($C_{\text{top3}}$) with Shannon entropy. Neutralize legitimate satire ($0.00$), but invoke `SPJ-1.6` cloaking overrides (disabling satire protection) on factual defamatory/health allegations.
- **`inv-fastmcp-serialization` — FastMCP Text Evaluation & Serialization Parity**: Standalone text audits (`credence_evaluate_text`) must persist complete `Snapshot`, `Audit`, and `Violation` entities to SQLite (`text://inline` pseudo-URLs) and serialize nested `datetime` instances to ISO-8601 strings.
---

## 2. Tier 1: Progressive Subsystem Skills (`.agents/skills/`)
*Scoped subsystem rules and operational playbooks loaded dynamically on-demand.*

- ☁️ [`cloudrun-ops`](.agents/skills/cloudrun-ops/SKILL.md): Google Cloud Run compute plane, Workload Identity Federation (WIF), **Scale-to-Zero Container Cold Start Optimization** (Startup CPU Boost, direct virtualenv execution, `compileall` bytecode precompilation, aggressive HTTP `/health` probe, Gen 2 execution, build context exclusions <5MB), and zero-downtime rollback.
- 🧠 [`knowledge-governance`](.agents/skills/knowledge-governance/SKILL.md): Invariant lifecycle & demotion highway, 3-tier invariant scalability, 4-tier knowledge taxonomy router (`/remember`), `AGENTS.md` context economy (<800 tokens), and progressive disclosure governance.
- 🔍 [`invariant-audit`](.agents/skills/invariant-audit/SKILL.md): Living Canon audit, token budget verification (<800 tokens), 3-class priority taxonomy audit, 4-phase lifecycle enforcement, dynamic naming audit, and 7-manifest parity.
- 🌐 [`mesh-cluster`](.agents/skills/mesh-cluster/SKILL.md): 13-node Watts-Strogatz local P2P mesh cluster simulation, Highest Random Weight (HRW) feed rendezvous hashing, Byzantine Sybil cartel resistance ($3f+1$), and Barbell partition testing.
- 🏛️ [`white-label-ops`](.agents/skills/white-label-ops/SKILL.md): Sovereign organization scaffolding (`credence init-org`), multi-cloud Terraform templates, and zero-build multi-domain edge routing.
- 🏛️ [`architecture-governance`](.agents/skills/architecture-governance/SKILL.md): 500 LOC Ceiling Law, `compute_*` naming ontology, and modular subpackage decoupling across CLI, Server, TUI, and Mesh.
- 📊 [`epistemic-benchmark`](.agents/skills/epistemic-benchmark/SKILL.md): Golden 12 cross-profile evaluation benchmark suite, Expertise-Weighted Consensus Medians, and Galileo Rule consensus.

---

## 3. Tier 2: Shift-Left Automated Integrity Test Gates (`tests/test_docs_integrity.py`)
*Deterministic rules verified automatically in <0.3s during `just check` (bypassing prompt clutter).*

- **Markdown YAML Frontmatter**: All docs/blogs must define `title` and `description` (`test_all_markdown_files_valid_frontmatter`).
- **Markdown Code Fence & AST Hygiene**: Validates that all markdown files across the ecosystem have strictly column-0 code fences with zero leading whitespace indentation and balanced closures (`test_all_markdown_code_fences_and_syntax`).
- **Zero-npm Invariant**: Enforces zero `package.json` or `node_modules` on web surfaces (`test_zero_npm_invariant`).
- **7-Manifest Version Parity**: Enforces synchronized semantic versions across all repos and badges (`test_ecosystem_version_parity`).
- **Sitemap & Deep Link Coverage**: Validates all anchors, links, and route registries (`test_sitemap_integrity_and_route_coverage`).
- **Mermaid WCAG Contrast**: Enforces high contrast dark slate styling on diagrams (`test_mermaid_diagram_syntax_integrity`).
- **Hermetic Unit Test Marker Integrity**: Statically verifies that no `@pytest.mark.unit` test imports Playwright or executes browser scraping (`test_hermetic_unit_test_markers_invariant`).
- **Learning Lifecycle & Invariant Governance Contracts**: Verifies that all 4 `AGENTS.md` declare the 4-Phase Lifecycle, CI/CD invariant, and `invariant-audit` skill (`test_learning_lifecycle_and_invariant_governance_contracts`).

---

## 4. Standard Task Commands (`Justfile`)
- `just preflight [tool]`: Verify developer CLI dependencies (`gcloud`, `wrangler`, `gh`, `terraform`, `poetry`, `docker`, `all`).
- `just check`: Complete pre-commit QA gate (`preflight` -> `lint` -> `test unit` -> `test docs` -> `tf validate` -> `agent-check`).
- `just ignite [burst]`: One-command developer onboarding (setup -> preflight -> germinate -> mock test -> doctor).
- `just doctor`: Multi-plane diagnostic health check across Edge, Compute, Infra, and Declarative Agents.
- `just test [suite]`: Run targeted test suites (`unit`, `all`, `mock`, `live`, `e2e`, `docs`, `docker`).
- `just lint` / `just format`: Run static analysis, type checking, and Ruff auto-formatting.
- `just serve [transport]`: Launch server engine (`sse`, `stdio`, `web`).
- `just tui` / `just benchmark`: Launch terminal workstation or Golden 12 benchmark suite.
- `just audit-invariants`: Run comprehensive invariant token budget, dynamic naming, lifecycle, and parity audit.
- `just gcp [action] [arg]`: Google Cloud Run operations (`status`, `logs`, `tail`, `revisions`, `describe`, `probe`, `germinate`, `rollback`).
- `just edge [action]`: Cloudflare Edge router operations (`status`, `logs`, `login`, `deploy`).
- `just pipeline [action]`: GitHub Actions telemetry and secret auditing (`status`, `watch`, `secrets`).
- `just tf [action]`: Terraform multi-cloud operations (`validate`, `plan`, `apply`, `output`).
- `just deploy [target]`: Safe deployment pipeline with automated health probe (`backend`, `edge`, `all`).
- `just release <version> <message>`: Complete atomic ecosystem release sequence.

*For complete mathematical proofs, formulas, and architectural references, see 📘 [`docs/invariants.md`](docs/invariants.md) and 🏛️ [`docs/blueprints/invariant-scalability-and-knowledge-governance.md`](docs/blueprints/invariant-scalability-and-knowledge-governance.md).*
