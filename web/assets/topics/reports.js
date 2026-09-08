/**
 * Credence Workstation Info Topics: Reports Lab
 * Zero-npm native ES module.
 */

export const REPORTS_TOPICS = {
  search: {
    title: "Epistemic Query & Multi-Criteria Search",
    icon: "🔍",
    tag: "FORENSICS",
    tier1_plain_english: `
      <b>In plain words:</b> This is your search engine for truth on the web. Instead of just searching for keywords like Google does, Credence checks whether an article gives real evidence for its claims.
      <br><br>
      You can paste any web link (like a news story or blog post), type a headline, or search for specific red flags (like <i>"Unsourced Claims"</i> or <i>"Ad Hominem Attacks"</i>) to see an instant forensic audit.
    `,
    tier1_article: {
      title: "📰 Real-World Example: Clean Energy Transition (Reuters)",
      desc: "See how a high-trust news report passes all journalistic checks with zero red flags.",
      url: "../credence.report/index.html?query=reuters"
    },
    tier2_mechanics: [
      "<b>Multi-Criteria Search</b>: Filter articles by Rule Code (e.g. <code>SPJ-1.1</code>), Risk Tier (A to D), or Severity (1 to 5).",
      "<b>Live Web Ingestion</b>: Pasting an HTTP/HTTPS URL triggers immediate text extraction, DOM stripping, and statement evaluation.",
      "<b>Universal Parity</b>: Identical results are returned whether you use this web page, the terminal CLI, or Claude/Cursor FastMCP."
    ],
    cli: "credence audit https://reuters.com/world/energy/clean-grid-transition-2026",
    math_proof: null,
    invariants: ["inv-verbatim-grounding", "inv-fastmcp-datetime-serialization"],
    links: [
      { label: "📘 CLI Scripting & Search Guide", url: "https://docs.credence.run/integrations/cli-scripting-guide", desc: "Automate batch evaluations and headless search queries" },
      { label: "🧪 Interactive Playground", url: "https://docs.credence.run/playground", desc: "Simulate adversarial payloads and cloaking in-browser" }
    ]
  },

  backup: {
    title: "Sovereign Database Backup & Cold-Boot Recovery",
    icon: "💾",
    tag: "STORAGE GRAVITY",
    tier1_plain_english: `
      <b>In plain words:</b> Credence safeguards all of your evaluations, snapshots, and node trust scores so you never lose work.
      <br><br>
      It creates compact, compressed backups with cryptographic checksums. If a server restarts or crashes, it automatically restores your data in less than a quarter of a second.
    `,
    tier1_article: {
      title: "📘 Architectural Blueprint: Sovereign Data Gravity & CAS Portability",
      desc: "How Credence ensures sovereign node data custody and zero-effort re-evaluation.",
      url: "https://docs.credence.run/blueprints/sovereign-data-gravity-and-cas-portability"
    },
    tier2_mechanics: [
      "<b>Atomic SQLite Snapshots</b>: Uses the SQLite Backup API with WAL truncation to ensure zero-lock snapshots.",
      "<b>SHA-256 Manifests & Ed25519 Signatures</b>: Every backup archive is hashed and signed with the node's sovereign private key.",
      "<b>Cold-Boot Auto Restore</b>: Pre-boot lifespan hook downloads the latest cloud backup before initialization in &lt;200ms."
    ],
    cli: "credence db backup --output /data/backups/credence_latest.db.gz",
    math_proof: "Archive Integrity: SHA256(Gzip(SQLite)) == Manifest.sha256_hash verified under Ed25519(CanonicalJSON(Manifest)).",
    invariants: ["inv-canonical-json-ed25519", "inv-4way-parity-symmetric-web"],
    links: [
      { label: "📘 Sovereign Data Gravity Blueprint", url: "https://docs.credence.run/blueprints/sovereign-data-gravity-and-cas-portability", desc: "CAS portability and SQLite-to-PostgreSQL storage architecture" },
      { label: "📘 Cloud Run Deployment & Ops", url: "https://docs.credence.run/deployment-cloudrun", desc: "Automated container lifecycle and cloud backup hooks" }
    ]
  },

  boredom: {
    title: "Autonomous Epistemic Boredom Engine",
    icon: "🌀",
    tag: "AUTONOMOUS INGESTION",
    tier1_plain_english: `
      <b>In plain words:</b> When your node is idling and has extra token budget available, it gets 'bored' and goes hunting for new knowledge.
      <br><br>
      It checks RSS feeds, audits breaking news, and balances 60% clean sources with 40% adversarial probes to discover deceptive tactics.
    `,
    tier1_article: {
      title: "📘 Curiosity Loop Architecture & Dual-Soil Ingestion",
      desc: "How autonomous agents maintain high-velocity truth detection within token ceilings.",
      url: "https://docs.credence.run/blueprints/sovereign-data-gravity-and-cas-portability"
    },
    tier2_mechanics: [
      "<b>Dual-Soil Balancing</b>: Partitions ingestion into 60% trusted sources and 40% adversarial/probationary probes.",
      "<b>Token Headroom Circuit Breakers</b>: Automatically sleeps when daily spend exceeds 70% of safety limit.",
      "<b>Zero-Token Mesh Dedup</b>: Adopts existing peer attestations from the P2P gossip swarm at $0.00 token cost."
    ],
    cli: "credence boredom --force",
    math_proof: "Curiosity Equilibrium: Harvest(t) = 0.60 * S_clean + 0.40 * S_adversarial constrained by Headroom(t) >= 0.30.",
    invariants: ["inv-multi-model-sovereignty", "inv-production-telemetry-boundary"],
    links: [
      { label: "📘 Feed Ingestion & Boredom Guide", url: "https://docs.credence.run/tutorials/09-zero-trust-feed-sifter-digest", desc: "Autonomous ingestion daemons and background tasks" }
    ]
  },

  browse: {
    title: "Curated Audit Directory & Case Studies",
    icon: "📚",
    tag: "GROUND TRUTH",
    tier1_plain_english: `
      <b>In plain words:</b> Think of this as a verified library of real-world test cases. It contains audited articles from major wire services, local investigative papers, scientific journals, and satire websites.
      <br><br>
      It helps you explore how different types of writing are graded—showing you clear examples of pristine reporting, sneaky stealth edits, disguised ads, and protected parody humor.
    `,
    tier1_article: {
      title: "📰 Real-World Case Study: Sriracha Solar Flares (The Onion)",
      desc: "Explore why legitimate satire is protected and receives a 0.0 suspicion score.",
      url: "../credence.report/index.html?query=onion"
    },
    tier2_mechanics: [
      "<b>Quick Category Filters</b>: Switch between Clean Wire, Flagged Violations, Satire Neutralized, and Local Beats.",
      "<b>Golden 12 Benchmark Alignment</b>: Built from our standard test gauntlet measuring precision, recall, and cross-entropy.",
      "<b>Session Pinning & Dossiers</b>: Pin sources directly to your active sidebar to compare publishers side-by-side."
    ],
    cli: "credence benchmark --profile balanced",
    math_proof: "Cross-Entropy: H(P, Q) = -Σ P(x) log Q(x) evaluated across Free, Balanced, and Ultra inference profiles.",
    invariants: ["inv-canonical-json-ed25519", "inv-playwright-rendering-tests"],
    links: [
      { label: "📘 Golden 12 Benchmark Blueprint", url: "https://docs.credence.run/tutorials/10-reusable-live-e2e-and-mesh-gauntlet", desc: "Precision, recall, and cross-entropy evaluation gauntlet" },
      { label: "✍️ The Blue Checkmark is Dead", url: "https://blog.credence.run/the-blue-checkmark-is-dead", desc: "Why cryptographic receipts replace centralized platform trust badges" },
      { label: "✍️ The Pareto Frontier of Truth", url: "https://blog.credence.run/the-pareto-frontier-of-truth", desc: "Balancing false positives with high-severity evasion detection" }
    ]
  },

  lensing: {
    title: "3-Tier Epistemic Lensing Hierarchy",
    icon: "🔬",
    tag: "COGNITIVE ARCHITECTURE",
    tier1_plain_english: `
      <b>In plain words:</b> We don't overwhelm you with raw data all at once. We organize information like a pyramid with three lenses:
      <br><br>
      1. <b>Surface Glance:</b> Look at the score and verdict in 1 second.<br>
      2. <b>Focus Evidence:</b> Read the exact highlighted quotes and rule violations in 10 seconds.<br>
      3. <b>Deep Spectrum:</b> Inspect cryptographic digital signatures and mathematical proofs when you need forensic certainty.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Scoring the Lens, Not the Window",
      desc: "How structured cognitive depth prevents auditor fatigue and information overload.",
      url: "https://blog.credence.run/scoring-the-lens-not-the-window"
    },
    tier2_mechanics: [
      "<b>Lens 1 (Glance)</b>: Circular score dial (0–100), trust badge (Tier A–D), and a 1-sentence verdict with zero math.",
      "<b>Lens 2 (Evidence)</b>: Exact quoted sentences matching the source page character-for-character, plus rule violation tags.",
      "<b>Lens 3 (Forensic Proof)</b>: In-browser WebCrypto attestation, Ed25519 digital signatures, and RFC 8785 canonical bytes."
    ],
    cli: "credence audit <url> --lens focus",
    math_proof: "Information Pyramid Invariant: Depth(L1) ⊂ Evidence(L2) ⊂ CryptographicProof(L3). Strict zero-redundancy across layers.",
    invariants: ["inv-information-pyramid-lensing", "inv-verbatim-grounding"],
    links: [
      { label: "📘 Epistemic Lensing Technical Blueprint", url: "https://docs.credence.run/blueprints/information-pyramid-and-epistemic-lensing", desc: "Full architectural specification of the 3-tier cognitive hierarchy" },
      { label: "🧪 Interactive Lensing Simulator", url: "https://docs.credence.run/playground", desc: "Test real-time switching across Surface, Focus, and Spectrum lenses" }
    ]
  },

  score: {
    title: "Epistemic Suspicion Score (0.0 – 100.0)",
    icon: "📊",
    tag: "SCORING METRIC",
    tier1_plain_english: `
      <b>In plain words:</b> Like a golf score, lower is better. 
      <br><br>
      • <b>0 to 15 (Tier A - Pristine):</b> Clean, honest, factual news backed by verified primary sources.<br>
      • <b>15 to 40 (Tier B - Low Suspicion):</b> Minor sourcing gaps or uncorroborated quotes.<br>
      • <b>40 to 75 (Tier C - Suspicious):</b> Flawed logic, anonymous attacks, or unlabelled advertorial framing.<br>
      • <b>75 to 100 (Tier D - Quarantine):</b> Severe deception, fake error popups, or manipulative scams.
    `,
    tier1_article: {
      title: "📰 Real-World Example: Miracle Elixir Health Claim",
      desc: "See how an unverified medical claim gets flagged with an 84.5 Tier D quarantine score.",
      url: "../credence.report/index.html?query=clinical"
    },
    tier2_mechanics: [
      "<b>Severity Multipliers</b>: Violations range from Severity 1 (Minor Advisory) to Severity 5 (Critical Fraud / Defamation).",
      "<b>Satire Neutrality</b>: Protected comedy & parody automatically receive a 0.0 score.",
      "<b>Satire Cloaking Override</b>: If a satire disguise is used to make defamatory or false health claims, protection is overridden (SPJ-1.6)."
    ],
    cli: "credence score <url>",
    math_proof: "S = min(100, Σ (w_i · severity_i · domain_multiplier)). Satire: S = 0.0 unless SPJ-1.6 cloaking override triggered.",
    invariants: ["inv-topic-entropy-defense", "inv-poes-law-satire"],
    links: [
      { label: "📘 Scoring & Thresholds Blueprint", url: "https://docs.credence.run/walkthroughs/01-auditing-webpages-and-text", desc: "Mathematical formulations, severity weights, and threshold boundaries" },
      { label: "✍️ The Pareto Frontier of Truth", url: "https://blog.credence.run/the-pareto-frontier-of-truth", desc: "Balancing false positive rates with high-severity evasion detection" }
    ]
  },

  grounding: {
    title: "Verbatim Empirical Grounding (G = 1.00)",
    icon: "🎯",
    tag: "INTEGRITY GUARANTEE",
    tier1_plain_english: `
      <b>In plain words:</b> This is our zero-hallucination guarantee. 
      <br><br>
      Whenever Credence points out a flaw in an article, it must quote the <b>exact sentence</b> character-for-character from the web page. An AI is never allowed to make up or paraphrase evidence. If it does, its evaluation is instantly thrown out.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Confessions of a Bored AI",
      desc: "How strict character-for-character grounding eliminates synthetic hallucinations.",
      url: "https://blog.credence.run/confessions-of-a-bored-ai"
    },
    tier2_mechanics: [
      "<b>Character-for-Character Exactness</b>: Quotes must match the source web page text exactly after basic whitespace collapse.",
      "<b>Anti-Hallucination Slashing</b>: Nodes that produce fake or altered quotes lose 50% of their network reputation immediately.",
      "<b>Cryptographic DOM Offsets</b>: Exact start and end character positions are signed directly into the verification receipt."
    ],
    cli: "credence audit <url> --verify-grounding",
    math_proof: "Grounding Exactness: G = |Quote_cited ∩ DOM_source| / |Quote_cited| = 1.000. Rejects any G < 1.00.",
    invariants: ["inv-verbatim-grounding", "inv-canonical-json-ed25519"],
    links: [
      { label: "📘 Living Invariant Canon", url: "https://docs.credence.run/invariants", desc: "Mathematical proofs and non-negotiable guardrails" }
    ]
  },

  temporal_diff: {
    title: "Bitwise Temporal Diff & Stealth Edit Forensics",
    icon: "⏱️",
    tag: "TEMPORAL FORENSICS",
    tier1_plain_english: `
      <b>In plain words:</b> Catching silent edits after a story is published.
      <br><br>
      When an author quietly changes a headline, deletes a quote, or rewrites a factual claim without telling readers, Credence compares snapshots over time and highlights the exact stealth modifications in red and green.
    `,
    tier1_article: {
      title: "📰 Real-World Case Study: The Stealth City Council Rewrite",
      desc: "See how a silent modification to local zoning vote tallies was caught by temporal diffing.",
      url: "../credence.report/index.html?query=municipal"
    },
    tier2_mechanics: [
      "<b>SimHash-64 Locality Hashing</b>: Computes bitwise similarity between historical snapshots of an article.",
      "<b>SPJ-4.1 Stealth Edit Detection</b>: Flags substantive narrative rewrites that lack reader correction notices.",
      "<b>Signed Revision History</b>: Every captured snapshot is timestamped and cryptographically signed."
    ],
    cli: "credence diff <url> --snap-a <id1> --snap-b <id2>",
    math_proof: "Hamming Distance: d_H(SimHash(t_0), SimHash(t_1)) = Σ (b_0 ⊕ b_1). Drift flagged when d_H > 3 bits without correction.",
    invariants: ["inv-bittorrent-worksharing", "inv-version-governance"],
    links: [
      { label: "📘 Temporal Content Evolution Lab", url: "https://docs.credence.run/lab-content-evolution", desc: "Inspect live multi-snapshot diff trajectories and stealth edit flags" },
      { label: "📘 SimHash Mirror Detection Mathematics", url: "https://docs.credence.run/lab-content-evolution", desc: "Mathematical proof of 64-bit Hamming distance thresholds" }
    ]
  },

  webcrypto: {
    title: "Native W3C WebCrypto In-Browser Verification",
    icon: "🧪",
    tag: "CRYPTOGRAPHY",
    tier1_plain_english: `
      <b>In plain words:</b> You don't have to trust our servers. 
      <br><br>
      Your own web browser verifies the digital signatures in less than 1 millisecond using built-in browser cryptography. You can check the math right on your computer without installing anything.
    `,
    tier1_article: {
      title: "📘 Frontend Zero-Build Architecture",
      desc: "How Credence runs client-side cryptographic verification with zero npm packages.",
      url: "https://docs.credence.run/feature-parity"
    },
    tier2_mechanics: [
      "<b>Native Browser Crypto</b>: Uses standard <code>window.crypto.subtle.verify</code> with pure Ed25519 keys.",
      "<b>RFC 8785 Canonical JSON</b>: Formats data identically across all programming languages to prevent key mismatches.",
      "<b>Zero Backend Reliance</b>: Verification executes completely client-side in your browser tab."
    ],
    cli: "credence verify-envelope envelope.json",
    math_proof: "PureEdDSA Verification: Verify(K_pub, M_rfc8785, Sig_Ed25519) ∈ {0, 1}. Executed in-memory in <0.3ms.",
    invariants: ["inv-canonical-json-ed25519", "inv-zero-build-standards"],
    links: [
      { label: "📘 Security Architecture & Threat Model", url: "https://docs.credence.run/blueprints/security-architecture-and-threat-model", desc: "Dual-crypto conformance and key rotation ceremonies" }
    ]
  },

  dossier: {
    title: "Publisher Epistemic Dossier & Track Record",
    icon: "🏛️",
    tag: "REPUTATION PROFILE",
    tier1_plain_english: `
      <b>In plain words:</b> Like a restaurant inspection grade for news websites and publishers.
      <br><br>
      Instead of judging a publisher by a single story, the dossier looks at their long-term track record over months—tracking how often they get facts right, how quickly they issue corrections, and whether they publish undisclosed advertorials.
    `,
    tier1_article: {
      title: "✍️ Empirical Case Study: Conflict of Pun-terest",
      desc: "Investigating undisclosed councilmember co-ownership, native advertorial marketing, and police press release republishing in local journalism.",
      url: "https://dev.credence.run/blog/conflict-of-pun-terest"
    },
    tier2_mechanics: [
      "<b>Longitudinal Track Record</b>: Aggregates verified audit scores across all stories published by this domain.",
      "<b>Epistemic Integrity Classifications</b>: Detects conflicts of interest (COI), ungrounded claims, and sponsored content masquerading as reporting.",
      "<b>Direct Article Access</b>: Inspect individual articles in the 3-tier lensing inspector or open standalone reports in the viewer."
    ],
    cli: "credence dossier inmaricopa.com",
    invariants: ["inv-production-telemetry-boundary", "inv-verbatim-anti-truncation"],
    links: [
      { label: "📝 Conflict of Pun-terest Case Study", url: "https://dev.credence.run/blog/conflict-of-pun-terest", desc: "Longitudinal investigation of local publisher ownership conflicts and native advertorials" },
      { label: "📘 Domain Epistemic Index Blueprint", url: "https://docs.credence.run/blueprints/domain-epistemic-index-and-sourcing-forensics", desc: "Bayesian reputation mechanics, domain normalization, and DCI scoring" },
      { label: "🏛️ The Living Invariant Canon", url: "https://docs.credence.run/invariants", desc: "Epistemic grounding, anti-truncation, and verbatim source invariants" }
    ]
  },

  dci: {
    title: "Domain Credence Index (DCI) Honor Roll",
    icon: "🏆",
    tag: "ECOSYSTEM RANKINGS",
    tier1_plain_english: `
      <b>In plain words:</b> The public leaderboard of web publishers ranked by factual accuracy.
      <br><br>
      You can sort publishers by their average suspicion score, total verified articles, or trust tier to see which outlets consistently uphold high journalistic standards.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: BitTorrent Economics of Fact-Checking",
      desc: "How decentralized peer incentives create unbiased publisher rankings without corporate gatekeepers.",
      url: "https://blog.credence.run/bittorrent-economics-of-fact-checking"
    },
    tier2_mechanics: [
      "<b>Interactive Column Sorting</b>: Click any table header to sort publishers ascending or descending.",
      "<b>Trust Tiers</b>: Tier A (0–15 Pristine), Tier B (15–40 Low Risk), Tier C (40–75 Watchlist), Tier D (75–100 Quarantine).",
      "<b>Clean Table Design</b>: Displays only meaningful, actionable metrics per publisher."
    ],
    cli: "credence dci top --limit 20",
    math_proof: "Rank Order: Sort by DCI_score DESC, AvgSuspicion ASC. Laplace Smoothing: α_prior = 1.0, β_prior = 1.0.",
    invariants: ["inv-cloudflare-assets", "inv-progressive-disclosure"],
    links: [
      { label: "📘 Terminology & Ontology Lexicon", url: "https://docs.credence.run/blueprints/terminology-and-ontology-lexicon", desc: "Comprehensive definition of trust bands and scoring scales" },
      { label: "📘 Robust Consensus Proofs", url: "https://docs.credence.run/tutorials/08-sybil-cartel-demolition", desc: "Mathematical theorems on Byzantine consensus resilience" }
    ]
  },

  sifter: {
    title: "Sifter Continuous Syndication Stream",
    icon: "📡",
    tag: "STREAM INGESTION",
    tier1_plain_english: `
      <b>In plain words:</b> An automated scout that constantly scans news feeds.
      <br><br>
      Instead of waiting for people to search, the Sifter continuously monitors RSS and Atom feeds, flags breaking stories, and checks whether new articles contain misleading claims.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Boredom Engine and Expanding Roots",
      desc: "How automated curiosity helps discover emerging news publishers before they go viral.",
      url: "https://blog.credence.run/the-boredom-engine-and-expanding-roots"
    },
    tier2_mechanics: [
      "<b>Curiosity Loop</b>: Triggers candidate exploration when news cycles enter repetitive echo chambers.",
      "<b>Security Defenses</b>: Blocks SSRF network probes and XML entity bombs before parsing feeds.",
      "<b>Budget Protection</b>: Automatically pauses background scans when daily AI spending reaches safety limits."
    ],
    cli: "credence sifter stream --interval 300",
    math_proof: "Boredom Score: B(t) = 1.0 - CosineSimilarity(Embedding_latest, Centroid_window). Explores when B(t) > 0.65.",
    invariants: ["inv-ssrf-defense", "inv-4k-thinking-budget"],
    links: [
      { label: "📘 Morning Feed Sifter Cookbook", url: "https://docs.credence.run/cookbooks/morning-feed-sifter", desc: "Setup automated headless RSS monitoring pipelines" }
    ]
  },

};
