---
title: Universal Feature Parity Matrix
description: Synchronous capability matrix across CLI, FastMCP 2.0, Textual TUI, and
  Zero-Build Web portals.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Universal Feature Parity Matrix

In accordance with **[Invariant 24](invariants.md#invariant-24) (Universal Presentation Layer Feature Parity Invariant)**, Credence maintains synchronous feature parity across all four official interfaces:

1. **🖥️ CLI**: Rich terminal command-line interface (`credence <cmd>`).
2. **⚡ FastMCP 2.0 Server**: Model Context Protocol tools, dynamic resources, and prompt templates (`credence serve`).
3. **📟 Textual TUI Workstation**: Interactive live terminal dashboard (`credence tui`).
4. **🌐 Zero-Build Web UI**: Client-side Web Cryptography portals (`credence.run`, `credence.report`, `credence.foundation`, `credence.nexus`).

---

## 🏛️ Interface Architecture

```mermaid
graph TD
    Core["Credence Core Epistemic Engine<br>(Dual-Capture, Grounding Gate, Scoring Math, Ed25519)"]
    
    Core --> CLI["🖥️ CLI Interface<br>credence audit / feed / sifter / digest"]
    Core --> MCP["⚡ FastMCP 2.0 Server<br>stdio & SSE Streaming for AI Agents"]
    Core --> TUI["📟 Textual TUI Workstation<br>Full-Screen Terminal Workspace"]
    Core --> Web["🌐 Zero-Build Web Suite<br>credence.run / .report / Extension"]
```

---

## 1. Interface Capability Matrix

| Feature Area | 🖥️ CLI Command | ⚡ FastMCP 2.0 Endpoint | 📟 Textual TUI View | 🌐 Zero-Build Web Portal | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Audit Webpage (Live DOM)** | `credence audit <url>` | Tool: `credence_check_url` | `/` Shortcut Dialog | `credence.run` Form | **Full Parity** |
| **Direct Text Evaluation** | `credence audit` | Tool: `credence_evaluate_text` | Live Inspector View | `credence.report` Form | **Full Parity** |
| **Attestation Lookup** | `credence lookup <hash>` | Tool: `credence_get_audit` | Recent Table | `credence.report/viewer.html` | **Full Parity** |
| **Human Report Viewer** | `credence report view --open` | Resource: `credence://reports/{id}/human` | Tab 1: 🛡️ Inspector Dual-Pane | `credence.report/viewer.html` (In-Context) | **Full Parity** |
| **Dynamic Feed Discovery** | `credence feed discover <url>` | Tool: `credence_discover_feeds` | Feed Autodiscovery Bar | Feed Discovery Widget | **Full Parity** |
| **Pre-Flight Feed Inspection** | `credence feed inspect <url>` | Tool: `credence_inspect_feed_health` | 1-Click Inspect Modal | Interactive Pre-Flight Modal | **Full Parity** |
| **Dynamic Quality Scoring ($F_j$)**| `credence feed health` | Resource: `credence://feeds/status` | Tab 4: `📡 Feeds & Dedup` | Feed Status Dashboard | **Full Parity** |
| **Real-Time Sifter Daemon** | `credence sifter` | FastMCP Sifter Task | Sifter Status Indicator | Web Status Indicator | **Full Parity** |
| **Morning Epistemic Digest** | `credence digest` | Resource: `credence://digest/morning` | Tab 7: `🌅 Morning Digest` | Morning Briefing Card | **Full Parity** |
| **Token Headroom Governor** | `credence quota` | Tool: `credence_get_quota_status` | Tab 5: `⚡ Quota` | Status Badge at `credence.run` | **Full Parity** |
| **Cost Profiles** | `credence profile list` | Resource: `credence://profiles` | Profile Badge `[FREE/BALANCED]` | Cost Tier Grid | **Full Parity** |
| **Taxonomy Governance** | `credence taxonomy list` | Resource: `credence://taxonomies` | Tab 2: `📚 Taxonomies` | `taxonomies.credence.foundation` | **Full Parity** |
| **Cryptographic Identity** | `credence identity show` | Resource: `credence://node/identity` | Tab 6: `🔑 Node Identity` | `keys.credence.foundation` | **Full Parity** |
| **Attestation Verification** | `credence verify-file` | Tool: `credence_verify_attestation` | Row Selection Auto-Verify | W3C WebCrypto API | **Full Parity** |
| **Consensus Aggregation** | Consensus Engine | Tool: `credence_get_consensus` | Consolidated Verdict Panel | Consensus Badge | **Full Parity** |
| **P2P Mesh Seeds & Ranking** | `credence seeds`, `rank` | Resource: `credence://mesh/seeds` | Peer Status Indicators | `seeds.credence.nexus/peers.json` | **Full Parity** |
| **Hierarchical Subjects** | `credence subjects list` | Resource: `credence://subjects/registry`| Tab 3: `🧠 Domain Subjects` | Subject Explorer | **Full Parity** |
| **Epistemic Leaderboards** | `credence leaderboard` | Tool: `credence_get_leaderboard`<br/>Resource: `credence://leaderboard/{cat}` | Tab 8: `🏆 Leaderboard` | `credence.nexus` Leaderboards | **Full Parity** |
| **Sovereign Node Merit** | `credence merit` | Tool: `credence_get_node_merit`<br/>Resource: `credence://node/merit` | Tab 8: Split Merit Card | `credence.nexus` Merit Card | **Full Parity** |
| **Live Vector SVG Badges** | `credence badge export` | Endpoint: `/api/badge/{id}`<br/>Resource: `credence://merit/badges` | Badge Showcase Panel | `credence.nexus` Badge Embedder | **Full Parity** |
| **Domain Epistemic Index (DEI)** | `credence rankings` | Tool: `credence_get_domain_rankings`<br/>Resource: `credence://rankings/domains/{cat}`| DEI Honor Roll Table | `credence.report` Honor Roll / Shame | **Full Parity** |
| **Top Violated Rules** | `credence rankings --type rules` | Tool: `credence_get_taxonomy_analytics`<br/>Resource: `credence://rankings/rules`| Rules Breakdown View | `credence.report` Rules Aggregator | **Full Parity** |
| **Epistemic Weather Barometer** | `credence rankings --type weather` | Tool: `credence_get_epistemic_weather`<br/>Resource: `credence://weather/global` | Global Climate Widget | `credence.report` Weather Barometer | **Full Parity** |
| **Community Bounties** | `credence bounties` | Tool: `credence_get_bounties`<br/>Resource: `credence://bounties` | Open Quests List | `credence.nexus` Bounties Board | **Full Parity** |
| **White-Label Org Generator** | `credence init-org` | *Intentionally CLI-Only* | *Intentionally CLI-Only* | *Intentionally CLI-Only* | OS Scaffolding |
| **P2P Relay Daemon** | `credence mesh` | *Intentionally CLI-Only* | *Intentionally CLI-Only* | *Intentionally CLI-Only* | OS Daemon |

---

## 2. 4-Way Presentation Layer Showcase

See how the same epistemic audit report is presented across all four surfaces:

:::tabs
=== 📟 Textual TUI Workstation
![TUI Inspector](assets/tui/01-inspector-rich.svg)
*Full-screen terminal workstation with split-pane finding navigation, live filtering (`f`), and in-context evidence.*

=== 🌐 Zero-Build Web UI
Navigate to **`credence.report`** for a zero-build client-side cryptographic viewer featuring responsive dark mode, trust dimension breakdowns, and W3C WebCrypto Ed25519 signature validation.

=== 🖥️ Rich CLI
```bash
$ credence audit https://arstechnica.com/science/2026/08/fusion-breakthrough
🛡️ Credence Audit Report
├─ Verdict: FACTUAL_REPORTING (Score: 8.5 / 100.0)
├─ Density: 0.0 violations / 1k words  |  Confidence: 98%
├─ Content SHA-256: 1a2b3c4d5e6f7a8b...
└─ Attestation: ✓ Signed (Ed25519: 7a4c9f...)
```

=== ⚡ FastMCP 2.0 JSON-LD
```json
{
  "url": "https://arstechnica.com/science/2026/08/fusion-breakthrough",
  "content_sha256": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
  "suspicion_score": 8.5,
  "suspicion_density": 0.0,
  "confidence_score": 0.98,
  "classification": "FACTUAL_REPORTING",
  "is_satire": false,
  "node_signature": "ed25519:sig:clean123456789",
  "violations": []
}
```
:::
