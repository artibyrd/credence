# Release Lifecycle — Credence Project Overlay

Self-contained Credence release-lifecycle policy. Applies automatically on top of `release-lifecycle` when `antigravity-customizations` is installed, and serves as a standalone Credence release runbook on any agent harness.

---

## Overrides

- **PR & Live Dev Before Mk1 Eyeball:** Feature-branch commits, version sync (`just sync-version`), `just pr-create`, CI monitoring, and live Dev probing are **prerequisites** to requesting Mk1 Eyeball—never pause before opening PRs. Mk1 Eyeball strictly gates `just pr-merge`, release tags, and production rollout.
- **Changelog & Roadmap Paths:** Canonical release records live in `credence-docs/docs/changelog.md` (with `## [X.Y.Z]` heading) and `credence-docs/docs/roadmap.md` (strictly forward-looking; completed items removed), NOT only in root `CHANGELOG.md` / `ROADMAP.md`.
- **Bare Semver Argument Format:** Always pass bare semver (`2.23.0`, without a leading `v`) to `just sync-version <version>` and `just release <version> "<msg>"` because `credence/just/release.just` prepends `v` to tags and manifest strings automatically.
- **3-Repo Topological Merge Order:** When merging a Credence PR triad into `main`, ALWAYS merge strictly in this order:
  1. `credence-docs` first (because `credence`'s `deploy-edge.yml` immediately clones `credence-docs/main` to publish Production Cloudflare Pages)
  2. `credence-agent` second
  3. `credence` third
  *(If `antigravity-customizations` also has upstream changes for the milestone, merge `antigravity-customizations` before the Credence triad.)*

---

## Extensions

### 1. 7-Manifest Synchronization & Ed25519 Attestations (`just sync-version`)
Before staging a release PR or tagging a release, run `just sync-version <X.Y.Z>` (from `credence/`), which atomically synchronizes all 7 ecosystem manifests and re-signs documentation attestations:
1. `credence/pyproject.toml`
2. `credence/credence/__init__.py`
3. `credence-docs/app.js` (`CURRENT_ECOSYSTEM_VERSION`)
4. `credence/web/assets/credence-workstation.js` (`CREDENCE_VERSION`) & `credence-widget.js`
5. `credence-agent/plugin.json`
6. Multi-domain HTML version badges (`web/` + `credence-docs/`)
7. Open Graph cards (`og-card.svg` -> `og-card.png` rendered via `just render-assets`)
8. Ed25519 documentation attestations (`poetry run credence audit-docs --update` -> `credence-docs/assets/attestations.json`)

### 2. Pre-PR QA, Staged PR Triad & Live Dev Verification Gate
Execute the full Credence workflow chain prior to requesting human Mk1 Eyeball sign-off (`inv-mk1-eyeball`):

```bash
# 1. Sync standalone overlays if credence-agent/overrides/ changed
just sync-overlays

# 2. Full parallel pre-commit QA gate (lint, unit, docs, terraform, agent-check)
just check

# 3. Synchronize all 7 version manifests & attestations (when bumping version)
just sync-version <X.Y.Z>

# 4. Open staged PR triad with required [vX.Y.Z] <type>(<scope>): <summary> title
just pr-create "[vX.Y.Z] <type>(<scope>): <imperative summary>"

# 5. Monitor Dev CI/CD (deploy-dev.yml) and probe live Dev Cloud Run + Edge endpoints
just ci-watch
just cloud-probe credence-dev dev
```

- **Playwright Live Dev Gate:** For any UI, documentation engine (`app.js`), or workstation change, run headless Playwright verification against live Dev (`https://dev.credence.run/docs/`, `https://dev.credence.run/`) asserting zero `pageerror` exceptions, substantive `#doc-content` rendering, and scrolled lazy-loaded `<img>` completeness before presenting `walkthrough.md`.
- **Cloudflare Secret Centralization:** `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` live exclusively in `artibyrd/credence`. Pushing isolated commits to `credence-docs` requires dispatching `credence`'s Dev workflow to preview edge changes.
- **Push-and-Delegate CI/CD:** After `just pr-merge` and `just --yes release <X.Y.Z> "<msg>"` (clean tree enforced by `inv-commit-before-deploy`), let GitHub Actions WIF execute production Cloud Run and Cloudflare Edge deployments; monitor with `gh run watch` instead of running manual local production deploys.

### 3. Museum Invariant for Walkthrough & Plan Artifacts (`inv-artifact-curation`)
- Append new milestones (`# Milestone M+1: ...`) to `implementation_plan.md` and `walkthrough.md`; never overwrite earlier milestone history.

---

## Disabled / Not Applicable

- **Manual Local Production Deploys Post-Push:** Do not run `just cloud-deploy-prod` or `just edge-deploy` after pushing a release tag; GitHub Actions CI/CD handles authoritative production deployments.
