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
