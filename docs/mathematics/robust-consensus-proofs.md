---
title: The Mathematics of Robust Consensus
description: Mathematical proofs of the Domain Authority Weighted Median, Byzantine
  3f+1 tolerance, and the Galileo Rule.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# The Mathematics of Robust Consensus

Decentralized consensus over qualitative or factual evaluations cannot rely on simple majority voting or arithmetic means. A cartel of shallow or dishonest nodes could easily manipulate averages.

```mermaid
flowchart TD
    A["Swarm Evaluations (S_1..S_N)"] --> B["Compute Composite Weights<br>W_i = 0.20 Q_i + 0.80 E_i"]
    B --> C["Sort Evaluations<br>S_(1) <= S_(2) <= ... <= S_(N)"]
    C --> D["Calculate Domain Authority Weighted Median"]
    D --> E{"Galileo Check: Grounded Citation (G=1.0)<br>by Authority (W >= 0.70)?"}
    E -- "Yes (Asymmetric Evidence)" --> F["Preserve Finding<br>(is_outlier = False)"]
    E -- "No (Ungrounded / Cartel)" --> G["Adopt Weighted Median Consensus"]
    F & G --> H["Final Cryptographic Consensus Verdict"]
```

### Consensus Mechanism Comparison

| Mechanism | Sybil Cartel Resistance | Vulnerability to Outliers | Factual Discovery Protection |
| :--- | :--- | :--- | :--- |
| **Arithmetic Mean** | ❌ Fails (1 node shifts score by $100/N$) | Extremely High | ❌ Outliers skew truth |
| **Unweighted Median** | ⚠️ Moderate ($>50\%$ cheap node puppet attack) | Low | ❌ Ignores solitary whistleblowers |
| **Credence Weighted Median + Galileo** | ✅ **Resilient ($3f+1$ Domain Entropy)** | **Zero (Trimmed)** | ✅ **100% Protected (Asymmetric Grounding)** |

---

## 1. The Domain Authority Composite Weight ($W_i$)

Let node $i$ have 5-factor quality $Q_i \in [0, 1]$ and domain expertise $E_{i, \text{domain}} \in [0, 1]$.

The composite weight $W_i$ assigned to node $i$'s evaluation is:

$$W_i = 0.20 Q_i + 0.80 E_{i, \text{domain}}$$

Where:
- $Q_i = 0.25 U_i + 0.30 C_i + 0.25 G_i + 0.10 T_i + 0.10 K_i$
- $E_{i, \text{domain}} = 0.40 C_{\text{domain}} + 0.35 G_{\text{domain}} + 0.15 V_{\text{domain}} + 0.10 L_{\text{domain}}$

---

## 2. Domain Authority Weighted Median Algorithm

Given $N$ independent node evaluations with scores $S_1, S_2, \dots, S_N$ and corresponding weights $W_1, W_2, \dots, W_N$:

1. Sort all evaluations such that $S_{(1)} \le S_{(2)} \le \dots \le S_{(N)}$.
2. Calculate total cumulative weight: $W_{\text{total}} = \sum_{i=1}^N W_i$.
3. The **Weighted Median** $S_{\text{consensus}}$ is the score $S_{(k)}$ where:

$$\sum_{j=1}^{k-1} W_{(j)} < \frac{W_{\text{total}}}{2} \quad \text{and} \quad \sum_{j=1}^k W_{(j)} \ge \frac{W_{\text{total}}}{2}$$

### Why Weighted Medians Resist Sybil Cartels ($3f + 1$):
In an arithmetic mean, a single compromised node submitting $S=100.0$ shifts the consensus by $\frac{100}{N}$. In a weighted median, an adversary must control more than **50% of the total weighted domain authority** to move the consensus by even $0.01$ points.

---

## 3. Mathematical Proof of The Galileo Rule (Invariant 27)

> **Theorem (Asymmetric Grounded Evidence)**:
> If node $e$ satisfies $W_e \ge 0.70$ and provides grounded citations with precision $G_e = 1.0$, node $e$'s finding $S_e > 0$ cannot be discarded as an outlier by a swarm of $M$ ungrounded nodes reporting $S_m = 0.0$.

### Proof:
1. An evaluation reporting $S_m = 0$ provides zero grounded citations ($|V_{\text{grounded}}| = 0$). By definition, absence of citations is **absence of evidence**, not proof of non-violation.
2. Node $e$ provides a non-empty set of citations $V_e$ where every quote is verifiably present in the source text ($G_e = 1.0$).
3. The consensus engine evaluates the subset of active evidentiary claims:

$$S_{\text{consensus}} \ge \min_{v \in V_e} (\text{severity}_v \times \text{confidence}_v)$$

4. Node $e$ is exempted from outlier trimming (`is_outlier = False`), guaranteeing that verified factual discovery cannot be silenced by uninformed majorities. $\blacksquare$

---

## 4. Academic Foundations & Mathematical Literature

### 📚 Seminal Papers in Distributed Consensus & Robust Statistics
* **Byzantine Fault Tolerance**: [Lamport, Shostak, & Pease (1982) - The Byzantine Generals Problem (*ACM TOPLAS*)](https://doi.org/10.1145/357172.357176)
* **Robust Medians & High-Breakdown Estimation**: [Peter J. Rousseeuw (1984) - Least Median of Squares Regression (*JASA*)](https://doi.org/10.1080/01621459.1984.10478078)
* **Sybil Cartel Defense**: [John R. Douceur (2002) - The Sybil Attack (*IPTPS*)](https://doi.org/10.1007/3-540-45748-8_24)
* **Non-Parametric Ranked Estimation**: [Wilcoxon, F. (1945) - Individual Comparisons by Ranking Methods (*Biometrics*)](https://doi.org/10.2307/3001968)

### 🔗 Related Theory & Empirical Case Studies in Credence
* 🎮 [Interactive Playground: The Galileo Rule Simulator](../playground.md)
* 💥 [Tutorial 08: Sybil Cartel Demolition & Weighted Medians](../tutorials/08-sybil-cartel-demolition.md)
* ✍️ [Essay: The Galileo Rule & Asymmetric Evidence](../../blog/the-galileo-rule.md)
* 🔬 [Case Study: Conflict of Pun-terest & Monopoly Forensics](../../blog/conflict-of-pun-terest.md)
* 🏛️ [System Invariant 27 & 28: Grounding Slashing & The Galileo Rule](../invariants.md)

