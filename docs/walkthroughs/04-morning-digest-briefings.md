---
title: 'Feature Walkthrough: Daily Morning Epistemic Briefings'
description: Multi-interface walkthrough for compiling executive intelligence briefings,
  newsletter exports, and FastMCP morning digest streams.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 4
---

# Feature Walkthrough: Daily Morning Epistemic Briefings

Learn how to aggregate 24-hour syndicated coverage into high-contrast executive briefings, filter verified journalism from rhetorical fallacies, and measure BitTorrent mesh compute savings across all interfaces.

```mermaid
flowchart LR
    Sifter["Continuous Sifter Daemon<br/>(60+ Articles Evaluated)"] --> Categorizer["Digest Sifter & Classifier"]
    Categorizer --> S1["🛡️ Verified Journalism (Score < 20.0)"]
    Categorizer --> S2["⚠️ Rhetorical Fallacies (Score 20-50)"]
    Categorizer --> S3["🚨 Deceptive Flags (Score >= 50.0)"]
    Categorizer --> S4["🎭 Validated Satire (Score 0.0)"]
    
    S1 & S2 & S3 & S4 --> Publisher["Multi-Interface Exporter<br/>(Terminal, Markdown, FastMCP, JSON)"]
```

> [!NOTE]
> **Persistent Interface Preference**: Switching tabs updates your active preference across all documentation pages in the portal.

---

## 1. Compiling 24-Hour Epistemic Briefings

Generate the daily executive morning briefing across verified journalism, fallacy warnings, and satire alerts.

:::tabs
=== Terminal High-Contrast
```bash
# Render high-contrast colored executive briefing directly in terminal
credence digest --format terminal
```

```
╭─────────────────── 🌅 Credence Morning Epistemic Briefing ───────────────────╮
│ Total Articles Sifted: 61  |  Clean Verified: 49  |  Flagged Deceptions: 11  │
│ |  Satire Cues: 1                                                            │
│ Swarm Mesh Compute Savings: 32,000 tokens ($0.01) across 10 zero-token       │
│ adoptions.                                                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

=== FastMCP Resource (Claude / Cursor)
Query the live 24-hour morning briefing directly over MCP:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_generate_digest",
    "arguments": { "hours": 24 }
  }
}
```

Or subscribe to the live dynamic resource at `credence://digest/morning`.

=== Markdown Newsletter Export
```bash
# Export formatted Markdown report for static sites or newsletters
credence digest --format markdown --output morning_brief.md --hours 24
```

=== JSON API Stream
```bash
# Export structured JSON for database ingestion or webhook alerts
credence digest --format json --output /var/log/credence/digest.json
```

=== 📟 Textual TUI Workstation
1. Launch `credence tui`.
2. Navigate to the **🌅 Morning Digest** pane (or Tab 5).
3. Review the live 24-hour briefing breakdown:
   - Total articles evaluated & clean verified coverage.
   - Flagged deceptions with violation rule IDs and severity scores.
   - Swarm mesh compute savings ($0.00 zero-token adoptions).

![Credence TUI Morning Digest](../../assets/tui/08-morning-digest.svg)
:::

---

## 2. Inspecting Swarm Compute Savings

Measure the empirical compute savings achieved by adopting signed attestations from peer nodes.

:::tabs
=== CLI Digest
```bash
# Display compute savings breakdown
credence digest stats
```

=== FastMCP Tools
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_get_quota_status",
    "arguments": {}
  }
}
```

=== Python SDK
```python
from credence.feeds.digest import calculate_digest_savings

stats = await calculate_digest_savings(hours=24)
print(f"Total Sifted: {stats.total_articles}")
print(f"Tokens Saved: {stats.tokens_saved}")
print(f"Mesh Savings %: {stats.savings_percentage}%")
```

=== 📟 Textual TUI Workstation
1. In `credence tui`, press `5` to open the **⚡ Token Quota** pane.
2. Monitor your hourly and daily token headroom budgets in real time.
3. Verify that the **Circuit Breaker Status** remains `🟢 HEALTHY (Normal Concurrency)` and review 24h estimated spend.

![Credence TUI Token Quota](../../assets/tui/09-token-quota.svg)
:::

---

## 3. Executive Intelligence Section Breakdown

| Section | Inclusion Criteria | Key Metadata Displayed |
| :--- | :--- | :--- |
| **🛡️ Verified Journalism** | Suspicion $< 20.0$, $G = 1.00$, diverse sources | Publisher identity, character offset, topic entropy |
| **⚠️ Rhetorical Warnings** | Suspicion $20.0 - 50.0$, informal fallacies | Rule URI (`IEP:INFORMAL/...`), verbatim quote |
| **🚨 Flagged Deceptions** | Suspicion $\ge 50.0$, corporate astroturfing | Violation severity (1–5), dark pattern classifier |
| **🎭 Validated Satire** | Suspicion $= 0.00$, Poe's Law cues matched | Schema.org badge, satire indicator, neutral verdict |
| **⚡ Swarm Compute Savings** | Zero-token adoptions across 13-node cluster | Total LLM tokens avoided, $0.00 cost multiplier |

> [!TIP]
> Run `credence digest --hours 12` in a cron job at 06:00 UTC to automate your morning briefing dispatch via email or webhooks.
