# Universal Interface Feature Parity Matrix & Architecture Reference

This document defines the interface capability matrix across all four official presentation layers in Credence:
1. **CLI**: Rich terminal command-line interface (`credence <cmd>`).
2. **FastMCP 2.0 Server**: Model Context Protocol tools, dynamic resources, and prompt templates (`credence serve`).
3. **Textual TUI Workstation**: Interactive live terminal dashboard (`credence tui`).
4. **Zero-Build Web UI**: Client-side Web Cryptography portals (`credence.run`, `credence.report`, `credence.foundation`, `credence.nexus`).

---

## 1. Feature Parity Matrix

| Feature Area | CLI Command | FastMCP 2.0 Endpoint | Textual TUI View / Action | Zero-Build Web Portal | Parity & Architectural Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Audit Webpage (Live DOM)** | `credence audit <url> [--force] [--profile <p>]` | Tool: `credence_check_url(url, force_refresh, profile)` | Shortcut: `/` (Opens Audit Dialog) | Form input at `credence.run` | **Full Parity**. In Web UI, live browser scraping is routed via edge serverless API (`mcp.credence.run`) to comply with browser CORS and sandbox constraints. |
| **Direct Text Evaluation** | `credence audit` / script | Tool: `credence_evaluate_text(text, title, profile)` | Live Inspector View | Evaluation form at `credence.report` | **Full Parity**. Evaluates raw text without network requests. |
| **Attestation Lookup** | `credence lookup <url_or_hash>` | Tool: `credence_get_audit(identifier)` | Left Sidebar Recent List (`history_table`) | Search bar at `credence.report/viewer.html` | **Full Parity**. Queries local cache and snapshot records. |
| **Token Headroom Governor** | `credence quota` | Tool: `credence_get_quota_status()` | Tab 5: `⚡ Token Quota` | Status badge at `credence.run` | **Full Parity**. Real-time spend %, token usage, and circuit breaker status. |
| **Operational Cost Profiles** | `credence profile [list\|show <p>]` | Resource: `credence://profiles` | Active Profile Subtitle Badge `[FREE/BALANCED/ULTRA]` | Cost Tier Grid at `credence.run` | **Full Parity**. Free ($0.00 ceiling), Balanced ($0.50/day), Ultra ($15.00/mo deep reasoning). |
| **Taxonomy Governance** | `credence taxonomy [list\|show <id>]` | Resource: `credence://taxonomies`, `credence://taxonomies/{id}` | Tab 2: `📚 Taxonomies` | Catalog explorer at `taxonomies.credence.foundation` | **Full Parity**. SPJ ethics, IEP fallacies, and deceptive design rules. |
| **Cryptographic Identity** | `credence identity [show\|generate]` | Resource: `credence://node/identity` | Tab 6: `🔑 Node Identity` | Key download at `keys.credence.foundation/root.pub` | **Full Parity**. Ed25519 public/private keypair management. |
| **Attestation Verification** | `credence verify-file <path.json>` | Tool: `credence_verify_attestation(json)` | Automated verification on row selection | Native Web Crypto (`window.crypto.subtle`) at `credence.report/viewer.html` | **Full Parity**. 100% cryptographic signature validity under RFC 8785 canonical bytes. |
| **Consensus Aggregation** | Consensus Engine | Tool: `credence_get_consensus(hash, subject_id)` | Inspector Consolidated Verdict Panel | Consensus badge at `credence.report` | **Full Parity**. Bayesian agreement, outlier rejection, and subject-weighted scoring. |
| **P2P Mesh Seeds & Ranking** | `credence seeds`, `credence rank` | Tool: `credence_get_seed_nodes()`, Resource: `credence://mesh/seeds` | Peer status indicators | Verified manifest at `seeds.credence.nexus/peers.json` | **Full Parity**. 5-factor quality equation ($Q_i$) and active seed discovery. |
| **Syndicated Feed Ingestion** | `credence feeds [list\|add\|remove\|sync\|stats]` | Tools: `credence_sync_feeds`, `credence_add_feed_subscription`, `credence_list_feeds`, `credence_remove_feed_subscription`, `credence_get_feed_stats`, Resource: `credence://feeds/status` | Tab 4: `📡 Feeds & Dedup` + `s` sync keybinding | Feed status ticker at `credence.run` | **Full Parity**. RSS/Atom/JSON feeds with HTTP `ETag`/`304` conditional requests and zero-token mesh adoption. |
| **Hierarchical Subject Registry** | `credence subjects [list\|show <id>]` | Resources: `credence://subjects/registry`, `credence://subjects/{id}`, `credence://subjects/leaderboard` | Tab 3: `🧠 Domain Subjects` | Subject explorer at `credence.foundation` | **Full Parity**. Empirical domain expertise ($E_i$), subject-weighted authority ($W_i$), and hallucination slashing. |
| **White-Label Org Generator** | `credence init-org -n <name> -d <domain>` | *Intentionally CLI-Only* | *Intentionally CLI-Only* | *Intentionally CLI-Only* | **Design Choice**: Scaffolding directories, generating `.env` secrets, and writing Terraform files requires local OS filesystem and shell privileges. |
| **P2P Relay Daemon** | `credence mesh --port <port> --seeds <urls>` | *Intentionally CLI-Only* | *Intentionally CLI-Only* | *Intentionally CLI-Only* | **Design Choice**: Hosting a long-running WebSocket relay socket is a background operating system daemon process. |

---

## 2. Invariant 24 Enforcement

In accordance with **Invariant 24 (Universal Presentation Layer Feature Parity Invariant)**:
- Whenever a new epistemic evaluation, governance, or mesh coordination capability is designed, corresponding tools and resources MUST be added simultaneously across CLI, FastMCP 2.0, Textual TUI, and Zero-Build Web frontends.
- Any discrepancy must be explicitly justified (e.g. filesystem initialization tools like `init-org` or background daemon listeners like `credence mesh` are inherently CLI-scoped).
