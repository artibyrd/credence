---
title: 'Tutorial 05: 3-Node Mesh Quickstart'
description: Boot a 3-node local P2P mesh cluster and verify zero-token attestation
  adoption across peers.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 5
---

# Tutorial 05: 3-Node Mesh Quickstart

Learn how to boot a 3-node local P2P mesh cluster, divide syndicated feeds across peers using Rendezvous Hashing, and verify how Node 2 and Node 3 adopt pre-ingested audit attestations at **$0.00 token cost**.

---

## 🏛️ 3-Node Small Mesh Topology

| Node Alias | WebSocket Port | Node Role | Peer Interconnects | Latency SLA ($T_i$) |
| :--- | :--- | :--- | :--- | :--- |
| **`seed-node-alpha`** | `:8765` | Bootstrap Seed Node | Accepts inbound connections from Beta & Gamma | $< 50\text{ms}$ |
| **`peer-beta`** | `:8766` | Sifting Peer (Tier 1 & 2) | Connects to `ws://127.0.0.1:8765` (Alpha) | $< 100\text{ms}$ |
| **`peer-gamma`** | `:8767` | Sifting Peer (Tier 3 & 4) | Connects to `ws://127.0.0.1:8765` & `8766` | $< 100\text{ms}$ |

> [!TIP]
> **Zero-Token Adoption**: When `peer-beta` evaluates an article and signs its RFC 8785 envelope, `seed-node-alpha` and `peer-gamma` ingest and verify the cryptographic signature in $<1\text{ms}$, caching the evaluation locally with **zero LLM API calls**.

---

## 1. Booting Node 1 (Bootstrap Seed)

In Terminal 1:
```bash
credence mesh start --port 8765 --node-id "seed-node-alpha"
```

---

## 2. Booting Node 2 & Node 3

In Terminal 2:
```bash
credence mesh start --port 8766 --peer "ws://127.0.0.1:8765" --node-id "peer-beta"
```

In Terminal 3:
```bash
credence mesh start --port 8767 --peer "ws://127.0.0.1:8765" --node-id "peer-gamma"
```

---

## 3. Auditing on Node 1 & Adopting on Nodes 2 & 3

1. **Trigger Audit on Node 1**:
   ```bash
   credence audit https://example.com/breaking-story --profile BALANCED
   ```
2. **Observe Zero-Token Adoption on Node 2**:
   ```bash
   credence lookup https://example.com/breaking-story
   # Output: [CACHE_HIT / MESH_ADOPTION] Tokens Burned: 0 ($0.00)
   ```

Both nodes now hold cryptographically identical, Ed25519-verified truth records without paying double inference fees.
