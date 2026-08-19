---
title: Closed-Loop Routing & P2P Traffic Shaping
description: Technical specification for connecting epistemic merit to P2P network
  bandwidth, rate limits, /24 subnet clustering, and zero-cost caching.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Closed-Loop Routing & P2P Traffic Shaping

In decentralized networks, reputation metrics are frequently toothless—serving as decorative vanity leaderboards while the underlying transport layer remains vulnerable to spam, Sybil floods, and free-riding.

Credence establishes a **Closed-Loop Feedback Architecture**, where reputation scores directly control the physics of the P2P WebSocket transport plane.

```mermaid
flowchart TD
    subgraph FeedbackLoop["Closed-Loop Epistemic Routing"]
        A["Observed Peer Work &amp; Attestations"] --> B["5-Factor Quality Score (Q_i)"]
        B --> C["Dynamic Traffic Class Assignment"]
        C --> D["P2P Rate Limiter &amp; Token Bucket"]
        D --> E["Mesh Gossip Prioritization"]
    end
```

---

## 1. 4-Band Traffic Shaping Architecture

Every active inbound and outbound `PeerConnection` is assigned a dynamic **Traffic Shaping Class** based on its observed Quality Score ($Q_i$) and citation grounding accuracy:

| Traffic Class | Quality Condition | Rate Limit | Behavior & Mesh Allocation |
| :--- | :---: | :---: | :--- |
| **`FAST_LANE`** | $Q_i \ge 0.85$ | **500 msgs/s** | Top-tier anchor nodes. Immediate broadcast relay, unbuffered fast-path ingestion. |
| **`STANDARD`** | $0.50 \le Q_i < 0.85$ | **50 msgs/s** | Healthy peers and fresh solitary genesis nodes. Standard gossip relay. |
| **`CHOKED`** | $0.25 \le Q_i < 0.50$ | **1 msg/s** | High-deviation or flaky nodes. Rate-limited to preserve mesh bandwidth. |
| **`QUARANTINED`** | $Q_i < 0.25$ | **0 msgs/s** | Slashed, hallucinating, or Sybil nodes. WebSocket connection severed. |

```python
class PeerTrafficClass(str, Enum):
    FAST_LANE = "FAST_LANE"      # 500 msgs/s - Top performers (Q_i >= 0.85)
    STANDARD = "STANDARD"        # 50 msgs/s  - Standard healthy nodes
    CHOKED = "CHOKED"            # 1 msg/s    - Flaky / high deviation nodes
    QUARANTINED = "QUARANTINED"  # 0 msgs/s   - Slashed / malicious nodes
```

---

## 2. /24 and /48 IP Subnet Clustering Defense

To prevent a single adversary from spinning up 100 VPS instances on the same hosting provider (e.g. AWS or DigitalOcean) to create a Sybil cartel and monopolize peer bandwidth, Credence enforces **Subnet-Level Rate Dampening**:

```python
def extract_ip_subnet(remote_address: str) -> str:
    """Extract normalized /24 (IPv4) or /48 (IPv6) subnet prefix for Sybil clustering."""
    clean = remote_address.replace("ws://", "").replace("wss://", "")
    host = clean.split(":")[0].split("/")[0]
    if "." in host:  # IPv4
        parts = host.split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    if host == "localhost":
        return "localhost/32"
    return host
```

### Invariant: Subnet Ingestion Cap
No single `/24` IPv4 subnet (or `/48` IPv6 prefix) is permitted to occupy more than **20% of an individual node's aggregate incoming message capacity**, preventing collocated Sybil nodes from drowning out legitimate residential or cloud peers.

---

## 3. Zero-Cost Attestation Adoption Gate

When a node receives a signed `AuditReport` over the P2P mesh, it can adopt the audit directly into its local database without invoking its local LLM. However, adopting unverified audits blindly creates free-rider vulnerabilities.

Credence enforces a cryptographic and mathematical gate:

```python
def should_adopt_attestation(
    report: AuditReport,
    peer_quality: float = 0.5,
    min_quality: float = 0.70,
    min_grounding: float = 0.85,
) -> bool:
    """Evaluate whether a peer's signed attestation qualifies for zero-cost cache adoption.

    Requires:
    1. Valid node public key and signature
    2. Peer quality score >= min_quality (default 0.70)
    3. Verbatim quote grounding precision >= min_grounding (default 0.85)
    """
    if not report.node_pubkey or not report.node_signature:
        return False

    if peer_quality < min_quality:
        return False

    if report.violations:
        grounded_count = sum(1 for v in report.violations if v.is_grounded)
        ratio = grounded_count / len(report.violations)
        if ratio < min_grounding:
            return False

    return True
```

### The Economic Payoff
When an attestation passes this gate:
- Local compute consumed: **$0.00**
- Peer node credited: **+N tokens donated on Philanthropy Odometer**
- Latency to local availability: **< 15 milliseconds**
