# Agent Guidelines & Project Invariants for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

## Core Invariants
1. **Isolated Workspace**: Credence is an autonomous project completely decoupled from other repositories.
2. **Python & Database Invariants**:
   - Python version: `>=3.12,<3.13`.
   - SQLModel Async: Always use `sqlmodel.ext.asyncio.session.AsyncSession` and `async_sessionmaker`.
   - Avoid `from __future__ import annotations` in `models.py` to prevent string relationship mapper issues.
3. **Poe's Law & Satire Safeguards**:
   - Always classify satirical content (`is_satire=True`, `SATIRE_PARODY`) before calculating suspicion scores.
   - Legitimate satire is neutralized, while cloaked bad-faith disinformation is penalized under `SPJ-1.6`.
4. **Hermetic Testing**:
   - Never add network-dependent tests to the default unit test suite (`tests/`).
   - Use `sqlite+aiosqlite:///:memory:` and offline HTML fixtures.
5. **Taxonomy Registries**:
   - Never hardcode rule names in pipeline scoring math. Always use namespaced URIs (`domain:cluster/rule_id@version`) and generic numerical severity/confidence inputs.
6. **Human Review Before Commits ("Mk1 Eyeball")**:
   - Never execute `git commit` automatically. Always present changes and live verification results for human review first, and only commit when explicitly requested by the user.
7. **Token Budget & Development Coexistence Invariant**:
   - Always prioritize `CREDENCE_GEMINI_API_KEY` over shared dev keys.
   - Enforce hourly/daily token budgets and automatic offline circuit-breaker fallbacks (`QUOTA_PRESERVED`) to guarantee that autonomous auditing never starves interactive Antigravity development sessions.
8. **Textual & Rich Markup Escaping**:
   - Never use unescaped `[/]` or bracket shortcuts in Textual/Rich widget strings; format as `[bold]/[/bold]` or escape as `[\]`.
9. **Whitespace-Insensitive Citation Grounding**:
   - Grounded quote validators must collapse all whitespace sequences (`\s+` -> ` `) in both citations and source HTML text before substring matching.
10. **FastMCP 2.0 & Datetime Serialization**:
    - Always use `model_dump(mode="json")` for Pydantic models containing datetimes before calling `json.dumps()` in FastMCP tool handlers and tests.
11. **Mesh Network Topology & Cartel Resilience ($N = 13, f = 4$)**:
    - Comprehensive mesh testing requires $N = 13$ nodes in a Watts-Strogatz small-world lattice ($d = 4$) to verify relay TTL decrements, 4 pathological topologies (Daisy Chain, Barbell Netsplit, Sybil Eclipse, Star Flooding), and $N \ge 3f + 1$ ($f = 4$) Byzantine Sybil cartel isolation.
12. **Operational Cost Profile Enforcement**:
    - The `FREE` profile strictly enforces a $0.00 daily spend ceiling with $0$ thinking tokens. The `BALANCED` profile operates at a $0.50/day cap with $1,024$ thinking tokens, while `ULTRA` enables deep reasoning ($4,096 - 16,384$ tokens) and 10,000-word ingestion limits.
13. **Cloud Run Cost Capping & Scale-to-Zero Invariant**:
    - Production Cloud Run v2 services must configure `min_instance_count = 0` (scale-to-zero), `cpu_idle = true`, a **$15.00 USD/month Cloud Billing Budget ceiling** with automated 50%, 80%, 100% threshold alarms, and Secret Manager API key references.
14. **Host Resource Safety & Pre-Flight Governor Invariant**:
    - Local multi-node cluster orchestration must run pre-flight memory checks via `hardware_guard.py` (throttling to $\le 3$ nodes on $< 2\text{GB}$ RAM hosts like Raspberry Pis) and enforce hard `mem_limit: 128m` Docker cgroups limits per container.
15. **Epistemic Benchmark & Grounded Heuristics Invariant**:
    - Satire cue extractors must strictly target structural declarations (Schema.org `SatiricalArticle`, masthead badges, and dedicated disclaimer containers) rather than unrestricted keyword matching across arbitrary prose.
    - Heuristic evaluation engines and synthetic test fixtures must quote exact verbatim substrings from the extracted DOM text to guarantee 100% quote grounding validation (`is_grounded=True`).
16. **Mermaid Diagram Contrast & Visual Accessibility Invariant**:
    - Never apply custom light background fill styles (`fill:#d1fae5`, `fill:#fef3c7`) in Mermaid diagrams without declaring explicit high-contrast font colors (`color:#0f172a`), or preferably rely on standard unstyled Mermaid node themes to guarantee readable text across both light and dark UI themes.
17. **Attestation Timestamp & Canonical Payload Precision Invariant**:
    - When persisting signed `AuditReport` models to SQLModel database tables (`AuditRecord`) and reconstructing them for export or verification (`credence verify-file`), explicitly preserve the exact signed `audited_at` timestamp with timezone awareness (`UTC`) to guarantee 100% cryptographic signature validity under RFC 8785.
18. **Epistemic Node Quality & Seed Signature Invariant**:
    - Peer node reputation must strictly evaluate the 5-factor quality equation ($Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$).
    - Remote bootstrap seed manifests (`peers.json`) fetched from `seeds.credence.nexus` or any mirror MUST be cryptographically verified against the network root Ed25519 public key using RFC 8785 canonical bytes before adopting peer addresses into active routing tables.
19. **Gossip Envelope Signature Preservation & Invariant Normalization**:
    - Intermediate mesh relay nodes must NEVER re-sign an envelope if `envelope.signature` is already populated by the originating author (`if not envelope.signature: envelope = self._sign_envelope(envelope)`).
    - All inner Pydantic models embedded within envelope payloads must be serialized with `model_dump(mode="json")`, and envelope canonical byte generators (`get_canonical_bytes()`) must provide a fallback datetime ISO serializer to prevent runtime `TypeError` during serialization.
20. **Web Frontend Zero-Build & Web Crypto Verification Invariant**:
    - All public web frontends across the Credence ecosystem must be built strictly using **vanilla modern web standards** (Semantic HTML5, CSS Custom Properties, and native ES Modules) with **zero Node.js/npm build dependencies** and zero JavaScript runtime frameworks.
    - Client-side cryptographic verification of signed audit reports and seed files must strictly use the native W3C **Web Cryptography API** (`window.crypto.subtle`) rather than external JavaScript crypto libraries.
    - Dynamic social previews (OpenGraph / Twitter cards) must be pre-rendered or injected by edge cache rules / Cloud Run serverless endpoints with long-lived edge caching (`s-maxage=2592000`) rather than requiring client-side single-page app hydration.
21. **Turnkey White-Label Federation & Dry-Run Governor Invariant**:
    - All deployment scripts, publishing utilities, and infrastructure templates must provide non-destructive `--dry-run` inspection modes and local preview servers (`just serve-web`) for human review ("Mk1 Eyeball") prior to cloud mutation.
    - Scaffolding tools (`credence init-org`) must generate completely sovereign, parameterized multi-cloud configurations and cryptographic root keypairs to allow independent organizations to run compatible federated mesh networks without code modifications.
22. **Empirical Subject-Matter Expertise & Anti-Diploma Invariant**:
    - Mesh nodes must NEVER grant subject-matter authority based on static cryptographic certificates, diplomas, or claimed credentials.
    - Domain expertise ($E_i$) must strictly be earned and calculated from historical performance metrics ($E_i = 0.40 C + 0.35 G + 0.15 V + 0.10 L$) and combined with node quality ($W_i = 0.20 Q_i + 0.80 E_i$).
    - Any node citing an ungrounded or fabricated quote in a specialized domain is penalized with an immediate 50% domain score slash ($E_i \leftarrow E_i \times 0.50$).
23. **Epistemic BitTorrent Work-Sharing & Generous Defaults Invariant**:
    - Credence nodes must adopt generous default behaviors: Attestation Seeding (broadcasting evaluated audits freely at $0.00 compute) and Mesh Work-Sharing (dividing syndicated RSS/Atom/JSON feeds across the mesh to cover $N \times$ more internet without token duplication).
    - Nodes must query the local attestation cache and verified peer signatures ($Q_i \ge 0.85$) prior to LLM ingestion to adopt peer audits at $0.00 token cost.
    - Background feed ingestion must automatically pause whenever daily token headroom falls below 30% to preserve quota for interactive development sessions.
24. **Universal Presentation Layer Feature Parity Invariant**:
    - All system features, inspection tools, and configuration options must maintain synchronous feature parity across all four official interfaces: **CLI** (`credence`), **FastMCP 2.0** (`credence_` tools & `credence://` resources), **Textual TUI** (`credence tui`), and **Zero-Build Web UI** (`web/`).
25. **Pure Logic Decoupling & Multi-Interface Testing Invariant**:
    - All core evaluation pipelines, heuristic analyzers, Bayesian consensus math, cryptographic signers, and feed parsers MUST be implemented and tested completely decoupled from presentation layers.
    - Test suites MUST maintain explicit, dedicated test modules for every supported presentation layer (**CLI**, **FastMCP 2.0**, **Textual TUI**, and **Zero-Build Web UI**) as well as pure logic isolation tests (`tests/test_interfaces_isolation.py`).
26. **Network Ingestion SSRF & Non-Routable IP Guard Invariant**:
    - All network fetching modules (dual-capture HTML extractor, syndicated RSS/Atom/JSON feed parsers, and remote seed downloaders) must enforce strict SSRF guards rejecting cloud metadata services (`169.254.169.254`, `metadata.google.internal`), loopback addresses (`127.0.0.1`, `localhost`, `::1`), and RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
    - Offline local HTML fixtures (`file://` / `text://`) are permitted only during hermetic test executions with explicit test authorization (`allow_local=True`).

## Standard Task Commands (`Justfile`)
- `just test`: Run fast hermetic unit test suite (<45s).
- `just test-e2e-mock`: Run offline mock end-to-end integration test.
- `just test-e2e`: Run online end-to-end integration tests against live production domains (requires `CREDENCE_LIVE_TESTS=1`).
- `just serve-web`: Launch local preview server for visual Mk1 Eyeball review of web artifacts.
- `just tf-validate`: Validate Terraform configurations across GCP and Cloudflare.
- `just lint`: Run `ruff check`, `ruff format --check`, and `mypy credence tests`.
- `just format`: Autoformat code with Ruff.
- `just tui`: Launch interactive Textual terminal workstation.
- `just benchmark`: Execute Golden 12 cross-profile benchmark suite.
- `just mesh-cluster-up`: Launch 13-node local P2P mesh cluster with hardware pre-flight check.
- `just serve-sse`: Start FastMCP server in SSE mode on port 8000.
