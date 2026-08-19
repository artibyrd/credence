---
title: Air-Gapped Truth Bundles & Sneakernets
description: Exporting and importing cryptographically signed .credence.bundle archives
  across air-gapped secure facilities, vessels, or conflict zones.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Air-Gapped Truth Bundles & Sneakernets

In environments with total internet censorship, maritime isolation, or military air-gaps, live WebSocket mesh peering is impossible.

Credence supports **Air-Gapped Truth Bundles (`.credence.bundle`)** allowing offline nodes to exchange signed attestations, consensus scores, and taxonomy catalogs over physical media (USB drives, SD cards, local ad-hoc Wi-Fi).

---

## 1. The Air-Gapped Sneakernet Flow

```mermaid
graph LR
    subgraph Connected Base Station (Europe)
        OnlineNode[Credence Online Seed Node] --> Export["credence bundle export --since 24h"]
        Export --> USB[(Encrypted USB / SD Card)]
    end

    subgraph Physical Transport
        USB --> Courier[Physical Courier / Satellite Drop]
    end

    subgraph Air-Gapped Island / Research Facility
        Courier --> OfflineNode[Isolated Credence Node]
        OfflineNode --> Import["credence bundle import bundle.credence.json"]
        Import --> Verify[100% In-Memory Ed25519 Signature Verification]
    end
```

---

## 2. Exporting an Epistemic Truth Bundle

From an online node:

```bash
# Export all attestations and taxonomy updates from the past 48 hours
credence bundle export \
  --output ./bundles/truth-bundle-2026-08-17.credence.json \
  --since 48h \
  --include-taxonomies
```

### Bundle Structure (`truth-bundle.credence.json`):
```json
{
  "bundle_version": "1.0.0",
  "generated_at_utc": "2026-08-17T18:00:00Z",
  "issuer_pubkey": "ed25519:e4d9b2a1f0c8e7d6b5a4938271605f4e3d2c1b0a9f8e7d6c5b4a3928170f",
  "attestation_count": 142,
  "attestations": [ ... ],
  "taxonomies": [ ... ],
  "bundle_signature_ed25519": "c9a8b7..."
}
```

---

## 3. Importing into an Air-Gapped Node

On the isolated system:

```bash
credence bundle import ./bundles/truth-bundle-2026-08-17.credence.json
```

### Verification Safeguards:
1. **Root Signature Verification**: Verifies the bundle envelope signature against known genesis public keys.
2. **Itemized Attestation Verification**: Iterates over every enclosed `AuditReport`, checking Ed25519 signatures and RFC 8785 canonical bytes.
3. **Hermetic DB Ingestion**: Populates local SQLite database without initiating any outbound network connections.
