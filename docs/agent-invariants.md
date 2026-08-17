# Credence Agent Invariants & Architectural Rules

This document outlines mandatory rules and design invariants for human contributors and AI agents working on Credence.

---

## 1. Project Isolation Invariant
- Credence is an autonomous project living exclusively at `/home/pendragon/Projects/credence/`.
- Never reference or import modules from external repositories.

---

## 2. Python & Database Invariants
- **Python Version**: `>=3.12,<3.13`.
- **SQLModel Async**: Always use `sqlmodel.ext.asyncio.session.AsyncSession` combined with `sqlalchemy.ext.asyncio.async_sessionmaker`.
- **Avoid string forward references**: Never use `from __future__ import annotations` in `credence/models.py` to prevent SQLAlchemy mapper resolution bugs in Python 3.12.
- **SQLite Database Isolation**: All automated unit tests must use in-memory SQLite (`sqlite+aiosqlite:///:memory:`).
- **SQLite Performance Pragmas**: The production engine operates in WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`).

---

## 3. Extensible Taxonomy Invariants
- Taxonomies reside in [`credence/taxonomies/*.yaml`](file:///home/pendragon/Projects/credence/credence/taxonomies).
- Every rule must define: `rule_id`, `name`, `severity` ($1 \dots 5$), `description`, `evidence_guidelines`, and a computed `namespaced_uri` (`domain:cluster/rule_id@version`).
- The `TaxonomyRegistry` must dynamically discover all YAML files without code changes.
- Never hardcode rule names in pipeline scoring math. Always use namespaced URIs and generic numerical severity/confidence inputs.

---

## 4. Ingestion & Memory Safeguards
- All Playwright snapshot executions must pass through the `asyncio.Semaphore(1)` gate (`MAX_CONCURRENT_SNAPSHOTS`) to prevent Chromium OOM spikes.
- Both a visual full-page screenshot (`.png`) and rendered DOM (`.html`) are persisted alongside normalized SHA-256 and SimHash-64.

---

## 5. Poe's Law & Satire Safeguards
- Always classify satirical content (`is_satire=True`, `SATIRE_PARODY`) before calculating suspicion scores.
- Legitimate satire is neutralized to score `0.0`, while cloaked bad-faith disinformation is penalized under `SPJ-1.6`.

---

## 6. Grounded Citation & Text Normalization Rules
- Grounded citation matching must normalize all whitespace sequences (`\s+` $\to$ ` `) in both the extracted DOM prose and cited excerpts before matching.
- Any ungrounded (hallucinated) citation is stripped from scoring math.

---

## 7. Token Safety & Development Coexistence Invariant
- Always prioritize `CREDENCE_GEMINI_API_KEY` over shared dev keys.
- Enforce hourly/daily token budgets and automatic offline circuit-breaker fallbacks (`QUOTA_PRESERVED`) to guarantee that autonomous auditing never starves interactive Antigravity development sessions.
- Factor Gemini 3.7 Flash **thinking tokens** into all cost and budget calculations.

---

## 8. Human Review Before Commits ("Mk1 Eyeball")
- Never execute `git commit` automatically. Always present changes and live verification results for human review first, and only commit when explicitly requested by the user.

---

## 9. Textual & Rich Markup Escaping
- Never use unescaped `[/]` or bracket shortcuts in Textual/Rich widget strings; format as `[bold]/[/bold]` or escape as `[\]`.

---

## 10. FastMCP 2.0 & Datetime Serialization
- Always use `model_dump(mode="json")` for Pydantic models containing datetimes before calling `json.dumps()` in FastMCP tool handlers and tests.

---

## 11. Mesh Network Topology & Cartel Resilience ($N = 13, f = 4$)
- Comprehensive mesh testing requires $N = 13$ nodes in a Watts-Strogatz small-world lattice ($d = 4$) to verify relay TTL decrements, 4 pathological topologies (Daisy Chain, Barbell Netsplit, Sybil Eclipse, Star Flooding), and $N \ge 3f + 1$ ($f = 4$) Byzantine Sybil cartel isolation.

---

## 12. Operational Cost Profile Enforcement
- The `FREE` profile strictly enforces a $0.00 daily spend ceiling with $0$ thinking tokens.
- The `BALANCED` profile operates at a $0.50/day cap with $1,024$ thinking tokens and dynamic escalation on ambiguity.
- The `ULTRA` profile enables deep reasoning ($4,096 - 16,384$ tokens), `gemini-1.5-pro` escalation, and 10,000-word ingestion limits.

---

## 13. Cloud Run Cost Capping & Scale-to-Zero Invariant
- Production Cloud Run v2 services must configure `min_instance_count = 0` (scale-to-zero), `cpu_idle = true`, and resource limits dynamically tuned to the active cost profile.
- GCP projects must configure a **$15.00 USD/month Cloud Billing Budget ceiling** (`google_billing_budget`) with automated 50%, 80%, and 100% threshold alarms.
- All API keys must be referenced securely through Google Secret Manager (`CREDENCE_GEMINI_API_KEY`).

---

## 14. Host Resource Safety & Pre-Flight Governor Invariant
- Local multi-node cluster orchestration must run pre-flight memory checks via `hardware_guard.py` (throttling to $\le 3$ nodes on $< 2\text{GB}$ RAM hosts like Raspberry Pis) and enforce hard `mem_limit: 128m` Docker cgroups limits per container.

---

## 15. Epistemic Benchmark & Grounded Heuristics Invariant
- Satire cue extractors must strictly target structural declarations (Schema.org `SatiricalArticle`, masthead badges, and dedicated disclaimer containers) rather than unrestricted keyword matching across arbitrary prose.
- Heuristic evaluation engines and synthetic test fixtures must quote exact verbatim substrings from the extracted DOM text to guarantee 100% quote grounding validation (`is_grounded=True`).

---

## 16. Mermaid Diagram Contrast & Visual Accessibility Invariant
- Never apply custom light background fill styles (`fill:#d1fae5`, `fill:#fef3c7`) in Mermaid diagrams without declaring explicit high-contrast font colors (`color:#0f172a`), or preferably rely on standard unstyled Mermaid node themes to guarantee readable text across both light and dark UI themes.

---

## 17. Attestation Timestamp & Canonical Payload Precision Invariant
- When persisting signed `AuditReport` models to SQLModel database tables (`AuditRecord`) and reconstructing them for export or verification (`credence verify-file`), explicitly preserve the exact signed `audited_at` timestamp with timezone awareness (`UTC`) to guarantee 100% cryptographic signature validity under RFC 8785.

---

## 18. Epistemic Node Quality & Seed Signature Invariant
- Peer node reputation must strictly evaluate the 5-factor quality equation ($Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$).
- Remote bootstrap seed manifests (`peers.json`) fetched from `seeds.credence.nexus` or any mirror MUST be cryptographically verified against the network root Ed25519 public key using RFC 8785 canonical bytes before adopting peer addresses into active routing tables.

---

## 19. Gossip Envelope Signature Preservation & Invariant Normalization
- When relaying or re-broadcasting gossip envelopes, intermediate mesh relay nodes must NEVER re-sign an envelope with their local private key if `envelope.signature` is already present from the originating node. Overwriting original signatures causes downstream signature verification failures (`Received message with INVALID envelope signature`) across multi-hop small-world lattices.
- When packing payloads into `MeshMessageEnvelope`, always normalize inner Pydantic models using `model_dump(mode="json")`, and envelope canonical byte generators (`get_canonical_bytes()`) must provide a fallback datetime ISO serializer to prevent runtime `TypeError` during serialization.

---

## 20. Web Frontend Zero-Build & Web Crypto Verification Invariant
- All public web frontends across the Credence ecosystem must be built strictly using **vanilla modern web standards** (Semantic HTML5, CSS Custom Properties, and native ES Modules) with **zero Node.js/npm build dependencies** and zero JavaScript runtime frameworks.
- Client-side cryptographic verification of signed audit reports and seed files must strictly use the native W3C **Web Cryptography API** (`window.crypto.subtle`) rather than external JavaScript crypto libraries.
- Dynamic social previews (OpenGraph / Twitter cards) must be pre-rendered or injected by edge cache rules / Cloud Run serverless endpoints with long-lived edge caching (`s-maxage=2592000`) rather than requiring client-side single-page app hydration.
- See 📘 **[Web Frontend Architecture](frontend-architecture.md)** for full evaluation and rationale.

---

## 21. Turnkey White-Label Federation & Dry-Run Governor Invariant
- All deployment scripts, publishing utilities, and infrastructure templates must provide non-destructive `--dry-run` inspection modes and local preview servers (`just serve-web`) for human review ("Mk1 Eyeball") prior to cloud mutation.
- Scaffolding tools (`credence init-org`) must generate completely sovereign, parameterized multi-cloud configurations and cryptographic root keypairs to allow independent organizations to run compatible federated mesh networks without code modifications.
- See 📘 **[White-Label Mesh Federation Guide](federation-whitelabel.md)** and 📘 **[Multi-Cloud Deployment](deployment-multi-domain.md)** for full operator guides.

---

## 22. Empirical Subject-Matter Expertise & Anti-Diploma Invariant
- Mesh nodes must NEVER grant subject-matter authority based on static cryptographic certificates, diplomas, or claimed credentials.
- Domain expertise ($E_i$) must strictly be earned and calculated from historical performance metrics ($E_i = 0.40 C + 0.35 G + 0.15 V + 0.10 L$) and combined with node quality ($W_i = 0.20 Q_i + 0.80 E_i$).
- Any node citing an ungrounded or fabricated quote in a specialized domain is penalized with an immediate 50% domain score slash ($E_i \leftarrow E_i \times 0.50$).

---

## 23. Epistemic BitTorrent Work-Sharing & Generous Defaults Invariant
- Credence nodes must adopt generous default behaviors: Attestation Seeding (broadcasting evaluated audits freely at $0.00 compute) and Mesh Work-Sharing (dividing syndicated RSS/Atom/JSON feeds across the mesh to cover $N \times$ more internet without token duplication).
- Nodes must query the local attestation cache and verified peer signatures ($Q_i \ge 0.85$) prior to LLM ingestion to adopt peer audits at $0.00 token cost.
- Background feed ingestion must automatically pause whenever daily token headroom falls below 30% to preserve quota for interactive development sessions.

---

## 24. Universal Presentation Layer Feature Parity Invariant
- All system features, inspection tools, and configuration options must maintain synchronous feature parity across all four official interfaces: **CLI** (`credence`), **FastMCP 2.0** (`credence_` tools & `credence://` resources), **Textual TUI** (`credence tui`), and **Zero-Build Web UI** (`web/`).

