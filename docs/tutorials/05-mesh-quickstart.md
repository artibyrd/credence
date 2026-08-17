# Tutorial 05: 5-Minute 3-Node Mesh Peering & Zero-Token Feed Adoption

Learn how to boot a 3-node local P2P mesh cluster, divide syndicated feeds across peers, and verify how Node 2 and Node 3 adopt pre-ingested audit attestations at **$0.00 token cost**.

---

## 1. Booting Node 1 (Bootstrap Seed)

In Terminal 1:
```bash
credence mesh start --port 8765 --node-id "seed-node-alpha"
```

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

## 3. Cooperative Feed Syndication (BitTorrent Economics)

Subscribe Node 1 to a high-volume RSS feed:
```bash
credence feeds add https://feeds.reuters.com/news --target-node "http://127.0.0.1:8765"
credence feeds sync
```

Node 1 evaluates the feed articles, signs the attestations with its Ed25519 key, and gossips the envelopes to Peer Beta and Peer Gamma.

Now audit that same URL on Peer Gamma:
```bash
credence audit https://reuters.com/breaking-article --endpoint "http://127.0.0.1:8767"
```

### Output:
```text
Attestation Adopted from P2P Mesh!
Source Node: seed-node-alpha (Quality: Q = 0.95)
Signature: VERIFIED (Ed25519 / RFC 8785)
LLM Tokens Consumed: 0 (100% Compute Savings)
```
