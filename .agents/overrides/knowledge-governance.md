# Knowledge Governance — Credence Project Overlay

Self-contained Credence knowledge-governance policy. Applies automatically on top of `knowledge-governance` when `antigravity-customizations` is installed, and serves as a standalone Credence governance guide on any agent harness.

---

## Overrides

- **Tier 1 Progressive Disclosure Split:** Domain-specific Credence operational skills live in `credence-agent/skills/` (6 focused skills: `invariant-audit`, `epistemic-benchmark`, `forensic-audit`, `cloudrun-ops`, `mesh-cluster`, `white-label-ops`). Repo-specific extensions to generalized engineering workflows live in `credence-agent/overrides/<skill>.md` (symlinked at workspace `.agents/overrides/` and synced into `credence/.agents/overrides/` via `just sync-overlays`).
- **Cognitive Hierarchy in `AGENTS.md`:** Tier 0 invariants in all Credence `AGENTS.md` files MUST be organized under **Class α (Alpha — Sovereign Safety)**, **Class β (Beta — Topology & Lifecycle)**, and **Class γ (Gamma — Ergonomics & Governance)** while remaining strictly `< 800` tokens (`word_count * 1.33`).
- **Tier 1.5 `CODING_STANDARDS.md` (D5):** Lazy optional — do not pre-scaffold an empty `CODING_STANDARDS.md`; create it only if unlintable repo-wide style rules emerge.

---

## Extensions

### 1. Credence Governance CLI Tooling & Automated Gates
Run these harness-agnostic Credence recipes during `/learn` retrospectives, invariant audits, and pre-commit checks:

```bash
# Scan AGENTS.md token budget & flag mechanical Demotion Highway candidates
just audit-demotions

# Run forensic scrutiny on a specific invariant slug (PRESERVE / DEMOTE / AMEND / NULLIFY)
just challenge-invariant <inv-slug>

# Validate skills schema, overrides 3-section contract, plugin.json, and demotion hygiene
just agent-check
```

- **Automated Demotion Guard (`test_tier0_invariants_demotion_redundancy`):** Located in `credence/tests/governance/test_architecture_governance.py`. Fails CI if previously demoted mechanical invariants (`inv-living-canon`, `inv-article-h1-header`, `inv-web-component-isolation`, `inv-hermetic-unit-tests`, `inv-clean-slug-routing`, `inv-production-telemetry-boundary`) ever re-accumulate in Tier 0 `AGENTS.md`.
- **Token Budget Ceiling (`test_agents_md_token_budget_ceiling`):** Mechanically asserts every `AGENTS.md` across the ecosystem stays `<= 800` estimated tokens.
- **Dynamic Canon Naming ("The Invariant Bible"):** Never hardcode invariant counts in docs or web surfaces (`test_zero_hardcoded_invariant_counts_in_docs`).

### 2. The 5-Level Documentation Progressive Disclosure Hierarchy
Every documentation entry point and feature guide in `credence-docs` follows Credence's 5-level disclosure ladder:
1. **Level 1 — Hook & Value Prop:** Plain English, everyday relatable examples (zero internal constants).
2. **Level 2 — 60-Second Quickstart:** 3-step jump-in (`curl ... | bash` -> `credence audit` -> `credence tui`).
3. **Level 3 — Everyday Interfaces:** Terminal CLI, FastMCP AI Assistant, TUI Workstation, Web Report Viewer.
4. **Level 4 — Core Concepts:** Grounded DOM quotes ($G=1.00$), ethical taxonomy (SPJ/IEP), satire protection, Ed25519 receipts.
5. **Level 5 — Deep Dives & Specifications:** Formal proofs, Living Canon of System Invariants (`docs/invariants.md`), and P2P mesh dynamics.

### 3. Frontmatter Version Provenance
Every Markdown document in `credence-docs/docs/` and `credence-docs/blog/` MUST maintain version provenance frontmatter:
- `since_version`: Semantic version when first published (e.g., `v1.0.0`).
- `verified_version`: Most recent semantic version verified against (e.g., `v2.22.1`).
- `last_verified`: ISO-8601 date of the last verification audit (`YYYY-MM-DD`).

### 4. Credence 4-Phase Delivery & Continuous Learning Lifecycle
1. **Code & Local QA:** Implement vertical slices, run `just check`, open staged PR triad (`just pr-create`), monitor `deploy-dev.yml`, and verify live Dev endpoints.
2. **Mk1 Eyeball Review & Feature Release (`vX.Y.0`):** Present `walkthrough.md` with live Dev links, merge in topological order (`just pr-merge`), and tag/release (`just release`).
3. **`/learn` Retrospective & Admission Gate:** Route discoveries through the 3-question Admission Gate ("Why not a test?", "Why not a skill/overlay?", "Token budget impact?").
4. **Autonomous Lean Patch Release (`vX.Y.1`):** Apply approved learnings, bump patch version (`just sync-version`), run `just check`, and release.

### 5. Socratic Architecture Pre-Mortem Checklist
Before major structural changes, stress-test against: (1) core invariants (zero-npm, hermetic unit tests, $G=1.00$), (2) Simplicity Veto (zero new dependencies via stdlib), (3) partition / scale-to-zero resilience, and (4) `<800`-token `AGENTS.md` economy.

---

## Disabled / Not Applicable

- None. All base `knowledge-governance` mechanics (4-tier taxonomy, Demotion Highway, `/learn` Admission Gate, 7-category retrospective checklist) apply in full.
