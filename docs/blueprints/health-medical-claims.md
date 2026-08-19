---
title: Medical & Health Claim Auditing Blueprint
description: Auditing health journalism, supplement landing pages, and clinical trial
  reporting against peer-reviewed meta-analyses.
since_version: v1.11.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Medical & Health Claim Auditing Blueprint

Health misinformation and unverified medical claims present direct threats to public well-being. From predatory dietary supplement landing pages to sensationalized interpretations of preliminary laboratory studies, evaluating medical prose requires strict evidentiary standards.

This blueprint outlines deploying Credence for **medical and public health auditing**.

---

## 1. The Medical Evaluation Threat Model

```mermaid
graph LR
    subgraph Ingestion
        Webpage[Health Article / Supplement Landing Page]
    end

    subgraph Specialist Audits
        Bio[Biomedical Claim Auditor]
        Fallacy[Causal Fallacy Auditor]
        Deceptive[Urgency & Dark Pattern Auditor]
    end

    subgraph Evidence Gate
        Bio --> MetaCheck{Correlation with PubMed/Cochrane Evidence?}
        Fallacy --> PostHoc{Post-Hoc Ergo Propter Hoc?}
        Deceptive --> FakeScarcity{Fake Stock Counter?}
    end

    subgraph Scoring
        MetaCheck & PostHoc & FakeScarcity --> CalibratedScore[Calibrated Suspicion Score]
    end
```

---

## 2. Key Rule Clusters (`medical_claims.yaml`)

- **`MEDICAL:TRIALS/in_vitro_extrapolation@1.0.0`** (Severity: 4): Reporting laboratory cell culture results (*in vitro*) or preliminary mouse models (*in vivo*) as proven human cures without stating trial limitations.
- **`MEDICAL:EVIDENCE/anecdotal_causation@1.0.0`** (Severity: 4): Using individual patient testimonials to substantiate general therapeutic efficacy.
- **`MEDICAL:DISCLOSURE/undisclosed_supplement_sponsor@1.0.0`** (Severity: 3): Publishing health articles that secretly promote specific branded wellness supplements without affiliate disclosures.

---

## 3. Example CLI Audit

```bash
credence audit https://example-wellness.test/miracle-anti-aging-cure \
  --taxonomy medical_claims \
  --profile ULTRA
```

### Result:
```text
Suspicion Score: 88.2 / 100 [DISINFORMATION]
Violations:
  - [MEDICAL:TRIALS/in_vitro_extrapolation@1.0.0] Severity 4
    Quote: "New study proves Root X reverses human aging by 10 years."
    Rationale: Cited study was conducted exclusively on yeast cells in vitro.
```
