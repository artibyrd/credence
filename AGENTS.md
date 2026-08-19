# Agent Guidelines & Project Invariants for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

---

## 1. Core Engineering, Safety & Knowledge Governance
- **Isolated Workspace**: Credence is completely decoupled from other repositories.
- **Python & SQLModel Async**: Python `>=3.12,<3.13`. Always use `sqlmodel.ext.asyncio.session.AsyncSession` and `async_sessionmaker`. Avoid `from __future__ import annotations` in `models.py`.
- **Continuous Changelog & Semantic Version Governance**: Diligently maintain `docs/changelog.md` and manage Semantic Version bumps across the ecosystem whenever notable features or fixes are completed.
- **Hermetic Testing & Docs Integrity**: Default test suite (`tests/`) must be 100% network-free using `sqlite+aiosqlite:///:memory:`, offline HTML fixtures, and automated validation (`test_docs_integrity.py`).
- **Scoped Verification for Docs-Only Changes**: When modifying purely Markdown documentation, tutorials, blog essays, or static zero-build assets (`docs/`, `blog/`, `credence-docs`), bypass the full Python regression test suite (`just test`). Verify using local static inspection or web preview (`just serve web`).
- **Human Review Before Commits ("Mk1 Eyeball") & Target Version Disclosure**: Never execute `git commit` automatically. Always present changes, live verification results, and explicitly declare the target Semantic Version about to be released (e.g. `v1.7.0` / `v1.8.0`) for human review and approval first.
- **Knowledge Governance & Context Economy (/remember)**: Never dump multi-step procedural runbooks into `AGENTS.md`. Strictly enforce the 4-tier knowledge taxonomy (`AGENTS.md` < 1,000 tokens for universal invariants, `.agents/skills/` for progressive runbooks, `Justfile` for tooling, and `docs/` for specs).
- **Multi-Model Sovereignty & Token Budget**: Abstract inference via decoupled adapters (Gemini 3.7 Flash default reference engine with 4k thinking budget Pareto sweet spot, Claude 3.7 Sonnet, GPT-4o, DeepSeek R1, Ollama/vLLM) with automatic offline circuit breakers (`QUOTA_PRESERVED`) at 30% headroom.
- **Network Ingestion SSRF Guard**: Reject cloud metadata (`169.254.169.254`, `metadata.google.internal`), loopback (`127.0.0.1`, `localhost`), and RFC 1918 private subnets unless running hermetic local fixtures (`allow_local=True`).
- **Red Team Ingestion & Protocol Defense**: XML parsers must reject `<!DOCTYPE` / `<!ENTITY` declarations (Billion Laughs protection). External LLM inputs must be enclosed in `<untrusted_source_text>` containers with prompt injection guard directives.
- **XML ElementTree Traversal Safety**: Never use boolean `or` expressions on ElementTree elements (e.g. `find(a) or find(b)`); always check `elem is not None` or use `_find_first_elem()`.
- **Model Default Truth & Verification Guardrail**: Never assume or hallucinate model version defaults. Always treat `credence/config.py` as canonical ground truth (`gemini-3.7-flash` default reference engine).
- **FastMCP 2.0 Reverse Proxy Transport Security**: FastMCP servers running over SSE must configure `TransportSecuritySettings(enable_dns_rebinding_protection=False, allowed_hosts=["*"], allowed_origins=["*"])` behind Cloudflare.
- **Cloudflare Workers Zero-Build Static Assets Invariant**: All Cloudflare Worker deployments utilizing custom `_worker.js` routing with static assets must define `binding = "ASSETS"` in `wrangler.toml` and maintain a `.assetsignore` file excluding `_worker.js` and `wrangler.toml`.
- **Edge Routing Origin Header Translation**: Cloudflare Worker edge routers must rewrite `Host` headers to native Cloud Run target URLs (`<service>.run.app`) to bypass Google Search Console domain verification requirements.
- **FastMCP Text Evaluation & Serialization Parity**: All standalone text evaluation endpoints (`credence_evaluate_text`) must persist complete `SnapshotRecord`, `AuditRecord`, and `ViolationRecord` entities to SQLite (`text://inline` pseudo-URLs) and serialize nested `datetime` instances to ISO-8601 strings.
- **Stratified Live Web Mutation & Anti-Overfitting Invariant**: Live E2E test suites (`test_live_rotating_suite.py`) must sample targets from a stratified multi-category corpus (`live_corpus.py`) using deterministic date hashing (`YYYY-MM-DD`).
- **Node Germination & Zero-Touch Ignition Invariant**: Fresh, unseeded nodes starting up must execute autonomous germination (`credence germinate` / `germinate_node`) as a non-blocking background task during lifespan startup—minting Ed25519 identity, inoculating Genesis peer attestations at $0.00 token cost, sowing 24 preset feeds, and auditing initial novel articles.
- **Swarm Rendezvous Partitioning & Atomic Inoculation**: Swarm feed sifting must partition candidate feeds using Highest Random Weight (HRW) Rendezvous Hashing (`compute_feed_affinity`) and wrap seed insertions in atomic commit/rollback sub-transactions.
- **3-Plane Deployment Governance**: Ecosystem pipelines operate across 3 decoupled planes: **Edge Plane** (`web/` and `credence-docs` via Cloudflare & `just deploy edge`), **Compute Plane** (`credence-server` on Cloud Run via `just deploy backend`), and **Infra Plane** (Terraform via `just tf apply`).

---

## 2. Epistemic Ingestion & Scoring Engine
- **Topic Entropy Astroturfing Defense (Pizza Hut Problem)**: Topic diversity calculators must incorporate Top-Token Concentration penalties ($C_{\text{top3}}$) alongside Shannon entropy to ensure single-topic promotional pivots trigger autonomous quarantine ($H < 0.30$).
- **Poe's Law & Satire Safeguards**: Treat structural Schema.org and masthead badges as candidate cues. Neutralize legitimate satire ($0.00$), but invoke `SPJ-1.6` cloaking overrides (disabling satire protection) on factual defamatory/health allegations.
- **Attribute-Order Agnostic Metadata Parsing**: HTML meta tag and Schema.org regex parsers must remain order-agnostic with respect to `name`, `property`, and `content` attributes.
- **Namespaced Fixed Taxonomies**: Never hardcode rule names in scoring math; use namespaced URIs (`domain:cluster/rule_id@version`) pinned by catalog SHA-256 hashes.
- **Whitespace-Insensitive Grounding**: Quote validators must collapse whitespace sequences (`\s+` -> ` `) in both citations and source DOM text before substring matching ($G=1.0$).
- **Transparent Heuristic Disclosure**: When the offline governor activates, explicitly populate `evaluation_method: "offline_structural_heuristic"` with confidence capped at $\le 0.50$.

---

## 3. Cryptographic Mesh & Empirical Authority
- **RFC 8785 Canonical JSON & Ed25519 Custody**: Signatures must use RFC 8785 canonical bytes with UTC timestamps. Intermediate relay nodes must never re-sign valid envelopes.
- **Attestation Anti-Tampering Contract**: Any alteration to signed payload fields (`suspicion_score`, `classification`, `content_sha256`) immediately invalidates Ed25519 signature verification.
- **5-Factor Node Quality ($Q_i$)**: Reputation evaluates $Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$. Bootstrap seeds require root Ed25519 signature verification.
- **Empirical Expertise ($E_i$) & Anti-Diploma Invariant**: Authority is earned via performance ($E_i = 0.40 C + 0.35 G + 0.15 V + 0.10 L$) and combined with node quality ($W_i = 0.20 Q_i + 0.80 E_i$). Requires domain entropy across $\ge 5$ distinct FQDNs. Hallucinations incur a 50% score slash.
- **The Galileo Rule (Asymmetric Grounded Evidence)**: Verified domain authorities submitting 100% grounded citations cannot be outlier-dismissed by swarms reporting zero violations. Consensus uses Domain Authority Weighted Medians.
- **BitTorrent Work-Sharing & Generous Defaults**: Nodes seed attestations freely and divide syndicated feeds across peers to achieve 92.3% compute savings at $0.00 token cost.

---

## 4. Universal Presentation Layer & Zero-Build Web
- **Universal Feature Parity**: Maintain synchronous feature parity across all 4 interfaces: **CLI** (`credence`), **FastMCP 2.0** (`credence_` tools & `credence://` resources), **Textual TUI** (`credence tui`), and **Zero-Build Web UI** (`web/`).
- **Human-First In-Context Report Presentation Invariant**: Report inspection interfaces across all four surfaces must present human-first executive briefings, visual trust dimension breakdown meters, and in-context quoted evidence before presenting dense technical metadata or raw JSON payloads.
- **Multi-Display Mode & Stream Discovery Invariant**: All four presentation interfaces must support 3 distinct display modes (`Human`, `Compact`, `Machine` canonical RFC 8785 JSON/NDJSON/TSV and Schema.org `ClaimReview` JSON-LD) alongside 5 standard stream discovery filters (`recent`, `best` $\le 15.0$, `worst` $\ge 60.0$, `satire`, `random`).
- **Universal Zero-Build Standards (Zero-npm Invariant)**: All public web surfaces, documentation portals (`credence-docs`), and sovereign blogs strictly use vanilla HTML5, CSS Custom Properties (`credence-ui.css`), and native ES Modules with **zero npm dependencies, zero package.json, and zero build toolchains**.
- **Edge Subdirectory Canonicalization**: Multi-domain edge routers (`_worker.js`) must intercept internal `env.ASSETS` folder redirects and enforce 301 canonical redirects to prevent folder names (e.g. `/credence.run/`) from appearing in browser address bars.
- **Pure Logic Decoupling**: Business logic must execute and test decoupled from presentation layers (`tests/test_interfaces_isolation.py`).
- **Universal Mermaid & Visual Syntax Guardrail**: All Mermaid diagrams must strictly use standard flow/graph/sequence syntax with special characters enclosed in double quotes (e.g. `id["Label (Details)"]`) and WCAG AA/AAA high contrast on dark slate.

---

## 5. Standard Task Commands (`Justfile`)
- `just preflight [tool]`: Verify developer CLI dependencies (`gcloud`, `wrangler`, `gh`, `terraform`, `poetry`, `docker`, `all`).
- `just check`: Complete pre-commit QA gate (`preflight` -> `lint` -> `test unit` -> `test docs` -> `tf validate` -> `agent-check`).
- `just ignite [burst]`: One-command developer onboarding (setup -> preflight -> germinate -> mock test -> doctor).
- `just doctor`: Multi-plane diagnostic health check across Edge, Compute, Infra, and Declarative Agents.
- `just test [suite]`: Run targeted test suites (`unit`, `all`, `mock`, `live`, `e2e`, `docs`, `docker`).
- `just lint` / `just format`: Run static analysis, type checking, and Ruff auto-formatting.
- `just serve [transport]`: Launch server engine (`sse`, `stdio`, `web`).
- `just tui` / `just benchmark`: Launch terminal workstation or Golden 12 benchmark suite.
- `just gcp [action] [arg]`: Google Cloud Run operations (`status`, `logs`, `tail`, `revisions`, `describe`, `probe`, `germinate`, `rollback`).
- `just edge [action]`: Cloudflare Edge router operations (`status`, `logs`, `login`, `deploy`).
- `just pipeline [action]`: GitHub Actions telemetry and secret auditing (`status`, `watch`, `secrets`).
- `just tf [action]`: Terraform multi-cloud operations (`validate`, `plan`, `apply`, `output`).
- `just deploy [target]`: Safe deployment pipeline with automated health probe (`backend`, `edge`, `all`).
- `just release <version> <message>`: Complete atomic ecosystem release sequence.

---

## 6. Progressive Skills Index (`.agents/skills/`)
- 🧠 [`knowledge-governance`](.agents/skills/knowledge-governance/SKILL.md): 4-tier knowledge taxonomy router (`/remember`), `AGENTS.md` context pruning, and progressive disclosure governance.
- ☁️ [`cloudrun-ops`](.agents/skills/cloudrun-ops/SKILL.md): Google Cloud Run compute plane operations, Workload Identity Federation (WIF) setup, and rollback playbooks.
- 🌐 [`mesh-cluster`](.agents/skills/mesh-cluster/SKILL.md): 13-node Watts-Strogatz local P2P mesh cluster simulation, Byzantine Sybil cartel resistance, and Barbell partition testing.
- 🏛️ [`white-label-ops`](.agents/skills/white-label-ops/SKILL.md): Sovereign organization scaffolding (`credence init-org`), multi-cloud Terraform templates, and zero-build multi-domain edge routing.
- 📊 [`epistemic-benchmark`](.agents/skills/epistemic-benchmark/SKILL.md): Golden 12 cross-profile evaluation benchmark suite and cross-entropy measurement.

*For complete mathematical proofs, formulas, and architectural references, see 📘 [`docs/agent-invariants.md`](docs/agent-invariants.md).*
