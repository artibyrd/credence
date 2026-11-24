# Bootstrap Approvals — Credence Project Overlay

Self-contained Credence command-approval scope catalog. Applies automatically on top of `bootstrap-approvals` when `antigravity-customizations` is installed, and serves as a standalone safe command reference on any agent harness.

---

## Overrides

- **Strict "No Spicy Prefixes" Enforcement (D4):** Never prime `git checkout`, `git branch`, `gh pr`, `gh auth`, `gh run`, `poetry version`, `poetry run`, bare `curl`, `gcloud config`, `wrangler secret`, or `rm`. Prime only narrow, read-only, non-mutating recipe prefixes and strictly read-only CLI inspection prefixes.
- **Zero Wrapper Scripts (Subprocess Isolation Rule):** Never execute a helper script (`scripts/bootstrap_approvals.py` is retired) to prime approvals. Issue each safe command individually as a discrete top-level terminal tool call after presenting the confirmation table to the operator.

---

## Extensions

### 1. Credence Core Scope (`scope="core"` — Open-Source Contributors & Forks)
Safe, read-only `Justfile` recipes and inspection commands for local development:

```bash
# Preflight & Auth Inspection
just preflight all
just auth-check gh
just auth-check env

# Quality, Testing & Agent Governance Gates
just check
just lint
just test-unit
just test-docs
just agent-check
just audit-skills
just audit-demotions
just check-models

# Read-Only VCS & PR Inspection (Safe Recipes)
just status
just git-diff
just git-log 5
just pr-status
just pr-checks
just pr-view

# Safe Standalone Inspection Commands
git status -s
git diff --stat
git log -n 3 --oneline
```

### 2. Credence Hosted Maintainer Scope (`scope="hosted"` — Cloud & Edge Operators)
Only run when the operator explicitly requests hosted maintainer approval priming:

```bash
# Hosted Auth Inspection
just auth-check gcloud
just auth-check wrangler
just auth-check all

# Read-Only Cloud Run, Edge, CI & Terraform Diagnostics
just cloud-status
just cloud-probe credence-dev dev
just cloud-probe credence-server prod
just edge-status
just ci-status
just tf-validate
just doctor
```

---

## Disabled / Not Applicable

- **Mutating & Gated Recipes:** Never include `just branch`, `just commit`, `just pr-create`, `just pr-merge`, `just sync-version`, `just release`, `just cloud-deploy-dev`, `just cloud-deploy-prod`, `just cloud-rollback`, `just edge-deploy`, `just tf-apply`, or `just docker-prune-all` in approval bootstrapping passes.
