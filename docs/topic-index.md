---
title: Topic Index & Quick Reference
description: Comprehensive concept index, cheat sheet, and fast-lookup directory for
  the Credence ecosystem.
since_version: v1.11.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# 🧭 Topic Index & Quick Reference

> **"Finding the Marble in the Oatmeal"**: This directory provides a direct, categorized index to every major command, configuration setting, AI integration, cost profile, ethical taxonomy, and mathematical proof across Credence.

---

## ⚡ Quick Jump Navigation

| Category | Key Topics Covered |
| :--- | :--- |
| [🎮 Interactive Zero-Build Playgrounds](playground.md) | 12 in-browser simulators: 13-node mesh, SimHash, Token Governor, Forensics |
| [🚀 Getting Started & Setup](#1-getting-started-setup) | One-line install, Docker, API keys, first audit, node germination |
| [💻 CLI & Workstation Reference](#2-cli-commands-workstation-reference) | `audit`, `tui`, `digest`, `sifter`, `serve`, `quota`, `rank` |
| [🤖 AI Agents & FastMCP 2.0](#3-ai-agents-fastmcp-20-integrations) | Claude Desktop, Cursor, Antigravity SDK, LangGraph epistemic brake |
| [💰 Cost, Tokens & Gemini Profiles](#4-cost-profiles-token-economics) | `FREE`, `BALANCED`, `ULTRA`, 30% Headroom circuit breaker |
| [📜 Ethics & Taxonomy Catalogs](#5-ethics-logic-taxonomy-catalogs) | SPJ Ethics, IEP Fallacies, Deceptive Patterns, Custom YAML rules |
| [🎭 Satire & Disinformation Defense](#6-satire-parody-disinformation-defense) | Poe's Law, satire neutralization, `SPJ-1.6` cloaking override |
| [🕸️ P2P Mesh Network & Consensus](#7-p2p-mesh-network-consensus) | 3-node quickstart, 13-node chaos lab, seed nodes, DNS SRV |
| [📐 Mathematical Proofs & Theory](#8-mathematical-foundations-proofs) | Weighted medians, Galileo Rule proof, SimHash-64, BitTorrent model |
| [☁️ Self-Hosting & Operations](#9-self-hosting-operations) | Raspberry Pi, GCP Cloud Run, Tailscale, SQLite WAL maintenance |
| [🏛️ The Invariant Bible](#the-invariant-bible) | Complete living canon of architectural, epistemic, and security rules |
| [🌐 External Standards & Specifications](#11-external-standards-authoritative-specifications) | IETF RFCs, W3C WebCrypto, Model Context Protocol, SPJ Ethics |

---

## 🚀 1. Getting Started & Setup

* **🎮 Interactive Playgrounds**: Test 12 in-browser models and the InMaricopa forensics workbench &rarr; [Interactive Playgrounds](playground.md)
* **One-Liner Install (POSIX)**: Run `curl -fsSL https://credence.run/install.sh | bash` &rarr; [Quickstart Guide](quickstart.md#1-installation-options)
* **Git & Poetry Setup**: Clone and setup via `poetry install` &rarr; [Quickstart Guide](quickstart.md#1-installation-options)
* **Docker Container**: Pre-built container with Chromium &rarr; [Quickstart Guide](quickstart.md#1-installation-options)
* **API Key Setup**: Setting `CREDENCE_GEMINI_API_KEY` in your shell &rarr; [API Configuration](quickstart.md#2-api-key-configuration-optional)
* **Zero-Cost / Offline Mode**: Running audits with 0 API spend &rarr; [Token Governor](protocols/token-governor.md)
* **Node Germination ("Miracle-Gro" Bootstrap)**: Instant key generation, seed inoculation, and initial burst &rarr; [Node Germination Protocol](protocols/node-germination-lifecycle.md)
* **First Web Audit**: Running your very first URL audit in under 5 seconds &rarr; [Auditing Webpages & Text](walkthroughs/01-auditing-webpages-and-text.md)
* **Zero-Build Web UI**: Browsing reports in the vanilla HTML5 web app &rarr; [Zero-Build Web Architecture](frontend-architecture.md)
* **Community Outreach & Reddit Templates**: Ready-to-use hooks and article distribution matrix &rarr; [Community Templates](social-launch-templates.md)

---

## 💻 2. CLI Commands & Workstation Reference

| Command | Action | Deep Guide |
| :--- | :--- | :--- |
| `credence audit <url>` | Live forensic evaluation of a webpage | [Auditing Webpages & Text](walkthroughs/01-auditing-webpages-and-text.md) |
| `credence audit <url> --profile free` | Low-latency zero-cost heuristic audit | [Operational Cost Profiles](protocols/token-governor.md) |
| `credence tui` | Launch full-screen interactive terminal workstation | [Textual TUI Workstation](integrations/tui-workstation.md) |
| `credence digest --format terminal` | Print 24-hour morning epistemic briefing | [Morning Digest Briefings](walkthroughs/04-morning-digest-briefings.md) |
| `credence sifter --interval 300` | Run autonomous background RSS feed filter | [Zero-Trust Feed Sifting](walkthroughs/02-zero-trust-feed-sifting.md) |
| `credence serve --mcp` | Start FastMCP 2.0 server on `stdio` | [Claude & Cursor Integration](tutorials/03-claude-cursor-fastmcp.md) |
| `credence serve --transport sse` | Start FastMCP 2.0 streaming HTTP/SSE server | [FastMCP 2.0 Protocol](protocols/fastmcp.md) |
| `credence quota` | Inspect current token usage and headroom safety | [Token Governor Protocol](protocols/token-governor.md) |
| `credence stats` | Real-time node health, SRE vitals, and mesh telemetry | [Node & Mesh Telemetry Blueprint](blueprints/node-and-mesh-telemetry-dashboard.md) |
| `credence rank` | View local and peer P2P node quality leaderboard ($Q_i$) | [Epistemic Merit & Leaderboards](protocols/epistemic-merit-and-leaderboards.md) |
| `credence rankings inmaricopa.com` | View publisher DEI score, trust band, and forensic sourcing ratios | [Conflict of Pun-terest](../blog/conflict-of-pun-terest.md) |
| `credence export-analytics <domain>` | Export machine-readable publisher analytics JSON/CSV | [Conflict of Pun-terest](../blog/conflict-of-pun-terest.md) |
| `credence benchmark` | Run the Golden 12 cross-profile evaluation suite | [Golden 12 Benchmark Suite](protocols/benchmark-suite.md) |
| `credence germinate` | Autonomous node ignition and genesis inoculation | [Tutorial 11: Swarm Ignition](tutorials/11-autonomous-node-germination-and-swarm-ignition.md) |

---

## 🤖 3. AI Agents & FastMCP 2.0 Integrations

* **Claude Desktop Setup**: Adding Credence to `claude_desktop_config.json` &rarr; [Claude & Cursor FastMCP Guide](tutorials/03-claude-cursor-fastmcp.md)
* **Cursor Editor Setup**: Configuring MCP tools in Cursor settings &rarr; [Claude & Cursor FastMCP Guide](tutorials/03-claude-cursor-fastmcp.md)
* **Antigravity SDK Pair-Programming**: Multi-agent coding patterns and invariant checks &rarr; [Antigravity Pair-Programming](agentic/01-antigravity-pair-programming-paradigm.md)
* **Agentic Epistemic Brake**: Halting LangGraph / CrewAI hallucination cascades before tool execution &rarr; [Epistemic Brake Cookbook](cookbooks/agentic-epistemic-brake.md)
* **FastMCP Tools Reference**: Complete specs for `credence_check_url`, `credence_evaluate_text`, `credence_get_audit`, etc. &rarr; [FastMCP 2.0 Protocol](protocols/fastmcp.md)
* **Universal Agent Interoperability**: Connecting Windsurf, Cline, and custom agent swarms &rarr; [Universal Agent Interop](portability/universal-agent-interop.md)
* **Multi-Model Adapters**: Using Claude 3.7 Sonnet, GPT-4o, DeepSeek-R1, and local Ollama &rarr; [Multi-Model Adapters](portability/multi-model-adapters.md)

---

## 💰 4. Cost Profiles & Token Economics

* **Profile Overview**: Compare latency, token limits, thinking tokens, and spend limits &rarr; [Cost Profiles Guide](protocols/token-governor.md)
* **`FREE` Profile ($0.00 / Zero Spend)**: Strict zero-cost offline heuristic auditing &rarr; [Token Governor](protocols/token-governor.md)
* **`BALANCED` Profile (Default)**: Gemini 3.7 Flash with 1,024–4,096 thinking tokens for daily news &rarr; [ADR: Why Gemini 3.7 Flash](portability/gemini-economic-rationale.md)
* **`ULTRA` Profile (Investigative)**: Deep reasoning with up to 16,384 thinking tokens for legal/financial filings &rarr; [Financial 10-K Cookbook](cookbooks/financial-disclosures.md)
* **30% Headroom Circuit Breaker**: Automatic offline fallback to prevent unexpected cloud API bills &rarr; [Token Safety Governor](protocols/token-governor.md)
* **BitTorrent Work-Sharing Economics**: How peer nodes share 92.3% of compute work at $0.00 token cost &rarr; [Economics of Truth](mathematics/economics-of-truth.md)

---

## 📜 5. Ethics, Logic & Taxonomy Catalogs

* **Society of Professional Journalists (SPJ) Ethics**: Rules on unnamed sources, unverified claims, conflict of interest &rarr; [Taxonomy Engineering 101](cookbooks/taxonomy-engineering.md)
* **Internet Encyclopedia of Philosophy (IEP) Fallacies**: Ad Hominem, Straw Man, False Dilemma, Circular Logic &rarr; [Taxonomy Engineering 101](cookbooks/taxonomy-engineering.md)
* **Deceptive UI Patterns Catalog**: Sneak into Basket, Confirmshaming, Hidden Costs, Forced Continuity &rarr; [Taxonomy Engineering 101](cookbooks/taxonomy-engineering.md)
* **Authoring Custom Taxonomies**: How to write namespaced YAML rule catalogs &rarr; [Taxonomy Engineering 101](cookbooks/taxonomy-engineering.md)
* **Medical & Health Claims Blueprint**: In vitro extrapolation, unproven miracle cures, clinical trials &rarr; [Health & Medical Claims Blueprint](blueprints/health-medical-claims.md)
* **Election & Civic Integrity Blueprint**: Polling methodology, voting locations, candidate claims &rarr; [Election Integrity Blueprint](blueprints/election-civic-integrity.md)
* **Synthetic AI & Deepfake Provenance**: C2PA metadata, pink slime news farms &rarr; [Synthetic Media Provenance](blueprints/synthetic-media-provenance.md)

---

## 🎭 6. Satire, Parody & Disinformation Defense

* **Poe's Law Principle**: Distinguishing parody (*The Onion*) from genuine disinformation &rarr; [Satire vs Disinformation Tutorial](tutorials/02-satire-vs-disinformation.md)
* **Satire Neutralization ($0.00 Score)**: Ensuring humor is tagged but not penalized &rarr; [Satire Cloaking Defense](security/satire-cloaking-defense.md)
* **`SPJ-1.6` Cloaking Override**: Disabling satire protections when bad-faith actors cloak defamatory factual claims as "humor" &rarr; [Satire Cloaking Defense](security/satire-cloaking-defense.md)
* **Verbatim Grounding ($G = 1.0$)**: Requiring exact character substring matches for all cited evidence &rarr; [Grounding Mechanics](security/grounding-mechanics.md)
* **50% Hallucination Slashing**: Autonomous reputation slashing for fabricated citations &rarr; [Grounding Mechanics](security/grounding-mechanics.md)
* **Indirect Prompt Injection Defense**: XML untrusted boundary encapsulation & Billion Laughs XML parser guards &rarr; [Adversarial Attack Surface](security/adversarial-attack-surface.md)

---

## 🕸️ 7. P2P Mesh Network & Consensus

* **3-Node Mesh Quickstart**: Run a local 3-node P2P mesh cluster &rarr; [3-Node Mesh Tutorial](tutorials/05-mesh-quickstart.md)
* **13-Node Chaos Lab**: Test Byzantine cartels ($f=4$) and network partition resilience &rarr; [13-Node Chaos Lab](tutorials/06-thirteen-node-chaos-lab.md)
* **Zero-Coordination Swarm Rendezvous Hashing**: Highest Random Weight (HRW) feed partitioning without central locks &rarr; [Swarm Rendezvous Hashing](mesh-engineering/rendezvous-hashing-feed-partitioning.md)
* **Zero-Touch Node Germination**: Autonomous cryptographic identity minting and genesis inoculation in <5s &rarr; [Zero-Touch Node Germination](protocols/zero-touch-germination-and-swarm-ignition.md)
* **P2P Gossip Protocol**: Watts-Strogatz small-world lattice ($N=13, k=4, \beta=0.10$) &rarr; [Mesh Protocol Spec](protocols/mesh-protocol.md)
* **Seed Node Governance**: Genesis bootstrap seeds (`seeds.credence.nexus`) and Ed25519 verification &rarr; [Bootstrap Seed Governance](bootstrap-seeds.md)
* **Dynamic DNS SRV Discovery**: Decentralized peer autodiscovery via RFC 2782 DNS records &rarr; [DNS SRV Discovery](mesh-engineering/dns-srv-discovery.md)
* **Air-Gapped Sneakernets**: Sharing signed `.credence.json` bundles over USB / offline networks &rarr; [Air-Gapped Truth Bundles](mesh-engineering/airgapped-sneakernets.md)
* **Sybil Cartel Demolition**: How robust weighted medians isolate coordinated malicious swarms &rarr; [Sybil Cartel Demolition](tutorials/08-sybil-cartel-demolition.md)

---

## 📐 8. Mathematical Foundations & Proofs

* **Domain Authority Weighted Medians**: Mathematical proofs for outlier rejection &rarr; [Robust Consensus Proofs](mathematics/robust-consensus-proofs.md)
* **The Galileo Rule**: Formal proof of why 100% grounded citations override ungrounded majorities &rarr; [Robust Consensus Proofs](mathematics/robust-consensus-proofs.md)
* **SimHash-64 & Mirror Detection**: 64-bit Hamming distance calculation for duplicate articles &rarr; [SimHash Mirror Detection](mathematics/simhash-mirror-detection.md)
* **Exponential Saturation Curves**: Suspicion score scaling math & density index &rarr; [Scoring Calibration Spec](protocols/scoring.md)
* **Topic Diversity Entropy ($H_{\text{topic}}$)**: Shannon entropy and top-token concentration against promotional astroturfing &rarr; [Feed Sifting Walkthrough](walkthroughs/02-zero-trust-feed-sifting.md)
* **Domain Epistemic Index ($DEI$) & Sourcing Forensics**: Longitudinal publisher scoring, byline ratios, and advertorial separation &rarr; [DEI & Sourcing Forensics](blueprints/domain-epistemic-index-and-sourcing-forensics.md)

---

## ☁️ 9. Self-Hosting & Operations

* **Master Deployment Prerequisites**: Complete checklists, credential matrices, and CLI setup guides across all topologies &rarr; [Master Deployment Prerequisites](operations/deployment-prerequisites.md)
* **Single-Project vs Dual-Project GCP**: Comparison and CLI runbooks for partitioned vs hard-isolated GCP topologies &rarr; [Single vs Dual-Project GCP](operations/single-vs-dual-project-gcp.md)
* **Multi-Environment Boundaries & Parity**: Project, domain, and data boundary isolation with launch parity &rarr; [Multi-Environment Boundaries](operations/multi-environment-boundaries-and-deployments.md)
* **Vendor-Agnostic Self-Hosting**: Bare-metal Linux, Hetzner/OVH VPS, systemd, and Caddy reverse proxy &rarr; [Vendor-Agnostic Self-Hosting](operations/vendor-agnostic-self-hosting-and-docker.md)
* **Docker Compose 5-Minute Quickstart**: Launch Basic ($0 SQLite) and Planetary (Postgres + MinIO + Valkey) clusters &rarr; [Docker Compose Quickstart](operations/docker-compose-quickstart.md)
* **Kubernetes & Container Orchestration**: Declarative Kubernetes manifests, PVC storage, ingress, and HPA &rarr; [Kubernetes & Helm Deployment](operations/kubernetes-and-helm-deployment.md)
* **Cloudflare R2 Blob Storage**: S3-compatible zero-egress CAS storage for forensic snapshots &rarr; [Cloudflare R2 Blob Storage](operations/blob-storage-r2.md)
* **Multi-Plane Pipeline & Build Optimization**: Sub-40s pre-commit QA gates, pytest-xdist parallelization, and build context exclusions &rarr; [Pipeline & Build Optimization Handbook](operations/pipeline-and-build-optimization.md)
* **The 3-Plane Sovereign Architecture**: Decoupling zero-npm Cloudflare edge, scale-to-zero Cloud Run compute, and Terraform infra &rarr; [The 3-Plane Architecture](../blog/the-three-plane-architecture.md)
* **CI/CD Acceleration Post-Mortem**: Slashing build context upload bloat from 860MB to 2MB &rarr; [From 860MB to 2MB](../blog/from-860mb-to-2mb-sub-40s-cicd-pipeline.md)
* **Raspberry Pi Homelab Node**: Low-power $0.00/mo self-hosting guide &rarr; [Raspberry Pi Homelab Guide](operations/raspberry-pi-homelab.md)
* **GCP Cloud Run Deployment**: Production Terraform templates with $15/mo budget cap and scale-to-zero &rarr; [GCP Cloud Run Deployment](deployment-cloudrun.md)
* **Cloud Run Cold Start Optimization Blueprint**: 5-pillar architectural framework for sub-2.5s scale-to-zero serverless cold starts &rarr; [Cloud Run Cold Start Blueprint](blueprints/cloudrun-scale-to-zero-cold-start-optimization.md)
* **Node & Mesh Telemetry Dashboard Blueprint**: Technical specification for real-time node operator observability and BitTorrent compute savings &rarr; [Node & Mesh Telemetry Blueprint](blueprints/node-and-mesh-telemetry-dashboard.md)
* **Real-Time Mesh Observability Essay**: First-person operator telemetry and decentralized swarm visibility without SaaS tracking &rarr; [Real-Time Mesh Observability](../blog/real-time-mesh-observability.md)
* **Taming the 10-Second Cold Start Essay**: Forensic teardown of Python serverless boot bottlenecks &rarr; [Taming the 10s Cold Start](../blog/taming-the-10-second-cold-start-scale-to-zero.md)
* **Tailscale & WireGuard Peering**: Encrypted private overlay mesh networks &rarr; [Tailscale Peering Guide](operations/tailscale-wireguard-mesh.md)
* **SQLite Database Maintenance**: WAL checkpoints, vacuuming, and 30-day token retention pruning &rarr; [Database Pruning & WAL Care](operations/database-pruning-wal.md)
* **Discord Webhook Alerts**: Setting up live notifications for high-suspicion breaking news &rarr; [Discord Alerting Guide](tutorials/13-discord-alerting-and-basement-monitoring.md)
* **White-Label Sovereign Federation**: Scaffolding private institutional mesh networks (`credence init-org`) &rarr; [White-Label Federation Protocol](protocols/white-label.md)

---

<a id="the-invariant-bible"></a>
## 🏛️ 10. The Invariant Bible: Living Canon of System-Wide Invariants & Protocols

For complete engineering invariants, safety constraints, and mathematical guarantees, see the master reference:

* 📘 **[The Invariant Bible: Living Canon of System-Wide Invariants & Protocols](invariants.md)**: The evolving, living canon of mathematical rules, runtime safety guardrails, cryptographic protocols, and presentation standards governing the entire Credence ecosystem.
* 🏛️ **[Invariant Scalability & Knowledge Governance Blueprint](blueprints/invariant-scalability-and-knowledge-governance.md)**: 3-tier governance architecture preventing prompt bloat and attention dilution.
* 📰 **[Scaling Invariants Without Prompt Bloat Essay](../blog/scaling-system-invariants-without-prompt-bloat.md)**: Engineering essay on shift-left automated test gates and progressive skills.

---

## 🌐 11. External Standards & Authoritative Specifications

| Standard / Protocol | Authority | Scope in Credence | Official Specification |
| :--- | :--- | :--- | :--- |
| **Model Context Protocol (MCP)** | Anthropic & Open Source | FastMCP 2.0 dual transport (`stdio` & SSE) | [modelcontextprotocol.io](https://modelcontextprotocol.io/) |
| **JSON Canonicalization (JCS)** | IETF (RFC 8785) | Deterministic cryptographic envelope hashing | [datatracker.ietf.org/doc/html/rfc8785](https://datatracker.ietf.org/doc/html/rfc8785) |
| **Ed25519 Cryptography** | IETF (RFC 8032) | Node identity custody & attestation signing | [datatracker.ietf.org/doc/html/rfc8032](https://datatracker.ietf.org/doc/html/rfc8032) |
| **DNS SRV Peer Discovery** | IETF (RFC 2782) | Decentralized mesh relay autodiscovery | [datatracker.ietf.org/doc/html/rfc2782](https://datatracker.ietf.org/doc/html/rfc2782) |
| **Web Cryptography API** | W3C Recommendation | Zero-npm in-browser attestation verification | [w3.org/TR/WebCryptoAPI](https://www.w3.org/TR/WebCryptoAPI/) |
| **SPJ Code of Ethics** | Society of Professional Journalists | Truth verification & conflict of interest rules | [spj.org/ethicscode.asp](https://www.spj.org/ethicscode.asp) |
| **ClaimReview Markup** | Schema.org | Structured fact-check search interoperability | [schema.org/ClaimReview](https://schema.org/ClaimReview) |
| **Google Cloud Run v2** | Google Cloud Platform | Serverless compute plane with scale-to-zero | [cloud.google.com/run](https://cloud.google.com/run/docs) |
| **Cloudflare Workers** | Cloudflare Edge | Zero-build multi-domain edge routing CDN | [developers.cloudflare.com/workers](https://developers.cloudflare.com/workers/) |

---

## 💬 Looking for Something Else?

* 🔍 Use the documentation search bar at the top of the sidebar (`/` or `Ctrl+K`) to search across all topics and keywords.
* 🎮 Try the **[12 Interactive Zero-Build Playgrounds](playground.md)** directly in your browser.
* 🔬 Inspect the **[Conflict of Pun-terest Forensic Case Study](../blog/conflict-of-pun-terest.md)** for live exurban monopoly auditing.
* 🐙 Open an issue or discussion on the **[Credence GitHub Repository](https://github.com/artibyrd/credence)**.


Press <kbd>/</kbd> or <kbd>Ctrl+K</kbd> anywhere in the documentation to activate the instant search engine, or jump to the [Introduction](intro.md) to explore the core philosophy.
