---
title: 'Epistemic Protocol Specification: Domain Reputation, Soft Quarantine & Redemption (EPEP-17)'
description: Technical protocol specification for domain reputation tracking, exponential polling backoff, HRW adversarial swarm coordination, and the BuzzFeed News Doctrine.
since_version: v1.21.0
verified_version: v1.21.1
last_verified: '2026-08-19'
---

# Epistemic Protocol Specification: Domain Reputation, Soft Quarantine & Redemption (EPEP-17)

## 1. Abstract

This specification defines the protocol, mathematical state machine, and distributed invariants for **Domain Reputation, Soft Quarantine Backoff, and Asymmetric Bayesian Redemption (The BuzzFeed News Doctrine)** in the Credence decentralized trust network.

Autonomous nodes operate under a dual-drive epistemic ingestion engine:
1. **Positive Soil Expansion ($\mathcal{S}^+$, weight $\rho$)**: Discovering authoritative primary sources cited by verified clean articles.
2. **Adversarial Inoculation ($\mathcal{S}^-$, weight $1 - \rho$)**: Preemptively caching signed Ed25519 attestations for viral deceptive campaigns and mapping deceptive syndication rings.

---

## 2. State Machine & Transition Invariants

```mermaid
stateDiagram-v2
    [*] --> NEUTRAL: New Domain Discovered (R = 50.0)
    NEUTRAL --> TRUSTED: k &ge; 3 Clean Audits (R &ge; 75.0)
    NEUTRAL --> SUSPICIOUS: Suspicion &ge; 50.0 (R &lt; 50.0)
    
    TRUSTED --> SUSPICIOUS: Severity 4/5 Finding or G &lt; 1.00
    SUSPICIOUS --> QUARANTINED: Deceptions &ge; 3 OR R &le; 20.0
    
    state QUARANTINED {
        [*] --> EXPONENTIAL_BACKOFF: Polling Backoff 16x-64x
        EXPONENTIAL_BACKOFF --> LAZARUS_PROBE: HRW Rendezvous Sample (1 item / 7d)
        LAZARUS_PROBE --> EXPONENTIAL_BACKOFF: Fails Audit (Backoff Resets to Max)
        LAZARUS_PROBE --> PROBATIONARY_RECOVERY: k = 5 Clean Audits across &ge; 2 Namespaces
    }
    
    QUARANTINED --> PROBATIONARY_RECOVERY: BuzzFeed Doctrine Invariant 40
    PROBATIONARY_RECOVERY --> NEUTRAL: Stable Audits (R &ge; 50.0, Polling 1x)
    PROBATIONARY_RECOVERY --> QUARANTINED: Any Severity &ge; 3 Violation (Immediate Relapse)
```

### 2.1 Asymmetric Bayesian Scoring Update Rule

Let $R_t \in [0.0, 100.0]$ denote the domain reputation score at audit step $t$:

$$\Delta R_{\text{down}} = -15.0 \times \left( \frac{\text{MaxSeverity}}{2.0} \right) \times \text{Confidence}$$

$$\Delta R_{\text{up}} = +5.0 \times \left( 1.0 - \frac{\text{SuspicionScore}}{100.0} \right)$$

### 2.2 Exponential Polling Backoff Factor

For domains in `QUARANTINED_PROBATION`, syndicated feed polling intervals scale exponentially:

$$T_{\text{poll}}(d) = T_{\text{base}} \times 2^{\min(\text{consecutive\_deceptions}, 6)}$$

Where $T_{\text{base}} = 900\text{s}$ ($15\text{ minutes}$), bounding the maximum backoff to $64.0\times$ ($16\text{ hours}$ to $7\text{ days}$).

---

## 3. The BuzzFeed News Doctrine (Redemption Protocol)

To prevent permanent blindspots and recognize authentic editorial reform:

1. **Lazarus Sampling Probe**: When token headroom $\mathcal{H}_{\text{daily}} \ge 50\%$, the Boredom Engine samples at most 1 item per cycle from quarantined feeds.
2. **Diversity Constraint**: To graduate from `QUARANTINED_PROBATION` to `PROBATIONARY_RECOVERY`, a domain must accumulate:
   - $k \ge 5$ consecutive clean audits ($\text{SuspicionScore} \le 20.0, G=1.00$).
   - Spanning $|\text{Subjects}| \ge 2$ distinct subject namespaces.
   - Verified verbatim quote grounding ($G = 1.00$).
3. **Relapse Circuit Breaker**: If any audit during `PROBATIONARY_RECOVERY` triggers a grounded violation with $\text{Severity} \ge 3$, the domain relapses immediately to `QUARANTINED_PROBATION` with maximum backoff ($64.0\times$) and $0\%$ progress.

---

## 4. Swarm Rendezvous Coordination (Anti-Stampede)

In multi-node P2P mesh swarms, adversarial investigation targets are partitioned using **Highest Random Weight (HRW) Hashing**:

$$\mathcal{N}^* = \arg\max_{i \in \text{Peers}} H\left( k_i \parallel \text{candidate\_url} \right)$$

Only node $\mathcal{N}^*$ executes the live LLM audit; all other peer nodes adopt the signed Ed25519 attestation at $\$0.00$ token cost via gossip diffusion within $<400\text{ms}$.
