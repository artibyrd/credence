---
title: Node Germination & Swarm Ignition Specification
description: Technical protocol specification for Credence autonomous node ignition,
  Genesis peer mesh inoculation, HRW Rendezvous Hashing feed partitioning, and atomic
  sub-transaction invariants.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Node Germination & Swarm Ignition Specification

This specification defines the protocol, data structures, mathematical formulas, and concurrency invariants governing **Autonomous Node Germination** and **Swarm Ignition** across the Credence ecosystem.

```mermaid
sequenceDiagram
    autonumber
    participant Node as Credence Node
    participant DB as SQLite WAL (credence.db)
    participant Mesh as Peer Mesh / Genesis Seeds
    participant LLM as Multi-Agent LLM Pipeline
    participant Web as Web Viewer (reports.json)

    Node->>DB: 1. Epistemic Genesis (Load/Gen Ed25519 Keypair)
    Node->>Mesh: 2. Request Genesis Seed Attestations
    Mesh-->>Node: Return signed Genesis Attestation Pack
    Node->>DB: Inoculate Genesis Attestations ($0.00 token spend)
    Node->>DB: 3. Sow 26 Categorized Feed Subscriptions
    Node->>DB: 4. Sort Feeds via HRW Rendezvous Hashing
    Node->>LLM: Miracle-Gro Burst: Audit Top N Novel Items
    LLM-->>Node: Return signed AuditReport entities
    Node->>Mesh: Broadcast Newly Signed Attestations
    Node->>Web: 5. Export reports.json Static Catalog
```

---

## 1. The 5-Phase Germination Lifecycle

A complete germination lifecycle executes deterministically via `credence.germinate.germinate_node()`:

```python
async def germinate_node(
    session: AsyncSession,
    burst_items: int = 3,
    sync_mesh: bool = True,
    profile_override: Any = None,
    verbose: bool = True,
    relay: Optional[MeshGossipRelay] = None,
) -> GerminationSummary: ...
```

### Phase Definitions

1. **Phase 1: Epistemic Genesis (`load_or_create_node_identity`)**
   - Generates or loads the node's persistent Ed25519 cryptographic keypair from `node_identity.json`.
   - Derives the 64-character hexadecimal public key $K_{\text{node}} \in \{0\dots 9, a\dots f\}^{64}$.

2. **Phase 2: Peer Mesh Inoculation (`inoculate_from_mesh_seeds`)**
   - Ingests canonical signed Genesis seed attestations (`genesis_attestations.json`) into local SQLite records:
     - `SnapshotRecord` (clean text, content SHA-256, SimHash-64).
     - `AuditRecord` (suspicion score, classification, Ed25519 signature, `evaluation_method="mesh_adopted"`).
     - `ViolationRecord` (itemized taxonomy rule violations and verbatim quotes).
     - `FeedItemRecord` (`processing_status="mesh_adopted"`).
   - Cost: **$0.00 / 0 LLM tokens**.

3. **Phase 3: Soil Preparation (`bootstrap_preset_feeds`)**
   - Populates 26 categorized feed subscriptions across 6 curated tiers:
     - `core-news` (AP, Reuters, NPR, BBC, The Guardian).
     - `investigative-tech` (ProPublica, The Markup, Ars Technica, Krebs on Security, 404 Media, EFF).
     - `science-preprints` (Nature, arXiv AI, ScienceDaily, Retraction Watch, NIH).
     - `regional-civic` (CalMatters, Texas Tribune, Spotlight PA, Voice of San Diego).
     - `financial-corporate` (MarketWatch, SEC Press Releases, FTC News).
     - `satire-commentary` (The Onion, The Babylon Bee).

4. **Phase 4: Miracle-Gro Sifting Burst (`run_germination_sifting_burst`)**
   - Polls highest-affinity feeds and evaluates up to $N$ novel articles within token governor headroom limits ($\ge 30\%$).
   - If connected to an active `MeshGossipRelay`, broadcasts newly minted attestations to the mesh.

5. **Phase 5: Web Catalog Hydration (`export_catalog_to_disk`)**
   - Queries SQLite audit records and writes canonical `reports.json` to `web/credence.report/reports.json`.

---

## 2. Highest Random Weight (HRW) Rendezvous Hashing

To guarantee orthogonal feed partition across a decentralized swarm without a centralized coordinator, nodes sort candidate subscriptions using **Rendezvous Hashing (HRW)**:

$$\text{Affinity}(K_{\text{node}}, U_{\text{feed}}) = \frac{\text{int}(\text{SHA-256}(K_{\text{node}} \parallel U_{\text{feed}})[0:8], 16)}{2^{32} - 1}$$

```python
def compute_feed_affinity(node_pubkey: str, feed_url: str) -> float:
    """Calculate Rendezvous Hash (HRW) affinity score between node pubkey and feed URL."""
    combined = f"{node_pubkey}:{feed_url}".encode("utf-8")
    digest = hashlib.sha256(combined).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF
```

### Swarm Partitioning Matrix

| Node Alias | Public Key Prefix | Highest Affinity Feed | Category Tier |
| :--- | :--- | :--- | :--- |
| **Node 1 (Anchor A)** | `9580dc91...` | ProPublica Main Feeds | Investigative Tech (Priority 1) |
| **Node 2 (Anchor B)** | `4fa821cd...` | Nature Latest Research | Science Preprints (Priority 1) |
| **Node 3 (Relay C)** | `1b89ef02...` | CalMatters Policy | Regional Civic (Priority 2) |
| **Node 4 (Relay D)** | `7c44e99a...` | MarketWatch Top Stories | Financial Disclosures (Priority 2) |
| **Node 5 (Relay E)** | `e019fb34...` | The Onion American Finest | Satire & Cloaking (Priority 3) |

---

## 3. Concurrency & Sub-Transaction Invariants

### The Atomic Ignition Sub-Transaction Invariant
When multiple processes or coroutines boot simultaneously against a shared database:
1. Every individual `SnapshotRecord`, `AuditRecord`, and `FeedSubscriptionRecord` insertion **must** execute in an isolated `try ... await session.commit() except Exception: await session.rollback()` sub-transaction block.
2. If another concurrent process inserts the same `content_sha256` or `feed_url` milliseconds earlier, the caught constraint violation safely rolls back without corrupting the broader session.

### The Multi-Node Session Isolation Invariant
In asynchronous test suites and multi-worker runners:
1. Never share a single `AsyncSession` across concurrent coroutines in `asyncio.gather(*tasks)`.
2. Each concurrent node routine **must** be allocated an independent `AsyncSession` via `async_sessionmaker(bind=engine, class_=AsyncSession)`.

---

## 4. REST API Gateway & Auto-Ignition Endpoints

### `POST /api/germinate`
Trigger manual or programmatic node germination:

```json
// Request Payload
{
  "burst": 3,
  "sync_mesh": true,
  "profile": "balanced"
}
```

```json
// Response Payload (HTTP 200)
{
  "status": "germinated",
  "identity_pubkey": "9580dc91601992b33e3fd76718fcf94a69c76bf233b634221a9ae2ee59974cd0",
  "peer_attestations_adopted": 5,
  "tokens_saved_mesh": 12500,
  "feeds_sowed": 26,
  "novel_items_audited": 3,
  "total_reports_ready": 194,
  "duration_seconds": 12.35,
  "timestamp": "2026-08-18T22:47:52.123456Z"
}
```
