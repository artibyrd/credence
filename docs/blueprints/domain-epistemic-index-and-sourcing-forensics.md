---
title: "The Domain Epistemic Index & Sourcing Forensics"
description: "Forensic methodology, mathematical ratios, and longitudinal metrics for evaluating public publisher integrity and detecting disguised advertorials."
---

# The Domain Epistemic Index & Sourcing Forensics

Evaluating individual articles provides episodic truth verification, but bad actors often exploit cumulative editorial patterns: omitting author bylines, disguising sponsored commercial copy as breaking civic news, or failing to disclose financial conflicts of interest across dozens of articles.

Credence aggregates article-level audit records into the **Domain Epistemic Index ($DEI$)** and a suite of **Forensic Sourcing Ratios**. This enables researchers, investigative journalists, and readers to track longitudinal publisher integrity over time.

---

## 1. The Domain Epistemic Index ($DEI$)

The $DEI$ is a calibrated composite metric on a scale from $0.00$ (completely deceptive or advertorial farm) to $100.00$ (gold-standard journalistic rigor):

\[
DEI = \max\Big(0.00, \; 100.00 - \bar{S}_{\text{suspicion}} - 5 \cdot \bar{V}_{\text{density}} - \Pi_{\text{penalties}}\Big)
\]

Where:
- $\bar{S}_{\text{suspicion}}$ is the domain's average suspicion score ($0.0$ to $100.0$).
- $\bar{V}_{\text{density}}$ is the average number of verified taxonomy violations per 1,000 words.
- $\Pi_{\text{penalties}}$ represents cumulative penalties for suppressed disclosures and uncorroborated single-source claims.

### Standardized Trust Bands

| Trust Band | $DEI$ Range | Editorial Characteristics |
| :--- | :--- | :--- |
| 🟢 **HIGH_INTEGRITY** | $85.00 - 100.00$ | Verifiable human bylines, multi-source corroboration, explicit conflict disclosures. |
| 🔵 **RELIABLE** | $70.00 - 84.99$ | Standard journalistic sourcing with minor attribution ambiguities. |
| 🟡 **MIXED** | $50.00 - 69.99$ | Frequent uncorroborated claims, intermittent native promotional blurbs. |
| 🟠 **POOR** | $30.00 - 49.99$ | Heavy single-source PR aggregation, undisclosed sponsor relationships. |
| 🔴 **DECEPTIVE** | $0.00 - 29.99$ | Systematic advertorial camouflage, fake bylines, high topic entropy collapse. |

---

## 2. The Four Forensic Sourcing Ratios

```mermaid
flowchart TD
    subgraph SourcingRatios ["The 4 Forensic Sourcing Pillars"]
        R1["1. Byline Transparency Ratio (R_byline)<br/>Proportion of articles with verified human bylines"]
        R2["2. Single-Source Reliance Ratio (R_single)<br/>Frequency of articles relying on a single press release"]
        R3["3. Conflict Disclosure Rate (R_COI)<br/>Rate of explicit financial/political conflict disclosures"]
        R4["4. Advertorial Separation Index (ASI)<br/>Separation metric isolating disguised native advertorials"]
    end
```

### 1. Byline Transparency Ratio ($R_{\text{byline}}$)
Measures the proportion of articles attributed to verified human journalists rather than generic staff tags (`"Admin"`, `"News Staff"`, or `"Editorial Team"`):

\[
R_{\text{byline}} = \frac{N_{\text{verified\_author}}}{N_{\text{total}}}
\]

### 2. Single-Source Reliance Ratio ($R_{\text{single}}$)
Calculates the frequency with which an outlet publishes articles derived from a single uncorroborated source (e.g. police blotters, corporate press releases, or municipal handouts) without independent verification (`SPJ-1.1`, `SPJ-1.2`):

\[
R_{\text{single}} = \frac{N_{\text{single\_source}}}{N_{\text{total}}}
\]

### 3. Conflict Disclosure Rate ($R_{\text{COI}}$)
Measures compliance with ethical disclosure standards when covering stories involving the publisher's commercial advertisers, board members, or political candidates (`SPJ-3.1`, `SPJ-3.2`):

\[
R_{\text{COI}} = \frac{N_{\text{disclosed\_conflicts}}}{N_{\text{stories\_with\_conflicts}}}
\]

### 4. Advertorial Separation Index ($ASI$)
Quantifies how effectively an outlet separates paid commercial advertorials from genuine news coverage (`SPJ-3.3`, `DEC-1.4`, `AST-1.1`). Low $ASI$ scores indicate disguised native advertisements masquerading as editorial reporting.

---

## 3. Longitudinal Trend Visualization

Credence groups publisher audits into monthly longitudinal buckets (`period_label`, `audits_count`, `avg_suspicion`, `avg_dei`, `violations_count`). This exposes:
- **Sudden Quality Drops**: Detecting when an established outlet is acquired by a private equity roll-up or pink slime farm.
- **Topic Entropy Collapses**: Detecting promotional astroturfing pivots in real time.

---

## 4. 4-Way Interface Parity for Analytics

- **CLI Workstation**:
  ```bash
  credence rankings outlet inmaricopa.com
  credence export-analytics inmaricopa.com --format json -o analytics.json
  ```
- **FastMCP 2.0 Tools & Resources**:
  - Tool: `credence_get_publisher_analytics(domain="inmaricopa.com")`
  - Dynamic Resource: `credence://analytics/publisher/inmaricopa.com`
- **Starlette REST API**:
  ```http
  GET /api/analytics/publisher/inmaricopa.com
  ```
- **Zero-Build Web UI**:
  - Interactive **Publisher Analytics & Trends** tab on `credence.report/viewer.html` rendering inline SVG trend charts with zero npm dependencies.
