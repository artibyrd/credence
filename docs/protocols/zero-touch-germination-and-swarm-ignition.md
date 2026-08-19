---
title: "Zero-Touch Node Germination & Swarm Ignition"
description: "How fresh, unseeded Credence nodes autonomously bootstrap cryptographic identity, seed catalogs, and peer attestations in under 5 seconds."
---

# Zero-Touch Node Germination & Swarm Ignition

When deploying a new decentralized node—whether on a Raspberry Pi homelab, a developer workstation, or Google Cloud Run—manual initialization steps (generating keys, configuring seed feeds, and populating trust caches) create onboarding friction and configuration errors.

Credence introduces **Zero-Touch Node Germination** (also known as *Miracle-Gro Ignition*), an autonomous self-bootstrapping lifecycle that takes a completely blank, unseeded node to full operational readiness in **under 5 seconds** at **$0.00 initial token cost**.

---

## 1. The 4-Stage Germination Sequence

When a node starts up with an empty database, the germination engine (`credence germinate` / `germinate_node`) executes four deterministic phases:

```mermaid
flowchart TD
    Start["Unseeded Node Startup"] --> Phase1["1. Ed25519 Identity Minting<br/>(Generates or loads node_identity.key)"]
    Phase1 --> Phase2["2. Genesis Inoculation<br/>(Inoculates signed peer attestations @ $0.00)"]
    Phase2 --> Phase3["3. Preset Catalog Sowing<br/>(Sows 24 curated civic & tech RSS feeds)"]
    Phase3 --> Phase4["4. Initial Burst Audit<br/>(Evaluates top novel article with grounded quotes)"]
    Phase4 --> Ready["Operational P2P Mesh Node"]
```

### Stage 1: Cryptographic Identity Minting
The node checks for the existence of `data/identity.key`. If absent, it mints a fresh Ed25519 keypair using RFC 8032:
- Generates 32-byte cryptographically secure private scalar.
- Derives 32-byte public key hex (`node_pubkey`).
- Persists key with strict POSIX permissions (`0600`).

### Stage 2: Genesis Attestation Inoculation
To give the new node an immediate epistemic baseline without spending LLM tokens, the germination engine inoculates authentic Genesis peer attestations directly into the local database.
- Verifies root Ed25519 signatures of verified seed nodes.
- Populates `SnapshotRecord`, `AuditRecord`, and `ViolationRecord` entities at **$0.00 token cost**.

### Stage 3: Curated Feed Sowing
Sows 24 preset RSS/Atom feeds across regional civic news, science journals, technology disclosures, and public notice feeds into the local feed catalog.

### Stage 4: Initial Burst Audit
Selects the first novel un-audited article from the sifter queue, runs a full epistemic verification pass using the default reference engine (`gemini-3.7-flash`), signs the canonical receipt, and stores the signed envelope for P2P gossip relay.

---

## 2. Non-Blocking Lifespan Execution

To ensure that HTTP health probes (`/health`, `/api/health`) and FastMCP reverse proxies respond instantaneously without cold-boot timeouts, germination runs as a decoupled background task inside the Starlette server lifespan:

```python
# credence/server/app.py
@asynccontextmanager
async def lifespan(app: Starlette):
    # Launch autonomous germination in background task
    germination_task = asyncio.create_task(
        germinate_node_safe(burst_count=1, db_path=settings.DATABASE_URL)
    )
    
    # Yield immediately so Uvicorn binds ports and answers HTTP health probes
    yield
    
    # Clean up background task during graceful shutdown
    if not germination_task.done():
        germination_task.cancel()
```

---

## 3. Developer & Operator Commands

### One-Command Full Setup (`just ignite`)
To onboard a new developer machine or initialize a cloud container:
```bash
# Setup virtual environment, run preflight, germinate node, and test
just ignite
```

### Manual CLI Germination
```bash
# Execute germination with a 3-article burst audit
credence germinate --burst 3
```

### Inspecting Node Identity
```bash
credence identity show
# Outputs:
# Node Pubkey: 9580dc91601992b33e3fd76718fcf94a69c76bf233b634221a9ae2ee59974cd0
# Reputation (Qi): 0.950 | Quality Band: HIGH_INTEGRITY
```
