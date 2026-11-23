# Architecture Review — Credence Project Overlay

Self-contained Credence architectural policy. Applies automatically on top of `architecture-review` when `antigravity-customizations` is installed, and serves as a standalone Credence architecture rulebook on any agent harness.

---

## Overrides

- **Deep Modules & 1,000-LOC Anti-God-File Safety Rail (D1):** Prefer Ousterhout Deep Modules (rich behavior behind small public seams). Treat `~500 LOC` as a soft *internal* decomposition trigger rather than a rigid ceiling that splinters cohesive logic into shallow public wrappers. A hard Tier 2 safety rail (`test_500_loc_ceiling_invariant`) fails at **1,000 LOC** on `.py` and `.js` source files.
- **Zero-Build Vanilla ES Modules (`inv-zero-build-standards`):** Web surfaces (`credence/web/` and `credence-docs/`) strictly prohibit `npm`, `package.json`, `package-lock.json`, `node_modules`, and JS bundlers. Use native ES Modules with explicit symbol imports (`import { foo } from './submodule.js'` — never rely on `export *` to bind local identifiers), run an automated cross-module unresolved-import static scan across `.js` files whenever decomposing ES modules, and append `?v=${VERSION}` cache-busting query parameters on static CSS/JS tags.

---

## Extensions

### 1. Python Subpackage Topology & `compute_*` Naming Ontology
- **`compute_*` Naming Law:** Every pure calculation and metric derivation function MUST use the `compute_*` prefix (`compute_topic_entropy`, `compute_half_life_uptime`, `compute_effective_weight`, `compute_thinking_config`). Prefixes `calc_*` and `calculate_*` are banned by Tier 2 AST gate `test_compute_naming_ontology_invariant`.
- **DAG Subpackage Boundaries & `models.py`:** Keep Pydantic/dataclass schemas in dedicated `models.py` modules, enforce strict DAG imports (zero circular imports), and expose subpackage public APIs cleanly via `__all__`:
  - `credence/cli/`: `helpers.py`, `dispatch.py`, `main.py`
  - `credence/server/`: `lifespan.py`, `middleware/`, `mcp/`, `api/`, `app.py`
  - `credence/tui/`: `screens/`, `widgets/`, `app.py`
  - `credence/mesh/`: `topology.py`, `badges.py`, `merit.py`, `stats.py`, `models.py`
  - `credence/subjects/`: `analytics.py`, `weather.py`, `models.py`
- **Modular Justfiles:** Keep root `credence/Justfile` lean (`<80 LOC`) importing focused `just/*.just` modules (`preflight.just`, `quality.just`, `engine.just`, `vcs.just`, `cloud.just`, `release.just`). Isolate read-only inspection recipes (`[group('vcs: safe')]`, `[group('hosted: safe')]`) from state-mutating gated recipes (`[confirm('...')]`).

### 2. Epistemic Lensing & Information Pyramid (`inv-epistemic-lensing`)
Separate every audit report and workstation view into three progressive epistemic lenses:
- **Lens 1 (Surface Glance):** Plain-English executive verdict, qualitative bullets, pillar scores, and contextual cross-links. Zero mathematical formulas ($G=1.00$, $\Delta S$, $3f+1$) or raw cryptographic hashes on top-of-funnel hero cards or Open Graph images.
- **Lens 2 (Focus Evidence):** Verbatim DOM quotes ($G=1.00$), claim evaluations, and inline temporal diffs.
- **Lens 3 (Deep Forensic):** Mathematical proofs, RFC 8785 canonical JSON bytes, Ed25519 signatures, and topic entropy metrics.
- **Single-Source-of-Truth Score Parity:** Domain scores across browse, dossier, and DCI tables MUST compute from identical formulas ($\text{DCI} = 100 - \bar{S}$) and pre-initialize counts from pre-loaded catalogs to prevent UI count flashes.

### 3. `<credence-badge>` Anti-Spoofing & Zero-Mock Telemetry (`inv-production-telemetry-boundary`)
- **Zero Synthetic Fallbacks:** Live workstations (`web/`) and `<credence-badge>` components must NEVER render mock Ed25519 keys, synthetic trajectory sparklines, or sample datasets. Simulations belong strictly in `credence-docs/docs/playground.md` or `tools/simulations/`.
- **Fail-Closed Empty States & Unearned Milestones:** Query canonical `get_local_node_merit()`. Render unearned milestones in muted slate (`#475569` to `#334155`) as `UNEARNED` with locked embed copy buttons. Offline or empty API responses render an explicit `.ws-empty-card` (`STANDALONE`, `NO DATA`, or `CRITERIA PENDING`).
- **Live WebCrypto Anti-Tamper Hashing:** Execute real `window.crypto.subtle.digest('SHA-256')` (`computeLiveDomHash`) to detect `MODIFIED_POST_AUDIT` tampering; never fake verification with `setTimeout`.

### 4. Workstation Viewport, `:has()` Scoping & Brand Assets
- **Scoped Desktop Layout (`:has()`):** Never apply `height: 100vh; overflow: hidden;` globally to `html, body`. Scope desktop workstation locks strictly to `html:has(.workstation-container), body:has(.workstation-container)` inside `@media (min-width: 921px)` so docs, landing pages, and blog essays scroll naturally.
- **Dense Viewport Containers:** Enclose high-density card grids in `.ws-scroll-pane` (`max-height: 580px; overflow-y: auto;`), use `.ws-table-container` with sticky table headers (`position: sticky; top: 0; z-index: 2;`), apply consistent 6px cyan scrollbars across scroll containers, derive filter chip counts dynamically (`updateCategoryCounts()`), and ensure `.tab-panel.active` uses vertical flex scrolling without `overflow: hidden` clipping.
- **Cyan Checkmark Shield Brand & Favicon Suite:** Reference `assets/logo.svg` across headers/modals and include `/assets/favicon.svg`, `/assets/favicon.png` (32x32), and `/assets/apple-touch-icon.png` (180x180) on all HTML templates.
- **Balanced Decks, Minimalist Badges, Concise Navigation & Subdomain Separation:** Use `.studio-modality-grid` cards and `repeat(auto-fit, minmax(360px, 1fr))` responsive grids; keep only battle-tested badge styles (Interactive Web Component and High-Contrast Shield); place Publisher Dossier primary credibility hero scores in the top-right corner with stacked action buttons directly below; keep header plane-switcher labels concise (e.g., `[ Docs | Blog ]`) and route technical reference to `docs.credence.run` vs. sovereign essays to `blog.credence.run` (`getDocsBaseUrl()` / `getBlogBaseUrl()`).

### 5. Clean URL Routing, Origin-Aware `HTMLRewriter`, Docs Integrity & Dark-Theme Vector SVGs
- **Clean URL Paths (`inv-clean-slug-routing`):** Store doc and essay slugs strictly in `window.location.pathname` using HTML5 History API (`pushState`/`popstate`), Cloudflare Pages `_redirects` (`/* /index.html 200`), and dynamic `<base>` initialization. Reserve `#<id>` strictly for in-page anchor navigation: cache `currentLoadedDocId`, resolve multi-pattern anchors (direct `id`, `name`, `cleanId`, `inv-<slug>`, `invariant-<slug>`), compute dynamic clearance (`headerOffset = hasFilterBar ? 135px : 90px`), set CSS `html { scroll-behavior: smooth; scroll-padding-top: 135px; }` and `.invariant-card, [id] { scroll-margin-top: 135px; }`, auto-unhide `.scope-btn`/`<details>`, and apply a 2.5s `.highlight-anchor` cyan glow.
- **Leading H1, Companion Studies & Platform-Neutral Specs:** Every doc/article starts with `# <Title>` matching frontmatter `title:` (`parseMarkdown` defensively prepends `<h1>` if absent), links invariants canonically (`[`inv-...`](/docs/invariants#inv-...)`), actively cross-references related companion studies, uses zero `file:///` URIs, uses platform-neutral env naming (`CREDENCE_MODEL_API_KEY`), separates Minimum vs. Recommended hardware rows, and never labels a provider-specific Terraform stack (e.g., GCP Cloud Run) as generic multi-cloud without linking dedicated multi-cloud guides.
- **Dynamic Origin-Aware `HTMLRewriter`:** Edge workers (`web/_worker.js`) inspect request `url.origin` / `Host` and rewrite `<meta property="og:image">` and `<meta property="og:url">` dynamically so staging/dev previews never escape to production.
- **Dark-Theme Vector SVG Schematics & Narrative Visual Discipline:** Place architecture schematics under `credence-docs/assets/illustrations/<slug>.svg` with byte-identical copies in `credence/web/assets/illustrations/` (enforced by SHA-256 parity test). Use `viewBox="0 0 880 380"` (or `880 440`), dark background gradient `#090d16` to `#050810` with boundary stroke `rgba(56, 189, 248, 0.2)`, `#0f172a` cards, directional markers (`#38bdf8`, `#22c55e`, `#ef4444`), visible descriptive `<figcaption>` alt text, and an accompanying structured Markdown table (zero generic text-in-boxes or ASCII pseudo-boxes). Pure reference manuals, CLI tables, changelogs, topic indices, and sitemaps remain clean text with zero forced decorative illustrations; after architectural reductions, audit narrative-heavy essays for "wall of text" fatigue and add targeted high-fidelity conceptual visuals only where genuine breathing room is needed.
- **Multi-Model Sovereignty (`inv-multi-model-sovereignty`):** Keep LLM providers decoupled via `credence/pipeline/adapters.py` and `model_registry.py`; trip offline circuit breakers (`QUOTA_PRESERVED`) whenever model quota headroom falls below **30%**.

### 6. Docker Cache Hygiene
- Reclaim dangling container build caches via `just docker-clean` (safe) or `just docker-prune-all` (gated) after heavy Docker test or mesh runs.

---

## Disabled / Not Applicable

- None. All base `architecture-review` principles (Ousterhout Deep Modules, operational guardrails, safe DOM sinks, non-interactive CLI flags, Playwright lazy-image verification) apply in full.
