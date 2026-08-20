---
title: 'Feature Walkthrough: Webpage & Prose Epistemic Auditing'
description: Comprehensive multi-interface walkthrough for auditing live URLs and
  raw prose text across CLI, FastMCP 2.0, Python SDK, and Zero-Build Web UI.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 1
---

# Feature Walkthrough: Webpage & Prose Epistemic Auditing

Learn how to audit digital media, news articles, and raw prose against formal journalistic ethics (SPJ), logical fallacies (IEP), and deceptive UI patterns across all supported interfaces.

```mermaid
flowchart LR
    Source["Input Content<br/>(Live URL / Raw Prose / HTML DOM)"] --> Engine["Credence Epistemic Engine"]
    Engine --> Specialist1["1. SPJ Ethics Specialist"]
    Engine --> Specialist2["2. Fallacy Specialist"]
    Engine --> Specialist3["3. Deceptive UI Specialist"]
    Engine --> Specialist4["4. Provenance & Satire Specialist"]
    
    Specialist1 & Specialist2 & Specialist3 & Specialist4 --> Gate["G=1.0 Grounding Gate"]
    Gate --> Output["Signed RFC 8785 Ed25519 Attestation"]
```

> [!NOTE]
> **Persistent Interface Preference**: Selecting a tab below saves your preference (`localStorage`). As you navigate across documentation pages, all tabbed examples will automatically match your selected interface.

---

## 1. Auditing a Live Webpage URL

Audit any public URL for journalistic bias, missing citations, deceptive UI, or satire.

:::tabs
=== CLI
```bash
# Basic audit with default Balanced profile (1,024 thinking tokens)
credence audit "https://arstechnica.com/science/2026/08/fusion-breakthrough"

# Free offline heuristic audit (0 tokens, instant CI gate)
credence audit "https://arstechnica.com/science/2026/08/fusion-breakthrough" --profile FREE

# Deep investigative audit with 8k thinking tokens
credence audit "https://arstechnica.com/science/2026/08/fusion-breakthrough" --profile ULTRA
```

=== FastMCP 2.0 (Claude / Cursor)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_check_url",
    "arguments": {
      "url": "https://arstechnica.com/science/2026/08/fusion-breakthrough",
      "cost_profile": "BALANCED"
    }
  }
}
```

=== Python SDK
```python
import asyncio
from credence import CredenceEngine

async def main():
    engine = CredenceEngine()
    report = await engine.audit_url(
        url="https://arstechnica.com/science/2026/08/fusion-breakthrough",
        profile="BALANCED"
    )
    print(f"Suspicion Score: {report.suspicion_score}")
    print(f"Classification: {report.classification}")
    print(f"Ed25519 Signature: {report.signature_ed25519[:16]}...")

asyncio.run(main())
```

=== Zero-Build Web UI
1. Navigate to **[credence.report](https://credence.report)** in your browser.
2. Enter `https://arstechnica.com/science/2026/08/fusion-breakthrough` into the URL field.
3. Select **Balanced (4k Thinking)**.
4. Click **Run Epistemic Audit** to view rendered DOM highlights and character-offset verification in real time.

=== 📟 Textual TUI Workstation
1. Launch `credence tui`.
2. Press `/` to open the **Target URL Audit** modal.
3. Enter `https://arstechnica.com/science/2026/08/fusion-breakthrough` and press `Enter`.
4. Inspect the split-screen report:
   - **Top Banner**: Calibrated suspicion score, classification badge, and density per 1k words.
   - **Left Panel**: Itemized grounded findings table with severity indicators (1–5).
   - **Right Panel**: In-context cited excerpts and specialist reasoning.
   - Press `f` to live-filter findings by keyword (e.g. `MED`, `SPJ`, `fallacy`).

![Credence TUI Inspector](../../assets/tui/01-inspector-rich.svg)
:::

---

## 2. Auditing Raw Unstructured Prose (Zero Scraping Overhead)

When evaluating draft articles, emails, or offline snippets, audit raw text directly without network requests.

:::tabs
=== CLI
```bash
# Audit raw text directly from shell pipeline
echo "Preliminary in-vitro lab studies definitively prove that drinking green tea cures 100% of human cancers immediately." | credence evaluate -

# Audit text from a local markdown file
credence evaluate --file draft_article.md --title "Draft Medical Report"
```

=== FastMCP 2.0 (Claude / Cursor)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_evaluate_text",
    "arguments": {
      "text": "Preliminary in-vitro lab studies definitively prove that drinking green tea cures 100% of human cancers immediately.",
      "title": "Draft Medical Report"
    }
  }
}
```

=== Python SDK
```python
from credence import CredenceEngine

engine = CredenceEngine()
report = await engine.evaluate_text(
    text="Preliminary in-vitro lab studies definitively prove that drinking green tea cures 100% of human cancers immediately.",
    title="Draft Medical Report"
)

for v in report.violations:
    print(f"[{v.rule_id}] Sev {v.severity}: {v.quote}")
```

=== 📟 Textual TUI Workstation
1. In `credence tui`, press `/` to audit or paste content into the terminal inspector.
2. Press `v` to cycle between **Rich Takeaway**, **Compact Digest**, and **Raw RFC 8785 JSON** view modes.
3. Review flagged deceptions with instant severity highlighting and grounding checks.

![Credence TUI Compact View](../../assets/tui/02-inspector-compact.svg)
:::

---

## 3. Verifying Cryptographic Attestations

Verify an Ed25519 signature and verbatim DOM offsets against the canonical RFC 8785 envelope.

:::tabs
=== CLI
```bash
# Verify attestation JSON payload
credence verify attestation.json
```

=== FastMCP 2.0 (Claude / Cursor)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "credence_verify_attestation",
    "arguments": {
      "signed_attestation_json": "{\"content_sha256\": \"...\", \"signature_ed25519\": \"...\"}"
    }
  }
}
```

=== Python SDK
```python
from credence.identity import verify_attestation_envelope

is_valid = verify_attestation_envelope(attestation_dict)
print(f"Attestation Valid: {is_valid}")
```

=== In-Browser WebCrypto
```javascript
// Pure client-side verification with W3C Web Cryptography API
const isValid = await window.crypto.subtle.verify(
  "Ed25519",
  publicKey,
  signatureBytes,
  canonicalJsonBytes
);
```

=== 📟 Textual TUI Workstation
1. Launch `credence tui` and select any audit in the **Recent Audits** sidebar (`Up`/`Down` arrows).
2. The header automatically verifies the cryptographic signature: `[✓ Signed]` or `[Unsigned]`.
3. Press `6` to jump to the **Node Identity** pane to inspect your local Ed25519 public key and attestation capabilities.

![Credence Node Identity](../../assets/tui/10-node-identity.svg)
:::

---

## 4. Operational Comparison Matrix

| Feature / Interface | CLI (`credence`) | FastMCP 2.0 | Python SDK | Zero-Build Web | Textual TUI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Audit URL** | `credence audit` | `credence_check_url` | `.audit_url()` | Interactive Input | TUI Modal |
| **Evaluate Raw Prose** | `credence evaluate` | `credence_evaluate_text` | `.evaluate_text()` | Textarea Input | TUI Modal |
| **Ed25519 Verification** | `credence verify` | `credence_verify_attestation` | `.verify_envelope()` | `window.crypto` | Auto-verify |
| **Primary Audience** | DevOps & Shell Scripts | Claude, Cursor, AI Agents | Python Devs & Data Science | End Users & Readers | Power Operators |

> [!TIP]
> Use `--profile FREE` for hermetic CI pipelines to perform offline structural audits in $< 0.1\text{s}$ at **$0.00 token cost**.
