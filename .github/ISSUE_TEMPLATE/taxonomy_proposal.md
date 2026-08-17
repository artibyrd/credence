---
name: Taxonomy Rule Proposal
about: Propose a new epistemic rule catalog or modification to existing rules
title: "[TAXONOMY] "
labels: ["taxonomy", "rules"]
assignees: []
---

**Rule Catalog & Domain**
- Catalog ID: (e.g. `medical-sourcing`, `financial-disclosure`)
- Domain: (e.g. `JOURNALISTIC_ETHICS`, `SCIENTIFIC_GROUNDING`, `FINANCIAL_DISCLOSURE`)
- Version: (e.g. `v1.0.0`)

**Proposed Rule Specification**
- **Rule ID**: `DOMAIN-X.Y`
- **Namespaced URI**: `domain:cluster/RULE-ID@v1.0.0`
- **Title**: Short human-readable summary
- **Severity**: [1 to 5]
- **Base Suspicion Weight**: [0.0 to 100.0]

**Description & Violation Criteria**
What constitutes a direct violation of this rule?

**Grounded Citation Extraction Rule**
How should the grounded quote validator extract deterministic character substrings from the DOM?

**Adversarial / Satire Considerations**
Does this rule interact with Poe's Law or satire cloaking? (Refer to Invariants 13 & 28).
