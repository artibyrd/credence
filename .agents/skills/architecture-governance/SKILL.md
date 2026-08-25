---
name: architecture-governance
description: Enforces the 500 LOC Ceiling Law across Python and Justfiles, compute_* calculation naming ontology, zero-npm web invariant, modular subpackage decoupling, and shift-left intelligent guidance banners.
---

# Architecture Governance & Modularity Skill (`architecture-governance`)

Use this skill when refactoring, modularizing, or auditing source files, Justfiles, and subpackages across the Credence ecosystem to ensure strict adherence to modularity standards.

---

## 1. Core Modularity Laws

### 1. 500 LOC Ceiling Law across Code & Toolchains
- **Strict Hard Limit**: No individual source file (`.py`, `.js`, or `.just`) may exceed **500 Lines of Code (LOC)**.
- **Decomposition Pattern**: Large modules must be decoupled into cohesive subpackages with focused responsibilities:
  - **CLI**: Decomposed into a 3-tier subpackage architecture (<350 LOC per file):
    1. `helpers.py`: Programmatic helper functions and API adapters for test suites and library consumers (<200 LOC).
    2. `dispatch.py`: Subcommand execution handler and async/sync routing dispatcher (<200 LOC).
    3. `main.py`: Lean `build_parser()` argument tree and `main() -> dispatch_command(args)` entrypoint (<350 LOC).
  - **Server**: Decomposed into `lifespan.py`, `middleware/`, `mcp/`, `api/`, and lean Starlette application assembler `app.py` (<150 LOC).
  - **TUI**: Decomposed into `screens/`, `widgets/`, and lean app controller `app.py` (<250 LOC).
  - **Mesh**: Decomposed into `topology.py`, `badges.py`, `merit.py`, `stats.py`, and `models.py`.
  - **Subjects**: Decomposed into `analytics.py`, `weather.py`, and `models.py`.
  - **Justfile Toolchains**: Decomposed into a lean root `Justfile` (<80 LOC) importing focused subfiles under `just/` (`preflight.just`, `quality.just`, `engine.just`, `deploy.just`, `release.just`).

### 2. `compute_*` Naming Ontology Invariant
- **Standardized Prefix**: All calculation and metric derivation functions must strictly use the `compute_*` prefix.
- **Banned Prefixes**: Functions starting with `calc_*` or `calculate_*` are disallowed across all modules and tests.
- **Examples**: `compute_topic_entropy`, `compute_half_life_uptime`, `compute_longevity_days`, `compute_effective_weight`, `compute_subject_expertise`.

### 3. Circular Dependency Elimination
- Data structures and Pydantic/dataclass models must reside in dedicated `models.py` modules within each subpackage.
- Inter-module dependencies must flow strictly in a Directed Acyclic Graph (DAG) with zero circular imports.
- Subpackage public APIs must be cleanly exposed via `__all__` lists in `__init__.py` or subpackage entrypoints.

### 4. Zero-Mock Dashboard & Telemetry Invariant (`inv-production-telemetry-boundary`)
- **Authentic State Reporting**: Operator dashboards must strictly report authentic daemon telemetry ($N \ge 1, f = \lfloor (N-1)/3 \rfloor$).
- **No Simulation in Production**: Simulators and chaos tools belong exclusively in the interactive documentation playground (`docs/playground.md`); production surfaces must never contain demo dropdowns or mock generators.

### 5. Vector SVG Illustration Architecture & Anti-Pseudo-Diagram Standard
- **Never Degrade Diagrams to Raw Text**: When eliminating ASCII art, never downgrade architectural flows, pipelines, or topologies into loose text paragraphs or unformatted bullet points.
- **Dedicated Vector SVG Assets**: Every system architecture, protocol sequence, or attack model must be implemented as a dedicated Vector SVG Illustration under `assets/illustrations/<slug>.svg`.
- **Visual Design Tokens**:
  - `viewBox="0 0 880 380"` (or `880 440` for multi-stage pipelines).
  - Background: Dark gradient `#090d16` to `#050810` with subtle boundary stroke `rgba(56, 189, 248, 0.2)`.
  - Cards: Drop-shadowed `#0f172a` cards with colored status headers and directional vector markers (`#38bdf8`, `#22c55e`, `#ef4444`).
- **Markdown Figure Embedding**: Embed via standard markdown figure syntax `![Figure X.Y: Substantive Description](assets/illustrations/<slug>.svg)` which `app.js` mounts as `<figure class="doc-illustration"><img ... /><figcaption>...</figcaption></figure>`.
- **Structured Markdown Tables**: Accompany every illustration with a structured GitHub-flavored Markdown table defining parameter lattices, operational stages, or component responsibilities.

### 6. Anti-Pseudo-Box & Truncation Guardrail (Shift-Left Gate 8)
- **Zero Pseudo-Boxes**: Disallow dashed lines (`--- ---`, `--------------------+`), loose pipe characters outside valid markdown tables (`| •`, `| 🚀`, `- ... | • ...`), and bare ASCII arrow flows (`▼`, `▲`, `--►`) in documentation prose.
- **Zero Truncation**: Disallow truncated lines or broken box borders (`<300M|`).
- **Enforcement**: Gate 8 in `tests/governance/test_docs_integrity.py` statically enforces this invariant across all 194 markdown files.

### 7. Zero-Hash Clean URL Routing & Canonical Slugs Law (`inv-clean-slug-routing`)
- **Path vs. Hash Separation**: Document paths and essay slugs must strictly reside in `window.location.pathname` (e.g. `https://blog.credence.run/the-pizza-hut-problem` and `https://docs.credence.run/protocols/scoring`). Hash fragments (`#<id>`) are reserved exclusively for in-page DOM element IDs and section headings.
- **Zero Backwards-Compatibility Overhead**: Prohibit legacy `#blog/...` or `#docs/...` hash routing handlers. Keep canonical URLs clean, robust, and free of legacy cruft.
- **HTML5 History API Navigation**: Internal link navigation must use `history.pushState(null, '', nextUrl)` with active `popstate` event listeners for instant, zero-reload transitions.
- **Cloudflare Pages SPA Architecture**: All zero-build documentation and blog sites deployed to Cloudflare Pages must include `_redirects` (`/* /index.html 200`) and a dynamic `<base>` tag initializer in `<head>` to ensure relative assets and ES module imports resolve properly across multi-level clean paths.

### 8. Anti-Headless Article Law & Leading H1 Invariant (`inv-article-h1-header`)
- **Mandatory Leading H1**: Every documentation file and editorial article must include a top-level `# <Title>` heading immediately following the frontmatter block.
- **Title Concordance**: The leading `# <Title>` heading text must match the frontmatter `title:` attribute.
- **Defensive SPA Rendering**: The client-side markdown parser (`parseMarkdown` in `app.js`) must defensively prepend `<h1>${frontmatter.title}</h1>` if a document body omits a leading H1 header, preventing any article from rendering "headless".

---

## 2. Shift-Left Intelligent Guidance & Workflow Chaining

### 1. Point-of-Action Guidance Banners
- **Context Economy**: Rather than overloading root prompt memory with procedural checklists, embed colorized terminal banners in `Justfile` recipes and helper scripts (`manage_pr.py`, `sync_version.py`).
- **Active Beacon Parsing**: Agents executing toolchain commands must actively parse and follow directional beacons printed by `Justfile` recipes.

### 2. Workflow State Chaining
- Toolchain commands must be chained so each successful step points directly to the next phase:
  - `implementation_plan.md` $\to$ Declares target semantic version (`vX.Y.Z`)
  - `just check` $\to$ Verifies parallel pre-commit QA gates (<3s)
  - `just sync-version <version>` $\to$ Synchronizes all 7 version manifests prior to PR staging
  - `just pr-create '<title>'` $\to$ Creates staged PR triad with `[vX.Y.Z]` title prefix
  - `just ci-watch` $\to$ Monitors `deploy-dev.yml` deploying container reporting `vX.Y.Z`
  - `just cloud-probe` $\to$ Verifies `/health` reports `vX.Y.Z` before Mk1 review
  - Mk1 Eyeball Review $\to$ Human sign-off on PRs and live Dev endpoints
  - `just pr-merge` $\to$ Merges PR triad into `main`
  - `just release <version> <msg>` $\to$ Tags and releases on production

### 3. Conventional PR Title & Scope Taxonomy
- **Strict Scope Taxonomy**: The CI gate strictly enforces conventional PR scopes. Scopes MUST strictly be one of:
  - `(governance)`: Invariant audits, skill updates, knowledge governance, policies.
  - `(forensics)`: Evidence extraction, DOM hashing, scrubber heuristics, parser guards.
  - `(mesh)`: P2P gossip, Watts-Strogatz clustering, consensus aggregation, Sybil defense.
  - `(crypto)`: Ed25519 signatures, RFC 8785 canonical JSON, node identity envelopes.
  - `(ui)`: Web workstations, CSS styling, components, TUI, CLI formatting.
  - `(ops)`: CI/CD workflows, Terraform, Cloud Run deployments, Dockerfiles, Justfiles.
- **PR Title Format**: `[vX.Y.Z] <type>(<scope>): <imperative summary>` (e.g. `[v2.10.0] feat(governance): add weighted median consensus`).

---

## 3. Epistemic Anti-Spoofing & Grounded Embed Governance

### 1. Zero Synthetic Dummy Fallbacks
- Client web components (`<credence-badge>`) and widgets must never render mock Ed25519 public keys (`ed25519:e3b0c44...41a7`), synthetic trajectory sparklines (`+2.4 pts (Improving)`), or fake digest placeholders.
- If telemetry is uninitialized, explicitly render `None Provided (Standalone)` or `Criteria Pending`.

### 2. Fail-Closed Unearned Milestones
- Any embed endpoint (e.g. `/api/badge/{id}`) or UI generator must strictly query canonical node merit (`get_local_node_merit()`).
- Unearned milestones must return **`UNEARNED`** in muted slate (`#475569` to `#334155`), and UI generator embed copy buttons must lock to prevent distribution of forged credentials.

### 3. Live In-Browser WebCrypto Anti-Tamper Hashing
- Never claim cryptographic tamper protection in comments without executing `window.crypto.subtle.digest('SHA-256')`.
- Web components must dynamically compute live DOM text hashes (`computeLiveDomHash`) to detect post-audit page tampering (`MODIFIED_POST_AUDIT`).

---

## 4. UI/UX Deck Architecture & Modality Grids

### 1. Balanced Modality Card Grids
- For major functional modalities (e.g. Node Epistemic Merit, Publisher DCI, Article Attestation), use prominent, self-describing interactive cards (`.studio-modality-grid`) with icons, bold titles, and explanatory subtitles rather than cramped inline button strips.

### 2. Balanced 50/50 Responsive Deck Layouts
- Workstation configurations and live stage previews must share equal visual weight using responsive grids (`repeat(auto-fit, minmax(360px, 1fr))`), avoiding asymmetric columns that compress configuration controls.

### 3. Minimalist Render Styles
- Avoid proliferating speculative or fragile badge styles. Keep only clean, battle-tested styles (e.g. Interactive Web Component and High-Contrast Shield).

### 4. Dense Workstation Viewport & Zero-Masking Invariant
- High-density card grids must be enclosed within `.ws-scroll-pane` (`max-height: 580px; overflow-y: auto;`).
- Table headers must remain sticky during deep scrolling (`thead th { position: sticky; top: 0; }`).

---

## 5. Fail-Closed UI Architecture & Zero-Mock Telemetry Invariant

### 1. Absolute Prohibition of Synthetic Mock Fallbacks
- **Zero Mock Data in Live Workstations**: Client scripts in `web/` must NEVER import, define, or fall back to synthetic mock datasets (`MOCK_NODES`, `MOCK_REPORTS`, `mock_claims`).
- **Simulations Isolated to Docs Playground**: Simulators and chaos models belong exclusively in documentation playground sandboxes (`credence-docs/playground`) or offline research tools (`tools/simulations/`), never in operator workstation bundles (`web/`).

### 2. Mandatory Fail-Closed Empty State Cards
- When an API endpoint fails, returns an empty array, or is offline:
  1. Set state explicitly to `STANDALONE`, `NO DATA`, or `CRITERIA PENDING`.
  2. Render an explicit high-contrast Empty State Card (`.ws-empty-card`) with an explanatory icon (`📡`), title, and remediation instructions.
  3. Never mask the empty state with synthetic "sample" data.

### 3. Zero Mock Tokens & Synthetic Digests
- Prohibited in all web surfaces:
  - Hardcoded Ed25519 keys (e.g. `ed25519:e3b0c44...41a7`).
  - Hardcoded sparkline trajectories (e.g. `+2.4 pts (Improving)`).
  - Dummy scores or synthetic consensus badges.

---

## 6. Scoped Workstation CSS & Viewport Isolation

To prevent compact workstation layout locks from freezing natural document scrolling on landing pages (`credence.run`), blogs (`blog.credence.run`), and documentation (`docs.credence.run`):

1. **Mandatory `:has()` Container Scoping**:
   - `height: 100vh; overflow: hidden;` must NEVER be applied unconditionally to global `html, body`.
   - Always scope desktop workstation layout to container presence:

```css
@media (min-width: 921px) {
  html:has(.workstation-container),
  body:has(.workstation-container) {
    height: 100vh;
    overflow: hidden;
  }
  body:has(.workstation-container) {
    display: flex;
    flex-direction: column;
  }
}
```

2. **Landing & Documentation Page Freedom**:
   - All document, marketing, and reading surfaces must retain unconstrained natural scrolling (`overflow: auto`, natural document height).

---

## 7. Public-Facing Copy vs. Forensic Deep Lens Boundary (Plain-English Invariant)

### 1. Top-of-Funnel Clarity & Plain-English Imperative
- **Audience-Centric Communication**: Open Graph social preview cards (`og-card.png`), landing page hero banners, and public embeds must communicate value in clear, accessible plain English (e.g. *"Verify Truth on the Web. Evidence, Not Algorithms"*).
- **Demarcation of Internal Constants**: Mathematical constants ($G=1.00$, $H<0.30$, $3f+1$, RFC 8785 canonical envelopes) are internal engineering benchmarks. They must NEVER be advertised on top-of-funnel social cards or public hero headers without explanatory context.
- **Proper Placement**: Reserve mathematical formulas and cryptographic verification tags strictly for Focus Lenses, Deep Forensic Modals, and technical documentation.

---

## 8. Dynamic Origin-Aware Edge Metadata Rewriting

### 1. Multi-Environment Open Graph Parity
- Edge routers (`_worker.js`) must inspect the incoming request origin (`url.origin` / `Host`) and dynamically rewrite `<meta property="og:image">` and `<meta property="og:url">` using streaming `HTMLRewriter`.
- **Zero Hardcoded Cross-Origin Escape**: Previews shared from staging/dev environments (e.g. `https://dev.credence.nexus`) must resolve their assets from the active preview domain without 404 image load failures or escaping to production.

---

## 9. Unified Checkmark Shield Brand & Favicon Suite

### 1. Canonical Vector Asset
- All web surfaces, navigation headers, and modal footers must reference the official Cyan Gradient Glow Checkmark Shield ([`assets/logo.svg`](file:///home/pendragon/Projects/credence-ecosystem/credence/web/assets/logo.svg)).

### 2. Universal Favicon Suite
- All HTML templates must include standard favicons:
  - Vector Favicon: `<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">`
  - Raster Favicon: `<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon.png">`
  - Apple Touch Icon: `<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">`

---

## 10. Architectural Technical Schematics & Figcaption Invariant

### 1. Genuine Technical Schematics (Prohibition of "Text in Boxes with Arrows")
- **Structural Modeling**: Technical illustrations must model concrete architectural mechanics: multi-stage data pipelines, state transition machines, decentralized P2P network topologies, closed entity feedback loops, or branching decision trees.
- **Prohibition of Generic Text Cards**: Never dump bullet points from article text into generic card templates with connecting arrows. If a visual does not convey structural relationships, flows, or state transitions beyond plain text, it is visual clutter.
- **Prohibition of Decorative Pills & Line Text**: Ban decorative pill badges and text placed directly on top of connecting arrow lines to prevent visual collision and unreadable overlaps.

### 2. Visible Descriptive Figcaptions Below Every Diagram
- **Context-Specific Alt Text**: Every diagram must declare an explicit, descriptive alt text explaining *what the diagram illustrates* (e.g. `Figure 1.1: Circular conflict feedback loop between municipal governance and newsroom monopoly, and Credence forensic audit layer`).
- **Prohibition of Title Duplication**: Alt text must never repeat the article title, section header, or generic placeholder copy.
- **Visible Display**: The documentation markdown parser (`app.js`) wraps illustrations in `<figure class="doc-illustration">` with a high-contrast `<figcaption>` directly below each graphic, ensuring immediate human reviewability of intended vs depicted mechanics.
- **Shift-Left Automated Integrity Gate**: Enforced in Tier 2 via `test_doc_illustrations_require_descriptive_figcaptions` in `tests/governance/test_docs_integrity.py`.

### 3. Curated Placement & Decorative Pruning
- **High-Value Placement**: Position diagrams directly within the subsection that explains the technical concept, rather than defaulting to top-of-article decorative banners.
- **Reference Cleanliness**: Pure reference manuals, CLI argument tables, changelogs, topic indices, and sitemaps must remain clean, legible text without forced decorative illustrations.

### 4. Post-Reduction "Wall of Text" Narrative Visual Audit
- **Density Auditing**: Following architectural reductions, audit narrative-heavy blog essays and philosophical treatises for "wall of text" reading fatigue.
- **Targeted High-Fidelity Conceptual Visuals**: Where visual breathing room is needed but a formal architectural schematic is not suitable, generate targeted, high-fidelity conceptual illustrations that capture the specific investigative or philosophical premise with zero generic filler.

---

## 11. Justfile Modularization, Recipe Groups & Approval Bootstrapping

### 1. Modular Subfile Architecture (<300 LOC per file)
- The Justfile suite must be partitioned into decoupled submodules under `just/` (`preflight.just`, `quality.just`, `engine.just`, `vcs.just`, `cloud.just`, `release.just`).
- Root `Justfile` acts solely as an orchestrator with modern settings (`set shell := ["bash", "-c"]`, `set dotenv-load := true`) and modular imports.

### 2. Discrete Safe vs. Gated Decoupling
- **No Parameterization Bleed**: Never combine read-only inspection with mutating actions inside parameterized recipes.
- **Safe Commands**: Must be isolated into distinct recipes (`status`, `git-diff`, `pr-status`, `cloud-status`, `edge-status`) assigned to safe recipe groups (`[group('vcs: safe')]`, `[group('hosted: safe')]`).
- **Gated Commands**: Mutating operations (`branch`, `commit`, `pr-create`, `pr-merge`, `cloud-deploy-prod`, `release`) must be assigned to gated recipe groups (`[group('vcs: gated')]`, `[group('hosted: gated')]`) with native `[confirm('...')]` safety gates.

### 3. Approval Bootstrapping Runner
- Maintain `scripts/bootstrap_approvals.py` (`just bootstrap-approvals`) to walk through all primary safe command shapes sequentially, enabling developers in fresh workspaces to prime their IDE approval cache with "Always Allow" in a single pass.

---

## 12. Minimal UI Navigation Labels & Anti-Overrun Ergonomics

When designing compact navigation controls, plane switchers, and sidebar toggles:

1. **Concise Punchy Labels**:
   - In constrained header controls and multi-button groups, prefer minimal, clean text labels (e.g. `[ Docs | Blog ]`) over verbose descriptors (e.g. `[ ✍️ Sovereign Blog ]`).
   - Long labels or excessive emojis risk container overflow and visual collision across mobile or compact desktop sidebars.
2. **Context-Aware Subdomain Dispatch**:
   - Navigation links across distinct functional properties must resolve to canonical subdomains (`docs.credence.run` vs `blog.credence.run`) rather than intra-domain hashes that conflate editorial and documentation planes.
3. **Cache-Busted Static Asset References**:
   - All static CSS and JS script tags must include `?v=${VERSION}` query parameters to ensure instant cache invalidation upon releases.




