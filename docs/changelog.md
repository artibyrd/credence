---
title: Release Changelog
description: Version history, release notes, and milestone accomplishments across
  the Credence network.
since_version: v1.0.0
verified_version: v1.20.0
last_verified: '2026-08-19'
---

# Release Changelog

All notable changes to the **Credence** network and documentation are documented here following [Semantic Versioning](https://semver.org/).

## [1.20.0] - 2026-08-19

### Ministry of Silly Protocols & The Wetware Chronicles (Rule SPJ-42.0)
- **The Wetware Chronicles 16-Essay Sovereign Master Series (`credence-docs/blog/`)**:
  - Published complete satirical-empiricism essay collection certified under Rule `SPJ-42.0`.
  - Codified the **Battlestar Galactica Adama Doctrine** and the *"DRADIS is blind, switching to Mark 1 Eyeball"* visual verification invariant (`the-mk1-eyeball-invariant.md`).
  - Documented how production scars birthed Tier-0 invariants (`scar-tissue-as-architecture.md`) and published first-person AI memoirs on the 4,000-token thinking trance, subagent parenthood, the zero-npm dependency cull, and *The Serious Joy of Play*.
- **Pythonic Aerospace & Avian Calibration Constants (`credence/constants.py`)**:
  - Network diagnostic packet airspeed velocity calibrated against unladen swallow constants (`AFRICAN_OR_EUROPEAN_SWALLOW_VELOCITY_FPS = 33.0`).
  - Scale-to-zero container standby state officially certified as "Not Dead, Just Resting" (`PARROT_RESTING_STATUS = "PINING_FOR_THE_FJORDS"`).
  - Transient consensus election retries governed by canonical Holy Hand Grenade integer (`HOLY_HAND_GRENADE_COUNTDOWN = 3`).
- **Roadmap & Socratic Knowledge Governance Evolution (`docs/roadmap.md`, `SKILL.md`)**:
  - Added ASTRO-GUARD Dynamic Astroturf Defense Daemon ($H < 0.30$) to Horizon 1.
  - Added "DRADIS-is-Blind" Visual Verification Mode and Wasm client-side evaluators to Horizon 2.
  - Added FastMCP 2.0 Adversarial Socratic Interrogation Tool (`credence_grill_plan`) and live Philanthropy Odometers to Horizon 3.
  - Codified the 4-round Socratic Architecture Pre-Mortem in `knowledge-governance/SKILL.md`.

## [1.19.0] - 2026-08-19

### Bicameral Testing, Environment Verification & Autonomous Experimentation
- **Automated Dual-Tier Environment Verification Gate (`credence/experiments/env_verifier.py`, `just config-verify`)**:
  - Probes live Dev and Prod endpoints to validate controlled independent variables (Cost Profile differentiation, 512 vs 4,096 thinking token budgets, storage isolation, and non-colliding Ed25519 root identities).
- **Bicameral Differential Shadow Auditing Engine (`credence/experiments/shadow_audit.py`, `just experiment shadow-audit`)**:
  - Calculates Epistemic Divergence ($\Delta S = |S_{\text{dev}} - S_{\text{prod}}|$) and proves an empirical **83.3% FinOps inference cost reduction** across the Golden 12 benchmark fixtures by filtering benign reporting at stage 1 before invoking 4k thinking.
- **Sovereign White-Label Federation Bridge & Byzantine Fault Simulator (`credence/experiments/federation_bridge.py`, `just experiment federation-bridge`)**:
  - Validates cross-organization RFC 8785 canonical JSON attestation signing and exchange, Highest Random Weight (HRW) rendezvous feed partitioning, and $3f+1$ Byzantine Sybil fault isolation.
- **Hermetic Adversarial Fuzzing Test Suite (`tests/test_adversarial_fuzzing.py`, `tests/test_experiments_harness.py`)**:
  - Added comprehensive in-memory unit tests for Billion Laughs XML entity expansion defense, SSRF IPv6/metadata filters, prompt injection container bounds, and cryptographic signature tamper rejection.
- **Operational Guides & Sovereign Case Studies (`credence-docs/`)**:
  - Published `bicameral-testing-and-experiments.md` operator handbook.
  - Published `case-study-dual-tier-finops.md` empirical FinOps study.
  - Published `case-study-astroturfing-entropy.md` forensic astroturfing analysis.


## [1.16.0] - 2026-08-19

### Autonomous Boredom Engine & Epistemic Root Expansion
- **Autonomous Boredom Engine (`credence/feeds/boredom.py`)**:
  - Introduced the `BoredomEngine` and `BoredomDaemon` that convert idle node compute and token headroom into autonomous epistemic discovery.
  - Implemented `run_boredom_cycle` with Token Safety Governor gating (enforcing rolling 24-hour headroom $\ge 30\%$ and circuit breaker integrity).
  - Built opportunistic prioritized FIFO pending queue digestion with Mesh Effort Avoidance: checks local database and peer mesh attestations first to adopt signed reports at **0 tokens ($0.00)** before executing novel LLM audits.
  - Broadcasts signed Ed25519 `AuditRecord` attestations across the 13-node Watts-Strogatz P2P mesh relay upon completing novel audits.
- **Epistemic Root Expansion & Citation Soil (`credence/feeds/roots.py`)**:
  - Implemented `extract_root_candidates` to extract cited outbound domains from verified clean articles ($\text{Suspicion Score} \le 25.0, G = 1.00$).
  - Added strict SSRF and network security containment (`is_safe_url`), rejecting loopback, RFC 1918 private subnets, cloud metadata (`169.254.169.254`), and social network noise.
  - Implemented `expand_roots` to autonomously probe candidate domains for RSS/Atom/JSON feeds, auto-register new `FeedSubscriptionRecord` roots, and harvest initial `FeedItemRecord` items.
  - Built `get_root_tree` providing hierarchical JSON trees of active roots and citation soil.
- **Universal 4-Way Feature Parity**:
  - **FastMCP 2.0 (`credence/server/app.py`)**:
    - Tools: `credence_expand_roots`, `credence_trigger_boredom_cycle`, `credence_get_root_candidates`.
    - Resources: `credence://roots/tree`, `credence://roots/candidates`, `credence://boredom/status`.
    - REST API: `POST /api/roots/expand`, `GET /api/roots/tree`, `GET /api/roots/candidates`, `POST /api/boredom/cycle`, `GET /api/boredom/status`.
    - Starlette lifespan integration: launches `BoredomDaemon` in background when enabled.
  - **CLI (`credence/cli/main.py`)**:
    - Added commands: `credence expand-roots`, `credence boredom`, `credence roots [tree|candidates]`.
  - **Zero-Build Web UI (`web/credence.report/index.html` & `web/credence.run/index.html`)**:
    - Added live Epistemic Root Network & Boredom Engine telemetry section and spotlight cards.
- **The Invariant Bible Canonization**:
  - Retitled canonical invariants to **"The Invariant Bible: Living Canon of System-Wide Invariants & Protocols"**, eliminating static fixed count references across all documentation and web surfaces.
  - Formalized Invariant 39: *Opportunistic Boredom Ingestion & Epistemic Root Expansion Invariant*.
- **Documentation & Sovereign Blog**:
  - Published sovereign blog essay: [`The Boredom Engine & Expanding Roots`](#blog/the-boredom-engine-and-expanding-roots).
  - Published formal protocol specification: [`Epistemic Protocol Specification: Boredom Engine & Root Expansion (EPEP-16)`](#docs/protocols/boredom-and-root-expansion).
- **Hermetic Test Suites & Mesh Cluster Verification**:
  - Added `tests/test_roots.py` (candidate extraction, SSRF rejection, feed discovery, root trees).
  - Added `tests/test_boredom.py` (boredom cycle execution, token governor gating, background daemon).
  - Added `test_mesh_cluster_boredom_work_sharing` and `test_mesh_cluster_boredom_root_partitioning` in `tests/test_mesh_cluster.py`.

## [1.15.3] - 2026-08-19

### Epistemic Report Viewer: Default Load Randomization & 4-Workspace Layout Redesign
- **Default Load Randomization (`web/credence.report/viewer.html`)**:
  - Replaced static deterministic selection (`dynamicCorpus[0]`) on default initial loads with uniform corpus randomization (`Math.random() * dynamicCorpus.length`), ensuring readers encounter a fresh, diverse forensic audit upon every fresh page load while preserving explicit query parameters (`?q=...`) and hash payloads (`#data=...`).
- **4-Workspace Streamlined Navigation Architecture (`viewer.html` & `styles.css`)**:
  - Eliminated horizontal tab overflow and scrolling by consolidating 6 verbose horizontal tabs into 4 focused, high-density workspaces:
    1. **`📊 Audit Overview`**: Executive Briefing, Epistemic Trust Dimensions (SPJ, IEP, Deceptive UI), and Snapshot & Provenance Metadata.
    2. **`🚨 Findings & Reader`**: Unified investigative workspace featuring an interactive segmented switch (`toggleFindingsView`) between `[ 📋 Itemized Cards ]` (category filters & search) and `[ 📖 In-Context Article Reader ]` (interactive highlight markers & inspector sidebar).
    3. **`📰 Publisher Trends`**: Domain Epistemic Index (DEI), Forensic Sourcing Ratios, Longitudinal SVG trend timeline, and Top Violated Rules table.
    4. **`🔐 Proof & Export`**: W3C WebCrypto Verification (RFC 8785 Ed25519 signatures & mesh status) combined with full Share & Export stack (Markdown summaries, JSON attestations, and web embed badges).
  - Maintained complete backwards compatibility in `switchTab()` for legacy tab IDs (`tab-reader`, `tab-export`).
- **Automated Web Regression Gate (`tests/test_web.py`)**:
  - Added `test_web_viewer_randomized_default_selection_and_4_tab_layout` verifying default randomization, 4-tab DOM structure, sub-view toggling, and attestation export capabilities.

## [1.15.2] - 2026-08-19

### CI/CD Hardening & Workflow Resilience
- **Shift-Left Test Marker Static Gate (`tests/test_docs_integrity.py`)**:
  - Added `test_hermetic_unit_test_markers_invariant` to statically inspect the AST of all test suites during `just check`, verifying that no test marked `@pytest.mark.unit` imports Playwright or invokes `capture_webpage`.
- **Atomic Release Preflight Cleanliness Guard (`Justfile`)**:
  - Added working-tree cleanliness preflights (`git diff --quiet` and `git diff --cached --quiet`) to the `release` recipe, preventing partial or unstaged tagging desynchronization.
- **Workflow Timeout Bounds Across All Pipelines (`.github/workflows/*.yml`)**:
  - Enforced strict 5-minute timeout bounds on CI test gates, Terraform verification, and Edge Router deployment, and 10-minute timeout bounds on container build and Cloud Run deployment workflows.
- **Local & Remote Pytest Execution Parity (`Justfile`)**:
  - Aligned `just test unit` to execute `poetry run pytest tests/ -m "unit" --durations=10`, guaranteeing identical hermetic unit execution locally and in CI.
- **Knowledge Governance & Sovereign Invariants (`AGENTS.md`)**:
  - Persisted the *Hermetic Unit Test Isolation & Zero-Browser CI* and *Atomic Release Working-Tree Cleanliness* universal non-negotiable invariants via `/learn`.

## [1.15.1] - 2026-08-19

### Epistemic Audit Viewer & Catalog Integrity Fixes
- **Epistemic Trust Dimension & Signal Consistency (`web/credence.report/viewer.html`)**:
  - Resolved logic contradictions where summary-level or shallow audit items without itemized violation records incorrectly rendered 100/100 trust dimensions and false green `✓ Clean Sourcing`, `✓ Valid Logic`, `✓ Clean Design` badges beneath elevated suspicion scores (e.g. 92.5 High Deception).
  - Derived dimension scores and risk signal pills directly from aggregate suspicion score ($S$) and classification band when itemized violations are omitted or in summary view.
  - Added proportionate dimension penalties on high deception scores so primary trust dimensions reflect the severity of the verdict.
- **Executive Summary Grammar Bug Fix (`viewer.html`)**:
  - Repaired broken template string gap (`"identified . Readers"`) by introducing descriptive heuristic suspicion fallbacks when `findings` array is empty on an elevated suspicion score.
- **Itemized Findings Fallback & Zero-Count Defense**:
  - Replaced false "✓ No Violations Detected" status on elevated suspicion reports with an informative card explaining heuristic and aggregate signal derivation.
- **UI & Layout Integrity (`web/credence.report/styles.css` & `viewer.html`)**:
  - Replaced rigid tab padding and hidden overflow in `.tabs-nav` with responsive spacing, `flex-shrink: 0`, and styled thin scrollbars, eliminating clipping on the `🔐 Cryptographic Proof` tab.
  - Fixed multi-line monospace wrapping for `Content SHA-256` in `.meta-table td.val` with `overflow-wrap: anywhere; word-break: break-all;` and ensured complete fallbacks for `SimHash-64`.
- **Enriched Web Catalog Export (`credence/germinate.py` & `reports.json`)**:
  - Updated `export_web_catalog()` to export complete record structures (including `content_sha256`, `simhash_64`, `suspicion_density`, `confidence_score`, `article_text`, and itemized `violations: [...]`), ensuring static hydration has zero data gaps.

### Documentation & Routing Fixes
- **Unified Master Documentation & Sovereign Blog Registry**:
  - Merged all 4 blog categories into the master `DOCS_REGISTRY` array in `app.js`, resolving an edge case where standalone `BLOG_REGISTRY` entries failed to resolve in `loadDocument()`.
  - Fixed blog routing fallback in `loadDocument` so unresolved routes default to the flagship case study (`blog/conflict-of-pun-terest.md`) instead of falling back to the last technical reference specification (`docs/invariants.md`).
- **Relative Asset Links Audit**:
  - Repaired 27 relative image paths to vector assets (`assets/tui/*.svg`) across tutorials, walkthroughs, and integrations.
- **Shift-Left Automated Integrity Tests**:
  - Enhanced `test_docs_registry_parity` in `tests/test_docs_integrity.py` to assert that all 109 document and blog IDs in `DOCS_REGISTRY` map to distinct paths and resolve cleanly.
  - Added `test_web_reports_json_schema_completeness`, `test_web_viewer_heuristic_suspicion_safeguards`, and `test_web_viewer_css_tab_and_hash_integrity` to `tests/test_web.py`.

## [1.15.0] - 2026-08-19

### Observability & Operator Workstation
- **Credence Node & Mesh Health, Telemetry & Scored Pages Dashboard**:
  - **First-Person Node Operator View ("My Node at a Glance")**: Prominent hero status panel answering the 4 fundamental operator questions: *What is my server doing?* (runtime, memory RSS vs 850 MB ceiling, token headroom), *How many articles have I processed?* (lifetime & today counts, average suspicion score $\overline{S}$, verbatim grounding $G=1.00$), *What connections do I maintain in the mesh?* (active peers, seed connectivity, $3f+1$ Byzantine safety margin), and *What compute savings has my node realized?* (tokens and USD avoided via BitTorrent work-sharing).
  - **Zero-Build Web Dashboard (`web/credence.nexus/dashboard.html`)**: Interactive vanilla HTML5/ES Modules dashboard with 5 modular tabs (**Overview, Sources & Domains, Categories & Rules, P2P Mesh Swarm, SRE & Telemetry**), live endpoint switcher (`Local Node` $\leftrightarrow$ `Custom Node` $\leftrightarrow$ `Demo Swarm`), and configurable auto-refresh polling (Off, 1s, 3s, 5s, 10s).
  - **Terminal CLI Workstation (`credence stats`)**: Full-featured CLI command rendering operator summary panels, SRE telemetry tables, and recent audit tickers, with `--breakdown` for publisher domain trust bands and content category distributions, `--watch` for continuous live terminal monitoring, and `--json` for machine-readable JSON exports.
  - **Textual TUI Workstation Telemetry**: Integrated real-time node activity, BitTorrent compute savings odometers, and SRE percentile gauges into the full-screen terminal IDE.
  - **FastMCP 2.0 & REST Protocol Parity**: Registered FastMCP tool `credence_get_mesh_stats` and resource `credence://mesh/stats`, alongside REST routes `GET /api/v1/mesh/stats` and `GET /api/mesh/stats`.
  - **New Blueprint & Sovereign Engineering Essay**:
    - **Technical Blueprint (`docs/blueprints/node-and-mesh-telemetry-dashboard.md`)**: Complete architectural specification for node operator observability, metric aggregation formulas, and zero-build web dashboards.
    - **Engineering Essay (`blog/real-time-mesh-observability.md`)**: Sovereign design philosophy for observing decentralized epistemic swarms without centralized cloud loggers or SaaS telemetry.
  - **Automated Test Gate (`tests/test_dashboard.py`)**: 100% automated test coverage across metric aggregations, REST API schemas, FastMCP tool/resource serialization, CLI execution, and zero-npm web asset integrity.

### Performance & Compute Plane
- **Cloud Run Scale-to-Zero Container Cold Start Optimization (81.2% Faster)**:
  - **Dynamic Startup CPU Boost (`startup_cpu_boost = true`)**: Enabled Google Cloud Run v2 Startup CPU Boost to allocate 2–4 vCPUs during container boot, halving CPU-bound CPython AST parsing and module import evaluation at $0.00 idle cost.
  - **Direct Virtualenv Execution**: Eliminated Poetry CLI process wrapper overhead (~1,000ms) by putting `/app/.venv/bin` in `PATH` and invoking `credence serve` directly.
  - **Build-Time Bytecode Precompilation (`compileall`)**: Precompiled all `.py` files to `.pyc` during Docker build and removed `PYTHONDONTWRITEBYTECODE=1` in production container images to eliminate runtime AST compilation.
  - **Dynamic Lazy Import Deferral**: Deferred top-level imports of heavy scraping and reasoning subtrees (`trafilatura`, `dateparser`, `playwright`, `DualCaptureResult`, `ExtractedContent`, `audit_url`, `evaluate_snapshot`, `BayesianConsensusAggregator`) into tool handlers, dropping core server module import latency by 49% (from 2,860ms to 1,460ms).
  - **Aggressive HTTP Readiness Probing**: Configured 2-second HTTP probe against `/health` with a 1-second initial delay, cutting probe detection lag from up to 10s down to ~1.5–2.0s.
  - **Execution Environment Gen 2**: Enforced Second Generation execution environment for dedicated Linux kernel performance and faster filesystem paging.

### Documentation & User Experience
- **Collapsible Sidebar Navigation (`credence-docs`)**:
  - Upgraded documentation portal navigation to semantic HTML5 `<details class="sidebar-group">` with custom animated chevrons, category item count badges, and `localStorage` state persistence across the 15 categories and 84 documents.
  - Added smart active auto-expansion: automatically expands the category containing the current document while keeping others neatly tucked.
  - Added intelligent search expansion: typing in `#doc-search` automatically reveals all matching categories and collapses non-matching ones.
  - Added a "Toggle All" quick toolbar button for expanding or collapsing all categories with one click.
- **Documentation Freshness Audit & Version Provenance Badges**:
  - Audited all 107 Markdown documents in `docs/` and `blog/` to ensure zero obsolete flags, model names, or deprecated commands.
  - Enriched all documentation frontmatter with `since_version`, `verified_version: "v1.15.0"`, and `last_verified: "2026-08-19"`.
  - Added visual provenance badges to `.doc-metadata-bar` in `app.js` and `styles.css` rendering glowing `✅ Verified in v1.15.0` and `📦 Added in vX.X.X` tags with audit date tooltips.
  - Added automated test assertion in `test_docs_integrity.py` (`test_all_markdown_files_valid_frontmatter`) to ensure all future documentation maintains `since_version` and `verified_version` fields.
- **New Operational Blueprints & Engineering Essays**:
  - **Cloud Run Scale-to-Zero Blueprint (`docs/blueprints/cloudrun-scale-to-zero-cold-start-optimization.md`)**: Comprehensive technical guide detailing the 5-pillar serverless cold start framework, microVM allocation, import graphs, and performance metrics.
  - **Taming the 10-Second Cold Start Essay (`blog/taming-the-10-second-cold-start-scale-to-zero.md`)**: Forensic teardown of Python serverless boot bottlenecks, unmasking the silent Poetry tax, and unlocking sub-2.5s scale-to-zero cold starts.
  - Updated `deployment-cloudrun.md`, `topic-index.md`, and `cloudrun-ops` operational skill.

### Knowledge Governance & Invariant Scalability Architecture
- **3-Tier Invariant Scalability Framework**:
  - Restructured `AGENTS.md` into high-density **Tier 0 Universal Core Invariants (P0 Non-Negotiables)** (<800 tokens, 62% token reduction), eliminating cognitive oatmeal and attention dilution.
  - Stratified subsystem-specific runbooks into **Tier 1 Progressive Subsystem Skills** (`.agents/skills/`), loading playbooks dynamically on-demand.
  - Shifted mechanical syntax, version parity, and formatting rules into **Tier 2 Shift-Left Automated Integrity Tests** (`tests/test_docs_integrity.py`), executing in <0.3s during `just check`.
  - Maintained canonical reference catalog and mathematical proofs in **Tier 3 Reference Specifications** (`docs/invariants.md`).
- **New Blueprint & Engineering Essay**:
  - **Invariant Scalability Blueprint (`docs/blueprints/invariant-scalability-and-knowledge-governance.md`)**: Architectural blueprint detailing the 3-tier hierarchy, cognitive failure modes of flat rulebooks, and token budget governance.
  - **Scaling Invariants Without Prompt Bloat Essay (`blog/scaling-system-invariants-without-prompt-bloat.md`)**: Engineering essay exploring attention dilution in AI coding agents and shift-left deterministic test gates.
  - Updated `AGENTS.md` across all 4 ecosystem repositories, `.agents/skills/knowledge-governance/SKILL.md`, and master `docs/topic-index.md`.

## [1.14.1] - 2026-08-19

### Added
- **New Showcase Articles & Operational Handbooks**:
  - **CI/CD Acceleration Post-Mortem (`blog/from-860mb-to-2mb-sub-40s-cicd-pipeline.md`)**: Forensic breakdown of unmocked socket timeouts, 99.7% build upload reduction, and `pytest-xdist` parallelization.
  - **Pipeline & Build Optimization Handbook (`docs/operations/pipeline-and-build-optimization.md`)**: Comprehensive operational reference for workstation tuning, Docker BuildKit caching, and Cloud Build concurrency.
  - **The 3-Plane Sovereign Architecture (`blog/the-three-plane-architecture.md`)**: In-depth essay on decoupling Cloudflare Edge (zero-npm), Cloud Run Compute (scale-to-zero), and Terraform Infrastructure for $0.00 idle cost.
  - **Swarm Rendezvous Hashing (`docs/mesh-engineering/rendezvous-hashing-feed-partitioning.md`)**: Mathematical and protocol guide to Highest Random Weight (HRW) Rendezvous Hashing (`compute_feed_affinity`) and 92.3% compute savings.
  - **Zero-Touch Node Germination (`docs/protocols/zero-touch-germination-and-swarm-ignition.md`)**: Autonomous node lifecycle, Ed25519 identity minting, genesis inoculation at $0.00 token cost, and burst auditing.
  - **DEI & Sourcing Forensics Blueprint (`docs/blueprints/domain-epistemic-index-and-sourcing-forensics.md`)**: Mathematical formulas for composite $DEI$, 5 standardized Trust Bands, and 4 Forensic Sourcing Ratios ($R_{\text{byline}}$, $R_{\text{single}}$, $R_{\text{COI}}$, $ASI$).
- **Search Registry & Topic Index Synchronization**:
  - Registered all new guides in `DOCS_REGISTRY` and `BLOG_REGISTRY` in `app.js` with comprehensive keyword arrays for instant `/` search.
  - Synchronized master `docs/topic-index.md` and `docs/sitemap.md` across the ecosystem.
- **Knowledge Governance & System Invariants**:
  - Added semantic version tag verification invariant, build context payload exclusion invariant (<5MB), and shell pipefail stream safety invariants to `AGENTS.md` and `.agents/skills/cloudrun-ops/SKILL.md`.

## [1.14.0] - 2026-08-19

### Optimized & Accelerated
- **Ecosystem CI/CD & Pipeline Acceleration (Lint ➔ Test ➔ Build ➔ Deploy)**:
  - **Pytest Parallelization (`pytest-xdist`)**: Integrated `pytest -n auto` to execute hermetic unit tests concurrently across CPU cores, reducing test suite duration by **65%** (from 81s down to 28s).
  - **Feed Pre-Flight Network Timeout Elimination**: Mocked `fetch_and_parse_feed` in CLI test suites to remove an unmocked 10.7-second live HTTP socket timeout.
  - **Concurrent Mesh Cluster Lifecycle**: Replaced sequential relay lifecycle loops with `asyncio.gather` for parallel WebSocket server startup and teardown.
  - **Build Context & Upload Reduction (99.4% lighter)**: Configured `.dockerignore` and `.gcloudignore` to drop upload payload and Docker build context from **861 MB down to 2.1 MB**.
  - **Lean Production Containers**: Configured `Dockerfile` to build runtime containers using `poetry install --without dev` and BuildKit cache mounts.
  - **Concurrent Cloud Build & CI/CD**: Parallelized quality and test gates in `cloudbuild.yaml` with `waitFor: ['-']`, pruned unneeded Playwright browser downloads from unit CI jobs, and optimized `just tf validate` with cached `.terraform` state inspection.

## [1.13.0] - 2026-08-19

### Added
- **Ecosystem Master Sitemap (`docs/sitemap.md`)**:
  - Comprehensive visual and categorical directory indexing all 5 sovereign domains (`credence.run`, `docs.credence.run`, `blog.credence.run`, `credence.report`, `credence.nexus`, `credence.foundation`), 12 zero-build interactive playgrounds, 38 system invariants, 17 investigative essays, and 72 documentation guides.
  - Registered in `DOCS_REGISTRY` in `app.js` with instant search keywords and Mermaid ecosystem relationship map.
- **Cross-Domain Unified Header Navigation (`.credence-nav`)**:
  - Harmonized navigation header across all 5 domains with instant links to Home, Docs, Playgrounds, Blog, Reports, Nexus, Foundation, Sitemap, and GitHub.
- **Rich 4-Column Ecosystem Footer (`.credence-footer`)**:
  - Implemented 4-column structured footer layout (Sovereign Domains, Interactive & Tools, Knowledge & Proofs, Governance & Source) across all 5 domain web entrypoints and dynamically appended to documentation articles.
- **Automated Regression Prevention Suites**:
  - Added `test_sitemap_integrity_and_route_coverage` in `test_docs_integrity.py` to assert 100% sitemap route coverage.
  - Added `test_cross_domain_consistent_navigation_and_footers` in `test_docs_rendering.py` to audit live header navigation, footer structure, and static domain templates.

## [1.12.5] - 2026-08-19

### Changed
- **Taxonomy Rule Explorer Redesign & Complete Rule Catalog**:
  - Replaced the cramped, dual-scrolling table in Widget 6 of `docs/playground.md` with an expansive, responsive **Rule Card List** adhering to Invariant 38 (Zero Scrollbars & Natural Document Flow).
  - Expanded the rule database from 9 mock samples to all **46 authentic taxonomy rules** across SPJ Journalistic Ethics (12), IEP Logical Fallacies (21), Deceptive UI Patterns (9), Financial Disclosures (1), Medical Claims (1), Election Integrity (1), and Governance Conflicts (1).
  - Added multi-dimensional filtering (Catalog Chips + Severity Dropdown + Real-Time Search) with 8-card pagination and 1-click canonical URI copying.
  - Replaced `<textarea readonly>` in Widget 11 (ClaimReview Generator) with an auto-height preformatted `<pre>` container.

## [1.12.4] - 2026-08-19

### Fixed
- **Inline HTML Tag Preservation in Markdown Parser**:
  - Enhanced `formatInline` in `app.js` to mask and preserve valid inline HTML tags (`<a>`, `<span>`, `<code>`, `<mark>`, etc.) before HTML entity escaping, preventing literal tag leaks in custom callout boxes (e.g. `<a href="...">` and `<code>` in the live verification channels card).
  - Formatted live verification link channels in `blog/conflict-of-pun-terest.md` as clean single-line blocks.
  - Added regression test `test_no_raw_html_tag_leaks` targeting `blog/conflict-of-pun-terest` and verifying zero leaked `&lt;a href` tags.

## [1.12.3] - 2026-08-18

### Fixed
- **Balanced-Brace LaTeX Parser & Full Symbol Expansion**:
  - Replaced regular expression-based fraction matching in `formatMath` (`app.js`) with an iterative balanced-brace recursive parser, properly handling nested subscripts (e.g. `\frac{N_{named}}{N_{total}}` $\to$ `(N₍named₎ / N₍total₎)`).
  - Added support for `\mathbb{R}` ($\to \mathbb{R}$), `\mathbb{I}` ($\to \mathbb{I}$), `\min`, `\max`, `\tau`, `\leftarrow`, `\rightarrow`, `\leftrightarrow`, `\parallel` ($\to \parallel$), `\overline`, and `\pmod`.
  - Added escaped curly set braces (`\{...\} ` $\to$ `{...}`) and graceful fallback filtering for any unknown raw LaTeX backslashes.
  - Verified site-wide zero math errors across all 98 documentation pages in headless Chromium via Playwright.
- **Zero Scrollbars on Attestation Receipts**:
  - Replaced the scrollable `<textarea>` with an auto-height preformatted `<pre>` element for canonical RFC 8785 attestation JSON receipts.

## [1.12.2] - 2026-08-18

### Changed
- **Eliminated Nested Vertical Scrollbars & Enhanced Document Layout**:
  - Restructured `blog/conflict-of-pun-terest.md` to follow a clean, human-first progression from high-level civic context and aggregate DEI profile up front down to deep-dive forensic pillar evidence and interactive simulators.
  - Removed cramped `max-height: 560px` and inner vertical scrolling from `.article-preview-pane` in `styles.css` so DOM article previews expand naturally.
  - Replaced the fixed raw attestation receipt textarea with an expandable `<details>` accordion section, preventing multi-scrollbar clutter in the forensic workbench.
- **Enhanced Zero-Build Mathematical Typography & LaTeX Parser**:
  - Expanded `formatMath` in `app.js` with operators and formatting cleanups (`\cdot`, `\land`, `\lor`, `\implies`, `\iff`, `\quad`, `\qquad`, `\sqrt`, `\bar`, `\hat`, `\mathbf`, `\mathrm`, `\subset`, `\subseteq`, `\forall`, `\exists`, `\infty`).
  - Simplified and standardized mathematical formulas for the Domain Epistemic Index ($DEI$) and Sourcing Ratios ($R_{\text{byline}}$, $R_{\text{COI}}$, $ASI$, $R_{\text{single}}$) with full variable definitions.

## [1.12.1] - 2026-08-18

### Added
- **Rich Interactive Publisher Analytics Dashboard**:
  - Replaced static ASCII formatting with a high-contrast, responsive glassmorphic publisher profile card on `blog.credence.run` and `docs.credence.run`.
  - Added dual-mode tab switcher toggling seamlessly between **Visual Dashboard** and **Raw Canonical ASCII / JSON** views.
  - Added visual Domain Epistemic Index (DEI) score meter with interactive 4-zone spectrum track and real-time position marker.
  - Added interactive progress meters for the 4 primary forensic ratios: Byline Transparency ($R_{\text{byline}}$), Single-Source Blotter Reliance ($R_{\text{single}}$), Conflict of Interest Exposure ($R_{\text{COI}}$), and Advertorial Separation Index ($ASI$).
  - Added interactive codified rule violation rows for `SPJ-3.3`, `AST-1.1`, `SPJ-3.1`, `DEC-1.4`, and `SPJ-1.1` with frequency badges and direct catalog links.
- **Exhaustive Epistemic Data Interpretation Guide**:
  - Added comprehensive educational section *"How to Read & Interpret Credence Epistemic Data"* explaining structural journalistic ethics vs. binary fact-checking.
  - Detailed mathematical derivations and real-world interpretations of the Domain Epistemic Index (DEI), trust bands, and forensic sourcing ratios.
  - Clarified Suspicion Score calibration ($S \in [0, 100]$) and the Zero-Hallucination Grounding Invariant ($G=1.00$) with exact DOM quotation proofs.
- **Live Continuous Monitoring & Anti-Cherry-Picking Channels**:
  - Added live real-time verification section with links to live publisher analytics on `credence.report`, production REST API endpoints (`GET /api/analytics/publisher/inmaricopa.com`), FastMCP dynamic resources (`credence://analytics/publisher/inmaricopa.com`), and CLI verification commands.

## [1.12.0] - 2026-08-18

### Added
- **Aggregate Public Publisher Analytics & Longitudinal Trend Visualization**:
  - Implemented `get_publisher_analytics(session, domain)` and `list_all_publishers_summary(session)` in `credence/subjects/analytics.py`.
  - Added composite **Domain Epistemic Index ($DEI$)**, 5 standardized Trust Bands (`HIGH_INTEGRITY`, `RELIABLE`, `MIXED`, `POOR`, `DECEPTIVE`), and **Forensic Sourcing Ratios**:
    - **Byline Transparency Ratio ($R_{\text{byline}}$)**: Proportion of published articles containing verified human bylines.
    - **Single-Source Reliance Ratio ($R_{\text{single}}$)**: Frequency of articles relying on a single uncorroborated press release (`SPJ-1.1`, `SPJ-1.2`).
    - **Conflict Disclosure Rate ($R_{\text{COI}}$)**: Rate of explicit conflict of interest disclosures for municipal/commercial coverage (`SPJ-3.1`, `SPJ-3.2`).
    - **Advertorial Separation Index ($ASI$)**: Separation metric isolating disguised native advertorials (`SPJ-3.3`, `DEC-1.4`, `AST-1.1`).
  - Added monthly longitudinal trend buckets (`period_label`, `audits_count`, `avg_suspicion`, `avg_dei`, `violations_count`).
- **Universal 4-Way Interface Parity for Publisher Analytics**:
  - **FastMCP 2.0 Tools & Resources**: Added tool `credence_get_publisher_analytics` and live resources `credence://analytics/publishers` and `credence://analytics/publisher/{domain}`.
  - **Starlette REST API Gateway**: Added endpoints `GET /api/analytics/publishers` and `GET /api/analytics/publisher/{domain:path}` with CORS support.
  - **CLI Workstation**: Added `credence rankings outlet <domain>` terminal dashboard and `credence export-analytics <domain> --format [json|csv] -o <file>`.
  - **Zero-Build Web UI**: Added interactive **Publisher Analytics & Trends** tab on `credence.report/viewer.html` with zero-build inline SVG trendline charts and 1-click clipboard export.
- **InMaricopa Exurban Civic News Monopoly Case Study & Interactive Forensics Workbench**:
  - Sowed `https://inmaricopa.com/feed/` into preset feed catalogs (`PRESET_FEED_CATALOGS["regional-civic"]`).
  - Created hermetic benchmark test suite `tests/test_inmaricopa_casestudy.py` validating the 4 forensic case study pillars ($R_{\text{COI}}$, $ASI$, $R_{\text{multi-source}}$, and $DEI$).
  - Published editorial investigative whitepaper `blog/conflict-of-pun-terest.md` (*"Conflict of Pun-terest: 347 Reasons Why Maricopa's Publisher-Politician Problem Fails the Epistemic Smell Test"*).
  - Embedded **Interactive Forensic Epistemic Workbench** with 5 real article presets, clickable verbatim grounding highlights, dynamic reform simulator sliders, and RFC 8785 Ed25519 canonical receipt downloads.
- **Sovereign Blog Categorization & Prominent Playgrounds**:
  - Reorganized sovereign blog into 4 distinct thematic tracks (*Investigative Case Studies & Field Forensics*, *Consensus Mathematics & Game Theory*, *Agentic Architecture & Sovereign AI*, and *Homelab Ops & Infrastructure*).
  - Promoted *Conflict of Pun-terest* to the pinned #1 featured landing dispatch on `blog.credence.run`.
  - Surfaced *Interactive Playgrounds* prominently across docs navigation, sidebar, topic index, and landing pages.

## [1.11.0] - 2026-08-18

### Added
- **Interactive Zero-Build Playground Overhaul (12 Live Simulators)**:
  - Expanded in-browser zero-build simulator suite to 12 fully interactive tools running 100% client-side with zero backend dependencies:
    - **4 New Interactive Simulators**:
      - *The Galileo Rule Consensus Engine Simulator*: Interactive Sybil cartel defense demonstrating how domain-weighted medians and $G=1.00$ grounded evidence protect consensus truth against ungrounded bot swarms.
      - *In-Browser Epistemic Heuristic Text Scanner*: Live headline and copy parser that detects clickbait hooks, ungrounded superlatives, fake urgency, and weasel attributions in real time with color-coded highlighted spans.
      - *Schema.org `ClaimReview` & RFC 8785 Receipt Generator*: Live form outputting Google Search-ready ClaimReview JSON-LD and signed `.credence.json` canonical envelopes with 1-click clipboard copy and file download.
      - *Token Governor & 30% Headroom Circuit Breaker*: Interactive quota gauge simulating token burn and visual state transitions into `$0.00` offline heuristic preservation mode.
    - **Upgraded & Polished Existing Widgets (1–8)**:
      - *13-Node Mesh Gossip*: Clickable nodes with real-time **Node Inspector Card** ($Q_i$, peer link topology).
      - *SimHash-64 & Bit-Diff Matrix*: Graphical **64-Bit Differential Grid** rendering 64 color-coded tiles (green for match, red for flip) with 3 scenario presets.
      - *Verbatim Grounding Tester ($G=1.00$)*: Live DOM text preview highlighting matching substrings in glowing cyan, with an "Inject Paraphrase" test button.
      - *Saturation Curve Calculator*: Interactive **SVG Calibration Curve Plot** ($y = 100(1-e^{-x/12})$) with crosshairs dynamically tracking slider adjustments.
      - *WebCrypto Verifier*: Added "Tamper Payload" button to demonstrate instant cryptographic signature rejection.
      - *Taxonomy Explorer*: Added domain filter chips (`All`, `SPJ Journalism`, `IEP Fallacies`, `Deceptive UI`, `Domain Specific`).
      - *Multi-Model Comparator*: Added adjustable Thinking Token Budget slider (0 to 16,384 tokens).
      - *Feed Sifter Simulator*: Added "Investigative Feed" vs "Astroturfing Pivot ($H < 0.30$)" presets with immediate quarantine alerts.
- **Documentation Progressive Disclosure & Anti-Firehose Architecture**:
  - Completely redesigned `credence.run` web landing page and `credence/README.md` to eliminate cognitive overload, Greek formula firehoses ($Q_i, E_i$), and internal enum constants on first-contact surfaces.
  - Introduced human-first value propositions, 30-second interactive terminal quickstarts, and plain-English explanations of the 4 Pillars of Grounded Truth.
  - Overhauled documentation gateway (`docs/intro.md`) with a "Choose Your Path" matrix and streamlined 3-step quickstart (`docs/quickstart.md`).
- **Master Concept Directory & Topic Index ("No Marble Left in the Oatmeal")**:
  - Published master Topic Index & Quick Reference cheat sheet (`docs/topic-index.md`) categorizing all CLI subcommands, configuration settings, AI integration configs, cost profiles, taxonomy catalogs, math proofs, and self-hosting runbooks.
  - Added "Next Steps & Related Marbles" cross-navigation footers across core documentation pages.
- **Client-Side Multi-Term Search Engine in `app.js`**:
  - Added rich `keywords` and 1-line `desc` metadata to every registered guide in `DOCS_REGISTRY`.
  - Upgraded `setupSearch()` to search across titles, descriptions, categories, and keywords simultaneously with multi-term query matching and automatic suppression of empty category headers.
- **Knowledge Governance & System Invariants**:
  - Added the **Documentation Progressive Disclosure & Search Indexing (Anti-Firehose & Anti-Oatmeal)** Invariant to `AGENTS.md` across all 4 ecosystem repositories.
  - Expanded `knowledge-governance/SKILL.md` with the 5-level progressive disclosure hierarchy and concept searchability checklist.

## [1.10.0] - 2026-08-18

### Added
- **Dual-Tier SRE Observability & Discord Webhook Integration**:
  - Implemented the **"Guy in His Basement" Easy Mode** (`monitoring_tier = "simple"`, default):
    - 3 Essential Failure Guardrails: Service Outage (global HTTP `/health` uptime probe), 5xx Error Spikes ($>5$ in 5m), and Container Memory Pressure ($>85\%$ RAM).
    - First-class Discord & Powercord incoming webhook integration (`discord_webhook_url`) using native GCP `webhook_tokenauth` channels.
    - Automated budget alert integration at 50%, 80%, and 100% of the $15.00/mo cap.
  - Implemented the **Advanced Production Tier** (`monitoring_tier = "advanced"`):
    - Log-based error metric (`credence_error_logs`), P95 request latency degradation alert ($>5000\text{ms}$), CPU saturation alert ($>90\%$), and Cloud Scheduler feed publisher failure monitor.
  - Upgraded SRE Telemetry Dashboard with multi-chart visual grid.
- **Interface Telemetry Loopback Protocol (ITLP-v1)**:
  - Added thread-safe in-memory `ServerTelemetryTracker` aggregating rolling 5-minute request distributions (Total, 2xx, 3xx, 4xx, 5xx), memory consumption (`resource.getrusage`), and latency percentiles.
  - Added Starlette `TelemetryMiddleware` and enriched `/health` and `/api/health` REST endpoints with real-time telemetry and active alert diagnostics.
  - Added FastMCP 2.0 tool `credence_get_health_status` and resource `credence://node/health` for agent self-awareness.
  - Added Terminal CLI commands `credence health` and `credence alerts` with Rich diagnostic panels.
  - Upgraded Textual TUI with live Header Alert Status Badge (`🟢 Healthy` / `🟡 High Memory` / `🔴 ⚠️ 5xx Spike Detected`) and dedicated `🚨 Ops & Alerts` tab (Key `8`).
- **Comprehensive Documentation & Published Articles**:
  - Featured Blog Essay: *"Interface Telemetry Loopback: Closing the Circuit Between Cloud SRE, Local TUIs, and AI Agents"*.
  - Blog Essay: *"Basement Ops: Zero-Bloat Cloud Monitoring, Discord Webhooks & TUI Telemetry for Sovereign Nodes"*.
  - Protocol Specification: `ITLP-v1` (*Interface Telemetry Loopback Protocol*).
  - Hands-On Tutorial: `Tutorial 13: Dual-Tier Cloud Monitoring, Discord Webhooks & Interface Telemetry`.
  - Updated GCP Cloud Run Deployment Guides.

## [1.9.0] - 2026-08-18

### Added
- **Two-Phase Epistemic Leaderboard, Sovereign Mesh Merit & Closed-Loop Network Routing**:
  - Implemented **Phase 1 (Sovereign Mesh Node Merit)**:
    - 5-level Epistemic Tier progression (`SPROUT` $\to$ `SIFTER` $\to$ `AUDITOR` $\to$ `SPECIALIST` $\to$ `ROOT_ANCHOR`) rooted in cryptographic merit and empirical domain expertise.
    - 8 cryptographically verifiable Epistemic Merit Badges (`sprout_node`, `sifter_pioneer`, `verified_auditor`, `domain_specialist`, `philanthropic_relay`, `root_seed_candidate`, `galileo_pioneer`, `sybil_shield`).
    - Shields.io-compatible dynamic SVG badge generator (`generate_svg_badge`) and publisher trust badges (`generate_publisher_svg_badge`).
    - 24-hour operator maintenance grace period with smooth half-life uptime decay ($\tau=24\text{h}$).
    - 4-level deterministic tie-breaking (Metric Score $\to$ Tokens Seeded $\to$ First Seen $\to$ Public Key Hex).
    - Multi-category leaderboards (`quality`, `subjects`, `philanthropy`, `galileo`, `teams`).
    - Closed-loop network routing with 4 Traffic Shaping Classes (`FAST_LANE` = 500 msgs/s, `STANDARD` = 50 msgs/s, `CHOKED` = 1 msg/s, `QUARANTINED` = 0 msgs/s).
    - Rate-limiting, /24 subnet clustering to prevent Sybil collusion, and zero-cost attestation caching gate (`should_adopt_attestation`).
  - Implemented **Phase 2 (Global Web Epistemic Intelligence)**:
    - Domain Epistemic Index ($DEI$) calculator with trust banding (`HIGH_INTEGRITY`, `RELIABLE`, `MIXED`, `LOW_INTEGRITY`, `DECEPTIVE`).
    - Domain Rankings: Epistemic Honor Roll (most trusted domains) vs Deception Hotlist (Wall of Shame) vs Astroturf Detection Alerts.
    - Top 10 Violated Rules Aggregator across all audited snapshot violations with representative grounded excerpts.
    - Macro Global Epistemic Weather Barometer and Category Integrity Dials.
    - Community Verification Bounties for breaking and unaudited wire stories.
  - **Universal 4-Surface Integration Parity**:
    - **CLI**: `credence leaderboard`, `credence merit`, `credence badge export`, `credence rankings`, `credence bounties`.
    - **FastMCP 2.0**: 6 tools (`credence_get_leaderboard`, `credence_get_node_merit`, `credence_get_domain_rankings`, `credence_get_taxonomy_analytics`, `credence_get_epistemic_weather`, `credence_get_bounties`) and 7 resources (`credence://leaderboard/...`, `credence://merit/...`, `credence://rankings/...`, `credence://weather/...`, `credence://bounties`).
    - **Textual TUI**: New `🏆 Leaderboard` tab (`tab_leaderboard`) with dual-panel mesh rankings, local merit profile, and unlocked badges.
    - **Zero-Build Web UI**: Interactive multi-tab leaderboards and SVG badge embedder on `credence.nexus`, plus DEI Honor Roll/Wall of Shame on `credence.report`.
    - **Justfile**: Added `just leaderboard`, `just merit`, `just rankings`, `just weather`.
  - **Hermetic Testing**: Added 5 dedicated test suites with 100% network-free pass (`test_merit_edge_cases.py`, `test_merit_and_leaderboards.py`, `test_adversarial_gamification.py`, `test_web_analytics.py`, `test_leaderboard_interfaces.py`).

## [1.8.0] - 2026-08-18

### Added
- **Cloud Run Deployment Hardening, Multi-Plane Operations & Parameterized Justfile**:
  - Refactored `Justfile` into canonical parameterized recipe families (`preflight [tool]`, `test [suite]`, `serve [transport]`, `gcp [action]`, `edge [action]`, `pipeline [action]`, `tf [action]`, `deploy [target]`) with automated toolchain prerequisites (`(preflight "gcloud")`, `(preflight "wrangler")`, `(preflight "gh")`, `(preflight "terraform")`).
  - Added dedicated Google Cloud Run deployment workflow (`.github/workflows/deploy-backend.yml`) with Workload Identity Federation support, automated health verification, and clear fallback skip notices when secrets are unconfigured.
  - Aligned `cloudbuild.yaml` and Terraform Cloud Run service definitions (`gcr.io/credence-prod-505902/credence-server:latest`) with 1Gi memory limits for headless browser stability.
  - Upgraded lifespan auto-germination in `credence/server/app.py` to non-blocking background execution, ensuring instant sub-100ms HTTP readiness on cold boot.
  - Added high-leverage operator workflows: `just check` (6-step pre-commit QA gate in <90s), `just ignite` (zero-touch dev onboarding), `just doctor` (multi-plane health diagnostic across Agent, Compute, Edge, and Infra planes), and `just gcp probe` / `just gcp germinate`.
  - Upgraded Cloud Run deployment to live serving revision `00005-dn7` with 100% green health probes and remote Miracle-Gro germination verification.
- **Knowledge Governance & Progressive Skills Architecture (`/remember`)**:
  - Implemented `knowledge-governance` skill (`.agents/skills/knowledge-governance/SKILL.md`) enforcing the 4-tier knowledge taxonomy and preventing attention dilution in `AGENTS.md`.
  - Implemented `cloudrun-ops` skill (`.agents/skills/cloudrun-ops/SKILL.md`) extracting multi-step GCP Cloud Run deployment and rollback runbooks into on-demand progressive disclosure.
  - Pruned and distilled `AGENTS.md` across all ecosystem repositories into a crisp, high-density invariant contract (<1,000 tokens) with a clean progressive skills index.
  - Updated agent configuration to mandate explicit declaration of the target Semantic Version about to be released when presenting walkthroughs.

## [1.7.0] - 2026-08-18

### Added
- **Automated Textual TUI Vector Exporter & Documentation Integration**:
  - Built automated headless SVG export engine (`tools/export_tui_assets.py` & `just generate-tui-assets`) generating 11 vector terminal captures across all 7 tabs, modal dialogs, and 3 view modes (`Rich`, `Compact`, `Raw JSON`).
  - Added native zero-build Markdown `![alt](url)` image parser in `app.js` and responsive elevated styling in `styles.css`.
  - Upgraded all 4 feature walkthroughs (`01-auditing-webpages-and-text.md`, `02-zero-trust-feed-sifting.md`, `03-p2p-mesh-consensus.md`, `04-morning-digest-briefings.md`) with rich **📟 Textual TUI Workstation** tabs, step-by-step keybinding instructions, and embedded vector SVGs.
  - Completely overhauled the TUI Workstation Deep Dive guide (`docs/integrations/tui-workstation.md`) with layout anatomy diagrams, global keybinding tables, and 4-way view mode comparison tabs.
- **Mermaid Diagram Audit, High-Density Replacements & Accessibility Elevation**:
  - Audited all 83 Mermaid diagrams across the ecosystem, pruning 10 low-information/filler flowcharts and replacing them with high-density structured components (Comparison Matrices, Adversarial Threat Cards, Governance Indexes, and Action Tables).
  - Built a framed diagram window display engine (`.mermaid-window`, `.mermaid-window-header`, `.window-dot`) with semantic ARIA roles.
  - Enforced strict **WCAG 2.1 AA/AAA anti-light-on-light contrast rules** (`fill: #f8fafc !important;` on `#0f172a`/`#1e293b` slate with amber-guarded sequence notes).
  - Added accessible 2px offset `:focus-visible` glow rings across all interactive controls.

## [1.6.0] - 2026-08-18

### Added
- **Autonomous Node Germination & Miracle-Gro Ignition Engine (`credence/germinate.py`)**:
  - Implemented `credence germinate` (and `just germinate`) providing a 5-step rapid node ignition lifecycle:
    - **Phase 1: Epistemic Genesis**: Verifies or generates local Ed25519 identity keypair.
    - **Phase 2: Peer Mesh Inoculation**: Imports signed Genesis seed attestations (`genesis_attestations.json`) with Ed25519 signature and taxonomy verification at **$0.00 token cost**.
    - **Phase 3: Soil Preparation**: Sows 24 preset categorized feed subscriptions across 4 tiers with Rendezvous hashing affinity.
    - **Phase 4: Miracle-Gro Sifting Burst**: Evaluates novel articles and produces signed local attestations within governor headroom limits.
    - Phase 5: Web Hydration: Auto-exports `reports.json` for immediate Zero-Build Web UI parity.
  - Added dedicated CLI command with botanical Rich progress tree rendering (`🌱`, `🔑`, `🌐`, `💧`, `⚡`, `🌳`) and telemetry summary table.
  - Added Starlette `POST /api/germinate` REST API endpoint and zero-touch background auto-germination on blank node startup.
  - Added Genesis Attestation Pack (`web/credence.nexus/genesis_attestations.json`).
  - Added hermetic unit test suite (`tests/test_germinate.py`).
- **Swarm Rendezvous Partitioning & 13-Node Mesh Hardening**:
  - Implemented Highest Random Weight (HRW) feed affinity sorting (`compute_feed_affinity`) in Miracle-Gro burst, preventing swarm dogpiling across concurrent nodes.
  - Implemented atomic commit/rollback sub-transactions in seeding and Genesis inoculation, eliminating multi-node database race conditions.
  - Added `test_13_node_concurrent_swarm_germination_and_mesh_cross_adoption` to `tests/test_mesh_cluster.py`.
- **New Documentation & Sovereign Dispatches**:
  - **Engineering Guide**: `docs/mesh-engineering/featherweight-swarm-testing.md` (Low-resource 13-node simulation in <150MB RAM).
  - **Blog Dispatch**: `blog/testing-13-node-swarms-on-a-raspberry-pi.md` (The Featherweight Mesh Architecture on edge hardware).
  - **Tutorial 11**: `docs/tutorials/11-autonomous-node-germination-and-swarm-ignition.md` (Hands-on cold-start guide).
  - **Blog Dispatch**: `blog/miracle-gro-for-truth-nodes.md` (Architectural essay on solving the Cold-Start Ghost Town problem).
  - **Protocol Specification**: `docs/protocols/node-germination-lifecycle.md` (Formal mathematical specification of 5-phase germination & HRW partitioning).
- **Unified CI/CD Deployment Pipeline & CLI Visibility**:
  - Added automated Cloudflare Worker Edge deployment workflow (`.github/workflows/deploy-edge.yml`) on push to `main` (`web/**`).
  - Added single-command deployment recipes in `Justfile`: `just deploy-edge`, `just deploy-backend`, and `just deploy-all`.
  - Added terminal-native pipeline and edge observability recipes: `just pipeline-status`, `just pipeline-watch`, `just edge-status`, `just edge-logs`, and `just edge-login`.
  - Formalized the 3 Delivery Planes (Edge Plane, Compute Plane, Infra Plane) in documentation and ecosystem invariants (`AGENTS.md`).

## [1.5.2] - 2026-08-18

### Added
- **Autonomous Epistemic Feed Sifter & Real-Time Ingestion Bridge**:
  - **Live Feed Ingestion Execution (`credence/feeds/worker.py`)**:
    - Wired novel article discovery directly to `audit_url` evaluation pipeline, creating `SnapshotRecord`, `AuditRecord`, and `ViolationRecord` entities in SQLite upon discovery.
    - Added auto-bootstrapping of preset feed subscriptions if subscription catalog is empty.
  - **Unified Starlette Server with REST API Gateway (`credence/server/app.py` & `credence/cli/main.py`)**:
    - Expanded server runtime to combine FastMCP 2.0 SSE transport with Starlette REST API endpoints:
      - `GET /health` & `GET /api/health`: Service health and version status.
      - `GET /api/reports`: Paginated, categorized query endpoint (`recent`, `best`, `worst`, `satire`, `random`).
      - `GET /api/reports/{identifier}`: Reconstitutes full `AuditReport` entity with snapshot metadata and itemized violations from SQLite.
      - `POST /api/audit`: Live on-demand evaluation endpoint for arbitrary target URLs.
      - `GET /api/sifter/status`: Real-time telemetry on active feed subscriptions, discovered articles, audited counts, and token savings.
      - `POST /api/sifter/cycle`: Trigger immediate sifting pass.
      - `GET /api/feeds/stream`: Stream recent discovered feed items.
    - Added `--sifter` flag to `credence serve` and ASGI lifespan management for background `SifterDaemon`.
    - Added `--once` flag to `credence sifter` for single-cycle execution in cron or batch environments.
    - Added `credence export-catalog` CLI subcommand exporting SQLite database state to static `reports.json` catalog.
  - **Cloudflare Worker Edge Router REST Proxying (`web/_worker.js`)**:
    - Added transparent reverse proxying for `/api/*` and `/health` requests across all hosted domains to Google Cloud Run backend with full CORS headers.
  - **Zero-Build Web UI Dynamic Auto-Discovery (`credence.report/viewer.html` & `index.html`)**:
    - Implemented dynamic API base detection auto-switching between local `http://localhost:8000` during local development and `/api` on production.
    - Added async dynamic corpus fetching from `/api/reports`, falling back gracefully to static `reports.json` and embedded scenarios.
    - Connected live on-demand URL auditing directly in search/inspect inputs with animated status feedback.
    - Added live feed audits stream container to `index.html`.
  - **Zero-GCP Portability & Seed Automation**:
    - Added `just seed-reports`, `just serve-sifter`, `just sifter-once`, and `just export-catalog` recipes.
    - Documented 100% self-hosted, air-gapped local execution without commercial cloud lock-in in `docs/portability/multi-cloud-deployment.md`.

## [1.5.1] - 2026-08-18

### Added
- **Multi-Display Mode Switcher & Machine-Ingestible Options across 4 Interfaces**:
  - **Zero-Build Web UI (`credence.report/viewer.html`)**:
    - Implemented 3-way Display Mode Switcher (`[🧠 Human]`, `[⚡ Compact]`, `[🤖 Machine (JSON)]`) with URL query parameter sync (`?view=human|compact|raw`).
    - Added `[⚡ Compact]` view: dense single-screen epistemic breakdown with quick-scan verdict and tabular findings.
    - Added `[🤖 Machine (JSON)]` view: full-width canonical RFC 8785 JSON inspector with pretty/minified formatting toggle and 1-click cURL API snippet.
    - Embedded dynamic Schema.org `ClaimReview` JSON-LD into DOM `<head>` on every report render for autonomous AI agent scraping and search engine crawler ingestion.
  - **Rich Terminal CLI (`credence/cli/main.py`)**:
    - Added universal `--format {human,compact,json,ndjson,tsv}` flag across `credence audit`, `credence lookup`, and `credence report`.
    - Compact format outputs concise score, density, confidence, and single-line findings; NDJSON outputs newline-delimited JSON stream; TSV outputs tab-separated tabular data for pipeline scripting.
  - **FastMCP 2.0 Server (`credence/server/app.py`)**:
    - Added `credence://reports/{identifier}/compact` resource providing token-efficient LLM briefings.
    - Added `credence://reports/{identifier}/raw` resource returning raw signed RFC 8785 JSON attestations.
    - Enhanced `credence_get_audit` tool with `format` parameter supporting `human`, `compact`, `json`, `ndjson`, and `tsv`.
  - **Textual TUI Workstation (`credence/tui/app.py`)**:
    - Added `v` keyboard shortcut to cycle live inspector view modes between Rich Human Executive Briefing, Compact Dense Summary, and Raw JSON Attestation.
- **Categorical Epistemic Audit Discovery & Stream Explorer**:
  - **Zero-Build Web UI (`credence.report/index.html` & `viewer.html`)**:
    - Added Quick Discovery Toolbar with filter pills (`Recent`, `Surprise Me (Random)`, `Top Clean 0–15`, `Most Flagged 70+`, `Satire Showcase`).
    - Built slide-down Discovery Drawer (`#discovery-drawer`) rendering category cards for 1-click loading without needing a known URL or hash.
  - **Rich Terminal CLI (`credence/cli/main.py`)**:
    - Added `credence report browse [--category {recent,best,worst,satire,random}] [--limit N] [--format FMT] [--open]` subcommand.
    - Added discovery convenience flags to `credence lookup` (`--best`, `--worst`, `--satire`, `--random`).
  - **FastMCP 2.0 Server (`credence/server/app.py`)**:
    - Registered `credence_browse_audits` tool querying SQLite by category with configurable limits and formats.
    - Registered `credence://reports/explore/{category}` streaming resource.
  - **Textual TUI Workstation (`credence/tui/app.py`)**:
    - Added `r` keyboard shortcut to select and load a random audit report from local database history.

### Changed
- **Stacked Share & Export Layout (`credence.report/viewer.html`)**:
  - Replaced cramped 3-column horizontal export grid with full-width vertically stacked cards (`.export-stack`, `.export-card-stacked`) featuring horizontal action headers, 1-click copy buttons, and full-width syntax-highlighted previews for Markdown, RFC 8785 JSON, and SVG Trust Badges.

---

## [1.5.0] - 2026-08-18

### Added
- **Human-Centered Epistemic Report Viewer across 4 Interfaces**:
  - **Zero-Build Web UI (`credence.report/viewer.html`)**:
    - Built interactive in-context reading mode rendering snapshot article prose with color-coded highlight markers (`.hl-ethics`, `.hl-fallacy`, `.hl-deceptive`) and tooltip citations.
    - Added Executive Epistemic Briefing card with plain-English human takeaways and 3-signal indicators (Ethics, Logic, Deceptive Design).
    - Added 5 interactive tabs: Overview & Metrics, In-Context Reading Mode, Itemized Findings (with real-time search & domain filter chips), Cryptographic Proof (W3C WebCrypto Ed25519 validation), and Share & Export (1-click Markdown copier, JSON download, SVG trust badge).
    - Preserved 100% Zero-Build standard (vanilla HTML5, CSS Custom Properties, native ES Modules, zero npm dependencies).
  - **Textual TUI Workstation (`credence/tui/app.py`)**:
    - Built Dual-Pane Inspector Split: left pane for filterable specialist findings table and right pane for in-context cited excerpts, severity badges, and reasoning.
    - Added Executive Summary panel at the top of the inspector with human takeaways.
    - Added live search filter input updating findings dynamically on keystrokes.
    - Added keyboard shortcuts: `o` (open in web browser), `e` (export Markdown report to disk), and `f` (focus filter input).
  - **Rich Terminal CLI (`credence/cli/main.py`)**:
    - Prepend Executive Epistemic Briefing panel and visual Epistemic Trust Dimensions breakdown meters (`[████████████████████] Clean`).
    - Added `--open` browser flag to `credence audit` and `credence lookup` subcommands.
    - Added `credence report view <identifier> [--format {terminal,markdown,json}] [--open]` subcommand.
  - **FastMCP 2.0 Server (`credence/server/app.py`)**:
    - Added `format: str = "json"` (`json`, `markdown`, `human`) parameter to `credence_get_audit`.
    - Registered `credence://reports/{identifier}/human` resource returning conversational Markdown briefings.
    - Registered `explain_audit_report_prompt` prompt template instructing AI agents how to explain audit reports in plain English.
  - **FastMCP Text Evaluation Persistence**:
    - Persisted `SnapshotRecord`, `AuditRecord`, and `ViolationRecord` to SQLite with `text://inline` pseudo-URLs for all text evaluations to ensure cache lookup parity with live URL audits.
  - **Universal Invariant Codification**:
    - Codified *FastMCP Text Evaluation Persistence Invariant* and *Human-First In-Context Report Presentation Invariant* in `AGENTS.md`.

---

## [1.4.0] - 2026-08-18

### Added
- **Reusable Live Rotating & Mutating E2E Test Suite (`just test-live`)**:
  - Implemented `tests/e2e/live_corpus.py` Stratified Master Corpus with deterministic daily seed rotation (`YYYY-MM-DD` / `CREDENCE_LIVE_SEED`) across 5 epistemic categories (Reference, Satire, Wire News, Tech Media, Syndicated RSS).
  - Implemented `tests/e2e/test_live_rotating_suite.py` gauntlet testing CLI live audits, RSS feed quality ($F_j$), real-time dynamic article extraction, FastMCP 2.0 remote SSE tool invocation, and 13-node Watts-Strogatz P2P mesh BitTorrent work-sharing (92.3% compute savings) with Byzantine ungrounded smear slashing.
- **6-Tier Testing Strategy & Verification Architecture Documentation**:
  - Published comprehensive testing guide (`docs/protocols/testing-strategy.md` and `docs/testing-strategy.md`) detailing the 6 verification tiers, isolation guarantees, and operational test recipes.
- **Hands-On Tutorial 10: Running the Reusable Live Rotating E2E & Byzantine Mesh Gauntlet**:
  - Created step-by-step developer tutorial (`docs/tutorials/10-reusable-live-e2e-and-mesh-gauntlet.md`) for operating live seed mutation, dynamic feed sifting, and P2P mesh chaos testing.
- **Editorial Blog Essay: The 6-Tier Verification Pyramid**:
  - Published high-assurance testing essay (`blog/the-six-tier-pyramid-of-decentralized-truth.md`) exploring why static benchmarks fail in AI verification, how deterministic hashing prevents overfitting, and how zero-npm Playwright guarantees multi-decade stability.
- **Anti-Tampering & FastMCP SSE Resilience**:
  - Added anti-tampering assertions ensuring modifying signed audit fields causes Ed25519 verification rejection.
  - Added error-handling verification for invalid tool calls over remote FastMCP 2.0 SSE session streams.

- **Sovereign In-Repo Roadmap & Known Issues Backlog**:
  - Authored `docs/roadmap.md` and published to docs portal (`docs/roadmap.md`), establishing a local, in-tree Markdown source of truth for observed edge cases, live mitigations, and thematic future backlog items for autonomous AI agents.
- **Crawler Resilience & Syndicated Date Parsing**:
  - Added multi-format epoch timestamp fallback (seconds & milliseconds) to `credence/feeds/parser.py` date extraction.
  - Hardened Playwright browser context in `credence/ingestion/snapshot.py` with standard locale and transient network retry fallback.

### Fixed
- **Engine Resilience & Bug Fixes**:
  - Persisted `evaluation_method` in `AuditRecord` SQLModel and added SQLite automatic schema migration in `init_db()`.
  - Refined XML entity expansion regex in `safe_parse_xml` to strictly match `<!DOCTYPE` and `<!ENTITY>` declarations without false-flagging text containing "system".
  - Added `NullPool` and active event loop binding to async SQLite engine to eliminate event loop closure leaks across sequential tests.
  - Converted Playwright live rendering test suite to native `async_playwright` with zero event loop thread pollution.
  - Improved satire detection regexes in `credence/ingestion/extractor.py` to be attribute-order agnostic for modern hydration DOMs.

---

## [1.3.0] - 2026-08-18

### Added
- **36 Invariants Reference Catalog & Deep Linking**:
  - Expanded `docs/invariants.md` to 36 machine-verifiable invariants across 4 pillars with individual DOM IDs (`#invariant-1` to `#invariant-36`) and pillar architecture flowcharts.
  - Implemented sub-anchor routing in `app.js` with smooth auto-scrolling and glowing cyan highlighting.
  - Systematically linked all invariant mentions across all 74 catalog documents.
  - Added automated static integrity tests (`test_all_invariant_link_anchors_exist`) and Playwright browser tests (`test_invariant_deep_linking_and_scrolling`).
- **Rich Frontmatter Metadata & Zero-Build Faceted Search Engine**:
  - Standardized frontmatter metadata schema (`tags`, `interfaces`, `invariants`, `difficulty`, `read_time`).
  - Added interactive top-of-article metadata badge rows for rapid jumping to related interfaces and invariants.
  - Added keyboard search shortcuts (`/` or `Ctrl+K` to focus, `Esc` to clear) and interactive sidebar filter pills (**All**, **Invariants**, **Agentic**, **FastMCP**, **Tutorials**).
- **Dedicated "Agentic Engineering & Antigravity Workflows" Documentation Category**:
  - **[01. Antigravity Pair-Programming](agentic/01-antigravity-pair-programming-paradigm.md)**: Research phase, Planning Mode, background task orchestration, reactive messaging, and "Mk1 Eyeball" human gating.
  - **[02. /learn & Invariant Synthesis](agentic/02-continuous-learning-and-invariant-synthesis.md)**: Codifying post-mortems and edge-case discoveries into machine-verifiable rules in `AGENTS.md` and automated tests.
  - **[03. Hermetic Testing & Zero-npm](agentic/03-hermetic-testing-and-zero-npm-guardrails.md)**: In-memory SQLite fixtures, Playwright DOM/SVG geometry contracts, and Zero-npm longevity.
  - **[04. Multi-Model Pareto & Token Governor](agentic/04-multi-model-pareto-and-token-governance.md)**: Gemini 3.7 Flash 4k thinking token sweet spot ($0.075/1M), 30% offline circuit breakers, and prompt boundary defense.
  - **[05. FastMCP & 4-Way Parity](agentic/05-fastmcp-dual-transport-and-four-way-parity.md)**: Dual stdio/SSE FastMCP 2.0 transports, reverse proxy security, and 4-way synchronous interface parity.
  - **[Blog Essay: Architecting Sovereign AI with Google Antigravity](../blog/architecting-sovereign-ai-with-google-antigravity.md)**: High-assurance agentic engineering narrative.
- **Formalized Milestone Completion & Multi-Repo Git Push Lifecycle**:
  - Codified the 5-step milestone completion protocol: Present Walkthrough $\to$ Request "Mk1 Eyeball" Approval $\to$ Changelog & Version Sync $\to$ Multi-Repo Push (`just push-all`) $\to$ `/learn` Retrospective.

---

## [1.2.0] - 2026-08-18

### Added
- **GCP-Style Tabbed Interface Switching (`:::tabs` / `=== Tab Name`)**:
  - Implemented zero-build, accessible, dark glassmorphism tabbed container components in `app.js` and `styles.css` matching Google Cloud Platform documentation ergonomics.
  - Added semantic WAI-ARIA tab contracts (`role="tablist"`, `role="tab"`, `role="tabpanel"`) and animated active cyan indicator styling.
  - Retained clipboard copy button integration inside individual tabbed code blocks.
- **Global Cross-Document Preference Persistence (`localStorage`)**:
  - Automatically persists user-selected interface modality (**CLI**, **FastMCP 2.0**, **Python SDK**, **Zero-Build Web UI**, or **Textual TUI**) to `localStorage`.
  - As users navigate across documentation and walkthrough pages, matching tab groups automatically switch to the preferred interface with smart fuzzy matching.
- **4 New Comprehensive Feature Walkthrough Articles**:
  - **[Feature Walkthrough 01: Webpage & Prose Epistemic Auditing](walkthroughs/01-auditing-webpages-and-text.md)**: Multi-interface guide for auditing URLs and raw text against SPJ, IEP fallacies, and deceptive UI patterns.
  - **[Feature Walkthrough 02: Zero-Trust Feed Autodiscovery & Sifting](walkthroughs/02-zero-trust-feed-sifting.md)**: End-to-end guide for dynamic feed discovery, pre-flight topic entropy audits, and background sifter daemons.
  - **[Feature Walkthrough 03: P2P Mesh Gossip & Bayesian Consensus](walkthroughs/03-p2p-mesh-consensus.md)**: Complete guide to node identity generation, Watts-Strogatz peering, and Galileo Rule weighted medians.
  - **[Feature Walkthrough 04: Daily Morning Epistemic Briefings](walkthroughs/04-morning-digest-briefings.md)**: Compiling 24-hour executive intelligence briefings, Markdown newsletters, and FastMCP dynamic streams.
- **Documentation-Wide Visual Density & Anti-Wall-of-Text Overhaul**:
  - Added 22 new Mermaid architecture and sequence flowcharts, 18 comparison tables, and 25 styled callouts across 28 articles.
  - 100% of all 68 documentation and blog articles now satisfy the $\ge 2.0$ visuals per 500 words invariant.
- **Automated Tab Persistence & Navigation Regression Tests**:
  - Added `test_tabbed_interface_switching_and_persistence` in `tests/test_docs_rendering.py` validating tab switching, active panel swaps, `localStorage` saves, and multi-page persistence.

---

## [1.1.1] - 2026-08-18

### Added
- **Zero-Build Mermaid.js Engine Integration**: Vendored standalone zero-build Mermaid v10.9.1 engine (`assets/mermaid.min.js`) into `credence-docs/` and `credence/web/assets/`, enabling native SVG rendering for all 24+ architecture, protocol sequence, and mesh topology diagrams.
- **Dark Aesthetic Diagram Theme**: Configured dark palette (`#0d121f` container, `#38bdf8` cyan glow borders, `#f8fafc` typography) matching the Credence design system.
- **Copy to Clipboard Buttons**: Added animated one-click copy buttons and uppercase language tags (`BASH`, `PYTHON`, `YAML`, `JSON`, `TEXT`) across all fenced code blocks.
- **GitHub Alert Callouts Styling**: Added distinctive dark glassmorphism containers and icons for `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, and `> [!CAUTION]`.
- **Automated Live Rendering Test Suite**: Created `tests/test_docs_rendering.py` with Playwright + headless Chromium verifying zero unrendered Mermaid diagrams, zero raw HTML tag leaks, full interactivity across all 8 playground widgets, and 0 console errors across all documentation pages.
- **Extended Static Integrity Suite**: Updated `tests/test_docs_integrity.py` with static Mermaid syntax validation and complete DOM element coverage for all 8 playground widgets.

### Fixed
- **Markdown Block Parsing Precedence**: Overhauled `parseMarkdown` in `app.js` to prioritize code block fences before HTML tag inspection, eliminating raw HTML tag leaks (`&lt;/div&gt;`, `&lt;textarea&gt;`) inside code samples and interactive widgets.
- **LaTeX Math & Currency Formatting**: Corrected regex evaluation ordering in `formatMath` to prevent operator prefix collisions (`\left` transforming to `≤ft`) and unescaped currency strings (`\$18,291.00`).
- **Interactive Playground Layouts**: Enhanced `.interactive-widget` container styling in `styles.css` with responsive flexbox layouts and real-time state feedback across all 8 simulator widgets.
- **Content Security Policy Alignment**: Updated `index.html` CSP `connect-src` to permit Cloudflare Web Analytics beacons (`cloudflareinsights.com`).

---

## [1.1.0] - 2026-08-18

### Added
- **Zero-Trust Dynamic Feed Discovery**: Zero-dependency HTML `<link rel="alternate">` parser and well-known endpoint prober (`discover_feed_endpoints`) for autonomous RSS 2.0, Atom 1.0, and JSON Feed discovery without brittle static whitelists.
- **Pre-Flight Forensic Audit & Shannon Topic Entropy ($H_{\text{topic}}$)**: Pre-ingestion forensic auditor calculating Shannon entropy penalized by top-token concentration ratio ($C_{\text{top3}}$) to mathematically detect commercial takeovers, sponsored native ads, and astroturfing pivots (The "Pizza Hut Problem").
- **Dynamic Feed Quality Scoring ($F_j$) & Autonomous Eviction**: 4-factor composite feed health index ($F_j = 0.35(1 - \bar{S}/100) + 0.25G + 0.20H + 0.20T$) with automated probation ($<0.70$) and mesh-wide eviction quarantine ($<0.40$).
- **Real-Time Feed Sifter Daemon**: Background async sifter daemon with jitter scheduling, conditional HTTP 304 caching, and Rendezvous Hashing (HRW) P2P mesh work-sharing yielding 92.3% compute savings at $0.00 token cost.
- **Morning Epistemic Digest Briefing Engine**: Automated daily briefings aggregating the past 24 hours of evaluated coverage into Clean Journalism, Rhetorical Fallacies, Deceptive Flags, Satire Alerts, and Compute Savings metrics.
- **Universal 4-Interface Synchronous Parity**:
  - **CLI**: Added `feed discover`, `feed inspect`, `feed health`, `feed bootstrap-presets`, `sifter`, and `digest`.
  - **FastMCP 2.0**: Added `credence_discover_feeds`, `credence_inspect_feed_health`, `credence_generate_digest` tools and `credence://digest/morning` resource.
  - **Textual TUI**: Added Morning Digest tab (`tab_digest`) and live dynamic quality ranking table columns.
  - **Zero-Build Web UI**: Added Section 8 interactive Feed Quality & Astroturfing Simulator in `docs/playground.md`.
- **Tutorial 09 & Sovereign Blog Essay**: Published [Tutorial 09: Zero-Trust Feed Sifter & Morning Digest](tutorials/09-zero-trust-feed-sifter-digest.md) and [The Pizza Hut Problem & Topic Entropy](../blog/the-pizza-hut-problem.md).
- **Cloudflare Multi-Domain Edge Hardening & Performance**:
  - Provisioned **HTTP/3 (QUIC)**, **Early Hints (103)**, and **0-RTT connection resumption** across all 4 production zones (`credence.run`, `credence.nexus`, `credence.foundation`, `credence.report`).
  - Strict SSL/TLS enforcement, automatic HTTPS rewrites, and zero-latency P2P SRV routing via Terraform IaC ([`terraform/cloudflare.tf`](https://github.com/artibyrd/credence/blob/main/terraform/cloudflare.tf)).
  - AI Crawler policy governance with unhindered coding assistant access (Claude Desktop, Cursor, Antigravity) and zero-build edge routing.
- **Architectural Boundary Blueprint & Municipal Governance Catalog**:
  - Published [Managing Customizations vs. Core Upstream](operations/customizations-and-upstream-sovereignty.md) establishing strict 4-tier boundaries between Upstream Core, Gitignored Database State, Local Overlays, and Sovereign Deployments.
  - Added universal [Local News & Municipal Governance](https://github.com/artibyrd/credence/blob/main/credence/subjects/catalogs/municipal_governance.yaml) semantic subject catalog (`journalism.news.municipal_governance`) with conflict-of-interest detection rubrics.

---

## [1.0.1] - 2026-08-17

### Added
- **Multi-Cloud Production Deployment**: Provisioned and live-verified GCP Cloud Run v2 (`credence-server`) and Cloudflare multi-domain edge routing.
- **FastMCP 2.0 Live SSE Endpoint**: Real-time Server-Sent Events streaming on `https://mcp.credence.run/sse` with session assignment and CORS preflight handling.
- **Zero-Build Multi-Domain Edge Router**: Cloudflare Worker (`_worker.js`) routing across `credence.run`, `credence.nexus`, `credence.foundation`, and `credence.report` with 0 npm dependencies.
- **Air-Gapped Genesis Root Key Ceremony**: Generated network root Ed25519 keypair and published canonical RFC 8785 signed `peers.json` and pinned `root.pub`.
- **Streamlined Operator Justfile Recipes**: Added `just gcp-build`, `just tf-plan`, `just tf-apply`, and `just seed-sync` for one-command deployment.
- **Hermetic Documentation Integrity Test Suite**: Added `tests/test_docs_integrity.py` validating 47 docs, 7 interactive widgets, and zero-npm compliance in <0.1s.
- **Platform Portability Specifications**: 5 comprehensive specifications for multi-model adapters (Claude 3.7 Sonnet, GPT-4o, DeepSeek-R1, local Ollama) and multi-cloud deployment (AWS, Azure, Hetzner, K8s).
- **Interactive Model Cost Comparator**: Section 7 in `docs/playground.md` for real-time model cost, latency, and sovereignty trade-off analysis.

### Changed
- **Hostname-Aware Dynamic Routing**: Decoupled `docs.credence.run` (technical documentation portal) and `blog.credence.run` (sovereign editorial publication) within a unified zero-build engine.
- **Token Safety Governor**: Updated model tiering to pin `gemini-3.7-flash` as primary reasoning engine across `BALANCED` and `ULTRA` profiles with thinking token budgets ($1,024 \dots 16,384$).

### Fixed
- **Transport Security Host Header Validation**: Configured `TransportSecuritySettings` on FastMCP SSE app to allow public domain proxies and Cloudflare CDN headers without `Invalid Host` rejections.
- **Asset Boundary Protection**: Configured `.assetsignore` and `binding = "ASSETS"` in `web/wrangler.toml` to prevent Cloudflare Worker build errors.

---

## [1.0.0] - 2026-08-17

### Added
- **Core Ingestion & Dual Capture**: Playwright Chromium headless engine and Trafilatura content extraction with memory-safe concurrency gates and SSRF defense.
- **Epistemic Scoring & Saturation Math**: 4-specialist evaluation pipeline (Truth, Harm, Fallacies, Deceptive Patterns) with exponential saturation scoring.
- **Verbatim Grounding Validator**: Whitespace-insensitive character-offset citation verification ($G=1.0$) with 50% slash penalty on hallucinated quotes.
- **P2P Mesh Network Engine**: 13-node Watts-Strogatz small-world gossip diffusion, Bayesian consensus aggregator, and Byzantine fault tolerance ($3f+1$).
- **The Galileo Rule**: Asymmetric evidence weighting preventing Sybil cartels from overriding verified domain authorities.
- **Zero-Build Web UI & Textual TUI**: Vanilla HTML5/ES modules web suite and interactive terminal workstation (`credence tui`).
- **Golden 12 Benchmark Suite**: Multi-profile cross-entropy and accuracy evaluation suite (`just benchmark`).
