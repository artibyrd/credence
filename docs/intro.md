---
title: "Introduction & Overview"
description: "Welcome to Credence: the open epistemic trust engine for AI and the web."
---

# Welcome to Credence 🛡️

**Credence** is an open-source trust engine, FastMCP 2.0 server, and decentralized verification network. It audits web articles, news stories, and research claims for **clickbait, logical fallacies, and deceptive tactics** — backing every finding with **100% exact quotes from the original text** so there are zero AI hallucinations.

Instead of subjective "truthiness" scores or centralized arbiters, Credence provides **transparent, verifiable receipts** that anyone can inspect.

---

## 🎯 Choose Your Path

Where would you like to start?

| Your Goal | Recommended Starting Point | Time Needed |
| :--- | :--- | :--- |
| **🚀 Just jump in and try it** | [Quickstart & Installation Guide](quickstart.md) | **1 minute** |
| **🧭 Find a specific command or topic** | [Topic Index & Concept Directory](topic-index.md) | **Instant** |
| **🤖 Connect to Claude Desktop or Cursor** | [Claude & Cursor FastMCP Tutorial](tutorials/03-claude-cursor-fastmcp.md) | **2 minutes** |
| **📰 Get an automated morning news brief** | [Morning Digest Walkthrough](walkthroughs/04-morning-digest-briefings.md) | **3 minutes** |
| **🌐 Explore reports in your browser** | [Zero-Build Report Viewer](https://credence.report/viewer.html) | **Instant** |
| **🕸️ Explore P2P mesh & consensus math** | [3-Node Mesh Quickstart](tutorials/05-mesh-quickstart.md) | **5 minutes** |

---

## 💡 The 4 Pillars of Grounded Truth

Credence is built around four fundamental design principles:

### 1. 🔍 Verbatim Evidence (Zero Hallucinations)
Every flagged violation requires an exact, word-for-word quote from the original source text. If an AI model flags a claim but cannot quote the exact sentence from the page, the finding is discarded.

### 2. 📜 Established Ethical & Logical Standards
Audits are evaluated against established, public taxonomy catalogs:
* **SPJ Journalistic Ethics**: Unnamed sources, unverified allegations, conflicts of interest.
* **IEP Logical Fallacies**: Ad Hominem, Straw Man, False Dilemma, Circular Reasoning.
* **Deceptive UI Patterns**: Fake countdown urgency, confirmshaming, hidden costs.

### 3. 🎭 Smart Satire Awareness (Poe's Law)
Legitimate humor and parody (*The Onion, The Babylon Bee*) are recognized and scored neutrally ($0.00$), preventing false alarms while signaling downstream AI agents not to treat hyperbole as literal fact. However, bad-faith disinformation attempting to cloak defamatory allegations as "humor" is strictly intercepted.

### 4. 🔏 Tamper-Proof Cryptographic Receipts
Every evaluation produces an Ed25519-signed `.credence.json` envelope. Anyone can verify that the score and quoted evidence haven't been altered by any intermediary or relay node.

---

## 🏛️ How Credence Works

```mermaid
graph TD
    Target["Target Webpage, Prose Text, or RSS Feed"] --> Capture["1. Clean Capture<br>(HTML DOM & Prose Text)"]
    Capture --> Grounding["2. Verbatim Quote Validation<br>(Zero Hallucination Filter)"]
    Grounding --> Specialists["3. Multi-Rule Audit Engine<br>(Ethics, Fallacies, Deceptive Patterns)"]
    Specialists --> Signer["4. Cryptographic Envelope<br>(Ed25519 Signed Receipt)"]
    
    Signer --> Output1["🖥️ Terminal CLI<br>credence audit"]
    Signer --> Output2["⚡ FastMCP 2.0 Server<br>Claude, Cursor & Antigravity"]
    Signer --> Output3["📟 Textual TUI<br>credence tui"]
    Signer --> Output4["🌐 Web Report Viewer<br>credence.report"]
```

---

## 🖥️ The 4 Universal Interfaces

Credence maintains 100% synchronous feature parity across 4 distinct interfaces:

* **🖥️ Command Line (CLI)**: Fast forensic audits, structured JSON pipes for shell scripting (`jq`, `xargs`), and CI/CD PR gates.
* **⚡ FastMCP 2.0**: Equip Claude Desktop, Cursor, and agent swarms with tools over `stdio` and streaming `HTTP/SSE`.
* **📟 Textual TUI (`credence tui`)**: Full-screen keyboard-driven workstation with live citation highlighting and taxonomy explorer.
* **🌐 Zero-Build Web UI (`web/`)**: High-contrast browser report viewer with zero npm dependencies and client-side Web Crypto verification.

---

## 📚 Deep Dives & Advanced References

When you're ready to explore under the hood:

* 🧭 **[Topic Index & Concept Directory](topic-index.md)**: Searchable directory of all commands, settings, and invariants.
* 🎓 **[Hands-On Tutorials](tutorials/01-clickbait-teardown.md)**: Step-by-step forensic teardowns and chaos labs.
* 🏛️ **[36 Core System Invariants](agent-invariants.md)**: Master architectural, mathematical, and safety guarantees.
* 📐 **[Mathematics of Robust Consensus](mathematics/robust-consensus-proofs.md)**: Formal proofs for weighted medians and the Galileo Rule.
* ☁️ **[GCP Cloud Run Deployment](deployment-cloudrun.md)**: Production Terraform templates with $15/mo budget cap.
