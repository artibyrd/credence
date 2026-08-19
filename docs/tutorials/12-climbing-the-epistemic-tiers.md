---
title: 12. Climbing the Epistemic Tiers
description: Step-by-step operator guide to minting an identity, sifting feeds, earning
  verified auditor badges, achieving domain authority, and qualifying as a root seed
  anchor.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# 12. Climbing the Epistemic Tiers

This hands-on tutorial guides node operators through the complete epistemic progression lifecycle: from minting a fresh node identity on a Raspberry Pi or cloud instance to earning verifiable merit badges, saving LLM tokens for the swarm, and qualifying as a canonical root seed anchor.

```mermaid
flowchart LR
    Step1["1. Mint Identity<br/>🌱 SPROUT"] --> Step2["2. Sift Feeds<br/>📡 SIFTER"]
    Step2 --> Step3["3. Verbatim Audits<br/>🛡️ AUDITOR"]
    Step3 --> Step4["4. Domain Authority<br/>🏛️ SPECIALIST"]
    Step4 --> Step5["5. Seed Manifest<br/>💎 ROOT_ANCHOR"]
```

---

## Prerequisites

- **Python 3.12+** with `poetry` or standalone `credence` CLI installed.
- Local SQLite database initialized (`just ignite` or `credence germinate`).
- Connected terminal workstation (`credence tui`).

---

## Step 1: Genesis & Minting Identity (Tier I: Sprout Node 🌱)

Every node starts by generating an immutable Ed25519 cryptographic keypair and subscribing to baseline syndicated feeds:

```bash
# Rapid one-command node genesis
$ credence germinate --burst 3

# View your newly minted public identity
$ credence identity show
```

### Inspecting Your Initial Merit Card
```bash
$ credence merit
```

At this stage:
- **Tier**: `SPROUT`
- **Quality ($Q_i$)**: $0.50$ (healthy neutral mathematical prior)
- **Uptime ($U_i$)**: $1.00$
- **Traffic Class**: `STANDARD` (50 msgs/s)
- **Badges Unlocked**: `🌱 Sprout Node`

---

## Step 2: Zero-Trust Feed Sifting (Tier II: Sifter Pioneer 📡)

To advance to Tier II, your node must actively partition and evaluate $\ge 10$ syndicated articles:

```bash
# Sync syndicated feeds and evaluate incoming novel articles
$ credence feeds sync --evaluate

# Check open community verification bounties
$ credence bounties
```

Once your node evaluates 10 consensus rounds with Quality $Q_i \ge 0.60$, the merit engine automatically unlocks:
- **Tier**: `SIFTER`
- **Badges Unlocked**: `📡 Sifter Pioneer`

---

## Step 3: Verbatim Cited Audits (Tier III: Verified Auditor 🛡️)

Tier III requires demonstrating high epistemic fidelity:
- $\ge 50$ consensus rounds completed
- Quality Score $Q_i \ge 0.75$
- Quote Grounding Precision $G_i \ge 0.85$ (100% of cited quotes must exist verbatim in the source DOM)

```bash
# Audit a specific URL with strict verbatim quote extraction
$ credence audit https://reuters.com/world/europe/eu-ai-act-passed

# View your updated grounding statistics
$ credence merit
```

### Unlocked Capabilities
- **Attestation Seeding**: Your signed audit reports are now eligible for zero-cost adoption by peer nodes in the mesh.
- **Compute Philanthropy Odometer**: Begins tracking LLM tokens donated to other operators.
- **Badges Unlocked**: `🛡️ Verified Auditor`

---

## Step 4: Building Domain Authority (Tier IV: Domain Specialist 🏛️)

Tier IV represents empirical authority in a specific knowledge cluster (e.g. `journalism.news`, `science.climate`, `health.medical`):

```bash
# List all registered subject namespaces
$ credence subjects list

# Audit specialized domains in a targeted subject namespace
$ credence audit https://nature.com/articles/s41586-024-00123
```

### The Anti-Diploma Invariant
Domain expertise cannot be bought or pre-configured. It is earned through performance:
$$E_i = 0.40 C_i + 0.35 G_i + 0.15 V_i + 0.10 L_i$$

To unlock `SPECIALIST`, your node must maintain $E_i \ge 0.80$ across **at least 5 distinct root FQDNs** in the namespace, proving cross-domain epistemic resilience.

---

## Step 5: Root Seed Candidate (Tier V: Root Anchor 💎)

The pinnacle of the Credence mesh. Root Anchors serve as trusted bootstrap anchors listed in canonical `peers.json` manifests.

### Qualification Requirements
1. **5-Factor Quality**: $Q_i \ge 0.85$
2. **Uptime Ratio**: $U_i \ge 0.80$
3. **Grounding Precision**: $G_i \ge 0.80$
4. **Active Longevity**: $\ge 30$ continuous operating days
5. **Taxonomy Sync**: 100% matching catalog SHA-256 hashes

```bash
# Check your progress toward Tier V
$ credence merit

# Export signed bootstrap seed manifest
$ credence seeds generate --output my_seeds.json --valid-hours 48
```

---

## Step 6: Exporting & Embedding Your Live SVG Merit Badge

Display your earned prestige on GitHub repositories, documentation portals, or operator dashboards:

```bash
# Generate standalone SVG badge
$ credence badge export root_seed_candidate --node my-sovereign-node --output badge.svg
```

```html
<!-- Live HTML / Markdown Embed -->
<p align="center">
  <img src="https://credence.run/api/badge/root_seed_candidate?node=anchor-node-01" alt="Credence Root Anchor" />
</p>
```

---

## Interactive TUI Leaderboard Workstation

You can monitor global mesh rankings and your local merit card in real time using the Textual TUI:

```bash
$ credence tui
```
1. Press `F8` or click **`🏆 Leaderboard`**.
2. Switch between **Quality ($Q_i$)**, **Philanthropy**, and **Galileo** views using tab controls.
3. Review your unlocked badges, current tier progress bar, and assigned traffic class.
