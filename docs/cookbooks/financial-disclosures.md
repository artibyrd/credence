---
title: Auditing Financial Disclosures & 10-K Filings
description: Using the ULTRA profile (16k thinking tokens) to audit SEC 10-K filings,
  earnings calls, and corporate releases.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

Corporate press releases and quarterly SEC filings often contain evasive phrasing, non-GAAP exclusions, ungrounded forward projections, and disguised conflicts of interest.

This cookbook shows how to use **Credence with the ULTRA operational profile** to execute deep syllogistic reasoning audits on financial texts.

---

## 1. Why the ULTRA Profile Matters for Finance

While the `BALANCED` profile (1,024 thinking tokens) excels at everyday journalism and dark patterns, financial audits require **deep chain-of-thought reasoning**:
- Correlating footnote disclosures with top-line GAAP operating income.
- Detecting subtle non-sequiturs in CEO answers during earnings call Q&A sessions.
- Identifying cherry-picked time horizons in performance graphs.

The `ULTRA` profile allocates up to **16,384 thinking tokens** on Gemini 3.7 Flash to exhaustively trace logical entailments before outputting findings.

---

## 2. CLI Audit of an SEC Filing or Earnings Transcript

```bash
# Audit an online SEC 10-K filing or earnings call transcript
credence audit https://www.sec.gov/edgar/data/.../10-k.htm \
  --profile ULTRA \
  --taxonomy financial_disclosures
```

### Auditing Raw Text / Local PDF Transcripts:

```bash
credence audit \
  --file ./transcripts/q3-earnings-call.txt \
  --profile ULTRA \
  --title "Acme Corp Q3 2026 Earnings Call"
```

---

## 3. Sample Financial Findings Output

```text
============================================================
Credence Financial Epistemic Audit Report
Target: Acme Corp Q3 2026 Earnings Call Transcript
Cost Profile: ULTRA (12,450 Thinking Tokens Consumed)
============================================================

Overall Suspicion Score: 68.4 / 100 [SUSPICIOUS]
Violation Density: 3.8 / 1k words
Citation Grounding: 100% (G = 1.0)

Key Violations:
  [FINANCIAL_DISCLOSURES:PROJECTIONS/ungrounded_ebitda@1.0.0] Severity: 4
    Quote: "Our Core Adjusted Community EBITDA grew 320% year-over-year, demonstrating exceptional unit economics."
    Rationale: Excludes recurring cloud infrastructure hosting fees, depreciation, and executive stock compensation without reconciliatory footnote disclosures.

  [LOGICAL_FALLACY:RELEVANCE/ad_hominem@1.0.0] Severity: 3
    Quote: "Short sellers who question our cash runway are simply bad-faith saboteurs who don't understand our industry."
    Rationale: Dismisses substantive questions regarding 6-month liquidity reserves by attacking the motives of critics rather than presenting audited balance sheet reserves.
============================================================
```
