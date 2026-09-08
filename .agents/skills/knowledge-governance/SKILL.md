---
name: knowledge-governance
description: Manage the 4-tier knowledge placement taxonomy (/remember), audit and prune AGENTS.md to prevent context bloat, route new learnings into progressive skills vs universal invariants, and enforce progressive disclosure.
---

# Knowledge Governance & Context Optimization Skill (`/remember`)

Use this skill when processing `/learn` proposals, post-mortems, or new operational discoveries. This skill prevents **Context Bloat and Attention Dilution** in `AGENTS.md` by routing insights into the lowest-cost cognitive layer using Antigravity's **Progressive Disclosure** architecture.

---

## 1. The 4-Tier Invariant Scalability & Knowledge Placement Architecture

When synthesizing new insights, evaluate each finding against this placement matrix:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   4-TIER INVARIANT SCALABILITY & KNOWLEDGE PLACEMENT ROUTER                      │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                               [New Finding / Invariant / Insight]                                │
│                                                │                                                 │
│                                                ▼                                                 │
│                                 [Knowledge Placement Router]                                     │
│                                                │                                                 │
│   ┌──────────────────────┬─────────────────────┼──────────────────────┬──────────────────────┐   │
│   ▼                      ▼                     ▼                      ▼                      │   │
│ ┌──────────────────────┐ ┌───────────────────┐ ┌────────────────────┐ ┌────────────────────┐ │   │
│ │ Tier 0: AGENTS.md    │ │ Tier 1: Skill     │ │ Tier 2: Test Gate  │ │ Tier 3: Specs      │ │   │
│ │ (Always-on, <800 tok,│ │ (.agents/skills/, │ │ (test_docs_        │ │ (docs/invariants.md│ │   │
│ │  P0 Core Invariants) │ │  On-demand guides)│ │  integrity.py)     │ │  Reference manual) │ │   │
│ └──────────────────────┘ └───────────────────┘ └────────────────────┘ └────────────────────┘ │   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Tier 0: Universal Core Invariants (`AGENTS.md`)
- **Loading Mode**: `always_on` (injected on every turn).
- **Target Size Budget**: **< 800 tokens** total across all sections.
- **Cognitive Hierarchy**:
  - **Class α (Alpha)**: Sovereign Safety, Custody & Human Authority (P0 Non-Negotiables).
  - **Class β (Beta)**: Execution Topology, Lifecycle & Release Architecture (P1 Process Boundaries).
  - **Class γ (Gamma)**: Interface Symmetry, Epistemic Parity & Governance (P2 Ergonomics & Presentation).
- **Format**: High-density 1-sentence invariant rules. Never embed execution steps or vendor CLI guides here.

### Tier 1: Specialized Progressive Skills (`.agents/skills/<name>/SKILL.md`)
- **Loading Mode**: On-Demand (Only title and description loaded initially; body loads when activated).
- **Best For**: Subsystem-scoped rules, mathematical formulas, and multi-step runbooks (`mesh-cluster`, `cloudrun-ops`, `forensic-audit`).

### Tier 2: Shift-Left Automated Integrity Test Gates (`tests/governance/` & `Justfile`)
- **Loading Mode**: Execution Time (`just check` runs in <3s).
- **Best For**: Deterministic mechanical validation (manifest version parity, code fence formatting, budget ceilings, and route verification).

### Tier 3: Canonical Reference Manuals & Architecture Blueprints (`docs/`)
- **Loading Mode**: Reference / Human Browsing (`docs.credence.run`).
- **Best For**: Formal mathematical proofs, complete protocol sequence diagrams, and exhaustive API references.

---

## 2. Invariant Mutability & The Demotion Highway

Invariants represent the **strongest validated empirical truth at project epoch $t$**. Over time, invariants must be continuously re-evaluated for ongoing merit.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             INVARIANT LIFECYCLE STATE MACHINE                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│    Proposed ─────────► Active (Minted vX.Y.0) ─────────► Under Review (Milestone Audit)          │
│       ▲                                                              │                           │
│       │                                      ┌───────────────────────┼──────────────────────┐    │
│  [/learn Run]                                ▼                       ▼                      ▼    │
│                                        Active (Affirmed)      Amended (Refined)      Demoted /   │
│                                                                                      Retired     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The Invariant Lifecycle
1. **`Proposed`**: Synthesized during `/learn` retrospectives or post-mortems in `learning_proposal.md`.
2. **`Active`**: Formally adopted and minted into `AGENTS.md` and `docs/invariants.md`.
3. **`Under Review`**: Evaluated during minor version release boundaries (`v2.X.0`) or milestone audits.
4. **`Amended`**: Refined, sharpened, or merged with related invariants.
5. **`Demoted` (The Demotion Highway)**: Graduated out of prompt context into automated deterministic test gates (Tier 2) or progressive skills (Tier 1).
6. **`Retired`**: Archived with rationale in `docs/invariants.md`.

### The Demotion Highway (Shift-Left Graduation)
- **Philosophy**: *If a machine can assert it deterministically in <0.3s, never waste LLM attention tokens prompting for it.*
- When deterministic static analysis or unit test coverage is built for an invariant, graduate the rule out of `AGENTS.md` into `tests/governance/test_docs_integrity.py` or `test_architecture_governance.py`.
- Automated test `test_tier0_invariants_demotion_redundancy` ensures demoted rules never re-accumulate in Tier 0.

### The `/learn` Invariant Admission Gate
Before any new invariant can be minted into `AGENTS.md`, the `/learn` proposal must satisfy 3 gates:
1. **"Why not a test?"**: Prove the rule cannot be deterministically asserted by a Tier 2 test gate in `test_architecture_governance.py` or `test_docs_integrity.py`. If it can, it goes directly to tests and never enters `AGENTS.md`.
2. **"Why not a skill?"**: Prove the rule applies universally across every turn, rather than within a specific subsystem. If domain-scoped, route to Tier 1 skills.
3. **Token Budget Impact**: Calculate estimated tokens (`word_count * 1.33`). If total Tier 0 tokens would exceed 800, identify which existing invariant will be demoted to make room.

---

## 3. The 4-Phase Delivery & Continuous Learning Lifecycle

Ecosystem development and knowledge synthesis strictly follow a 4-phase sequential progression:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        4-PHASE DELIVERY & LEAN LEARNING LIFECYCLE                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│ │ 1. Code & Local │ ──► │ 2. PR Staging & │ ──► │ 3. Mk1 Eyeball  │ ──► │ 4. Feature      │      │
│ │    QA Gauntlet  │     │    Dev Probing  │     │    Sign-Off     │     │    Release      │      │
│ └─────────────────┘     └─────────────────┘     └─────────────────┘     └────────┬────────┘      │
│                                                                                  │               │
│                                                 ┌────────────────────────────────┘               │
│                                                 ▼                                                │
│                         ┌─────────────────┐     ┌─────────────────┐                              │
│                         │ 6. Lean Patch   │ ◄── │ 5. /learn Retro-│                              │
│                         │    Release      │     │    spective     │                              │
│                         └─────────────────┘     └─────────────────┘                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Code, Local QA, PR Creation & Dev Probing
- Implement features with local unit tests, documentation integrity tests, and static checks (`just check`).
- Switch to feature branch (`just branch feat/...`) and open PR triad (`just pr-create '<title>'`).
- Monitor automated Dev deployment on Cloud Run (`deploy-dev.yml` / `just ci-watch`) and probe live Dev endpoints.
- Compile `walkthrough.md` with PR links and live dev verification results.

### Phase 2: Mk1 Eyeball Review & Milestone Release (`vX.Y.0`)
- Present `walkthrough.md` with live Dev links for human inspection ("Mk1 Eyeball").
- Upon approval, merge PRs via Code Owner authority (`just pr-merge`).
- Tag release across repositories (`just git-sync tag X.Y.0`) and push to production (`just git-sync push`).

### Phase 3: `/learn` Retrospective & Invariant Admission
- Review session corrections, security requirements, and operational discoveries.
- Subject each learning to the **Invariant Admission Gate** (Test vs. Skill vs. Tier 0).
- Draft and present `learning_proposal.md` for human review.

### Phase 4: Autonomous Lean Patch Release (`vX.Y.1`)
- Upon approval of `learning_proposal.md`, synthesize insights into skills, rules, and tests.
- Bump version to patch release (`just sync-version <X.Y.1>`), run `just check`, and immediately deploy (`just release <X.Y.1> "message"`).

---

## 4. Documentation Progressive Disclosure & Freshness

### The 5-Level Progressive Disclosure Hierarchy
1. **Level 1: The Hook & Value Prop**: Plain English, everyday relatable examples.
2. **Level 2: 60-Second Quickstart**: 3-step jump-in command card (`curl ... | bash` $\to$ `credence audit` $\to$ `credence tui`).
3. **Level 3: Everyday Interfaces**: Terminal CLI, AI Assistant FastMCP, TUI Workstation, Web Report Viewer.
4. **Level 4: Core Concepts**: Grounded DOM quotes, ethical taxonomy (SPJ, IEP), satire protection, Ed25519 receipts.
5. **Level 5: Deep Dives & Specifications**: Formal proofs, system invariants, and P2P mesh dynamics.

### Frontmatter Version Provenance
Every markdown document in `docs/` and `blog/` maintains version provenance:
- `since_version`: Semantic version when first published (e.g. `v1.0.0`).
- `verified_version`: Most recent semantic version verified against (e.g. `v2.20.0`).
- `last_verified`: ISO-8601 date of the last verification audit.

---

## 5. Socratic Architecture Pre-Mortems & The Invariant Challenger

### Socratic Review Checklist (`/grill-me`)
Before implementing major structural changes, evaluate:
1. **The Invariant Stress Test**: Does the proposal violate any core invariants (Zero-npm, Hermetic Unit Testing, $G=1.00$)?
2. **The Simplicity Veto**: Can this be built with zero new dependencies using standard library primitives?
3. **Partition Resilience**: What happens if the network splits or Cloud Run scales to zero?
4. **Cognitive Economy Audit**: Does this proposal keep root `AGENTS.md` under the 800-token hard ceiling?

### The Invariant Challenger (`just challenge-invariant <slug>`)
Automated tool (`scripts/challenge_invariant.py`) evaluating invariants under 4 dispositions:
1. **`PRESERVE`**: Requires cognitive reasoning or human safety custody; stays in `AGENTS.md`.
2. **`DEMOTE`**: 100% mechanically asserted by test gates; graduates to Tier 2 test suites.
3. **`AMEND`**: Requires updated parameters or refined boundary thresholds.
4. **`NULLIFY`**: Obsoleted constraints retired with rationale in `docs/invariants.md`.






