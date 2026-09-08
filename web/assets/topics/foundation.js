/**
 * Credence Workstation Info Topics: Foundation
 * Zero-npm native ES module.
 */

export const FOUNDATION_TOPICS = {
  taxonomies: {
    title: "Canonical Rule Catalogs (The Credence Rulebook)",
    icon: "📜",
    tag: "GOVERNANCE",
    tier1_plain_english: `
      <b>In plain words:</b> The official rulebook Credence uses to audit articles. 
      <br><br>
      It contains three standard rule catalogs:
      <br>• 📰 <b>Journalism Ethics (SPJ):</b> Checked for unsourced claims, misleading clickbait headlines, and stealth edits.
      <br>• 🧠 <b>Logical Fallacies (IEP):</b> Checked for flawed arguments like personal attacks and straw man reasoning.
      <br>• 🛑 <b>Deceptive UI Patterns:</b> Checked for hidden fees, guilt-trip buttons, and fake virus alerts.
    `,
    tier1_article: {
      title: "📘 Taxonomy Engineering Cookbook",
      desc: "How rule catalogs are written, calibrated, and cryptographically pinned.",
      url: "https://docs.credence.run/cookbooks/taxonomy-engineering"
    },
    tier2_mechanics: [
      "<b>Cryptographic Hash Pinning</b>: Each JSON rule catalog is locked with a SHA-256 hash so no one can silently change the rules.",
      "<b>Severity Weights</b>: Journalistic ethics (1.2x) and Deceptive Patterns (1.5x) carry higher penalties than informal fallacies (1.0x).",
      "<b>1-Click Real Examples</b>: Click '🔬 Find Real Examples' on any rule to jump directly to real articles exhibiting that violation."
    ],
    cli: "credence taxonomy list",
    math_proof: "Integrity Hash: SHA256(RFC8785(Catalog_JSON)) pinned in root seed manifest.",
    invariants: ["inv-verbatim-grounding", "inv-poes-law-satire", "inv-fixed-taxonomies"],
    links: [
      { label: "✍️ Poe's Law and the Satire Cloak", url: "https://blog.credence.run/poes-law-and-the-satire-cloak", desc: "Safeguarding humor while neutralizing malicious deceptive cloaking" }
    ]
  },

  spj_ethics: {
    title: "Society of Professional Journalists (SPJ) Code of Ethics",
    icon: "📰",
    tag: "ETHICAL STANDARD",
    tier1_plain_english: `
      <b>In plain words:</b> The gold standard of journalistic integrity used in professional newsrooms.
      <br><br>
      Credence checks 13 specific rules—such as whether a news story backs up its claims with named sources (SPJ-1.1), whether the headline matches what actually happened (SPJ-1.2), and whether corrections are clearly published when errors occur (SPJ-4.1).
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Buzzfeed News Doctrine",
      desc: "How digital newsrooms balance breaking speed with investigative sourcing rigor.",
      url: "https://blog.credence.run/the-buzzfeed-news-doctrine"
    },
    tier2_mechanics: [
      "<b>Core Rule Codes</b>: SPJ-1.1 (Unsourced Claims), SPJ-1.2 (Headline/Body Gap), SPJ-1.3 (Anonymous Attacks), SPJ-1.6 (Satire Cloaking), SPJ-4.1 (Stealth Edits).",
      "<b>Severity Range</b>: Scored from Severity 1 (Minor Advisory) to Severity 5 (Critical Fraud / Defamation).",
      "<b>1.2x Domain Weight</b>: Carries a 20% increased weight in overall suspicion calculations."
    ],
    cli: "credence taxonomy inspect SPJ",
    math_proof: "Weighted Impact: W_spj = 1.20 · Σ (Sev_i · GroundedMatch_i).",
    invariants: ["inv-verbatim-grounding", "inv-bittorrent-worksharing"],
    links: [
      { label: "📘 Taxonomy Engineering Cookbook", url: "https://docs.credence.run/cookbooks/taxonomy-engineering", desc: "Calibrating SPJ rule triggers and evidence thresholds" }
    ]
  },

  iep_fallacies: {
    title: "Internet Encyclopedia of Philosophy (IEP) Fallacies",
    icon: "🧠",
    tag: "LOGICAL RIGOR",
    tier1_plain_english: `
      <b>In plain words:</b> Spotting bad logic and manipulative arguments.
      <br><br>
      When an article insults a person instead of answering their point (<i>Ad Hominem</i>), invents a fake extreme position to argue against (<i>Straw Man</i>), or pretends there are only two choices (<i>False Dilemma</i>), Credence identifies the exact flawed reasoning.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Conflict of Pun-terest",
      desc: "How to distinguish playful wit and harmless satire from dishonest rhetorical deception.",
      url: "https://blog.credence.run/conflict-of-pun-terest"
    },
    tier2_mechanics: [
      "<b>15 Standard Fallacies</b>: IEP-1.1 (Ad Hominem), IEP-1.2 (Straw Man), IEP-1.3 (False Dilemma), IEP-2.1 (False Authority), IEP-3.1 (False Cause).",
      "<b>Context Awareness</b>: Differentiates healthy debate and irony from deliberate logical deception.",
      "<b>1.0x Domain Baseline</b>: Standard baseline weight in epistemic scoring."
    ],
    cli: "credence taxonomy inspect IEP",
    math_proof: "Fallacy Impact: W_iep = 1.00 · Σ (Sev_i · GroundedMatch_i).",
    invariants: ["inv-verbatim-grounding", "inv-topic-entropy-defense"],
    links: [
      { label: "📘 Mathematical Robustness Proofs", url: "https://docs.credence.run/tutorials/08-sybil-cartel-demolition", desc: "Mathematical dampening of rhetorical fallacies" }
    ]
  },

  deceptive_patterns: {
    title: "Deceptive UI Patterns & Consumer Protections",
    icon: "🛑",
    tag: "CONSUMER DEFENSE",
    tier1_plain_english: `
      <b>In plain words:</b> Protecting you from tricks and traps on websites.
      <br><br>
      Credence detects sneaky web tricks like hiding unexpected fees until the last page of checkout (<i>Drip Pricing</i>), making cancel buttons make you feel guilty (<i>Confirmshaming</i>), or displaying fake popup warnings that claim your computer is infected.
    `,
    tier1_article: {
      title: "✍️ Blueprint: Astroturfing Entropy & Dark Patterns",
      desc: "How coordinated deceptive funnels trick consumers across affiliate syndication networks.",
      url: "https://blog.credence.run/case-study-astroturfing-entropy"
    },
    tier2_mechanics: [
      "<b>8 Core Dark Patterns</b>: DEC-1.1 (Drip Pricing), DEC-1.2 (Confirmshaming), DEC-3.1 (Fake System Warnings), DEC-2.1 (Forced Continuity).",
      "<b>Highest Domain Weight (1.5x)</b>: Carries the steepest penalty due to direct consumer and financial harm.",
      "<b>Automated Microcopy Audits</b>: Scans button labels, pricing disclosures, and modal dialogues."
    ],
    cli: "credence taxonomy inspect DEC",
    math_proof: "Deceptive Impact: W_dec = 1.50 · Σ (Sev_i · GroundedMatch_i).",
    invariants: ["inv-web-component-zero-clone", "inv-zero-build-math"],
    links: [
      { label: "📘 Security Architecture & Threat Model", url: "https://docs.credence.run/blueprints/security-architecture-and-threat-model", desc: "Detecting clickjacking and deceptive interfaces" }
    ]
  },

  custody: {
    title: "Root Key Custody & Ed25519 Public Key Pinning",
    icon: "🔐",
    tag: "CRYPTOGRAPHIC ROOT",
    tier1_plain_english: `
      <b>In plain words:</b> The master cryptographic seal of the entire network.
      <br><br>
      Just like a government notary stamp or a wax seal on a historic document, every audit report is sealed with a digital key (<code>root.pub</code>). If anyone tries to alter a single letter of an audit, the digital seal breaks and the verification fails.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Blast Radius Containment",
      desc: "Why cryptographic seals protect historical audit receipts even if a single server goes down.",
      url: "https://blog.credence.run/blast-radius-containment-in-decentralized-networks"
    },
    tier2_mechanics: [
      "<b>Ed25519 High-Speed Signatures</b>: Tamper-proof Edwards-curve digital signatures with zero known backdoors.",
      "<b>Public Key Pinning</b>: Network root key is openly verifiable at <code>keys.credence.foundation/root.pub</code>.",
      "<b>Key Rotation Governance</b>: Structured multi-signature ceremony for upgrading keys without breaking past records."
    ],
    cli: "credence keygen --export-pubkey",
    math_proof: "Signature Scheme: PureEdDSA on Curve25519 with SHA-512 (RFC 8032). Key pinned at root.pub.",
    invariants: ["inv-canonical-json-ed25519", "inv-xml-safety"],
    links: [
      { label: "📘 Security Threat Model & Key Custody", url: "https://docs.credence.run/blueprints/security-architecture-and-threat-model", desc: "Cryptographic threat vectors, blast radius containment, and key rotation" }
    ]
  },

  canonical_json: {
    title: "RFC 8785 Canonical JSON Standard",
    icon: "📦",
    tag: "DATA INTEGRITY",
    tier1_plain_english: `
      <b>In plain words:</b> Making sure computers agree on exact formatting.
      <br><br>
      Different programming languages (Python, JavaScript, Go, Rust) format data slightly differently (extra spaces, different quote marks). RFC 8785 defines one universal, exact byte order so a digital signature matches 100% across every computer.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Beauty of Hermetic Environments",
      desc: "How deterministic byte serialization guarantees bit-for-bit parity across all platforms.",
      url: "https://blog.credence.run/the-beauty-of-hermetic-environments"
    },
    tier2_mechanics: [
      "<b>Alphabetical Key Ordering</b>: Object keys are strictly sorted by Unicode value.",
      "<b>Zero Extra Whitespace</b>: Strips out formatting spaces outside of string values.",
      "<b>Deterministic Float Precision</b>: Formats numbers consistently without scientific notation differences."
    ],
    cli: "credence canonicalize envelope.json",
    math_proof: "RFC 8785 Rule: CanonicalBytes(Obj_A) == CanonicalBytes(Obj_B) ⟺ Obj_A ≡ Obj_B.",
    invariants: ["inv-canonical-json-ed25519", "inv-4way-feature-parity"],
    links: [
      { label: "📘 Security Architecture & Threat Model", url: "https://docs.credence.run/blueprints/security-architecture-and-threat-model", desc: "Canonical JSON specifications and cross-runtime test gauntlets" }
    ]
  },

  governance: {
    title: "Living Invariant Canon & Governance RFCs",
    icon: "⚖️",
    tag: "CONSTITUTION",
    tier1_plain_english: `
      <b>In plain words:</b> The constitution of the Credence system.
      <br><br>
      These are the permanent rules (called <i>System Invariants</i>) that every developer, AI agent, and server must follow. Rules can only be changed through open proposals (RFCs) and multi-node community consensus.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Scaling System Invariants Without Prompt Bloat",
      desc: "How shift-left automated tests enforce rules without overwhelming AI memory.",
      url: "https://blog.credence.run/scaling-system-invariants-without-prompt-bloat"
    },
    tier2_mechanics: [
      "<b>The Invariant Bible</b>: The living canon of universal non-negotiable architectural laws governing every file and turn.",
      "<b>4-Phase Release Lifecycle</b>: Local QA Gate → Mk1 Eyeball Review → Version Release → /learn Retrospective → Patch Release.",
      "<b>Dynamic Invariant Scalability</b>: Never hardcoding static numerical counts in public web portals."
    ],
    cli: "credence invariants audit",
    math_proof: "Byzantine Quorum for RFC Ratification: Consensus ≥ 66.7% (2f+1 honest votes).",
    invariants: ["inv-mk1-eyeball", "inv-order-of-operations", "inv-version-governance"],
    links: [
      { label: "📘 Invariant Scalability & Knowledge Governance", url: "https://docs.credence.run/blueprints/invariant-scalability-and-knowledge-governance", desc: "3-tier scalable invariant architecture and context economy" },
      { label: "📘 The Living Invariant Canon", url: "https://docs.credence.run/invariants", desc: "Complete mathematical proofs and non-negotiable guardrails" }
    ]
  },

};
