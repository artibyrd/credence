# PR Brief — Credence Project Overlay

Self-contained Credence pull-request titling, scoping, and review-brief policy. Applies automatically on top of `pr-brief` when `antigravity-customizations` is installed, and serves as a standalone Credence PR standard on any agent harness.

---

## Overrides

- **Mandatory Credence PR Title Format:** Every Credence pull request title MUST strictly follow:
  `[vX.Y.Z] <type>(<scope>): <imperative summary>`
  Example: `[v2.23.0] feat(governance): adopt skill overlay architecture and Gemini 4 models`
- **Allowed Commit & PR Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`, `perf`.
- **Strict 6-Scope Taxonomy:** CI (`validate-pr`) and the local `commit-msg` hook (`credence-agent/scripts/install_hooks.py`) enforce exactly these 6 scopes:
  - `(governance)`: Invariant audits, skill/overlay updates, knowledge governance, policies.
  - `(forensics)`: Evidence extraction, DOM hashing, scrubber heuristics, parser guards.
  - `(mesh)`: P2P gossip, Watts-Strogatz clustering, consensus aggregation, Sybil defense.
  - `(crypto)`: Ed25519 signatures, RFC 8785 canonical JSON, node identity envelopes.
  - `(ui)`: Web workstations, CSS styling, components, TUI, CLI formatting.
  - `(ops)`: CI/CD workflows, Terraform, Cloud Run deployments, Dockerfiles, Justfiles.

---

## Extensions

### 1. Triad Lockstep PRs, Bidirectional Docs Review & Merge Order Callout
For cross-repo milestones touching `credence-docs`, `credence-agent`, and `credence`, prohibit single-repo PR dropouts on cross-plane features. Synchronize changes across all affected repos and perform bidirectional documentation review (`test_docs_schema_and_blueprint_staleness_guard`) whenever models, heuristics, or invariants change. Every PR description MUST include:
- **Triad PR Links:** Direct links to sibling PRs across all touched repos.
- **Explicit Topological Merge Order:** `credence-docs` -> `credence-agent` -> `credence` (plus `antigravity-customizations` first if modified).
- **Live Dev Verification Links:** Clickable links to the verified `deploy-dev.yml` Cloud Run health endpoint (`https://credence-dev-865363499314.us-central1.run.app/health`) and preview edge surfaces (`https://dev.credence.run/`, `https://dev.credence.run/docs/`) when applicable.

### 2. Required Verification Checklist in PR Body
Include exact command outcomes for:
- `just check` (lint, hermetic unit tests, docs Gates 1–15, Terraform validate, `agent-check`)
- `just sync-overlays` / standalone overlay parity (if `credence-agent/overrides/` changed)
- `just check-models` (if model catalog, adapters, or cost profiles changed)
- `agy plugin validate --strict credence-agent` (when `agy` is installed)

---

## Disabled / Not Applicable

- None. All base `pr-brief` visual-first structure and Merge Danger callouts apply in full.
