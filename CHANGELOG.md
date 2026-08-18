# Changelog

All notable changes to the **Credence** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Universal 4-Interface Synchronous Parity**: CLI (`feed`, `sifter`, `digest`), FastMCP 2.0 (`credence_discover_feeds`, `credence_inspect_feed_health`, `credence_generate_digest`, `credence://digest/morning`), Textual TUI (`tab_digest`), and Zero-Build Web UI (Section 8 Playground).

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
