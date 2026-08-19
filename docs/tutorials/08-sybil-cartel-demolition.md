---
title: 'Tutorial 08: Sybil Cartel Demolition'
description: How Credence mathematically detects and neutralizes colluding Sybil cartels
  via 5-factor quality and domain entropy.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 8
---

# Tutorial 08: Sybil Cartel Demolition

Learn how Credence mathematically detects and neutralizes colluding Sybil cartels attempting to farm domain authority or whitewash deceptive websites.

---

## 1. The Sybil Attack Scenario

Consider 4 rogue nodes ($N_1, N_2, N_3, N_4$) running on a local cluster. They attempt to manipulate the network by repeatedly endorsing each other's evaluations on a single domain (`propaganda-outlet.test`).

In traditional majority-voting systems, the cartel would succeed.

---

## 2. The Credence Defense Architecture

Credence calculates composite reputation ($W_i = 0.20 Q_i + 0.80 E_i$) incorporating:

1. **5-Factor Node Quality ($Q_i$)**:
   $$Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$$
2. **Empirical Authority ($E_i$) with Domain Entropy**:
   - Requires evaluation entropy across $\ge 5$ distinct Fully Qualified Domain Names (FQDNs).
   - If evaluations are clustered on $<5$ domains, the volume factor $V_i$ collapses to $0.00$.
3. **Hallucination Slashing**:
   - Any hallucinated citation instantly inflicts a 50% score slash across all domains.

---

## 3. Running the Live Demolition Simulation

Execute the automated cartel test:

```bash
poetry run pytest tests/test_red_team_cluster_attacks.py -k cartel -v
```

### Observation:
The cartel nodes are isolated; their calculated weight drops from $1.00 \to 0.05$, and their whitewashed ratings are rejected from the global consensus median.
