---
title: DNS SRV & Dynamic Discovery Architecture
description: Configuring RFC 2782 DNS SRV records (_mesh._tcp.credence.nexus) with
  weighted priorities and failover sequences.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# DNS SRV & Dynamic Discovery Architecture

When HTTPS seed endpoints are unreachable or undergoing maintenance, Credence falls back to **Tier 2 Discovery: Dynamic DNS SRV Records** (RFC 2782).

DNS SRV allows the Credence network to advertise live WebSocket relays and bootstrap seed peers with priority weights and port assignments directly via decentralized DNS resolution.

---

## 1. RFC 2782 DNS SRV Format

Credence queries the `_mesh._tcp.credence.nexus` service record:

```text
_service._proto.name.  TTL  Class  SRV  Priority  Weight  Port  Target.
```

### Production DNS Zone Example (`credence.nexus`):
```zone
; Primary North America Seed Relays (Priority 10)
_mesh._tcp.credence.nexus.  300  IN  SRV  10  60  8765  seed-us-east.credence.nexus.
_mesh._tcp.credence.nexus.  300  IN  SRV  10  40  8765  seed-us-west.credence.nexus.

; Secondary Europe & Asia Seed Relays (Priority 20)
_mesh._tcp.credence.nexus.  300  IN  SRV  20  50  8765  seed-eu-central.credence.nexus.
_mesh._tcp.credence.nexus.  300  IN  SRV  20  50  8765  seed-ap-east.credence.nexus.

; Fallback Community Relays (Priority 50)
_mesh._tcp.credence.nexus.  300  IN  SRV  50  100 8765  community-relay1.credence.org.
```

---

## 2. Weighted Selection Algorithm

When resolving SRV records:
1. **Sort by Priority**: The client attempts connections to records with the lowest `Priority` integer first ($10 \to 20 \to 50$).
2. **Weighted Probability**: Among records with identical priority, candidate peers are chosen proportionally based on `Weight`:
   $$P(\text{seed}_i) = \frac{\text{Weight}_i}{\sum_j \text{Weight}_j}$$
3. **Connection Handshake**: The client initiates a WebSocket connection (`ws://seed-us-east.credence.nexus:8765`) and requests the peer manifest.

---

## 3. Testing SRV Records via CLI

```bash
# Query live SRV records using dig
dig _mesh._tcp.credence.nexus SRV

# Query using Credence CLI discovery diagnostic
credence mesh discover --tier dns-srv
```
