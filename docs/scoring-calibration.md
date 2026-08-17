# Scoring Calibration & Mathematical Rubrics in Credence

This document provides the formal mathematical specifications and calibration curves used by the **Credence Scoring Engine** ([`credence/pipeline/scoring.py`](file:///home/pendragon/Projects/credence/credence/pipeline/scoring.py)).

---

## 1. Grounded Violation Inputs

Let $V$ be the set of violations discovered by the specialist subagents. Each violation $v \in V$ is defined as a tuple:

$$v = (\text{rule\_id}, \text{domain}, \text{severity}, \text{confidence}, \text{is\_grounded})$$

Where:
- $\text{severity}_v \in \{1, 2, 3, 4, 5\}$ (Defined by the taxonomy catalog).
- $\text{confidence}_v \in [0.0, 1.0]$ (Evaluator certainty).
- $\text{is\_grounded}_v \in \{\text{True}, \text{False}\}$ (Verified presence in source text).

If $\text{is\_grounded}_v = \text{False}$, the violation is treated as a hallucination and excluded from all scoring math:

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

To map the unbounded linear raw score into a normalized percentage scale that penalizes compounding violations while asymptotically saturating at 100.0, Credence uses an exponential saturation curve:

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

## 4. Suspicion Density Index (Violations per 1,000 Words)

To normalize violation counts across articles of varying lengths (e.g. short blog post vs 10,000-word investigative report), the **Suspicion Density** $D$ is calculated as:

$$D = \frac{|V_{\text{grounded}}|}{\max(50, \text{word\_count})} \times 1000$$

A minimum denominator floor of $50$ words is enforced to prevent division-by-zero or extreme distortion on ultra-short snippets.

---

## 5. Poe's Law Satire Neutralization & Cloaked Disinformation

### Legitimate Satire Neutralization
Satire, parody, and humor op-eds (*The Onion, The Babylon Bee, McSweeney's*) intentionally use comedic hyperbole, absurd premises, and fictitious quotes that would otherwise trigger severe fallacy and sourcing penalties.

If content is verified as authentic satire:
$$\text{is\_satire} = \text{True} \implies S_{\text{calibrated}} = 0.0, \quad \text{Verdict} = \text{SATIRE\_PARODY}$$

### Cloaked Disinformation Safeguard (`SPJ-1.6`)
If malicious disinformation or defamatory claims attempt to hide behind a false "it was just satire/parody" defense:
$$\text{has\_cloaked\_disinfo} = \text{True} \implies \text{Bypass Satire Neutralization}, \quad \text{Verdict} = \text{CLOAKED\_DISINFORMATION}$$

---

## 6. Classification Decision Bands

```
 0.0          15.0               40.0              70.0              100.0
  [--- CLEAN ---]-- LOW SUSPICION --[-- SUSPICIOUS --]-- HIGH DECEPTION --]
```

- **`CLEAN`** ($0.0 \le S \le 15.0$): High epistemic integrity, verifiable claims, clear byline.
- **`LOW_SUSPICION`** ($15.0 < S \le 40.0$): Minor framing issues, weak sourcing, or mild informal fallacies.
- **`SUSPICIOUS`** ($40.0 < S \le 70.0$): Substantial logical fallacies, emotional manipulation, or deceptive UI elements.
- **`DECEPTIVE`** ($S > 70.0$): Critical dark patterns, systemic disinformation, ungrounded defamatory claims.
- **`SATIRE_PARODY`**: Explicit comedic/satirical parody (score neutralized to 0.0).
- **`CLOAKED_DISINFORMATION`**: Malicious disinformation masquerading as satire.
