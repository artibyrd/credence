---
name: invariant-audit
description: Scan and audit AGENTS.md token budgets (<800 tokens), verify dynamic invariant canon naming ("The Invariant Bible"), validate 4-phase lifecycle compliance, audit Tier 1 progressive skill metadata, and execute shift-left integrity checks across all ecosystem surfaces.
---

# Living Invariant Audit & Governance Skill (`invariant-audit`)

Use this skill when auditing, verifying, or refactoring the **Living Canon of System Invariants**, `AGENTS.md` context budget, progressive skill declarations, or continuous learning workflows across the Credence ecosystem.

---

## 1. Core Audit Responsibilities

This skill enforces the **3-Tier Invariant Scalability Architecture** across five critical dimensions:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             INVARIANT AUDIT EXECUTION ENGINE                                     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                 [just audit-invariants]                                          │
│                                            │                                                     │
│      ┌─────────────────────┬───────────────┴───────────────┬─────────────────────┐               │
│      ▼                     ▼                               ▼                     ▼               │
│ ┌──────────────────┐ ┌──────────────────┐             ┌──────────────────┐ ┌──────────────────┐  │
│ │ 1. Token Budget  │ │ 2. Dynamic Canon │             │ 3. 4-Phase       │ │ 4. 7-Manifest    │  │
│ │    (<800 tokens) │ │    Bible Naming  │             │    Lifecycle     │ │    Parity        │  │
│ └──────────────────┘ └──────────────────┘             └──────────────────┘ └──────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Token Budget & Context Economy Audit
- Measures token consumption of `AGENTS.md` across all ecosystem repositories.
- Asserts that universal core rules strictly remain **< 800 tokens**.
- Flags procedural bloat (e.g. multi-step CLI commands, vendor-specific GCP flags) for refactoring into specialized Tier 1 skills.

### 2. Dynamic Invariant Canon Naming Audit
- Scans all public web surfaces (`web/`), documentation (`credence-docs/docs/`), sitemaps, and navigation footers.
- Asserts that invariant numerical counts (e.g. "36 Core", "38 Invariants") are never hardcoded.
- Enforces dynamic references to **The Invariant Bible** or **Living Canon of System Invariants**.

### 3. 4-Phase Delivery & Continuous Learning Lifecycle Audit
- Asserts that all ecosystem repositories declare the **4-Phase Release & Learning Lifecycle Invariant**:
  `1. Code & Local QA Gate -> 2. User Mk1 Eyeball Review -> 3. Feature Version Release -> 4. /learn Retrospective -> 5. Apply Lessons as Immediate Patch Release`.
- Validates that feature releases and patch releases are decoupled and properly documented in `docs/changelog.md` and `docs/roadmap.md`.

### 4. Progressive Disclosure & Skills Audit
- Audits `.agents/skills.json` and `.agents/skills/` directory structure.
- Verifies that all specialized skills have valid YAML frontmatter (`name`, `description`).
- Validates that enclosed UTF-8 technical box schematics and wire sequences are used across all skills.

### 5. 7-Manifest Semantic Version Parity & Pre-Staging Sync Audit
- Verifies simultaneous synchronization across all 7 version manifests:
  1. `credence/pyproject.toml`
  2. `credence/credence/__init__.py`
  3. `credence-docs/app.js`
  4. `credence/web/assets/credence-workstation.js`
  5. `credence-agent/plugin.json`
  6. Multi-domain HTML badges across all 5 web workstations
  7. Open Graph card assets (`og-card.svg` and `og-card.png`)
- **Dynamic Self-Auditing & Attestation Engine**: `just sync-version <version>` automatically triggers `@poetry run credence audit-docs --update`, dynamically deriving `__version__` from package metadata and minting Ed25519 cryptographic signatures in `credence-docs/assets/attestations.json`.

### 6. The 8 Shift-Left Automated Integrity Test Gates (`tests/governance/test_docs_integrity.py`)
- **Gate 1 (`test_docs_attestation_and_manifest_version_parity`)**: Verifies 100% version synchronization and Ed25519 signature validity.
- **Gate 2 (`test_all_registered_playgrounds_have_active_dom_mounts`)**: Verifies all registered playgrounds have DOM mount handlers.
- **Gate 3 (`test_docs_cli_commands_and_flags_validity`)**: Statically verifies that all documented CLI subcommands exist in the parser.
- **Gate 4 (`test_docs_justfile_recipes_exist`)**: Statically verifies that all documented `just` command invocations exist in Justfiles.
- **Gate 5 (`test_zero_hardcoded_invariant_counts_in_docs`)**: Prohibits hardcoded invariant counts, enforcing "The Invariant Bible".
- **Gate 6 (`test_docs_minimum_meaningful_length`)**: Enforces minimum word count thresholds per archetype (Blogs $\ge 600$, Protocols/Blueprints $\ge 700$, Operations/Tutorials $\ge 500$, Cookbooks $\ge 450$).
- **Gate 7 (`test_zero_empty_or_sparse_sections`)**: Prevents unpopulated headings, empty sections, or placeholder text across all documentation.
- **Gate 8 (`test_zero_pseudo_box_art_and_dashed_boundaries_invariant`)**: Asserts 100% eradication of dashed borders, loose pipe pseudo-boxes, bare arrows, and unformatted ALL CAPS headers across all documentation files.

### 7. Prioritized Cognitive Taxonomy & Invariant Lifecycle Audit
- Asserts that all 4 `AGENTS.md` files categorize Tier 0 invariants under the **Class α (Sovereign Safety)**, **Class β (Execution Topology)**, and **Class γ (Interface Symmetry)** headers.
- Audits newly proposed invariants for **Demotion Highway eligibility** (checking if the invariant can be verified deterministically via `test_docs_integrity.py` before adding to `AGENTS.md`).
- Enforces upward axiomatic consolidation when total Tier 0 word/token budget approaches threshold.

### 8. Vector SVG Illustration & Anti-Box-Art Integrity Audit
- **Zero ASCII Box Art Rule**: Prohibits both unicode box drawing (`┌`, `╔`) and ASCII boundary sequences (`+---+`, `+===+`, `+--`, `--►`). Code blocks and essays must use structured GitHub-Flavored Markdown tables, alerts, or vector SVGs.
- **Vector SVG Integrity**: Requires dark-theme tokens (`#090d16`, `#050810`, `#1e293b`), explicit `viewBox`, descriptive non-generic figcaptions, and 100% SHA-256 checksum parity between `credence-docs` and `credence/web` (`test_ecosystem_illustration_checksum_parity`).
- **Pre-Walkthrough Live HTTP Probe Gate**: Release walkthroughs must never be presented before verifying that GitHub Actions deployment has finished (`deploy-dev.yml`) and probing live Dev URLs directly via `curl -sI <url>` to assert `HTTP/2 200` with the updated asset content.

### 9. Decoupled Subdomain Routing & Cross-Plane Navigation Audit
- **Domain Identity Separation**: Enforces strict domain partitioning:
  - `docs.credence.run` hosts technical reference, quickstarts, tutorials, playgrounds, and invariants.
  - `blog.credence.run` hosts sovereign essays, forensic investigations, and memoirs.
- **Cross-Plane Navigation**: Plane switcher buttons, bridge cards, and relative hash links automatically navigate to the target subdomain (`getDocsBaseUrl()` vs `getBlogBaseUrl()`) while preserving single-host SPA behavior on local/preview environments.

### 10. Autonomous RFC Standards Governance & Golden FPR Audit
- **3-Tier Hierarchy**: Asserts standards belong strictly to Tier 0 (`UNIVERSAL_GENERAL`), Tier 1 (`DOMAIN_SPECIALIST`), or Tier 2 (`SOVEREIGN_NICHE`).
- **5-Stage State Machine**: Enforces automated promotion gates:
  $$\text{Draft} \longrightarrow \text{Proposed} \longrightarrow \text{Candidate} \longrightarrow \text{Shadow Trial} \longrightarrow \text{Voting} \longrightarrow \text{Ratified}$$
- **Synthetic Gauntlet & Golden Baseline**: All candidate catalogs must be evaluated against positive fixtures and the immutable Golden Control Corpus ($N=100$), asserting:
  $$\mathcal{F}_1 \ge 0.87, \quad \text{Precision} \ge 0.90, \quad \text{Recall} \ge 0.85, \quad \text{FPR}_{\text{golden}} = 0.00\%, \quad G = 1.00$$
- **CAS Pinning**: Ratified standards are pinned using RFC 8785 canonical JSON bytes and SHA-256 CAS hashes with dynamic hot-reload into `TaxonomyRegistry`.

### 11. Zero-Mock Telemetry Boundary Audit (`inv-production-telemetry-boundary`)
- **Real Node Reality**: Asserts that production operator dashboards (`credence.nexus`, `credence.report`, `admin.credence.run`, `credence.foundation`) never fall back to fake simulated datasets (`getDemoData()`, zeroed hashes, fake `setTimeout`).
- **Genesis State**: Fresh, unpeered nodes report authentic `STANDALONE (UNPEERED)` status ($N=1, f=0$) with authentic receipts or an explicit disconnected state.

---

## 2. Turnkey Audit Execution Commands

```bash
# Run complete ecosystem invariant audit
just audit-invariants

# Run targeted shift-left invariant and lifecycle tests
poetry run pytest tests/test_docs_integrity.py -k "lifecycle or invariant or parity"
```

---

## 3. Reference Blueprints & Documentation
- 📘 [`docs/agent-invariants.md`](../../../../credence-docs/docs/agent-invariants.md): Living Canon of System Invariants with mathematical formulas.
- 🏛️ [`docs/blueprints/invariant-scalability-and-knowledge-governance.md`](../../../../credence-docs/docs/blueprints/invariant-scalability-and-knowledge-governance.md): 3-Tier Scalability Architecture Blueprint.
- 🧠 [`docs/agentic/02-continuous-learning-and-invariant-synthesis.md`](../../../../credence-docs/docs/agentic/02-continuous-learning-and-invariant-synthesis.md): Continuous Learning with `/learn`.

### 4. The Cart-Before-the-Horse Order-of-Operations Check
- Verify that every proposed implementation plan is topologically sorted: scrubbers & schemas precede APIs, APIs precede UIs/CLI, and empirical tests precede case study essays.

---

## 4. Hermetic Pipeline Test Assertion Boundaries

When writing or modifying unit tests (`@pytest.mark.unit`) that execute pipeline evaluation (`evaluate_snapshot`):
- **Hermetic Boundary Principle**: CI runners operate offline without cloud LLM keys, triggering `evaluation_method: "offline_structural_heuristic"`.
- **Classification Range**: Tests evaluating profile overrides must assert against the full hermetic spectrum:
  `assert report.classification in ("LOW_SUSPICION", "SUSPICIOUS", "DECEPTIVE")`
- **Zero Mock Data Invariant**: Never mock LLM responses in unit tests unless explicitly tagged with `@pytest.mark.mock`. Real heuristic code paths must execute cleanly offline.

---

## 5. Shift-Left Node.js Markdown Parser & AST Integrity Gates

When modifying client-side markdown parsers (`credence-docs/app.js`) or adding new markdown documentation:
- **Comprehensive Document Scan**: Pre-commit test `test_javascript_markdown_parser_runtime_integrity` in `tests/governance/test_docs_integrity.py` executes the actual `parseMarkdown()` function via Node.js across all 189+ markdown documents.
- **Zero Unrendered Blockquote Leaks**: Asserts zero occurrences of raw `>` or `<p>&gt;` tokens in rendered output.
- **Container Hygiene**: Asserts that multi-line callouts (`> [!NOTE]`) are properly wrapped in a single `.alert-box` rather than broken into disconnected `<p>` or `<blockquote>` fragments.



