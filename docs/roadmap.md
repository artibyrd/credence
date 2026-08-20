---
title: Ecosystem Roadmap & Architecture Horizons
description: Sovereign in-tree tracker for verified foundation milestones, operational edge cases, and future architecture horizons across the Credence ecosystem.
since_version: v1.0.0
verified_version: v1.19.0
last_verified: '2026-08-19'
tags:
- roadmap
- backlog
- known-issues
- architecture
- edge-cases
interfaces:
- CLI
- FastMCP 2.0
- Textual TUI
- Zero-Build Web UI
invariants:
- 1
- 4
- 11
- 26
- 31
difficulty: Intermediate
read_time: 7 min
---

# Ecosystem Roadmap & Architecture Horizons 🧭

This document serves as the **sovereign, in-repository source of truth** for verified architectural milestones, empirical test findings, and future development horizons across the Credence ecosystem.

```mermaid
flowchart TD
    subgraph Foundation["Verified Stable Foundation (v1.19.0)"]
        F1["Dual-Tier Bicameral Engine & Pre-Flight Gate"]
        F2["Autonomous Boredom Engine & Epistemic Roots"]
        F3["White-Label Sovereign Org Scaffolding (credence init-org)"]
        F4["Dual-Project Cloud Run Scale-to-Zero & Anycast Edge"]
        F5["Universal 4-Way Interface Parity (CLI, MCP, TUI, Web)"]
        F6["RFC 8785 Canonical JSON & Ed25519 Custody"]
    end

    subgraph Horizons["Future Architecture Horizons (v2.0.0 Road)"]
        H1["<b>Horizon 1: Edge Traffic Shaping</b><br/><i>Autonomous Cascaded Gateway & ASTRO-GUARD</i>"]
        H2["<b>Horizon 2: Protocol & Identity</b><br/><i>W3C did:key / did:web & Fediverse Bridge</i>"]
        H3["<b>Horizon 3: Agentic Scale</b><br/><i>FastMCP 2.0 Async Batch SSE & Client-Side Wasm</i>"]
    end

    Foundation -.-> Horizons

    classDef darkSlate fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef highlight fill:#1e293b,stroke:#22c55e,stroke-width:2px,color:#fff;
    class Foundation darkSlate;
    class Horizons highlight;
```

---

## 1. Verified Stable Foundation (`v1.19.0`)

The following major subsystems are fully implemented, hermetically tested, and running in production:

* 🟢 **Bicameral Shadow Auditing & Controlled Pre-Flight Gate (`v1.19.0`)**: Automated dual-environment verification (`just config-verify`), differential auditing (`just experiment shadow-audit`), and empirical proof of **83.3% FinOps inference savings**.
* 🟢 **Dual-GCP Hard Isolation & Multi-Domain Edge Router (`v1.18.0 - v1.18.2`)**: Dual-project Terraform infrastructure (`credence-dev` vs `credence-prod`), Cloudflare Anycast edge subdomain routing (`dev.credence.run`), and sub-2.5s scale-to-zero cold start optimization.
* 🟢 **Autonomous Boredom Engine & Epistemic Root Expansion (`v1.16.0`)**: Opportunistic work-sharing, Token Safety Governor gating ($\ge 30\%$ headroom), citation soil harvesting, and automatic feed germination.
* 🟢 **Sovereign White-Label Mesh Federation (`v1.15.0`)**: 1-command organization scaffolding (`credence init-org`), multi-cloud Terraform templates, and $3f+1$ Byzantine Sybil fault tolerance.
* 🟢 **Universal 4-Way Feature Parity & Zero-npm Web Standard**: Synchronized parity across CLI, FastMCP 2.0 (`credence_` tools & `credence://` resources), Textual TUI, and zero-build web dashboards.

---

## 2. Empirical Findings from Real-World Testing

Our live dev/prod deployments, Golden 12 cross-profile benchmarks, and bicameral experiments revealed four key discoveries that guide our upcoming horizons:

1. **The 83.3% FinOps Cascading Law**:
   - *Finding*: 70% of ingress news articles are structurally benign ($S < 25.0$). Routing 100% of feeds to deep 4k thinking is economically inefficient ($135/100k).
   - *Architectural Action*: Build an automated, low-latency edge gateway that dynamically routes benign content to fast local heuristics ($0.00) and escalates only ambiguous or deceptive claims to Gemini 3.7 Flash 4k thinking ($22.50/100k).
2. **Lexical Entropy Collapse in Coordinated Astroturfing**:
   - *Finding*: Programmatic syndication networks and PR slop farms exhibit extreme topical collapse ($H < 0.30$ and $C_{\text{top3}} > 0.45$).
   - *Architectural Action*: Deploy an autonomous rolling entropy daemon (ASTRO-GUARD) across all subscribed RSS roots.
3. **Cross-Organization Zero-Secret Verification**:
   - *Finding*: RFC 8785 canonical JSON bytes signed with Ed25519 private keys can be authenticated by any external node with zero shared secrets.
   - *Architectural Action*: Standardize sovereign node keys into W3C `did:key` and `did:web` decentralization specifications.
4. **Batch Proxy Edge Execution Limits**:
   - *Finding*: Uncached multi-article 4k thinking audits take ~3.8s each. A batch request of 10+ URLs over a synchronous JSON-RPC proxy approaches Cloudflare Worker 30s CPU/wall-clock limits.
   - *Architectural Action*: Implement asynchronous FastMCP 2.0 batch job tokens with Server-Sent Events (SSE) streaming progress.

---

## 3. Future Architecture Horizons

### Horizon 1: Autonomous Traffic Shaping & Edge Intelligence
- **Autonomous Cascaded Gateway (`credence gateway`)**:
  - Transparent HTTP reverse proxy and MCP middleware that dynamically executes fast heuristic triage, evaluates Shannon entropy, and only escalates ambiguous claims to 4k thinking.
- **ASTRO-GUARD Rolling Feed Entropy Daemon**:
  - Background monitor tracking 24-hour topical entropy ($H$) across all subscribed feed roots to flag coordinated astroturfing campaigns.
- **CLI Authenticated Scraping**:
  - Optional `--session-cookie`, `--browser-profile`, or custom headers for auditing content behind subscriber paywalls.

### Horizon 2: Protocol & Decentralized Identity Standard
- **W3C Decentralized Identifier (`did:key` & `did:web`) Support**:
  - Map Ed25519 node identities to standard `did:key:z6M...` and `did:web:domain.org` formats for interoperability with external DID registries.
- **Fediverse & AT Protocol Attestation Bridge**:
  - Native broadcast of signed verification cards to Bluesky (AT Protocol `app.bsky.feed.post`) and Mastodon / ActivityPub networks.
- **Client-Side Cryptographic Certificates**:
  - Printable/exportable zero-npm cryptographic audit receipts for newsroom compliance and legal disclosures.

### Horizon 3: Agentic Scale & Async Workflows
- **Asynchronous FastMCP 2.0 Batch Streaming (`credence://jobs/...`)**:
  - `credence_batch_audit_start` tool returning a unique `job_id`, streaming progressive progress and partial findings over SSE to avoid edge timeouts.
- **WebAssembly (Wasm) In-Browser Evaluator**:
  - Core structural heuristic rules compiled to lightweight WebAssembly for 100% client-side execution in Chrome Extensions and serverless web pages.
- **Clustered PostgreSQL & Valkey Cache Invalidation**:
  - Automated schema migration and multi-worker cache invalidation for large-scale enterprise deployments.

---

## 4. Known Edge Cases & Operational Mitigations

| Edge Case | Observed Behavior | Current Tactical Mitigation | Target Horizon Resolution |
| :--- | :--- | :--- | :--- |
| **Bot-Wall Interstitials** | Cloudflare Turnstile / Akamai serves challenge interstitials to headless scrapers. | Test gauntlet detects challenge DOM strings and skips semantic assertions. | **Horizon 1**: Authenticated session cookie & browser profile passthrough. |
| **Edge Batch Proxy Timeouts** | Synchronous 10+ URL batch audits approach Cloudflare Worker 30s execution ceiling. | FastMCP server enforces single-URL requests with sub-5s latency. | **Horizon 3**: Asynchronous FastMCP batch queue (`credence://jobs/{id}`). |
| **Non-Standard RSS Dates** | Niche feeds publish unconventional timestamps (epoch integers, missing timezone offsets). | 4-tier flexible date parser in `credence/feeds/parser.py`. | **Complete**: Verified across all syndicated feeds. |

---

## 5. Guiding Invariants for Roadmap Contributions

All future roadmap implementations must preserve:
1. **[Invariant 31: Zero-npm Standard](invariants.md#invariant-31)**: Never introduce Node.js or npm dependencies into public web portals.
2. **[Invariant 4: Hermetic Testing](invariants.md#invariant-4)**: Default test suites (`@pytest.mark.unit`) must execute purely in-memory in <35s.
3. **[Invariant 26: Universal Feature Parity](invariants.md#invariant-26)**: New features must be exposed symmetrically across CLI, FastMCP 2.0, Textual TUI, and Web UI.
