---
name: forensic-audit
description: Antigravity-native forensic auditing workflow for deep multi-pass epistemics, granular cluster-level specialist swarms (3-6 rules per pass), verbatim DOM grounding (G=1.00), longitudinal sourcing ratio calculations (R_byline, R_single, R_COI, ASI, DCI), and automated taxonomy state drift detection.
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

---

## Strict Grounding & Invariant Guardrails
- **`inv-verbatim-grounding` ($G=1.00$)**: Cited quotes must match source text character-for-character with zero synthetic prefix drift.
- **`inv-canonical-json-ed25519`**: Attestations are sealed over RFC 8785 canonical bytes and signed with the node's Ed25519 identity key.
- **`inv-cart-before-horse`**: Taxonomy state root hashing runs before dispatching micro-agents.
