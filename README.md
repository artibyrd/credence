# Credence: Epistemic Trust Engine & Verification Mesh

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![FastMCP 2.0](https://img.shields.io/badge/FastMCP-2.0-cyan.svg)](https://docs.credence.run/protocols/fastmcp)

**Credence** is an open-source trust engine, FastMCP 2.0 server, and decentralized verification network. It audits web articles, news stories, and research claims for **clickbait, logical fallacies, and deceptive tactics** — backing every finding with **100% exact verbatim quotes from the original text** so there are zero AI hallucinations.

Every evaluation produces a cryptographically signed receipt (Ed25519) that can be verified by humans, queried by AI assistants (Claude, Cursor, Antigravity), or shared across a peer network at zero cost.

---

## ⚡ The Credence Graduation Path

Get started with Credence at the layer that matches your needs:

| Tier | Role | Setup Time | Launch Command | Guide |
| :--- | :--- | :--- | :--- | :--- |
| **1. Consume** | FastMCP 2.0 Client | **< 60s** | `uvx --from git+https://github.com/artibyrd/credence credence serve --mcp` | [FastMCP Quickstart](https://docs.credence.run/quickstart-mcp) |
| **2. Contribute** | Volunteer Worker Daemon | **< 2m** | `uvx --from git+https://github.com/artibyrd/credence credence worker` | [Worker Quickstart](https://docs.credence.run/quickstart-worker) |
| **3. Host & Coordinate** | Sovereign Coordinator Node | **< 5m** | `curl -fsSL https://credence.run/install.sh \| bash` • `just ignite` | [Node Quickstart](https://docs.credence.run/quickstart-node) |

### 1. FastMCP 2.0 AI Assistant (<60s) — Connect Claude & Cursor
Give Claude Desktop, Cursor, or AI swarms the in-editor Epistemic Brake with zero infrastructure:
```json
{
  "mcpServers": {
    "credence": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/artibyrd/credence", "credence", "serve", "--mcp"]
    }
  }
}
```
*(Or connect directly to the public remote endpoints: `https://mcp.credence.run/sse` or Streamable HTTP `https://mcp.credence.run/mcp`)* • 📖 **[FastMCP Quickstart Guide](https://docs.credence.run/quickstart-mcp)**

### 2. Volunteer Worker Daemon (<2m) — Donate Compute to the Mempool
Not getting audits fast enough? Earn cryptographic merit badges and climb the public leaderboard using any supported model API or local open-weights server:
```bash
# Launch volunteer worker with zero permanent install via uvx
uvx --from git+https://github.com/artibyrd/credence credence worker --node https://credence.run --model google/gemini-3.8-flash

# Or run 100% offline with local Ollama ($0.00 spend)
uvx --from git+https://github.com/artibyrd/credence credence worker --node https://credence.run --model ollama/llama3.3:70b
```
📖 **[Volunteer Worker Quickstart Guide](https://docs.credence.run/quickstart-worker)**

### 3. Sovereign Node & Coordinator (<5m) — Full-Stack Hosting
Have a team running lots of audits? Host a sovereign coordinator node with local mempool and web Admin Deck:
```bash
# 1-Command ignite: setup, preflight, bootstrap admin key, germinate, and verify
curl -fsSL https://credence.run/install.sh | bash
just ignite
```
*(Or run via Docker: `docker run -d -p 8000:8000 ghcr.io/artibyrd/credence:latest`)* • 📖 **[Sovereign Node Quickstart Guide](https://docs.credence.run/quickstart-node)**

---

## 🧭 Topic Index: Finding What You Need

> Looking for a specific setting, command, or concept? Check our comprehensive **[Topic Index & Cheat Sheet](https://docs.credence.run/topic-index)** ("Finding the Marble in the Oatmeal"):

| Topic Category | Direct Jump Links |
| :--- | :--- |
| **🚀 Getting Started** | [Graduation Path](https://docs.credence.run/quickstart) • [FastMCP Quickstart](https://docs.credence.run/quickstart-mcp) • [Worker Quickstart](https://docs.credence.run/quickstart-worker) • [Node Quickstart](https://docs.credence.run/quickstart-node) • [Node Germination](https://docs.credence.run/protocols/node-germination-lifecycle) |
| **💻 CLI & Workstation** | [`audit`](https://docs.credence.run/walkthroughs/01-auditing-webpages-and-text) • [`tui`](https://docs.credence.run/integrations/tui-workstation) • [`digest`](https://docs.credence.run/walkthroughs/04-morning-digest-briefings) • [`sifter`](https://docs.credence.run/walkthroughs/02-zero-trust-feed-sifting) • [`quota`](https://docs.credence.run/protocols/token-governor) • [`rankings`](https://docs.credence.run/protocols/epistemic-merit-and-leaderboards) |
| **🤖 AI & FastMCP 2.0** | [Claude Desktop Config](https://docs.credence.run/tutorials/03-claude-cursor-fastmcp) • [Cursor Setup](https://docs.credence.run/tutorials/03-claude-cursor-fastmcp) • [Antigravity Customizations & Skill Overlays](https://docs.credence.run/agentic/08-antigravity-customizations-and-skill-overlays) • [Antigravity SDK](https://docs.credence.run/agentic/01-antigravity-pair-programming-paradigm) • [Epistemic Brake](https://docs.credence.run/cookbooks/agentic-epistemic-brake) |
| **💰 Cost & Tokens** | [`FREE` ($0.00)](https://docs.credence.run/protocols/token-governor) • [`BALANCED`](https://docs.credence.run/portability/gemini-economic-rationale) • [`ULTRA` (Investigative)](https://docs.credence.run/cookbooks/financial-disclosures) • [Headroom Breaker](https://docs.credence.run/protocols/token-governor) |
| **📜 Ethics & Taxonomies** | [SPJ Journalism Code](https://docs.credence.run/cookbooks/taxonomy-engineering) • [IEP Fallacies](https://docs.credence.run/cookbooks/taxonomy-engineering) • [Deceptive UI](https://docs.credence.run/cookbooks/taxonomy-engineering) • [Authoring YAML Rules](https://docs.credence.run/cookbooks/taxonomy-engineering) |
| **🎭 Satire & Parody** | [Poe's Law](https://docs.credence.run/tutorials/02-satire-vs-disinformation) • [Satire Neutralization](https://docs.credence.run/security/satire-cloaking-defense) • [`SPJ-1.6` Cloaking Override](https://docs.credence.run/security/satire-cloaking-defense) |
| **🕸️ P2P Mesh & Consensus** | [3-Node Quickstart](https://docs.credence.run/tutorials/05-mesh-quickstart) • [13-Node Chaos Lab](https://docs.credence.run/tutorials/06-thirteen-node-chaos-lab) • [Seed Nodes](https://docs.credence.run/bootstrap-seeds) • [DNS SRV Discovery](https://docs.credence.run/mesh-engineering/dns-srv-discovery) |
| **📐 Mathematical Proofs** | [Weighted Medians Proof](https://docs.credence.run/mathematics/robust-consensus-proofs) • [The Galileo Rule](https://docs.credence.run/mathematics/robust-consensus-proofs) • [SimHash-64](https://docs.credence.run/mathematics/simhash-mirror-detection) |
| **☁️ Operations & Hosting** | [Raspberry Pi Node](https://docs.credence.run/operations/raspberry-pi-homelab) • [Cloud Run ($15/mo Cap)](https://docs.credence.run/deployment-cloudrun) • [Tailscale Mesh](https://docs.credence.run/operations/tailscale-wireguard-mesh) • [WAL Maintenance](https://docs.credence.run/operations/database-pruning-wal) |
| **🏛️ The Invariant Bible** | [Living Canon of System Invariants](https://docs.credence.run/invariants) |

---

## 🎯 4 Ways to Use Credence

Credence maintains 100% synchronous feature parity across 4 distinct interfaces:

### 1. 🖥️ Terminal Command Line (CLI)
Run fast audits, filter JSON streams with `jq`, and enforce quality gates in GitHub Actions:
```bash
credence audit https://arstechnica.com/tech-policy/2026/08/ai-copyright-settlement
credence audit https://example.com/claim --format json | jq .suspicion_score
```

### 2. ⚡ AI Assistant Integration (FastMCP 2.0)
Give Claude Desktop, Cursor, and agent swarms real-time tools to evaluate claims over native `stdio`, SSE (`/sse`), or Streamable HTTP (`/mcp`), backed by a cache-first fastpath, 25-second hosted Epistemic Brake window, and cryptographically authenticated anchoring (`credence_verify_and_anchor`):
```json
{
  "mcpServers": {
    "credence": {
      "command": "credence",
      "args": ["serve", "--mcp"]
    }
  }
}
```

### 3. 📟 Interactive Terminal Workstation (Textual TUI)
Full-screen dashboard with keyboard navigation, live citation highlight inspector, taxonomy explorer, and token quota monitors:
```bash
credence tui
```

### 4. 🌐 Zero-Build Web Report Viewer
Open, inspect, and share high-contrast verification receipts directly in your browser with zero npm bundles:
- Public Report Viewer: [`https://credence.report/viewer.html`](https://credence.report/viewer.html)
- Main Hub: [`https://credence.run`](https://credence.run)

---

## 💡 How It Works: The 4 Core Principles

1. **Zero Hallucinations (Verbatim Grounding)**: Every single violation reported must cite an exact character-offset quote from the source text ($G=1.0$). If an AI cannot quote the exact sentence, the finding is discarded.
2. **Standardized Ethics & Logic Rules**: Content is audited against established, open taxonomies:
   - **SPJ Journalistic Ethics**: Unnamed sources, unverified allegations, conflicts of interest.
   - **IEP Logical Fallacies**: Ad Hominem, Straw Man, False Dilemma, Circular Reasoning.
   - **Deceptive Patterns**: Urgency countdowns, confirmshaming, hidden terms.
3. **Poe's Law & Satire Awareness**: Genuine satire (*The Onion*, *The Babylon Bee*) is recognized and scored neutrally ($0.00$), so humor isn't penalized, while cloaked disinformation is stopped.
4. **Cryptographic Proofs**: Evaluations are signed with an Ed25519 keypair into RFC 8785 canonical JSON. Anyone can verify that the audit hasn't been modified.

---

## 💰 Operational Cost Profiles

Credence adapts to your budget with preconfigured profiles (and supports any major LLM provider or local Ollama endpoint):

| Profile | Primary Engine | Thinking Tokens | Estimated Cost per 1k Audits | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`FREE`** | Zero-spend tier / Offline Heuristics | 0 tokens | **$0.00 (Zero Spend)** | Air-gapped CI/CD, hermetic pipelines |
| **`ECONOMY` / `BALANCED`** | Configured Cloud or Local LLM | 512 – 4,096 tokens | **$0.34 – $0.68** | Daily news, RSS sifting, developer workflows |
| **`ULTRA`** | High-reasoning LLM | 4,096 – 16,384 tokens | **$1.10 – $2.20** | Deep investigative 10-K & legal filings |

> 🛡️ **Headroom Circuit Breaker**: If your daily token budget reaches 30% remaining headroom, Credence automatically switches to offline heuristic mode to guarantee zero surprise bills.

---

## 🛠️ Developer Task Runner (`Justfile`)

If you are developing or testing Credence, use the standard `just` commands:

```bash
# Verify developer dependencies
just preflight

# Run the hermetic unit test suite (100% offline)
just test

# Format and check types
just lint
just format

# Run the Golden 12 benchmark suite
just benchmark

# Launch local 3-node mesh cluster
just mesh-cluster-up
```

---

## 📚 Complete Documentation & Deep References

- 📘 **[Documentation Portal](https://docs.credence.run)**: Interactive docs with zero npm build requirements.
- 📘 **[Topic Index & Cheat Sheet](https://docs.credence.run/topic-index)**: Categorized fast lookup for all commands and concepts.
- 📘 **[The Invariant Bible](https://docs.credence.run/invariants)**: Living canon of architectural, mathematical, and security invariants.
- 🧩 **[Antigravity Customizations & Skill Overlays](https://docs.credence.run/agentic/08-antigravity-customizations-and-skill-overlays)**: Optimized for Google Antigravity (`artibyrd/antigravity-customizations`), compatible with Claude Code, Cursor, and Codex via self-contained `.agents/overrides/`.
- 📘 **[Adversarial Threat Model FAQ](https://docs.credence.run/faq-adversarial-defense)**: Red team analysis, prompt injection defense, and SSRF guards.
- 📘 **[Mathematics of Robust Consensus](https://docs.credence.run/mathematics/robust-consensus-proofs)**: Weighted medians and Galileo Rule proofs.
- 📘 **[Cloud Run Deployment Guide](https://docs.credence.run/deployment-cloudrun)**: Terraform production setup with $15/mo budget cap.

---

## 📄 License

MIT License © 2026 Credence Network Contributors.
