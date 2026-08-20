---
title: Taxonomy Rule Engineering 101
description: Authoring custom namespaced YAML catalogs, calibrating numerical severities,
  and defining grounded citation requirements.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Taxonomy Rule Engineering 101

Credence's evaluation engine is completely decoupled from hardcoded heuristics. All auditing logic is defined in **namespaced, content-addressed YAML taxonomy catalogs**.

This guide walks you through authoring a new domain taxonomy catalog (e.g. for `FINANCIAL_DISCLOSURES` or `MEDICAL_CLAIMS`).

```mermaid
graph TD
    Domain["Domain: FINANCIAL_DISCLOSURES"] --> Cluster1["Cluster: PROJECTIONS"]
    Domain --> Cluster2["Cluster: REVENUE_RECOGNITION"]
    Cluster1 --> Rule1["Rule: ungrounded_ebitda@1.0.0 (Severity 4)"]
    Cluster1 --> Rule2["Rule: unsupported_guidance@1.0.0 (Severity 3)"]
    
    Rule1 --> Invariant["Pinned SHA-256 Hash Verification"]
    Invariant --> Evaluator["Multi-Agent Auditor Invocation"]
```

> [!IMPORTANT]
> **Immutable URI Invariant**: Rule IDs are permanently pinned by catalog SHA-256 digests. Evaluator models cannot invent ad-hoc rules outside the active registered taxonomy.

---

## 1. Catalog Architecture & Namespacing

Every rule in Credence is identified by an immutable, content-addressed URI:

$$\text{URI} = \text{domain}:\text{cluster}/\text{rule\_id}@\text{version}$$

Example: `FINANCIAL_DISCLOSURES:PROJECTIONS/ungrounded_ebitda@1.0.0`

---

## 2. Anatomy of a Taxonomy File (`financial_disclosures.yaml`)

Place custom YAML files in `credence/taxonomies/`:

```yaml
version: "1.0.0"
domain: "FINANCIAL_DISCLOSURES"
name: "SEC & Financial Disclosure Integrity Catalog"
description: "Rules auditing corporate earnings calls, 10-K filings, and investor disclosures."

clusters:
  - id: "PROJECTIONS"
    name: "Forward-Looking Projections & Non-GAAP Metrics"
    description: "Evaluates forward projections for substantiation and risk disclosures."
    rules:
      - rule_id: "ungrounded_ebitda"
        name: "Adjusted EBITDA Without GAAP Reconciliation"
        severity: 4
        description: "Promoting non-GAAP metrics (e.g. Adjusted EBITDA) without providing standard GAAP reconciliation or required cautionary disclosures."
        detection_signals:
          - "Presentation of non-GAAP financial figures with no immediate reconciliation table."
          - "Exclusion of recurring normal cash expenses from adjusted performance metrics."
        grounding_criteria:
          - "Must quote the specific non-GAAP figure and the surrounding context lacking GAAP reference."
        sample_violations:
          - "Our Core Adjusted EBITDA rose 400%, completely excluding all operating expenses and stock compensation."

      - rule_id: "unsupported_guidance"
        name: "Definitive Guidance Without Caveats"
        severity: 3
        description: "Making categorical forward revenue guarantees without safe harbor forward-looking statements."
        detection_signals:
          - "Use of deterministic verbs ('will guarantee', 'certainly achieve') for future quarterly performance."
        grounding_criteria:
          - "Must quote the categorical projection verbatim."
```

---

## 3. Severity Calibration Rubric

When assigning `severity` ($1 \dots 5$), use the standardized Credence rubric:

| Severity Level | Definition | Impact on Calibrated Score |
|:---|:---|:---|
| **Severity 1** (Informational) | Minor formatting or slight stylistic ambiguity. | Minimal ($\approx +7.0$) |
| **Severity 2** (Low Concern) | Standard informal fallacy without malicious intent (e.g. mild straw man). | Noticeable ($\approx +15.0$) |
| **Severity 3** (Moderate Concern) | Sensationalized headline delta, unbacked statistical claims, or missing byline. | Substantial ($\approx +26.0$) |
| **Severity 4** (Severe Malice) | Anonymous smear, ungrounded medical cures, hidden native advertisement, non-GAAP deception. | Critical ($\approx +40.0$) |
| **Severity 5** (Catastrophic) | Overt phishing, financial fraud, fabricated emergency broadcast, cloaked dangerous disinfo. | Hard Threshold ($\ge 75.0$) |

---

## 4. Deterministic Catalog Hashing (Invariant 5)

When a node loads a catalog, it computes its SHA-256 hash across canonical bytes. Peer nodes verify that evaluations cite pinned catalog hashes:

```bash
credence taxonomy hash credence/taxonomies/financial_disclosures.yaml
```
Output: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
