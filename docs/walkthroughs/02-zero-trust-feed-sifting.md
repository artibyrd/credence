---
title: 'Feature Walkthrough: Zero-Trust Feed Autodiscovery & Sifting'
description: End-to-end multi-interface walkthrough for dynamic RSS/Atom autodiscovery,
  pre-flight forensic audits, and real-time sifting daemons.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 2
---

# Feature Walkthrough: Zero-Trust Feed Autodiscovery & Sifting

Learn how to dynamically discover syndicated feed endpoints, execute pre-flight forensic audits against covert astroturfing (The Pizza Hut Problem), and run real-time sifting workers across all interfaces.

```mermaid
flowchart TD
    Target["Target Web Domain"] --> Discover["Dynamic Autodiscovery<br/>(link tags & well-known paths)"]
    Discover --> PreFlight["Pre-Flight Forensic Audit"]
    PreFlight --> DynamicScore["Dynamic Quality Score (F_j)<br/>0.35 S + 0.25 G + 0.20 H + 0.20 T"]
    DynamicScore --> SifterDaemon["Continuous Sifter Daemon<br/>(Rendezvous Hash Partitioning)"]
    SifterDaemon --> MeshGossip["Gossip RFC 8785 Attestations<br/>(92.3% Compute Savings)"]
```

> [!NOTE]
> **Persistent Interface Preference**: Switch between **CLI**, **FastMCP 2.0**, **Python SDK**, or **TUI** below. Your choice is automatically remembered across all documentation pages.

---

## 1. Dynamic Feed Autodiscovery

Discover syndicated RSS, Atom, and JSON feed endpoints dynamically from any domain without maintaining hardcoded lists.

:::tabs
=== CLI
```bash
# Autodiscover feeds from tech, news, or scientific outlets
credence feed discover "https://arstechnica.com"
credence feed discover "https://apnews.com"
credence feed discover "https://www.nature.com"
```

=== FastMCP 2.0 (Claude / Cursor)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_discover_feeds",
    "arguments": {
      "target_url": "https://arstechnica.com"
    }
  }
}
```

=== Python SDK
```python
from credence.feeds.discovery import discover_feed_endpoints

feeds = await discover_feed_endpoints("https://arstechnica.com")
for f in feeds:
    print(f"Found: {f['title']} ({f['format']}) -> {f['url']}")
```

=== 📟 Textual TUI Workstation
1. Launch `credence tui`.
2. Press `4` to switch to the **📡 Feeds & Dedup** workstation pane.
3. Press `s` to execute live background feed synchronization and check mesh effort avoidance.
:::

---

## 2. Pre-Flight Forensic Audit & Topic Entropy Inspection

Audit a candidate feed's semantic topic entropy ($H_{\text{topic}}$) and SPJ ethics before committing compute or subscribing.

:::tabs
=== CLI
```bash
# Pre-flight forensic audit on a candidate feed URL
credence feed inspect "https://arstechnica.com/feed"
```

=== FastMCP 2.0 (Claude / Cursor)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_inspect_feed_health",
    "arguments": {
      "feed_url": "https://arstechnica.com/feed"
    }
  }
}
```

=== Python SDK
```python
from credence.feeds.inspector import inspect_feed_preflight

report = await inspect_feed_preflight("https://arstechnica.com/feed")
print(f"Composite Score (F_j): {report['composite_score']}")
print(f"Topic Entropy (H): {report['topic_entropy']}")
print(f"Status: {report['status']}")
```

=== 📟 Textual TUI Workstation
1. In `credence tui`, press `4` to view the active feed subscriptions table.
2. Review priority tiers (`T1`–`T4`), dynamic composite quality scores ($F_j$), classified subject namespaces, and active statuses.
3. Press `3` to cross-reference hierarchical domain subjects in the taxonomy browser.

![Credence TUI Feeds Stream](../../assets/tui/07-feeds-stream.svg)
:::

---

## 3. Running Continuous Sifter Workers

Run the continuous background sifting worker with Rendezvous Hashing (HRW) work partitioning.

:::tabs
=== CLI Daemon
```bash
# Run background sifter with 5-minute polling cycles
credence sifter --interval 300 --profile balanced
```

=== Systemd Service
```ini
# /etc/systemd/system/credence-sifter.service
[Unit]
Description=Credence Real-Time Epistemic Sifter Daemon
After=network.target

[Service]
Type=simple
User=credence
ExecStart=/usr/local/bin/credence sifter --interval 300 --profile balanced
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

=== Docker Compose
```yaml
version: '3.8'
services:
  sifter:
    image: ghcr.io/artibyrd/credence:latest
    command: ["sifter", "--interval", "300", "--profile", "balanced"]
    environment:
      - CREDENCE_GEMINI_API_KEY=${CREDENCE_GEMINI_API_KEY}
    restart: always
```

=== 📟 Textual TUI Workstation
1. In `credence tui`, press `s` to trigger background sifting on demand.
2. Watch status notifications report newly discovered articles vs items adopted from the mesh at $0.00 token cost.
3. Switch to Tab `7` (`Morning Digest`) to review accumulated swarm compute savings.
:::

---

## 4. Feed Health & Rotation Policy Reference

| Quality Score ($F_j$) | Topic Entropy ($H$) | Rotation Status | Swarm Action |
| :--- | :--- | :--- | :--- |
| **$F_j \ge 0.70$** | $H \ge 0.30$ | **ACTIVE** | Continuously polled and seeded across swarm |
| **$0.40 \le F_j < 0.70$** | $H \ge 0.30$ | **PROBATION** | Polled conditionally during off-peak token headroom |
| **$F_j < 0.40$** | $H < 0.30$ | **QUARANTINED** | **Autonomous eviction**; gossip alert sent to peers |

> [!IMPORTANT]
> **The Pizza Hut Invariant**: Outlets whose token entropy collapses ($H < 0.30$) due to promotional astroturfing are autonomously demoted without requiring manual admin intervention.
