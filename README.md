# Credence: Epistemic Trust Engine & Verification Mesh

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![FastMCP 2.0](https://img.shields.io/badge/FastMCP-2.0-cyan.svg)](https://docs.credence.run#docs/protocols/fastmcp)

**Credence** is an open-source trust engine, FastMCP 2.0 server, and decentralized verification network. It audits web articles, news stories, and research claims for **clickbait, logical fallacies, and deceptive tactics** — backing every finding with **100% exact verbatim quotes from the original text** so there are zero AI hallucinations.

Every evaluation produces a cryptographically signed receipt (Ed25519) that can be verified by humans, queried by AI assistants (Claude, Cursor, Antigravity), or shared across a peer network at zero cost.

---

## ⚡ 60-Second Quickstart

Get started immediately with the CLI or Docker:

### 1. Install

```bash
# Automated install (Linux & macOS)
curl -fsSL https://credence.run/install.sh | bash

# Or clone and install with Poetry
git clone https://github.com/artibyrd/credence.git
cd credence
poetry install
```

*(Or run via Docker: `docker run -d -p 8000:8000 ghcr.io/artibyrd/credence:latest`)*

### 2. Configure API Key & Operator Security (Optional)

```bash
# Multi-agent reasoning (Gemini 3.7 Flash)
export CREDENCE_GEMINI_API_KEY="your-gemini-api-key"

# Bootstrap local operator admin key for web command deck (https://credence.nexus#admin)
just auth-bootstrap local
```

> 💡 **Zero-Cost / Offline Mode**: If no API key is provided, Credence runs in **100% offline heuristic mode** ($0.00 cost) using structural rules.

### 3. Run Your First Audit & Launch Workstation

```bash
# 1-Command ignite: setup, preflight, bootstrap admin key, germinate, and verify
just ignite

# Audit any URL directly from your terminal
credence audit https://example.com/news-story

# Launch the interactive full-screen terminal dashboard
credence tui

# Print a 24-hour morning epistemic news briefing
credence digest
```

---

## 🧭 Topic Index: Finding What You Need

> Looking for a specific setting, command, or concept? Check our comprehensive **[Topic Index & Cheat Sheet](docs/topic-index.md)** ("Finding the Marble in the Oatmeal"):

| Topic Category | Direct Jump Links |
| :--- | :--- |
| **🚀 Getting Started** | [POSIX Install](docs/quickstart.md#1-quick-installation) &bull; [Docker Setup](docs/quickstart.md#1-quick-installation) &bull; [API Key Config](docs/quickstart.md#2-api-key-configuration) &bull; [Node Germination](docs/protocols/node-germination-lifecycle.md) |
| **💻 CLI & Workstation** | [`audit`](docs/walkthroughs/01-auditing-webpages-and-text.md) &bull; [`tui`](docs/integrations/tui-workstation.md) &bull; [`digest`](docs/walkthroughs/04-morning-digest-briefings.md) &bull; [`sifter`](docs/walkthroughs/02-zero-trust-feed-sifting.md) &bull; [`quota`](docs/protocols/token-governor.md) &bull; [`rank`](docs/protocols/epistemic-merit-and-leaderboards.md) |
| **🤖 AI & FastMCP 2.0** | [Claude Desktop Config](docs/tutorials/03-claude-cursor-fastmcp.md) &bull; [Cursor Setup](docs/tutorials/03-claude-cursor-fastmcp.md) &bull; [Antigravity SDK](docs/agentic/01-antigravity-pair-programming-paradigm.md) &bull; [Epistemic Brake](docs/cookbooks/agentic-epistemic-brake.md) |
| **💰 Cost & Tokens** | [`FREE` ($0.00)](docs/protocols/token-governor.md) &bull; [`BALANCED` (Default)](docs/portability/gemini-economic-rationale.md) &bull; [`ULTRA` (Investigative)](docs/cookbooks/financial-disclosures.md) &bull; [Headroom Breaker](docs/protocols/token-governor.md) |
| **📜 Ethics & Taxonomies**| [SPJ Journalism Code](docs/cookbooks/taxonomy-engineering.md) &bull; [IEP Fallacies](docs/cookbooks/taxonomy-engineering.md) &bull; [Deceptive UI](docs/cookbooks/taxonomy-engineering.md) &bull; [Authoring YAML Rules](docs/cookbooks/taxonomy-engineering.md) |
| **🎭 Satire & Parody** | [Poe's Law](docs/tutorials/02-satire-vs-disinformation.md) &bull; [Satire Neutralization](docs/security/satire-cloaking-defense.md) &bull; [`SPJ-1.6` Cloaking Override](docs/security/satire-cloaking-defense.md) |
| **🕸️ P2P Mesh & Consensus**| [3-Node Quickstart](docs/tutorials/05-mesh-quickstart.md) &bull; [13-Node Chaos Lab](docs/tutorials/06-thirteen-node-chaos-lab.md) &bull; [Seed Nodes](docs/bootstrap-seeds.md) &bull; [DNS SRV Discovery](docs/mesh-engineering/dns-srv-discovery.md) |
| **📐 Mathematical Proofs**| [Weighted Medians Proof](docs/mathematics/robust-consensus-proofs.md) &bull; [The Galileo Rule](docs/mathematics/robust-consensus-proofs.md) &bull; [SimHash-64](docs/mathematics/simhash-mirror-detection.md) |
| **☁️ Operations & Hosting**| [Raspberry Pi Node](docs/operations/raspberry-pi-homelab.md) &bull; [Cloud Run ($15/mo Cap)](docs/deployment-cloudrun.md) &bull; [Tailscale Mesh](docs/operations/tailscale-wireguard-mesh.md) &bull; [WAL Maintenance](docs/operations/database-pruning-wal.md) |
| **🏛️ The Invariant Bible** | [Living Canon of System Invariants](docs/agent-invariants.md) |

---

## 🎯 4 Ways to Use Credence

Credence maintains 100% synchronous feature parity across 4 distinct interfaces:

### 1. 🖥️ Terminal Command Line (CLI)
Run fast audits, filter JSON streams with `jq`, and enforce quality gates in GitHub Actions:
```bash
credence audit https://arstechnica.com/tech-policy/...
credence audit https://example.com/claim --json | jq .suspicion_score
```

### 2. ⚡ AI Assistant Integration (FastMCP 2.0)
Give Claude Desktop, Cursor, and agent swarms real-time tools to evaluate claims:
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

Credence adapts to your budget with 3 preconfigured profiles:

| Profile | Primary Engine | Thinking Tokens | Cost per 1k Audits | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`FREE`** | Offline Heuristics | 0 tokens | **$0.00 (Zero Spend)** | Air-gapped CI/CD, hermetic pipelines |
| **`BALANCED`** *(Default)* | Gemini 3.7 Flash | 1,024 – 4,096 tokens | **$0.34 – $0.68** | Daily news, RSS sifting, developer workflows |
| **`ULTRA`** | Gemini 3.7 Flash + Pro | 8,192 – 16,384 tokens | **$1.10 – $2.20** | Deep investigative 10-K & legal filings |

> 🛡️ **Headroom Circuit Breaker**: If your daily token budget reaches 30% remaining headroom, Credence automatically switches to offline heuristic mode to guarantee zero surprise bills.

---

## 🛠️ Developer Task Runner (`Justfile`)

If you are developing or testing Credence, use the standard `just` commands:

```bash
# Verify developer dependencies
just preflight

# Run the hermetic test suite (144 tests, 100% offline)
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
- 📘 **[Topic Index & Cheat Sheet](docs/topic-index.md)**: Categorized fast lookup for all commands and concepts.
- 📘 **[The Invariant Bible](docs/agent-invariants.md)**: Living canon of architectural, mathematical, and security invariants.
- 📘 **[Adversarial Threat Model FAQ](docs/faq-adversarial-defense.md)**: Red team analysis, prompt injection defense, and SSRF guards.
- 📘 **[Mathematics of Robust Consensus](docs/mathematics/robust-consensus-proofs.md)**: Weighted medians and Galileo Rule proofs.
- 📘 **[Cloud Run Deployment Guide](docs/deployment-cloudrun.md)**: Terraform production setup with $15/mo budget cap.

---

## 📄 License

MIT License &copy; 2026 Credence Network Contributors.
