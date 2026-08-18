# Agent Guidelines & Project Invariants for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

---

## 1. Core Engineering & Runtime Safety
- **Isolated Workspace**: Credence is completely decoupled from other repositories.
- **Python & SQLModel Async**: Python `>=3.12,<3.13`. Always use `sqlmodel.ext.asyncio.session.AsyncSession` and `async_sessionmaker`. Avoid `from __future__ import annotations` in `models.py`.
- **Hermetic Testing**: Default unit test suite (`tests/`) must be 100% network-free. Use `sqlite+aiosqlite:///:memory:` and offline HTML fixtures.
- **Scoped Verification for Docs-Only Changes**: When modifying purely Markdown documentation, tutorials, blog essays, or static zero-build assets (`docs/`, `blog/`, `credence-docs`), bypass the full Python regression test suite (`just test`). Verify using local static inspection or web preview (`just serve-web`). Reserve full `just test`, `just test-e2e`, and `just benchmark` for changes to Python source code (`credence/`), test suites (`tests/`), or data models.
- **Human Review Before Commits ("Mk1 Eyeball")**: Never execute `git commit` automatically. Always present changes and live verification results for human approval first.
- **Token Budget & Coexistence**: Prioritize `CREDENCE_GEMINI_API_KEY`. Enforce token budgets and automatic offline circuit-breaker fallbacks (`QUOTA_PRESERVED`) at 30% headroom to protect interactive dev sessions.
- **Network Ingestion SSRF Guard**: Reject cloud metadata (`169.254.169.254`, `metadata.google.internal`), loopback (`127.0.0.1`, `localhost`), and RFC 1918 private subnets unless running hermetic local fixtures (`allow_local=True`).
- **Red Team Ingestion & Protocol Defense**: XML parsers must reject `<!DOCTYPE` / `<!ENTITY` declarations (Billion Laughs protection). External LLM inputs must be enclosed in `<untrusted_source_text>` containers with prompt injection guard directives. FastMCP and P2P relay endpoints must enforce token-bucket rate limiters.
- **XML ElementTree Traversal Safety**: Never use boolean `or` expressions on ElementTree elements (e.g. `find(a) or find(b)`); always check `elem is not None` or use `_find_first_elem()` to prevent dropping leaf text elements.
- **Content Decoupling & Hermetic CI**: Keep application repos lean by separating marketing HTML from core code. Maintain technical tutorials in `docs/tutorials/` in clean Markdown. CI workflows (`ci.yml`) must run 100% hermetically without cloud secrets.
- **Context Governance & Progressive Disclosure**: Keep `AGENTS.md` lean (<1,000 tokens) in thematic categories. Place multi-step runbooks in `.agents/skills/` and complete specifications in `docs/`.

---

## 2. Epistemic Ingestion & Scoring Engine
- **Poe's Law & Satire Safeguards**: Treat structural Schema.org and masthead badges as candidate cues. Neutralize legitimate satire ($0.00$), but invoke `SPJ-1.6` cloaking overrides (disabling satire protection) on factual defamatory/health allegations.
- **Namespaced Fixed Taxonomies**: Never hardcode rule names in scoring math; use namespaced URIs (`domain:cluster/rule_id@version`) pinned by catalog SHA-256 hashes.
- **Whitespace-Insensitive Grounding**: Quote validators must collapse whitespace sequences (`\s+` -> ` `) in both citations and source DOM text before substring matching ($G=1.0$).
- **Transparent Heuristic Disclosure**: When the offline governor activates, explicitly populate `evaluation_method: "offline_structural_heuristic"` with confidence capped at $\le 0.50$.

---

## 3. Cryptographic Mesh & Empirical Authority
- **RFC 8785 Canonical JSON & Ed25519 Custody**: Signatures must use RFC 8785 canonical bytes with UTC timestamps. Intermediate relay nodes must never re-sign valid envelopes.
- **5-Factor Node Quality ($Q_i$)**: Reputation evaluates $Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$. Bootstrap seeds (`peers.json`) require root Ed25519 signature verification.
- **Empirical Expertise ($E_i$) & Anti-Diploma Invariant**: Authority is earned via performance ($E_i = 0.40 C + 0.35 G + 0.15 V + 0.10 L$) and combined with node quality ($W_i = 0.20 Q_i + 0.80 E_i$). Requires domain entropy across $\ge 5$ distinct FQDNs. Hallucinated findings incur a 50% score slash.
- **The Galileo Rule (Asymmetric Grounded Evidence)**: Absence of evidence is not evidence of absence. Verified domain authorities submitting 100% grounded citations cannot be outlier-dismissed (`is_outlier = False`) by swarms reporting zero violations. Consensus uses Domain Authority Weighted Medians.
- **BitTorrent Work-Sharing & Generous Defaults**: Nodes seed attestations freely and divide syndicated feeds across peers to achieve 92.3% compute savings at $0.00 token cost.

---

## 4. Universal Presentation Layer & Zero-Build Web
- **Universal Feature Parity**: Maintain synchronous feature parity across all 4 interfaces: **CLI** (`credence`), **FastMCP 2.0** (`credence_` tools & `credence://` resources), **Textual TUI** (`credence tui`), and **Zero-Build Web UI** (`web/`).
- **Universal Zero-Build Standards (Zero-npm Invariant)**: All public web surfaces, documentation portals (`credence-docs`), and sovereign blogs strictly use vanilla HTML5, CSS Custom Properties (`credence-ui.css`), and native ES Modules with **zero npm dependencies, zero package.json, and zero build toolchains**. Never introduce Node.js frameworks (Astro, Next.js, Vite) for any web property.
- **Pure Logic Decoupling**: Business logic must execute and test decoupled from presentation layers (`tests/test_interfaces_isolation.py`).

---

## 5. Standard Task Commands (`Justfile`)
- `just agent-check`: Verify declarative Antigravity skills and workspace configuration.
- `just test`: Run fast hermetic unit test suite (<65s).
- `just test-e2e-mock`: Run offline mock end-to-end integration test.
- `just test-e2e`: Run online end-to-end integration tests (requires `CREDENCE_LIVE_TESTS=1`).
- `just serve-web`: Launch local preview server for visual Mk1 Eyeball review.
- `just tf-validate`: Validate Terraform configurations across GCP and Cloudflare.
- `just lint`: Run `ruff check`, `ruff format --check`, and `mypy credence tests`.
- `just format`: Autoformat code with Ruff.
- `just tui`: Launch interactive Textual terminal workstation.
- `just benchmark`: Execute Golden 12 cross-profile benchmark suite.
- `just mesh-cluster-up`: Launch 13-node local P2P mesh cluster with hardware pre-flight check.
- `just serve-sse`: Start FastMCP server in SSE mode on port 8000.

*For complete mathematical proofs, formulas, and architectural references, see 📘 [`docs/agent-invariants.md`](docs/agent-invariants.md).*
