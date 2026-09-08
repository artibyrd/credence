---
name: forensic-audit
description: Antigravity-native forensic auditing for multi-pass epistemics, cluster swarms (3-6 rules/pass), verbatim DOM grounding (G=1.00), longitudinal sourcing ratios (R_byline, ASI, DCI), and taxonomy state drift detection.
---

# Forensic Auditing & Cluster-Swarm Protocol Skill

Use this skill when auditing web content, investigating local news publications, measuring publisher sourcing ratios, evaluating advertorial blurring, or verifying taxonomy version staleness.

---

## Core Commands
- `credence audit <url> --driver=agent`: Audit an article using Antigravity agent tokens and reasoning.
- `credence audit <url> --driver=ai-studio`: Audit an article using Google AI Studio / Gemini API.
- `credence audit <url> --check-staleness`: Verify if article was audited against an older taxonomy state.
- `credence audit <url> --incremental-delta`: Re-audit only the specific clusters that changed since the last audit.
- `just audit <url> [driver]`: Quick wrapper for executing audits.
- `just audit-stale [domain]`: Detect and re-audit stale articles across a domain.
- `just sentinel-audit <feed_url>`: Batch audit a publication feed under the forensic swarm.
- `just publish-attestations`: Reseal and broadcast signed attestations to dev and prod mesh nodes.

---

## Granular Cluster-Level Swarm Architecture
Audits are partitioned at the bounded `TaxonomyCluster` level (3–6 rules per specialist micro-agent pass):
1. **Fallacy Specialists**:
   - *Relevance & Personal Attacks* (`FALLACY-1.x`: Ad Hominem, Tu Quoque, Poisoning Well, Genetic Fallacy)
   - *Presumption & Circularity* (`FALLACY-2.x`: Begging Question, False Dilemma, Loaded Question, Cherry-Picking)
   - *Causal & Inductive Errors* (`FALLACY-3.x`: Post Hoc, Correlation/Causation, Hasty Generalization, Slippery Slope)
   - *Distortion & Authority* (`FALLACY-4.x`: Straw Man, Red Herring, False Authority, Emotional Appeal)
2. **Ethics Specialists**:
   - *Truth & Sourcing Provenance* (`SPJ-1.x`: Unsourced Claims, Headline Distortion, Blotter Reliance, Selective Omission)
   - *Independence & Governance COI* (`SPJ-3.x`: Conflict of Interest, Commercial Commingling, Distinguish News from Advertising)
   - *Harm Minimization & Accountability* (`SPJ-2.x`, `SPJ-4.x`: Privacy, Byline Transparency, Correction Acknowledgments)
3. **Deception Specialists**:
   - *Commercial Camouflage & Disguised Funnels* (`DEC-1.x`: Native Advertorials, Staff Byline Masking Sponsor)
   - *Urgency & Astroturfing Payload* (`DEC-1.4`, `AST-1.x`: Fake Urgency, Hidden Directories, Link Stuffing)
4. **Domain Specialists**:
   - *Municipal Governance*, *Clinical Evidence*, etc.

---

## Forensic Sourcing Ratios & Epistemic Formulas
- **Byline Transparency**: $R_{\\text{byline}} = \\frac{N_{\\text{named}}}{N_{\\text{total}}}$ ($100.0$ for named authors, $0.0$ for generic/staff handles).
- **Single-Source Blotter Ratio**: $R_{\\text{single}} = \\frac{N_{\\text{single}}}{N_{\\text{total}}}$ ($100.0$ if relying exclusively on law enforcement blotter/wire pass-through).
- **Conflict of Interest Exposure**: $R_{\\text{COI}} = \\frac{N_{\\text{unrecused}}}{N_{\\text{civic}}}$ ($100.0$ if unrecused governance/business conflict present).
- **Advertorial Separation Index**: $ASI = 100.0 - (\\sum \\text{Violations}_{\\text{advertorial}} \\times 15.0)$.
- **Domain Credence Index**: $\\text{DCI} = 100.0 - (0.50 \\cdot S_{\\text{recency}} + 0.30 \\cdot D + 0.20 \\cdot (1 - R_{\\text{byline}}) \\cdot 100)$.

## 5-Tier Domain Credence Index (DCI) Standard
The DCI framework evaluates publisher integrity across 5 calibrated trust tiers:

| Tier | Score Range | Classification | Theme Color | Representative Behavior |
| :--- | :---: | :--- | :---: | :--- |
| **Tier A** | $\ge 90.0$ | **Pristine / High Integrity** | `#22c55e` (Green) | Multi-sourced investigative reporting, transparent corrections, independent funding |
| **Tier B** | $80.0 - 89.9$ | **Reliable / Certified** | `#38bdf8` (Cyan) | High journalistic standards, named bylines, clear disclosure of affiliations |
| **Tier C** | $65.0 - 79.9$ | **Monitored / Mixed** | `#fbbf24` (Amber) | Mixed newsroom reality (75% clean news, 15% blotters, 10% advertorials/COI) |
| **Tier D** | $45.0 - 64.9$ | **Watchlist / Low Integrity** | `#f97316` (Orange) | Heavy clickbait, opaque bylines, frequent unverified aggregation |
| **Tier E** | $< 45.0$ | **Deceptive / Quarantine** | `#ef4444` (Crimson) | Undisclosed sponsored campaigns, astroturfing, financial scams, malware traps |
| **Satire** | *N/A* | **Satire / Parody** | `#c084fc` (Purple) | Transparent satire/parody protected under Poe's Law with zero penalty |

---

## Monotonic Article Verdict Bands ($S \in [0, 100]$)
All article suspicion scores strictly map to standardized verdict bands and UI badges:
- $0.0 \le S \le 15.0 \implies \mathbf{CLEAN}$ (`#22c55e`, Green tint)
- $15.0 < S \le 40.0 \implies \mathbf{LOW\_SUSPICION}$ (`#38bdf8`, Cyan tint)
- $40.0 < S \le 70.0 \implies \mathbf{SUSPICIOUS}$ (`#f59e0b`, Amber tint)
- $S > 70.0 \implies \mathbf{DECEPTIVE}$ (`#ef4444`, Crimson tint)
- `is_satire = true` $\implies \mathbf{SATIRE\_PARODY}$ (`#c084fc`, Purple tint)

---

## 4-Way Source Provenance Classification
Articles in publisher dossiers and live analytics are distinctly attributed to their authentic provenance:
1. 🌱 **Genesis Seeder** (`#a855f7`, Purple): Cryptographically sealed ground-truth seed articles.
2. 📡 **Sentinel Feed** (`#38bdf8`, Cyan): Automated high-priority background feed ingestion.
3. 🌐 **P2P Mesh** (`#22c55e`, Green): Authenticated peer node consensus submissions.
4. 💻 **CLI / Manual** (`#fbbf24`, Amber): Operator-submitted manual audits.

---

## Continuous Seed Cohort Sizing ($N \ge 50$)
To prevent cherry-picking bias during local news investigations, seed cohorts must include at least $N = 50$ articles spanning:
- $\ge 70\%$ standard clean civic/general news
- $\ge 15\%$ single-source police blotters / wire pass-throughs
- $\ge 10\%$ sponsored advertorials, op-eds, or governance conflict case studies

---

## Strict Grounding & Invariant Guardrails
- **`inv-verbatim-grounding` ($G=1.00$)**: Cited quotes must match source text character-for-character with zero synthetic prefix drift. Hallucinations incur an autonomous 50% score slash.
- **`inv-topic-entropy-defense` ($H < 0.30$)**: Detect astroturfing coordination by measuring penalized Shannon entropy:
  $$H_{\text{penalized}} = H \times (1 - C_{\text{top3}})$$
  where $H$ is normalized token entropy and $C_{\text{top3}}$ is top-3 token concentration. If $H_{\text{penalized}} < 0.30$, flag payload repetition. Neutralize satire ($0.00$), and invoke `SPJ-1.6` overrides on verified factual allegations.
- **`inv-canonical-json-ed25519`**: Attestations are sealed over RFC 8785 canonical bytes and signed with the node's Ed25519 identity key. Whenever audited content or classifications are updated, attestations must be systematically re-signed.
- **`inv-cart-before-horse`**: Taxonomy state root hashing runs before dispatching micro-agents.

