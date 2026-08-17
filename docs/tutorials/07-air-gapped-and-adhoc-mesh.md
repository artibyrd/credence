# Tutorial 07: Air-Gapped Truth: Offline USB Shuttling & Ad-Hoc Mesh Sync

Learn how investigative journalists, field researchers, and air-gapped secure facilities can export, verify, and shuttle cryptographically signed `.credence.json` bundles across physically isolated networks.

---

## 1. Exporting an Offline Audit Bundle

When working in an environment with zero internet access:

```bash
credence export --audit-id "aud_9f82ab34cd" --output /media/usb/truth-bundle-2026.credence.json
```

The exported file contains:
- The raw rendered DOM HTML snapshot.
- SHA-256 content hashes.
- Grounded citation quote offsets.
- The evaluating node's Ed25519 public key and RFC 8785 canonical signature.

---

## 2. Importing & Verifying on an Air-Gapped Workstation

On the target offline machine:

```bash
credence import /media/usb/truth-bundle-2026.credence.json
```

### Output:
```text
Importing Credence Attestation Bundle...
Snapshot Hash: a89f...3b12 (Verified)
Author Key: 3b12...ef89 (Ed25519 Verified)
Attestation Timestamp: 2026-08-17T12:00:00Z
Status: 100% Hermetic & Cryptographically Intact
```

You can now inspect the report in the offline Textual TUI (`credence tui`) or zero-build web viewer with zero network connectivity.
