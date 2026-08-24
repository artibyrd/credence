---
name: bootstrap-approvals
description: Bootstrap Antigravity IDE agent command approvals in fresh workspaces. Sequentially invokes individual run_command tool calls across core and hosted command shapes so the operator can click "Always Allow" for autonomous workflows.
---

# Agent Command Approval Bootstrapping Skill (`bootstrap-approvals`)

Use this skill when setting up a fresh development workspace, when command permissions have been purged or reset, or when onboarding a new development machine.

---

## 1. The Core Mechanical Principle of IDE Approvals

The Antigravity IDE permission system intercepts **top-level tool invocations (`run_command`)** issued by the AI agent.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      ANTIGRAVITY IDE AGENT COMMAND APPROVAL PIPELINE                             │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [Agent Tool Call: run_command(CommandLine="just check", BypassSandbox=true)]                    │
│                                │                                                                 │
│                                ▼                                                                 │
│                 [IDE Prefix Matching Engine]                                                     │
│                                │                                                                 │
│                 ┌──────────────┴──────────────┐                                                  │
│                 ▼                             ▼                                                  │
│         [Prefix Approved?]            [Unapproved Prefix]                                        │
│                 │                             │                                                  │
│                 ▼                             ▼                                                  │
│        (Executes Silently)          [IDE Approval Modal Dialog]                                  │
│                                               │                                                  │
│                                               ▼                                                  │
│                                     User clicks "Always Allow"                                   │
│                                               │                                                  │
│                                               ▼                                                  │
│                               (Prefix Cached for Future Tool Calls)                              │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Subprocess Isolation Rule**:
> Running a Python script or shell script containing `subprocess.run(["just", "check"])` will **NOT** register `just check` in the IDE's approval table because child processes run inside the parent script's subshell and are invisible to the top-level IDE tool dispatcher.
>
> To bootstrap permissions for autonomous workflows, the **agent itself must execute each distinct command shape as a discrete top-level `run_command` tool call**.

---

## 2. The Prefix-Safe Command Boundary Law ("No Spicy Prefixes")

The Antigravity permission system matches approved command shapes by **`binary subcommand` prefix**.

> [!CAUTION]
> **The Spicy Command Boundary**:
> Never include commands in the approval catalog whose prefix encompasses destructive or state-mutating subcommands.
>
> * **Prohibited (Spicy)**: `gcloud config ...` (Approving `gcloud config` would auto-authorize `gcloud config set ...`), `rm ...`, `git push --force`, `wrangler secret ...`.
> * **Permitted (Safe)**: `just auth-check gcloud` (encapsulated in read-only Just recipe), `git status -s`, `grep -i <pattern> <file>`, `poetry run ruff check ...`.

---

## 3. Core Scope Execution Protocol (`scope="core"`)

When asked to bootstrap core approvals, execute each of the following commands sequentially as an individual `run_command` tool call with `BypassSandbox: true` and `WaitMsBeforeAsync: 5000`:

```bash
# 1. Preflight & Auth Checks
just preflight all
just auth-check gh
just auth-check env

# 2. Quality & Verification Gates
just check
just lint
just format
just test-unit
just test-docs
just agent-check
just audit-skills
just audit-demotions

# 3. Justfile VCS Inspection
just status
just git-diff
just git-log 5
just pr-status
just pr-checks
just pr-view

# 4. Everyday Git Read Operations (Outside Just)
git status -s
git diff --stat
git log -n 3 --oneline
git branch --list
git checkout AGENTS.md

# 5. Everyday Python & Poetry Tooling (Outside Just)
poetry version
poetry run ruff check credence
poetry run mypy credence
poetry run pytest tests/governance/test_docs_integrity.py -k test_zero_npm_invariant

# 6. Everyday Coreutils & Text Search (Outside Just)
grep -i "version" pyproject.toml
head -n 5 pyproject.toml
wc -l AGENTS.md

# 7. GitHub CLI Inspection (Outside Just)
gh auth status
gh pr checks
gh pr view
gh run list --limit 5

# 8. Public Web Endpoints
curl -sI https://docs.credence.run
curl -sI https://raw.githubusercontent.com/artibyrd/credence/main/README.md
```

---

## 4. Hosted Scope Execution Protocol (`scope="hosted"`)

When asked to bootstrap hosted maintainer approvals, execute each of the following commands sequentially as an individual `run_command` tool call with `BypassSandbox: true` and `WaitMsBeforeAsync: 5000`:

```bash
# 1. Hosted Authentication Verification
just auth-check gcloud
just auth-check wrangler
just auth-check all

# 2. Hosted Justfile Telemetry Recipes
just cloud-status
just cloud-probe credence-dev dev
just cloud-probe credence-server prod
just edge-status
just ci-status
just tf-validate
just doctor

# 3. Live Cloud & Edge URL Probes
curl -sI https://credence-dev-865363499314.us-central1.run.app/health
curl -s https://credence-dev-865363499314.us-central1.run.app/health
curl -sI https://credence-server-663899237633.us-central1.run.app/health
curl -s https://credence-server-663899237633.us-central1.run.app/health
curl -sI https://credence.run/health
curl -sI https://dev.credence.run/health
curl -sI https://docs.credence.run
curl -sI https://credence.report
curl -sI https://credence.nexus
curl -sI https://credence.foundation
```

---

## 5. Execution Guidelines & Error Resilience

1. **Non-Zero Exit Tolerance**: If an individual command exits non-zero (e.g. `gcloud auth print-access-token` reports expired token or local servers are not running), log the result and proceed to the next command. The primary goal of the tool call is prompting the IDE's "Always Allow" modal dialog so future authorized invocations succeed autonomously.
2. **Single Contiguous Sequence**: Execute the sequence step-by-step so the developer can click "Always Allow" on each modal dialog in rapid succession.
3. **No Destructive Commands**: Never include destructive, mutating, or deployment-triggering commands (`just release`, `just commit`, `just pr-merge`, `just cloud-deploy-prod`) in approval bootstrapping passes.
