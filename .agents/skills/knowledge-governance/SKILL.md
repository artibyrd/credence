---
name: knowledge-governance
description: Manage the 4-tier knowledge placement taxonomy (/remember), audit and prune AGENTS.md to prevent context bloat, route new learnings into progressive skills vs universal invariants, and enforce progressive disclosure.
---

# Knowledge Governance & Context Optimization Skill (`/remember`)

Use this skill when processing `/learn` proposals, post-mortems, or new operational discoveries. This skill prevents **Context Bloat and Attention Dilution** in `AGENTS.md` by routing insights into the lowest-cost cognitive layer using Antigravity's **Progressive Disclosure** architecture.

---

## 1. The 3-Tier Invariant Scalability & Knowledge Placement Architecture

When synthesizing new insights, evaluate each finding against this scalability matrix to prevent context bloat and attention dilution:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   3-TIER INVARIANT SCALABILITY & KNOWLEDGE PLACEMENT ROUTER                      │
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
- **Loading Mode**: `always_on` (injected on every single turn).
- **Target Size Budget**: **< 800 tokens** total across all sections.
- **Prioritized 3-Class Cognitive Taxonomy**:
  - **Class α (Alpha) - Sovereign Safety, Custody & Human Authority (P0 Non-Negotiables)**: Human Review ("Mk1 Eyeball"), Verbatim DOM Grounding ($G=1.00$), RFC 8785 Canonical JSON & Ed25519 Custody, Untrusted Ingestion Boundary & SSRF/XML Defense, Clean Scratch Script Approvals.
  - **Class β (Beta) - Execution Topology, Lifecycle & Release Architecture (P1 Process Boundaries)**: 4-Phase Release & Learning Lifecycle, The Cart-Before-the-Horse Order-of-Operations, Commit-Before-Deploy & Push-and-Delegate CI/CD Gate, 3-Plane Decoupling, Hermetic Unit Test Isolation.
  - **Class γ (Gamma) - Interface Symmetry, Epistemic Parity & Governance (P2 Ergonomics & Presentation)**: Universal 4-Way Feature Parity, The Epistemic Lensing & Information Pyramid, Session-Driven Documentation Expansion, Dynamic Invariant Canon Naming ("The Invariant Bible"), Multi-Model Sovereignty.
- **Format**: High-density 1-sentence invariant rules. Never embed multi-step execution steps or vendor CLI guides here.

### Tier 1: Specialized Progressive Skills (`.agents/skills/<name>/SKILL.md`)
- **Loading Mode**: On-Demand (Only title and description are in the root prompt; full body loads when activated).
- **Target Size**: Unlimited per skill (50-200 lines typical).
- **Best For**:
  - Subsystem-scoped rules (e.g. Cloud Run scale-to-zero cold start optimization in `cloudrun-ops`).
  - Multi-step procedural runbooks and troubleshooting workflows (`white-label-ops`, `mesh-cluster`).
  - Complex domain simulations (`epistemic-benchmark`).

### Tier 2: Shift-Left Automated Integrity Test Gates (`tests/test_docs_integrity.py` & `Justfile`)
- **Loading Mode**: Execution Time (`just check` runs in <0.3s).
- **Best For**:
  - Semantic version parity across manifests (`test_ecosystem_version_parity`).
  - Code fence column-0 alignment (`test_all_markdown_code_fences_and_syntax`).
  - Frontmatter and title presence (`test_all_markdown_files_valid_frontmatter`).
  - Sitemap route validation (`test_sitemap_integrity_and_route_coverage`).

### Tier 3: Canonical Reference Manuals & Architecture Blueprints (`docs/`)
- **Loading Mode**: Reference / Human Browsing (`docs.credence.run`).
- **Best For**: Complete mathematical proofs, protocol sequence diagrams, and exhaustive API references.

---

## 2. Invariant Mutability, Constitutional Review & The Demotion Highway

Invariants are not immutable dogmas; they represent the **strongest validated empirical truth at project epoch $t$**. Over time, invariants must be continuously re-evaluated for ongoing merit.

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

### The Invariant Lifecycle State Machine
1. **`Proposed`**: Synthesized during `/learn` retrospectives or post-mortems. Documented in `learning_proposal.md`.
2. **`Active`**: Formally adopted and minted into `AGENTS.md` and `docs/invariants.md`.
3. **`Under Review`**: Evaluated during minor version release boundaries (`v2.X.0`) or constitutional review milestones.
4. **`Amended`**: Refined, sharpened, or merged with related invariants to adapt to architectural advancements.
5. **`Demoted` (The Demotion Highway)**: Graduated out of prompt context into automated deterministic test gates (Tier 2) or progressive skills (Tier 1).
6. **`Retired`**: Archived with rationale in `docs/invariants.md` when the underlying constraint or technology is obsoleted.

### The Demotion Highway (Shift-Left Graduation)
- **Philosophy**: *If a machine can assert it deterministically in <0.3s, never waste LLM attention tokens prompting for it.*
- When deterministic static analysis or unit test coverage is built for a Tier 0 invariant, that rule is **demoted** out of `AGENTS.md` and converted into a permanent test gate in `tests/test_docs_integrity.py`.
- This keeps `AGENTS.md` permanently bounded ($<800$ tokens) regardless of how many versions or invariants are discovered over years of development.

### Upward Axiomatic Consolidation Heuristic
- When the Tier 0 token budget approaches 800 tokens, tactical invariants must be synthesized upward into higher-order principles rather than expanding the list.
- *Example*: Consolidating SSRF IP blocking, XML entity injection, and LLM prompt framing into a single **Untrusted Ingestion Boundary & Network Defense** invariant.

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

### Phase 1: Code, Local QA, PR Creation & Dev Deployment Probing
- Implement features with local unit tests, documentation integrity tests, and static checks (`just check`).
- Push feature branch (`release/vX.Y.0` or `feat/...`) and create PRs across all ecosystem repositories.
- Monitor automated Dev deployment to Google Cloud Run (`deploy-dev.yml` / `gh run watch`).
- Probe live Dev endpoints (`https://credence-dev-wukzqiyqbq-uc.a.run.app/health`, `/api/v1/mesh/status`) to confirm operational readiness.

#### Mk1 Review Walkthrough Readiness Checklist
Before presenting `walkthrough.md` for human Mk1 Eyeball review, the agent must strictly verify:
1. [x] **Local QA Gauntlet**: `just check` passed cleanly (100% test pass rate, 0 mypy/ruff errors, token budget <800).
2. [x] **Feature Branching**: Work is committed and pushed on a feature branch (`feat/<slug>` or `release/vX.Y.Z`).
3. [x] **Staged PR Triad**: Pull requests are open across `credence`, `credence-docs`, and `credence-agent`.
4. [x] **CI/CD Health**: Automated CI and `deploy-dev.yml` workflows have completed successfully (`✓`) on GitHub Actions.
5. [x] **Live Dev Probing**: Cloud Run Dev endpoints (`/health`, `/api/health`, `/api/mesh/network-health`, `/api/cost/telemetry`) and Cloudflare Pages dev preview are probed and verified live.
6. [x] **Version Synchronized**: Ecosystem target version is synchronized across all 7 manifests prior to deployment.
7. [x] **Walkthrough PR Links**: `walkthrough.md` contains exact GitHub PR links for human Mk1 review.
- Compile `walkthrough.md` with:
  1. Direct markdown links to all opened Pull Requests.
  2. Live Dev Environment Interactive Verification Matrix linking specific endpoints and expected telemetry.
- Present `walkthrough.md` for human inspection ("Mk1 Eyeball").

### Phase 2: Feature Milestone Release (`vX.Y.0`)
- Upon receiving explicit human review approval, merge PRs to `main` via Code Owner authority (`just pr merge`).
- Pull `main`, create release tag `vX.Y.0` across all repositories (`just git-sync tag X.Y.0`), and push to GitHub (`just git-sync push`).
- Monitor production deployment workflows (`deploy-backend.yml`, `Release`) via `gh run watch`.

### Phase 3: `/learn` Retrospective & Bootstrap Trajectory Harvest
- Review session corrections, security requirements, and operational discoveries.
- **Session Command Trajectory Harvest**: Audit `transcript.jsonl` tool calls from the current session. Identify recurring safe, read-only commands (e.g. `grep`, `head`, `wc`, selective `git checkout`) that triggered manual IDE approval dialogs, and catalog them into `scripts/bootstrap_approvals.py` and `bootstrap-approvals/SKILL.md` under the **Prefix-Safe Command Boundary Law**.
- Classify new insights using the **4-Tier Knowledge Placement Architecture** (Tier 0 Universal Invariants, Tier 1 Progressive Skills, Tier 2 Shift-Left Tests, Tier 3 Documentation).
- Draft and present `learning_proposal.md` for human review and explicit approval.

### Phase 4: Apply Lessons as Lean Patch Release (`vX.Y.1`)
- Upon human approval of `learning_proposal.md` or a targeted patch plan, synthesize insights into `.agents/skills/`, `AGENTS.md`, and shift-left tests.
- Bump the version to the next patch release (e.g. `vX.Y.1`), run `just sync-version <version>`, run `just check`, and **immediately execute the deployment** (`just commit` + `just git-tag` + `just git-push` or `just release X.Y.1 "..."`).
- **Autonomous Fast-Follow Deploy Invariant**: Because fast-follow patches and learning releases bypass standard PR CI/CD staging, the agent must **never stop after local QA without pushing**. The agent must execute the push and monitor CI/CD (`gh run watch` / Cloudflare Pages) within the same turn to ensure changes actually deploy live to edge and compute planes.
- **Lean Governance Invariant**: Learning patches bypass redundant PR ceremony because the changes consist of declarative skills, documentation, and tests already approved via `learning_proposal.md` and verified locally via `just check`.

### The Lean Governance Matrix
| Dimension | **Feature Milestone (`vX.Y.0`)** | **Learning Patch Cycle (`vX.Y.1`)** |
| :--- | :--- | :--- |
| **Branching Topology** | Feature/Milestone Branch (`release/vX.Y.0`, `feat/...`) | Direct on `main` |
| **Staging Environment** | Automated Cloud Run Dev via PR (`credence-dev-495173`) | Hermetic Local QA Gate (`just check` in <25s) |
| **Human Authority Gate** | Code Owner Review on PR + Mk1 Eyeball (with Live Dev Links) | `learning_proposal.md` / Plan Approval |
| **Delivery Vehicle** | `just pr merge` $\rightarrow$ CI/CD Prod Deploy | `just release vX.Y.1` $\rightarrow$ CI/CD Prod Deploy |
| **Ceremony Overhead** | High rigor (staged feature changes & dev verification) | Zero friction (autonomous push & CI/CD deployment) |

### 3.1 Target Version & Scope Alignment Invariant
Before beginning execution on any task or implementation plan, the agent and operator must explicitly establish the **Target Release Version**:
1. **Feature Milestone (`vX.Y.0`)**: Used when picking up new capabilities, major protocol expansions, or new endpoints. Requires milestone branch (`release/vX.Y.0`), PR triad staging, Dev deployment probing, and Code Owner review.
2. **Targeted Patch Release (`vX.Y.Z`)**: Used for documentation enhancements, shift-left test gates, bugfixes, and continuous learning updates. Executed directly on `main` following local QA (`just check`).

*Why This Matters*: Explicitly identifying the target version during implementation planning forces immediate alignment on the boundaries of work, eliminating ambiguity between exploratory prototyping, maintenance patches, and full milestone feature releases.

---

## 4. Documentation Progressive Disclosure & Search Indexing

Whenever creating or modifying documentation across `credence-docs/` or landing pages (`credence.run`):

### 4.1 The Pure Forward-Looking Roadmap Standard (`docs/roadmap.md`)
The ecosystem roadmap serves exclusively as a **forward-looking decision engine and strategic compass**:
1. **Zero Retrospective Milestones**: Prohibits backward-looking "Verified Foundation" or past version lists. Past change records belong exclusively to `docs/changelog.md`.
2. **Zero Architecture Summary Duplication**: Prohibits redundant high-level system summaries that already exist in `docs/intro.md`, `docs/architecture.md`, or `docs/topic-index.md`.
3. **Embedded Horizon Decision Matrix**: Directly embeds an 11-initiative triage matrix evaluating Difficulty (Effort) vs. Impact / Value to enable rapid vs. structural prioritization.
4. **Concrete Strategic Execution Pathways**: Codifies Pathway A (Low-Hanging Fruit Rapid Wins), Pathway B (High-Impact Structural Leap), and Pathway C (Balanced Hybrid).
5. **Retirement upon Landing**: When an item ships, it is recorded in `changelog.md` and immediately removed from the active horizon queue.

### The 5-Level Progressive Disclosure Hierarchy (Anti-Firehose)
1. **Level 1: The Hook & Value Prop**: Explain the project in plain English with everyday relatable examples (cut clickbait, spot fallacies, zero AI hallucinations). Never lead with Greek notation ($Q_i$), raw enum identifiers, or complex consensus math.
2. **Level 2: 60-Second Quickstart**: Provide a 3-step jump-in command card (`curl ... | bash` $\to$ `credence audit <url>` $\to$ `credence tui`).
3. **Level 3: Everyday Use Cases & Interfaces**: Highlight the 4 ways to use Credence (Terminal CLI, AI Assistant FastMCP, Textual TUI Workstation, Web Report Viewer).
4. **Level 4: Core Concepts Simply Explained**: Clear intuitive explanations of verbatim grounded quotes, ethical taxonomy standards (SPJ, IEP), satire protection (Poe's Law), and Ed25519 cryptographic receipts.
5. **Level 5: Deep Dives & Specifications**: Direct, well-organized links to formal proofs, 36 system invariants, P2P mesh dynamics, and multi-cloud operations.

### Concept Searchability & Indexing (Anti-Oatmeal)
1. **Rich Registry Metadata**: Every document entry in `DOCS_REGISTRY` (`app.js`) must include a 1-line `desc` and a `keywords` array of relevant terms, tool names, synonyms, and subcommands.
2. **Master Topic Index Synchronized**: Every new guide, feature, command, or invariant must be linked in `docs/topic-index.md` ("The Marbles in the Oatmeal" directory).
3. **Cross-Navigation Footers**: End every core tutorial or guide with a "Next Steps & Related Marbles" section.

---

## 5. Documentation Freshness Auditing & Version Provenance

To prevent documentation from presenting obsolete models (e.g. `gemini-1.5`, `gpt-3.5`), deprecated flags, or outdated system architectures as the ecosystem advances:

### Mandatory Frontmatter Provenance Fields
Every `.md` document in `docs/` and `blog/` must maintain three version provenance fields:
- `since_version`: The semantic version when the feature/article was first published (e.g. `v1.0.0`, `v1.8.0`).
- `verified_version`: The most recent semantic version against which the document's code samples, commands, and architecture were audited and verified (e.g. `v1.15.0`).
- `last_verified`: The ISO-8601 date of the last verification audit (e.g. `2026-08-19`).

### Major Release Documentation Audit Procedure
During major release cycles:
1. **Freshness Scan**: Run `pytest tests/test_docs_integrity.py` to assert that all documentation markdown files have valid `since_version` and `verified_version` frontmatter.
2. **Obsolete Pattern Elimination**: Audit markdown bodies to eliminate legacy CLI patterns (e.g. `poetry run credence serve` &rarr; direct virtualenv execution), outdated LLM models, and deprecated cloud deployment flags.
3. **Bump Verification Metadata**: Update `verified_version` to target release (e.g. `v1.15.0`) and `last_verified` to the current release date.

### Visual Portal Provenance Badges
The zero-build docs engine (`app.js`) automatically renders:
- `✅ Verified in vX.X.X` (green badge) for documents verified in the latest release.
- `🟡 Verified in vX.X.X` (yellow badge) for documents needing a freshness review.
- `📦 Added in vX.X.X` (neutral badge) showing historical version provenance.

---

## 6. Socratic Architecture Pre-Mortems & Prompt Budget Invariants (`/grill-me` & `<800 Tokens`)

### Socratic Architecture Review Checklist (`/grill-me`)
Before implementing major structural changes, subject the plan to the **4-Round Socratic Interrogation**:
1. **The Invariant Stress Test:** Does the proposal violate any of Credence's 38 core invariants (e.g. Zero-npm, Hermetic Unit Testing, $G=1.00$ Verbatim Grounding)?
2. **The Simplicity Veto:** Can this feature be implemented with zero new dependencies using standard library primitives and native W3C standards (WebCrypto, ES Modules)?
3. **Partition & Partition Resilience:** What happens if the network splits or a Cloud Run instance scales to zero? Is state preserved locally via CAS/WAL?
4. **Cognitive Economy Audit:** Does this proposal add necessary capabilities without dumping formatting trivia or procedural bloat into root `AGENTS.md`?

### Prompt Context Budget Governance
- **Strict `< 800-token` Hard Ceiling:** Root `AGENTS.md` must be kept under 800 tokens.
- **Rule Pruning:** Whenever a new Tier-0 invariant is proposed, audit existing rules. If a rule can be verified mechanically (e.g. frontmatter or sitemaps), move it into `tests/test_docs_integrity.py` (Tier 2).
---

## 7. Canonical Lexicon Governance & Thematic Ontology

When coining, refactoring, or applying terminology across Credence surfaces (docs, code, CLI, MCP, Web), strictly align with the **5 Cohesive Thematic Families** and **3 Complexity Tiers** defined in `docs/blueprints/terminology-and-ontology-lexicon.md`:

### The 5 Cohesive Thematic Families
1. 🌿 **Botanical Network & Lifecycle**: Genesis Seeds $\to$ Node Germination (`credence germinate`) $\to$ Sprout Node $\to$ Expanding Roots $\to$ Root Anchor.
2. 🔭 **Optical & Forensic Grounding**: Verbatim Grounding ($G=1.00$) $\to$ Anti-Hallucination Slashing (50%) $\to$ The Galileo Theorem $\to$ Domain Credence Index (DCI) $\to$ Trust Bands.
3. 🌤️ **Meteorological Epistemics**: Truth Weather $\to$ Epistemic Drift $\to$ Astroturf Entropy Defense ($H < 0.30$) $\to$ The Pizza Hut Problem $\to$ Newsroom Partition $\to$ Humor Shield & Malice Override (`SPJ-1.6`).
4. 🏛️ **Sovereign Governance**: The Invariant Bible $\to$ The 500 LOC Ceiling Law $\to$ `compute_*` Naming Standard $\to$ Mk1 Eyeball Invariant $\to$ 4-Phase Lifecycle $\to$ Zero-npm Standard.
5. ⚡ **Self-Regulating Engine & FinOps**: Feed Sifter $\to$ Autonomous Curiosity Loop (Boredom Engine) $\to$ Curiosity Headroom $\to$ Token Safety Governor $\to$ 4k Pareto Thinking Invariant $\to$ BitTorrent Attestation Relay.

### Disambiguation Invariant
- **Domain Credence Index (DCI)**: Exclusively denotes longitudinal *publisher/website* credibility and sourcing forensics ($[0.0, 100.0]$).
- **Subject Expertise ($E_i$)**: Exclusively denotes decentralized *mesh node* historical domain competence ($[0.0, 1.0]$).

### Decision Tree: Documentation Consolidation over Proliferation
When capturing new session learnings or architectural improvements:
1. **Check Existing Canonical Docs First**: Can this insight expand an existing blueprint, tutorial, or essay? (e.g. adding deployment governance to `the-three-plane-architecture.md`).
2. **Enrich Rather Than Fragment**: Merge related micro-concepts into deep, authoritative reference documents.
3. **Threshold for New Documents**: Standalone `.md` files are strictly reserved for major new capabilities, standalone investigative case studies, or new interactive labs.

---

## 8. The Invariant Challenger Playbook (`just challenge-invariant <slug>`)

The Invariant Challenger (`scripts/challenge_invariant.py`) provides automated epistemic scrutiny of any living invariant to determine if it should remain active in Tier 0 prompt context, be demoted to Tier 2 automated test gates, amended, or nullified.

### The 4 Challenger Dispositions
```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         INVARIANT CHALLENGER DISPOSITION MATRIX                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                 [just challenge-invariant <slug>]                                │
│                                                │                                                 │
│                                                ▼                                                 │
│                                   [Challenger Evaluation Engine]                                 │
│                                                │                                                 │
│         ┌───────────────────┬──────────────────┴───────────────────┬───────────────────┐         │
│         ▼                   ▼                                      ▼                   ▼         │
│ ┌───────────────┐   ┌───────────────┐                      ┌───────────────┐   ┌───────────────┐ │
│ │ 1. PRESERVE   │   │  2. DEMOTE    │                      │  3. AMEND     │   │ 4. NULLIFY    │ │
│ │ (Cognitive/P0)│   │ (Mechanical)  │                      │ (Refine Scope)│   │  (Obsoleted)  │ │
│ └───────────────┘   └───────────────┘                      └───────────────┘   └───────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **`PRESERVE`**: Invariants requiring subjective cognitive evaluation, human custody, safety boundaries, or complex architectural reasoning remain active in `AGENTS.md` (Tier 0).
2. **`DEMOTE`**: When an invariant's rules are 100% mechanically covered by deterministic shift-left test suites (`test_docs_integrity.py`), graduate the rule out of LLM prompt memory to save context budget.
3. **`AMEND`**: Invariants that remain necessary but need updated parameters, new boundary thresholds, or consolidated scope.
4. **`NULLIFY`**: Obsoleted constraints are retired with documented epistemic rationale in `docs/invariants.md`.

---

## 9. The GitHub PR Author Self-Review & Code Owner Gating Protocol

GitHub branch protection enforces `require_code_owner_reviews: true` on `main`, but platform rules prohibit PR authors from approving their own PRs (`reviewDecision` remains `REVIEW_REQUIRED`).

### Dual-Scenario Governance Model:
1. **External Contributor PRs (Author $\neq$ Code Owner)**:
   - When an outside contributor submits a PR, `manage_pr.py` and GitHub branch protection strictly require a formal approving review from a designated Code Owner (`.github/CODEOWNERS`) before merge.
2. **Sovereign Code Owner Self-Authored PRs (Author $\in$ Code Owners)**:
   - When the PR is authored directly by the sovereign Code Owner (`@artibyrd`), `manage_pr.py` recognizes that GitHub prevents self-approval reviews.
   - Upon verifying that all CI/CD checks have passed (`SUCCESS`) and the author provides human Mk1 Eyeball approval, `manage_pr.py` / `just pr merge` executes the merge with repository administrator privileges (`gh pr merge --admin`).
3. **Extensibility for Growing Maintainer Circles**:
   - To authorize new human contributors, simply append their GitHub handle to `.github/CODEOWNERS` (e.g. `* @artibyrd @newcontributor`), with zero infrastructure or branch protection reconfiguration needed.

---

## 10. The Atomic 3-Repo PR Triad & Surgical Diff Isolation Protocol

### 1. Atomic 3-Repo PR Triad
- **Principle**: The Credence ecosystem consists of 3 synchronized repositories (`credence`, `credence-agent`, `credence-docs`).
- **Execution**: Feature milestones must always open, stage, and merge companion PRs across all 3 repos concurrently:
  - `artibyrd/credence#N` (Compute & Web UI)
  - `artibyrd/credence-agent#N` (Declarative Skills & Invariant Governance)
  - `artibyrd/credence-docs#N` (Documentation & Changelog)
- **Staged Version Parity**: Feature branches must update version manifests on the branch before PR creation so the deployed Dev staging environment displays the exact target release version under human review.

### 2. Surgical Diff Isolation & Zero Scope Creep
- **Principle**: Targeted edits (such as version bumps or localized styling fixes) must strictly touch only the intended lines.
- **Verification**: Always run `git diff` across all modified files before committing to assert zero unintended layout, tag, or whitespace mutations on untouched pages.

---

## 11. Active Guidance Highway Adherence (Reading & Acting on Justfile Beacons)

### 1. The Point-of-Action Guidance Principle
- **Dynamic Priming**: Instead of relying on static system prompt memory for complex, multi-phase operational procedures, agents must actively read and strictly follow the **colorized terminal guidance banners** emitted by `Justfile` recipes and automation scripts.
- **Sequential Execution Assurance**: When a `Justfile` recipe finishes execution, its output provides a dedicated `👉 NEXT STEP:` beacon. Agents should prioritize executing that exact indicated step rather than speculating on alternate or out-of-order procedures.

### 2. The Chained Delivery Lifecycle Beacons
- `just branch <name>` $\to$ Reminds to adhere to 500 LOC ceiling on all changed files and run `just check`.
- `just check` $\to$ Prompts to run `just pr create '<title>'` to open staged companion PRs.
- `just pr create` $\to$ Prompts to monitor `deploy-dev.yml` and probe live Dev links before presenting for Mk1 review.
- `just pr merge` $\to$ Prompts to pull `main`, run `just sync-version`, and update `docs/changelog.md`.
- `just sync-version` $\to$ Validates changelog release headers before tagging.
- `just release` $\to$ Prompts to watch production deployment and trigger `/learn` for continuous improvement.

---

## 12. Staged Semantic Versioning & Edge Subpath Proxy Invariants

### 1. Mandatory Pre-Staging Version Sync & Implementation Plan Invariant
- **Implementation Plan Mandate**: Every `implementation_plan.md` MUST explicitly declare the target semantic release version (e.g. `Target Semantic Version: v2.12.1 (Patch)` or `v2.13.0 (Minor)`).
- **Pre-Staging Synchronization**: Feature branches must synchronize semantic versions across all 7 manifests (`just sync-version <target-version>`) and add the corresponding `docs/changelog.md` release entry (`## [X.Y.Z] - YYYY-MM-DD`) **prior** to opening pull requests (`just pr create`) and deploying to Dev (`deploy-dev.yml`).
- **Anti-Masquerading Invariant**: Never push a feature branch to GitHub without synchronizing the target version. Unsynced deployments cause `deploy-dev.yml` to build container images reporting stale version numbers in `/health` telemetry, masquerading new code under old tags.
- **PR Title Prefix**: All companion PR titles and commits must carry the target version prefix `[vX.Y.Z] <type>(<scope>): <summary>`.

### 2. Multi-Domain Edge Proxy Subpath Preservation
- When proxying dedicated subdomains (`docs.credence.run`, `blog.credence.run`) to static asset buckets (Cloudflare Pages), the edge router (`_worker.js`) must preserve full directory paths (e.g. `/docs/intro.md`, `/blog/essay.md`) without prefix stripping.
- Path stripping is strictly limited to path-prefixed routes on the primary dev hostname (e.g. `dev.credence.run/docs/`).

### 3. Fail-Closed Client Markdown Fetch Validation
- Client-side document engines (`app.js`) must validate incoming text before parsing:

```javascript
if (md.trim().startsWith('<!DOCTYPE html>') || md.trim().startsWith('<html') || md.trim().startsWith('<head')) {
  throw new Error(`Invalid markdown response: received HTML payload for ${target.path}`);
}
```

This prevents SPA 404 fallback HTML documents from ever rendering nested navbars into content bodies.

---

## 13. The Autonomous Lean Patch Release Execution Gate (`/learn` $\to$ `vX.Y.1`)

- **Principle**: Continuous learning from `/learn` must never sit stranded in unreleased working trees or unversioned commits.
- **Immediate Patch Mandate**: Once the user approves `learning_proposal.md` and the skill/rule updates are applied and verified:
  1. Add `## [X.Y.1] - YYYY-MM-DD` release entry to `docs/changelog.md`.
  2. Execute `just sync-version <X.Y.1>`.
  3. Execute `just release <X.Y.1> "continuous learning skills update"`.
- **Zero-Stall Invariant**: The agent must proactively and autonomously execute the patch release sequence to completion (sync $\to$ commit $\to$ tag $\to$ push $\to$ verify prod deploy), ensuring every learning cycle produces an immutable, signed, and deployed patch version without waiting for user reminders.

---

## 14. Multi-Line Markdown Callout & Blockquote Parser Invariant

### 1. Contiguous Block Slurping & Recursive AST Evaluation
- **Cohesive Container Slurping**: Zero-build markdown state machines must slurp all contiguous blockquote lines (`> ...`), including empty blockquote spacing lines (`>` or `> `), into a unified container before parsing.
- **Recursive AST Ingestion**: Strip leading `^\s*>\s?` across all collected sublines and pass the joined content to `parseMarkdown()`. This ensures inner headings (`### ...`), bullet/numbered lists, inline math, bold, and code blocks render correctly inside alert callout boxes (`.alert-box`).
- **Fail-Closed Tag Matching**: Raw HTML tag detection must never match bare blockquote markers (`>`); use strict tag start regex (`HTML_TAG_START_REGEX = /^<([a-z][a-z0-9]*)\b[^>]*>/i`) rather than shallow checks like `line.trim().endsWith('>')`.

---

## 15. Clean Session Brain Scratch Scripts & Approval Bootstrapping Invariant (`inv-clean-scratch-scripts`)

### 1. Mandatory Brain Scratch Storage Location
- **Session History Preservation**: Ad-hoc scripts requiring user approval (`BypassSandbox: true`) must strictly be written to standalone files in the active session artifact brain directory (`<appDataDir>/brain/<conversation-id>/scratch/<name>.py`), never in repository root or workspace `/scratch/`.
- **Zero-Blob Standard**: Multi-line inline command blobs (`python -c "..."`) are prohibited for user approvals.
- **Single-Approval Iteration**: Saving scripts as standalone files allows the human operator to grant "Always Allow" on `python3 <appDataDir>/brain/<conversation-id>/scratch/<name>.py`, enabling subsequent agent edits to the script without re-prompting.

### 2. Workspace Approval Bootstrapping Gate
- Fresh workspaces must execute `just bootstrap-approvals` (`scripts/bootstrap_approvals.py --execute`) to prime the IDE command approval cache across all safe, read-only command shapes before starting feature development.






