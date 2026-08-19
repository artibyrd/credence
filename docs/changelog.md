# Release Changelog

All notable changes to the **Credence** network and documentation are documented here following [Semantic Versioning](https://semver.org/).

## [1.11.0] - 2026-08-18

### Added
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
    - **Phase 5: Web Hydration**: Auto-exports `reports.json` for immediate Zero-Build Web UI parity.
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
    - Expanded server runtime to combine FastMCP 2.0 SSE transport with Starlette REST API endpoints (`/health`, `/api/health`, `/api/reports`, `/api/reports/{id}`, `/api/audit`, `/api/sifter/status`, `/api/sifter/cycle`, `/api/feeds/stream`).
    - Added `--sifter` flag to `credence serve` and ASGI lifespan management for background `SifterDaemon`.
    - Added `--once` flag to `credence sifter` for single-cycle execution in cron or batch environments.
    - Added `credence export-catalog` CLI subcommand exporting SQLite database state to static `reports.json` catalog.
  - **Cloudflare Worker Edge Router REST Proxying (`web/_worker.js`)**:
    - Added transparent reverse proxying for `/api/*` and `/health` requests across all hosted domains to Google Cloud Run backend with full CORS headers.
  - **Zero-Build Web UI Dynamic Auto-Discovery (`credence.report/viewer.html` & `index.html`)**:
    - Implemented dynamic API base detection auto-switching between local `http://localhost:8000` during local development and `/api` on production.
    - Added async dynamic corpus fetching from `/api/reports`, falling back gracefully to static `reports.json` and embedded scenarios.
  - **Zero-GCP Portability & Seed Automation**:
    - Added `just seed-reports`, `just serve-sifter`, `just sifter-once`, and `just export-catalog` recipes.
    - Documented 100% self-hosted, air-gapped local execution without commercial cloud lock-in in `docs/portability/multi-cloud-deployment.md`.

## [1.5.1] - 2026-08-18

### Added
- **Multi-Display Mode Switcher & Machine-Ingestible Options across 4 Interfaces**:
  - **Zero-Build Web UI (`credence.report/viewer.html`)**: 3-way Display Mode Switcher (`[🧠 Human]`, `[⚡ Compact]`, `[🤖 Machine (JSON)]`) with URL query parameter sync (`?view=human|compact|raw`). Dynamic Schema.org `ClaimReview` JSON-LD in DOM `<head>`.
  - **Rich Terminal CLI (`credence/cli/main.py`)**: Universal `--format {human,compact,json,ndjson,tsv}` flag across `credence audit`, `credence lookup`, and `credence report`.
  - **FastMCP 2.0 Server (`credence/server/app.py`)**: `credence://reports/{identifier}/compact` and `credence://reports/{identifier}/raw` resources.
  - **Textual TUI Workstation (`credence/tui/app.py`)**: `v` keyboard shortcut cycling live inspector view modes between Rich Human, Compact Dense, and Raw JSON.
- **Categorical Epistemic Audit Discovery & Stream Explorer**:
  - Quick Discovery Toolbar on Web UI, `credence report browse` CLI subcommand, `credence_browse_audits` tool, and `r` shortcut in TUI.

## [1.5.0] - 2026-08-18

### Added
- **Human-Centered Epistemic Report Viewer across 4 Interfaces**:
  - **Zero-Build Web UI (`credence.report/viewer.html`)**: In-context reading mode with color-coded highlight markers, Executive Epistemic Briefing, and 5 interactive tabs.
  - **Textual TUI Workstation (`credence/tui/app.py`)**: Dual-Pane Inspector Split with live search filter and keyboard shortcuts (`o`, `e`, `f`).
  - **Rich Terminal CLI (`credence/cli/main.py`)**: Executive Briefing panel and Epistemic Trust Dimensions meters.
  - **FastMCP 2.0 Server (`credence/server/app.py`)**: `format: str = "json"` on `credence_get_audit`, `credence://reports/{id}/human` resource, and `explain_audit_report_prompt`.
  - **FastMCP Text Evaluation Persistence**: SQLite persistence with `text://inline` pseudo-URLs for all standalone text evaluations.

## [1.4.0] - 2026-08-18

### Added
- **Reusable Live Rotating & Mutating E2E Test Suite (`just test-live`)**: Stratified Master Corpus with deterministic daily seed rotation (`YYYY-MM-DD`).
- **6-Tier Testing Strategy & Verification Architecture**: Comprehensive testing guide (`docs/protocols/testing-strategy.md`).
- **Tutorial 10 & Verification Pyramid Essay**: `docs/tutorials/10-reusable-live-e2e-and-mesh-gauntlet.md` and `blog/the-six-tier-pyramid-of-decentralized-truth.md`.

## [1.3.0] - 2026-08-18

### Added
- **36 Invariants Reference Catalog & Deep Linking**: Expanded `docs/invariants.md` with individual DOM IDs (`#invariant-1` to `#invariant-36`).
- **Rich Frontmatter Metadata & Zero-Build Faceted Search**: Interactive metadata badge rows and search filter pills.
- **Dedicated Agentic Engineering Documentation Category**: 5 comprehensive guides and architectural essay.

## [1.2.0] - 2026-08-18

### Added
- **GCP-Style Tabbed Interface Switching (`:::tabs` / `=== Tab Name`)**: Accessible dark glassmorphism tabbed containers.
- **Global Cross-Document Preference Persistence (`localStorage`)**: Persists interface modality across docs.
- **4 Feature Walkthrough Articles**: End-to-end multi-surface guides.

## [1.1.1] - 2026-08-18

### Added
- **Zero-Build Mermaid.js Engine Integration**: Vendored Mermaid v10.9.1 engine (`assets/mermaid.min.js`).
- **Automated Live Rendering Test Suite**: Playwright Chromium test suite verifying 0 rendering errors.

## [1.1.0] - 2026-08-18

### Added
- **Zero-Trust Dynamic Feed Discovery & Quality Scoring ($F_j$)**: HTML autodiscovery, Shannon topic entropy ($H_{\text{topic}}$), and eviction quarantine.
- **Real-Time Feed Sifter Daemon & Morning Epistemic Digest**: Background sifter daemon with HRW Rendezvous Hashing.
- **Cloudflare Multi-Domain Edge Hardening**: HTTP/3 (QUIC), Early Hints, and 0-RTT connection resumption.

## [1.0.1] - 2026-08-17

### Added
- Multi-cloud production deployment on GCP Cloud Run and Cloudflare Workers.
- FastMCP 2.0 SSE endpoint on `https://mcp.credence.run/sse`.
- Air-gapped Genesis root key ceremony.

## [1.0.0] - 2026-08-17

### Added
- Initial release of Credence: Core Ingestion, Epistemic Scoring, Verbatim Grounding Validator, P2P Mesh Consensus, Textual TUI, and Zero-Build Web UI.
