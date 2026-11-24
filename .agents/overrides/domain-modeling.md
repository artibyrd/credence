# Domain Modeling — Credence Project Overlay

Self-contained Credence domain-terminology and ADR policy. Applies automatically on top of `domain-modeling` when `antigravity-customizations` is installed, and serves as a standalone Credence domain-modeling guide on any agent harness.

---

## Overrides

- **Canonical Domain Glossary Location (D6):** Credence maintains its authoritative ubiquitous language in `credence-docs/docs/blueprints/terminology-and-ontology-lexicon.md` rather than a root `GLOSSARY.md`. Always consult `terminology-and-ontology-lexicon.md` before minting new entity names, scoring metrics, or epistemic taxonomy terms.
- **Living Invariants vs. Historical Blueprints & ADRs:**
  - Active cross-cutting system invariants live in `AGENTS.md` (Tier 0, `<800` tokens), `credence/tests/governance/` (Tier 2), and `credence-docs/docs/invariants.md` (The Invariant Bible, Tier 3).
  - Architecture blueprints live in `credence-docs/docs/blueprints/`.
  - Immutable historical ADRs (`docs/adr/NNNN-*.md`) are adopted lazily only when future hard-to-reverse architectural trade-offs meet the 3-criteria ADR gate.

---

## Extensions

### 1. Credence Core Domain Primitives & Naming Laws
- **Verdict & Integrity Vocabulary:** `Snapshot`, `EvaluationReport`, `TaxonomyCluster`, `AttestationEnvelope`, `DomainCredenceIndex` (DCI), `AdvertorialSeparationIndex` (ASI), `PeerMetricRecord`, `NodeQuality` ($Q_i$).
- **Calculation Prefix (`compute_*`):** Every pure domain metric calculation MUST be named `compute_*` (enforced by `test_compute_naming_ontology_invariant`).
- **Tenant Decoupling (`inv-sovereign-config-decoupling`):** Core domain models, database schemas, and daemons MUST contain zero hardcoded publisher or tenant domains; inject tenant feeds strictly via environment variables (`CREDENCE_SENTINEL_FEEDS`) or org manifests.
- **Canonical Serialization (`inv-canonical-json-ed25519`):** Domain envelopes that cross trust boundaries (attestations, mempool claims, RFC standard catalogs) MUST serialize deterministically via RFC 8785 canonical JSON prior to SHA-256 hashing and Ed25519 signing.

---

## Disabled / Not Applicable

- **Pre-Scaffolding `GLOSSARY.md` or Empty `docs/adr/`:** Do not create a duplicate root `GLOSSARY.md` (use `credence-docs/docs/blueprints/terminology-and-ontology-lexicon.md`), and do not pre-create empty `docs/adr/` directories before an ADR is actually authored.
