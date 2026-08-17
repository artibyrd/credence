# Tutorial 01: Auditing Anonymous Clickbait & Inspecting Grounded Citations

Learn how to use the **Credence CLI** to audit an unverified, sensationalized web article, inspect its DOM extraction, verify grounded quote offsets ($G = 1.0$), and calculate suspicion scores.

---

## What You'll Learn
- How Credence captures web snapshots via Playwright headless Chromium.
- How the Multi-Agent Pipeline checks claims against the **SPJ Code of Ethics** catalog.
- How the Grounded Quote Validator eliminates hallucinations.
- How to inspect findings in the CLI and view the cryptographic JSON envelope.

---

## 1. Running Your First Audit

To evaluate an online URL or local fixture:

```bash
credence audit https://example.com/breaking-news --profile BALANCED
```

### What Happens Behind the Scenes:
1. **DOM Ingestion**: Headless Chromium navigates to the page, strips tracking scripts and cookie banners, extracts clean prose text, and hashes the DOM.
2. **Specialist Evaluation**: 4 specialist agents analyze sourcing attribution, sensationalized headlines, and logical fallacies.
3. **Citation Verification**: Every reported violation is tested against the DOM text. If a quote cannot be found verbatim (accounting for collapsed whitespace sequences), it is discarded and the node's quality score is penalized.

---

## 2. Reading the Terminal Output

```text
============================================================
Credence Epistemic Audit Report
Target URL: https://example.com/breaking-news
Snapshot SHA-256: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069
Evaluated At: 2026-08-17T16:00:00Z
============================================================

Overall Suspicion Score: 84.5 / 100 [HIGH SUSPICION]
Violation Density: 4.2 violations / 1,000 words
Grounded Quote Verification: 100% (G = 1.0)

Detected Violations:
  [SPJ-1.1] Anonymous Sourcing Violation (Severity: 4)
    Quote: "Officials who spoke on condition of anonymity revealed secret plans..."
    Rationale: Major factual assertion lacks named attribution or corroborating documents.

  [FALLACY-3.2] Appeal to Fear / Sensationalism (Severity: 3)
    Quote: "Total disaster is imminent unless drastic measures are taken immediately."
    Rationale: Emotional hyperbolic language without supporting statistical evidence.
============================================================
```

---

## 3. Exporting the Signed Attestation

To export the signed RFC 8785 canonical JSON envelope:

```bash
credence audit https://example.com/breaking-news --output audit_report.json
```

You can view the cryptographic attestation in the interactive viewer:
👉 [https://credence.report/viewer.html](https://credence.report/viewer.html)
