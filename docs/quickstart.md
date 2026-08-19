---
title: "Quickstart & Installation"
description: "Get started with Credence CLI, FastMCP 2.0 server, and Textual TUI in under 60 seconds."
---

# Quickstart & Installation ⚡

Get started with the Credence CLI, AI Assistant integration (FastMCP 2.0), and Textual TUI workstation in under a minute.

---

## 🚀 3-Step Quickstart

:::tabs
=== 1. Install
Install Credence via the automated installer, Poetry, or Docker:
```bash
# Automated installer (Linux & macOS)
curl -fsSL https://credence.run/install.sh | bash
```

=== 2. Audit
Run your first live audit on any URL or news article:
```bash
# Audit a live article
credence audit https://example.com/news-story
```

=== 3. Interface
Choose how you want to interact with Credence:
```bash
# Terminal Dashboard (TUI) | FastMCP (Claude/Cursor) | Daily Digest
credence tui
```
:::

---

## 1. Installation Options

:::tabs
=== POSIX One-Liner (macOS & Linux)
```bash
curl -fsSL https://credence.run/install.sh | bash
```

=== Git Clone & Poetry
```bash
git clone https://github.com/artibyrd/credence.git
cd credence
poetry install
```

=== Docker Container
```bash
docker run -d -p 8000:8000 ghcr.io/artibyrd/credence:latest
```
:::

---

## 2. API Key Configuration (Optional)

Credence uses **Gemini 3.7 Flash** by default for deep multi-agent evaluation. Set your API key in your shell environment:

```bash
export CREDENCE_GEMINI_API_KEY="your-gemini-api-key"
```

> 💡 **Zero-Cost / Offline Heuristics**: If no API key is provided, Credence automatically runs in **100% offline heuristic mode** ($0.00 spend) using structural rules.

---

## 3. Running Your First Audit

Audit any webpage directly from your command line:

```bash
# Default audit with Balanced profile (Gemini 3.7 Flash thinking model)
credence audit https://example.com/news-story

# Fast zero-cost audit (0 API tokens, 100% offline heuristics)
credence audit https://example.com/news-story --profile free

# Deep investigative audit (for complex legal, financial, or technical claims)
credence audit https://example.com/news-story --profile ultra
```

### Example Terminal Output

```text
🛡️ Credence Audit: https://example.com/breaking-news
Content SHA-256: 8f4e2b...
Classification: FACTUAL_REPORTING (is_satire: False)
Suspicion Score: 0.12 (Low Suspicion)
Violations Found: 1
  - [IEP:INFORMAL/straw_man@1.0.0] Severity: 2
    Quote: "Opponents believe that everyone should lose their jobs immediately."
    Grounding: Verified (Exact Verbatim Match)
Attestation Signed: Ed25519 (Node ID: e4d9...)
```

---

## 4. Launching the Interactive Terminal Dashboard (TUI)

Launch the full-screen terminal IDE to inspect live citation highlights, browse ethical taxonomies, and monitor token quotas:

```bash
credence tui
```

![Credence TUI Workstation](assets/tui/01-inspector-rich.svg)

* Press **`/`** to audit a new URL.
* Use **`j` / `k`** or **`↑` / `↓`** to navigate violations and view exact highlighted quotes.
* Press **`1`–`6`** to switch between Inspector, Taxonomies, Subjects, Feeds, Quota, and Identity panes.
* Press **`q`** to exit.

---

## 5. Connecting to Claude & Cursor (FastMCP 2.0)

Equip your AI coding assistant with real-time fact-checking and source verification tools:

### Claude Desktop Configuration

Add Credence to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "credence": {
      "command": "credence",
      "args": ["serve", "--mcp"],
      "env": {
        "CREDENCE_GEMINI_API_KEY": "your-gemini-api-key"
      }
    }
  }
}
```

### Cursor IDE Setup

In Cursor settings under **Features &rarr; MCP Servers**, add:
* **Name**: `credence`
* **Type**: `command`
* **Command**: `credence serve --mcp`

### FastMCP HTTP / SSE Streaming Server

For remote agents or network clients, launch the streaming SSE server:

```bash
credence serve --transport sse --port 8000
```
Connect via `http://localhost:8000/sse`.

---

## 6. Instant Node Germination (Bootstrap in 5s)

If you are setting up a full node, run `credence germinate` to mint cryptographic keys, inoculate Genesis seed data at $0.00 cost, and sow 24 preset feeds:

```bash
credence germinate
```

---

## 7. Running the Test Suite

Verify your installation by running the hermetic test suite:

```bash
just test
```
All 144 unit tests execute hermetically in under 60 seconds with zero external network access.

---

## 🧭 Next Steps & Related Marbles

* 🧭 **[Topic Index & Cheat Sheet](topic-index.md)**: Searchable reference covering all commands, settings, and flags.
* 📖 **[Auditing Webpages & Text Walkthrough](walkthroughs/01-auditing-webpages-and-text.md)**: In-depth guide to interpreting suspicion scores and violation categories.
* 📰 **[Morning Epistemic Digest](walkthroughs/04-morning-digest-briefings.md)**: Setting up automated daily 24-hour news briefings.
* 🤖 **[Claude & Cursor Integration Tutorial](tutorials/03-claude-cursor-fastmcp.md)**: Detailed multi-agent setup patterns.
