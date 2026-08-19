---
title: Global Web Intelligence, DEI & Epistemic Weather
description: Technical specification for Domain Epistemic Index (DEI), Top 10 Violated
  Rules Aggregator, Macro Epistemic Weather, and Community Bounties.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Global Web Intelligence, DEI & Epistemic Weather

The Credence Web Epistemic Analytics engine aggregates thousands of signed webpage snapshot evaluations to produce macro-level epistemic intelligence across digital publishers and the open web.

---

## 1. Domain Epistemic Index ($DEI$) Specification

The **Domain Epistemic Index ($DEI$)** evaluates publisher reliability across all audited URLs for an origin domain:

$$\text{DEI} = 100 - \left( 0.50 \cdot \overline{S} + 0.30 \cdot \min(50, \overline{D}) + 0.20 \cdot (1 - R_{\text{byline}}) \cdot 100 \right)$$

### Metric Definitions

```mermaid
flowchart TD
    subgraph Inputs["Audited Domain Metrics"]
        S["Mean Suspicion Score S (0-100)<br/>Weight: 50%"]
        D["Suspicion Density D (Violations / 1k words)<br/>Weight: 30%"]
        B["Byline Transparency Ratio R_byline<br/>Weight: 20%"]
    end

    Inputs --> DEI["Domain Epistemic Index (DEI)<br/>0.0% to 100.0%"]

    DEI --> Bands{"Trust Band Classifier"}
    Bands -->|&ge; 85%| TB1["HIGH_INTEGRITY (Clean Record)"]
    Bands -->|65 - 84.9%| TB2["RELIABLE"]
    Bands -->|45 - 64.9%| TB3["MIXED"]
    Bands -->|25 - 44.9%| TB4["LOW_INTEGRITY"]
    Bands -->|&lt; 25%| TB5["DECEPTIVE (High Risk)"]
```

---

## 2. Topic Entropy & Astroturfing Defense

To prevent coordinated commercial PR or political botnets from artificially inflating domain reputation, Credence computes **Shannon Entropy ($H$)** over audited article titles:

$$H(X) = - \sum_{i=1}^{k} P(w_i) \log_2 P(w_i)$$

Alongside Top-3 Token Concentration:

$$C_{\text{top3}} = \frac{\sum_{j=1}^{3} \text{count}(w_j)}{\sum_{i=1}^{k} \text{count}(w_i)}$$

### Astroturf Alert Conditions
If a domain has $\ge 5$ audits and exhibits:
1. $H(X) < 0.30$ (low semantic diversity), OR
2. $C_{\text{top3}} > 0.40$ (excessive repetition of specific promotional keywords)

The engine flags the domain with `📢 Astroturf Alert`, demoting its ranking on the Epistemic Honor Roll.

---

## 3. Top Violated Rules Aggregator

The analytics engine scans all itemized `ViolationRecord` entities and cross-references them against active catalog taxonomies (SPJ Journalism Ethics, IEP Logical Fallacies, Deceptive Patterns):

```python
@dataclass
class RuleViolationMetric:
    rank: int
    rule_id: str
    rule_uri: str
    domain: str
    name: str
    total_violations: int
    percentage_of_all_audits: float
    avg_severity: float
    example_quote: str
    example_reasoning: str
```

### Retrieval Query
```bash
# FastMCP Resource
GET credence://rankings/rules

# REST API Endpoint
GET /api/rankings/rules?limit=10

# CLI Command
$ credence rankings --type rules --limit 10
```

---

## 4. Macro Epistemic Weather Barometer

The **Epistemic Weather Barometer** aggregates web-wide integrity metrics into a single climate indicator:

```mermaid
flowchart LR
    A["Web Audits Stream"] --> B["Global Integrity Score (0-100)"]
    B --> C["Climate States"]
    C --> D["☀️ CLEAR_SKIES (Score &ge; 85)"]
    C --> E["⛅ PARTLY_CLOUDY (Score 70-84)"]
    C --> F["☁️ OVERCAST_HAZE (Score 50-69)"]
    C --> G["⛈️ STORMY_DECEPTION (Score &lt; 50)"]
```

### Category Integrity Dials
Each high-level industry sector receives a dedicated integrity health percentage:
- **Science & Academic Preprints**: Peer review fidelity, unverified statistical claim detection.
- **Tech & Engineering**: Benchmark integrity, sponsored review disclosure.
- **General World & Local News**: Sourcing verification, headline clickbait calibration.
- **Health & Supplements**: Defamatory or unverified medical allegations.
- **Partisan Opinion & Commentary**: Ad hominem attacks, straw man logical fallacies.

---

## 5. Community Verification Bounties

Credence automatically generates **Verification Bounties** from syndicated RSS/Atom/JSON wire feeds when:
1. A breaking article is discovered with high priority (Tier 1/2 wire feeds).
2. The article has not yet reached swarm consensus ($\le 2$ node audits).
3. The content touches sensitive high-impact subjects (health, civic elections, financial markets).

```json
{
  "bounty_id": "bounty-491",
  "title": "Clinical Trial Results for Novel Respiratory Therapeutic",
  "url": "https://wire.reuters.com/health/therapeutic-results",
  "subject": "health.medical.clinical_trials",
  "urgency": "HIGH",
  "node_audits_count": 1,
  "target_consensus_nodes": 4
}
```

Nodes that prioritize evaluating open bounties earn accelerated progress toward the **Sifter Pioneer** and **Verified Auditor** merit badges.
