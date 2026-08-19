---
title: Scoring Calibration & Mathematical Rubrics
description: Formal mathematical specifications, exponential saturation curves, and
  density indices used by Credence.
since_version: v1.9.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 4
---

# Scoring Calibration & Mathematical Rubrics

This document provides the formal mathematical specifications and calibration curves used by the **Credence Scoring Engine**.

---

## 1. Grounded Violation Inputs

Let $V$ be the set of violations discovered by specialist subagents. Each violation $v \in V$ is defined as a tuple:

$$v = (\text{rule\_id}, \text{domain}, \text{severity}, \text{confidence}, \text{is\_grounded})$$

Where:
- $\text{severity}_v \in \{1, 2, 3, 4, 5\}$ (Defined by the taxonomy catalog).
- $\text{confidence}_v \in [0.0, 1.0]$ (Evaluator certainty).
- $\text{is\_grounded}_v \in \{\text{True}, \text{False}\}$ (Verified presence in source DOM text).

If $\text{is\_grounded}_v = \text{False}$, the violation is treated as an ungrounded hallucination and excluded from all scoring math:

$$V_{\text{grounded}} = \{v \in V \mid \text{is\_grounded}_v = \text{True}\}$$

---

## 2. Linear Raw Suspicion Score

Each taxonomy domain has a base multiplier weight $W_{\text{domain}}$:

| Domain | Weight ($W$) | Rationale |
|---|---|---|
| `JOURNALISTIC_ETHICS` | $1.2$ | Direct factual integrity and attribution standards |
| `LOGICAL_FALLACY` | $1.0$ | Cognitive reasoning and rhetorical soundness |
| `DECEPTIVE_PATTERN` | $1.5$ | Active malice and intentional UX manipulation |
| `DOMAIN_SPECIFIC` (e.g. Medical) | $1.2$ | Critical domain accuracy standards |

The **Raw Suspicion Score** $S_{\text{raw}}$ is the weighted linear sum across all grounded violations:

$$S_{\text{raw}} = \sum_{v \in V_{\text{grounded}}} \text{severity}_v \times \text{confidence}_v \times W_{\text{domain}(v)}$$

---

## 3. Calibrated Non-Linear Suspicion Score ($0.0 \dots 100.0$)

Credence maps the unbounded raw score to a normalized percentage scale via an exponential saturation curve:

$$S_{\text{calibrated}} = 100.0 \times \left(1.0 - e^{-\frac{S_{\text{raw}}}{K}}\right)$$

Where $K = 12.0$ is the saturation constant.

### Calibration Behavior Curve

| Raw Score ($S_{\text{raw}}$) | Violation Example | Calibrated Score ($S_{\text{calibrated}}$) | Classification Band |
|---|---|---|---|
| $0.0$ | Clean article with byline and citations | **$0.0$** | `CLEAN` |
| $3.6$ | 1 Minor Ethical Issue (Sev 3, Conf 1.0, W 1.2) | **$25.9$** | `LOW_SUSPICION` |
| $7.2$ | 2 Fallacies / Minor Dark Pattern | **$45.1$** | `SUSPICIOUS` |
| $15.0$ | Multiple severe fallacies + ghost byline | **$71.3$** | `DECEPTIVE` |
| $30.0+$ | Phishing / Severe Disinformation campaign | **$91.8 \dots 100.0$** | `DECEPTIVE` |

---

## 4. Suspicion Density Index

To normalize evaluations across long-form investigations versus short social posts:

$$\text{Density} = \frac{|V_{\text{grounded}}|}{\text{Word Count}} \times 1,000$$
