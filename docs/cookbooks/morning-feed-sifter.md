---
title: Automated Morning Feed Sifter & Epistemic Digest
description: Setting up zero-trust feed autodiscovery, dynamic quality governance,
  background sifting daemons, and automated executive intelligence briefings.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

Newsrooms, OSINT analysts, enterprise compliance teams, and executive researchers spend hours filtering through hundreds of RSS, Atom, and JSON feeds every morning.

This cookbook shows how to set up an autonomous, zero-trust **Credence Morning Feed Sifter** that discovers feeds dynamically, executes pre-flight forensic audits against commercial takeover (the "Pizza Hut Problem"), partitions workloads across P2P mesh peers, and compiles daily executive epistemic digests at **92.3% compute savings**.

---

## 1. Zero-Trust Architecture Overview

```mermaid
graph TD
    Discover["Dynamic Discovery<br>credence feed discover"] --> PreFlight["Pre-Flight Forensic Audit<br>H_topic & SPJ Ethics"]
    PreFlight --> DynamicScore["Dynamic Quality Score (F_j)<br>F_j >= 0.70 Active | Evicted < 0.40"]
    
    DynamicScore --> SifterDaemon["Real-Time Sifter Daemon<br>credence sifter"]
    SifterDaemon --> MeshRelay{"Audit Cached on P2P Mesh?"}
    MeshRelay -- "Yes (92.3% of items)" --> Adopt["Zero-Token Mesh Adoption ($0.00 Token Burn)"]
    MeshRelay -- "No (Novel item)" --> Audit["Pareto Audit (Gemini 3.7 Flash 4k Thinking)"]
    Audit --> Gossip["Gossip Signed RFC 8785 Attestation"]
    
    Adopt & Gossip --> DigestGen["Morning Epistemic Digest Generator<br>credence digest"]
    DigestGen --> OutputReport["Executive Briefing (Terminal, Markdown, JSON)"]
```

> [!TIP]
> **Zero-Configuration Work-Sharing**: When multiple team members or automated agents run the sifter daemon across your local network or VPN, they automatically partition feed ingestion using Rendezvous Hashing without requiring a central coordination server.

---

## 2. Dynamic Zero-Trust Feed Discovery & Pre-Flight Inspection

Avoid static whitelists. Autodiscover feed endpoints dynamically and verify their topic entropy and editorial grounding before adding them to active ingestion:

```bash
# 1. Autodiscover feed candidate endpoints from any target website
credence feed discover "https://arstechnica.com"
credence feed discover "https://apnews.com"

# 2. Run a pre-flight forensic audit (evaluates topic diversity H_topic and SPJ ethics)
credence feed inspect "https://arstechnica.com/feed"

# 3. Bootstrap diverse categorized presets (investigative tech, science preprints, regional)
credence feed bootstrap-presets --category investigative-tech
credence feed bootstrap-presets --category science-preprints

# 4. Or ignite all 24 presets with 0-token mesh peer adoption in 1 command:
credence germinate
```

---

## 3. Dynamic Feed Health Governance (\(F_j\))

Every subscribed feed is continuously evaluated. Outlets that experience corporate acquisitions, undisclosed commercial astroturfing, or drops in verifiable grounding are autonomously demoted:

$$F_j = 0.35 (1.0 - \bar{S}_j/100) + 0.25 G_j + 0.20 H_{\text{topic}} + 0.20 T_{\text{freshness}}$$

View dynamic feed health rankings at any time:

```bash
credence feed health
```

```
                Dynamic Feed Health & Epistemic Quality Rankings                
┏━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ ┃                        ┃ Quality ┃        Avg ┃       ┃  Entropy ┃         ┃
┃ ┃ Feed Title / Channel   ┃  (F_j)  ┃  Suspicion ┃ Grou… ┃      (H) ┃ Status  ┃
┡━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ │ ProPublica: Main Feeds │  0.89   │        4.2 │  100% │     0.88 │ ACTIVE  │
│ │ The Markup: Investiga… │  0.87   │        6.1 │  100% │     0.84 │ ACTIVE  │
│ │ Ars Technica: Lab      │  0.84   │        8.5 │   95% │     0.81 │ ACTIVE  │
│ │ Krebs on Security      │  0.85   │        5.0 │  100% │     0.82 │ ACTIVE  │
│ │ 404 Media              │  0.82   │        9.0 │   92% │     0.79 │ ACTIVE  │
└─┴────────────────────────┴─────────┴────────────┴───────┴──────────┴─────────┘
```

---

## 4. Running the Background Sifter Daemon

Launch the real-time sifter daemon as a background systemd service or long-running worker. The daemon uses **Rendezvous Hashing (HRW)** to divide scraping duties across peer nodes, adopting attestations from peer nodes in **0 LLM tokens ($0.00 cost)**:

```bash
# Run sifter daemon with 5-minute polling cycles
credence sifter --interval 300 --profile balanced
```


## 5. Generating Daily Morning Epistemic Briefings

Generate executive intelligence summaries across 4 categories (Clean Journalism, Rhetorical Fallacies, Deceptive Flags, Satire Alerts, and Compute Savings):

```bash
# Display high-contrast terminal briefing
credence digest --format terminal

# Export to Markdown document for newsletters or static sites
credence digest --format markdown --output morning_brief.md --hours 24

# Export to JSON for downstream agent workflows
credence digest --format json --output digest.json
```

### Morning Briefing Structure & Sections

| Section | Content & Source Filters | Key Metrics Tracked |
| :--- | :--- | :--- |
| **🛡️ Verified Journalism** | $S < 20.0$, $G = 1.00$, Diverse sources | Grounding character offset, publisher key |
| **⚠️ Flagged Deceptions** | $S \ge 50.0$, Dark patterns, smears | Rule URI, violation severity (1–5) |
| **🎭 Satire & Parody** | $S = 0.00$, Poe's Law cues validated | Satire indicator, neutral score |
| **⚡ Swarm Compute Savings** | P2P zero-token adoption stats | Tokens saved, $0.00 cost multiplier |

### Sample Briefing Output

```markdown
# 🌅 Credence Morning Epistemic Digest
*Generated on 2026-08-18 06:00:00 UTC (Past 24 Hours)*

---
## 📊 Executive Swarm Summary
- **Total Articles Sifted**: `61`
- **Clean & Verified Coverage**: `49`
- **Questionable / Fallacious / Deceptive**: `11`
- **Verified Satire / Parody**: `1`
- **BitTorrent Mesh Compute Savings**: **`32,000` tokens (~$0.01)** across `10` zero-token adoptions.

---
## 🛡️ Clean & Verified Journalism (Top Scored)
- **[Autonomous Freight Safety Standards](https://example.org/clean-report)**  
  *Score: `0.0` | Zero violations detected*

## ⚠️ Rhetorical Fallacies & Clickbait Warnings
- **[Editorial: Inflation Policy Debate](https://example.org/op-ed)**  
  *Score: `61.3` | Flag: `FALLACY-1.1` (Ad Hominem)*  
  > "failed accountant who dresses like a circus clown"
```

---

## 6. Automating via FastMCP & AI Agents

If you use Claude, Cursor, or autonomous AI agents, you can generate digests or discover feeds directly through FastMCP 2.0:

* **Tool**: `credence_discover_feeds(target_url="https://apnews.com")`
* **Tool**: `credence_inspect_feed_health(feed_url="https://example.com/feed.xml")`
* **Tool**: `credence_generate_digest(hours=24)`
* **Resource**: `credence://digest/morning`
* **Resource**: `credence://feeds/active`
