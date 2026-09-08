/**
 * Credence Workstation Info Topics: Nexus NOC
 * Zero-npm native ES module.
 */

export const NEXUS_TOPICS = {
  topology: {
    title: "Decentralized P2P Mesh Topology & Byzantine Quorum",
    icon: "🕸️",
    tag: "P2P MESH",
    tier1_plain_english: `
      <b>In plain words:</b> A cooperative network of independent computers that verify news together.
      <br><br>
      Instead of one big tech company deciding what is true, hundreds of independent computers vote on evidence. Even if some computers are broken or dishonest, the network still reaches the correct truth.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Testing 13-Node Swarms on a Raspberry Pi",
      desc: "How we tested a cluster of 13 independent nodes running locally with zero memory leaks.",
      url: "https://blog.credence.run/testing-13-node-swarms-on-a-raspberry-pi"
    },
    tier2_mechanics: [
      "<b>Byzantine Fault Tolerance</b>: Formula: f = ⌊(N-1)/3⌋. Scales smoothly from a single laptop (f=0) to huge networks.",
      "<b>Highest Random Weight (HRW) Hashing</b>: Automatically splits incoming articles across nodes without any central master server.",
      "<b>Production vs Simulation</b>: The live dashboard only shows genuine running computers—not fake simulations."
    ],
    cli: "credence mesh status",
    math_proof: "HRW Rendezvous Function: Node_assigned(URL) = argmax_i ( HMAC-SHA256(Node_i.pubkey, URL) ).",
    invariants: ["inv-byzantine-cartel-resistance", "inv-edge-canonicalization"],
    links: [
      { label: "📘 Mesh Architecture Technical Blueprint", url: "https://docs.credence.run/walkthroughs/03-p2p-mesh-consensus", desc: "P2P protocol specification, HRW rendezvous routing, and gossip sync" },
      { label: "🧪 Interactive Mesh Playground", url: "https://docs.credence.run/playground", desc: "Simulate Byzantine partition attacks and cartel isolation in-browser" }
    ]
  },

  byzantine: {
    title: "Byzantine Fault Tolerance & Quorum Formulation",
    icon: "🛡️",
    tag: "CONSENSUS MATHEMATICS",
    tier1_plain_english: `
      <b>In plain words:</b> The math that makes the network impossible to rig or cheat.
      <br><br>
      Think of a jury where at least two-thirds of the jurors must agree with hard physical evidence before a verdict is signed. Even if bad actors set up fake computers to vote dishonestly, they cannot overpower the honest majority.
    `,
    tier1_article: {
      title: "📘 Robust Consensus Proofs Mathematics",
      desc: "Full mathematical proof of Byzantine cartel resistance and fault tolerance.",
      url: "https://docs.credence.run/tutorials/08-sybil-cartel-demolition"
    },
    tier2_mechanics: [
      "<b>The 2f+1 Quorum Rule</b>: Requires agreement from at least 2f+1 honest nodes out of 3f+1 total nodes.",
      "<b>Sybil Cartel Defense</b>: Prevents attackers from creating thousands of fake computers to cheat votes.",
      "<b>Standalone Mode</b>: When you are running 1 node alone (N=1), it works completely on your local computer."
    ],
    cli: "credence mesh quorum",
    math_proof: "Quorum Condition: |V_ratified| ≥ 2f + 1 where f = ⌊(N-1)/3⌋. Total nodes N ≥ 3f + 1.",
    invariants: ["inv-byzantine-cartel-resistance", "inv-galileo-rule"],
    links: [
      { label: "✍️ Blast Radius Containment", url: "https://blog.credence.run/blast-radius-containment-in-decentralized-networks", desc: "Decentralized containment of compromised nodes" }
    ]
  },

  gossip: {
    title: "Live P2P Gossip Stream & Peer Protocol",
    icon: "📡",
    tag: "GOSSIP PROTOCOL",
    tier1_plain_english: `
      <b>In plain words:</b> How computers quickly share verified audits with each other.
      <br><br>
      When one computer finishes verifying a story, it whispers the result to a few neighboring computers, who whisper it to their neighbors. Within a split second, every node in the world has the new verification receipt.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Real-Time Mesh Observability",
      desc: "How ultra-lightweight gossip protocols broadcast verifications without slowing down networks.",
      url: "https://blog.credence.run/real-time-mesh-observability"
    },
    tier2_mechanics: [
      "<b>Epidemic Dissemination</b>: Information spreads across the entire world in O(log N) quick rounds.",
      "<b>Zero Duplicate Waste</b>: Memory filters prevent computers from re-sending information they've already shared.",
      "<b>Airgapped Sneakernet Support</b>: Can also sync data via USB drives when internet access is unavailable."
    ],
    cli: "credence mesh gossip --tail",
    math_proof: "Gossip Latency: T_sync = O(log N) rounds with fanout k=3 peers per cycle.",
    invariants: ["inv-canonical-json-ed25519", "inv-byzantine-cartel-resistance"],
    links: [
      { label: "📘 Mesh Architecture Technical Blueprint", url: "https://docs.credence.run/walkthroughs/03-p2p-mesh-consensus", desc: "WebSocket transport, gossip payloads, and reconnection backoff" }
    ]
  },

  qi_scoring: {
    title: "5-Factor Node Quality Score (Qᵢ)",
    icon: "🏆",
    tag: "NODE QUALITY METRIC",
    tier1_plain_english: `
      <b>In plain words:</b> A report card for computers participating in the verification network.
      <br><br>
      Computers earn high scores by staying online, agreeing with verified facts, never making up quotes, and having a good reputation. Computers with high scores are trusted more during consensus votes.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Gamifying Truth Without the Casino",
      desc: "How decentralized peer quality scores reward factual accuracy without crypto speculation.",
      url: "https://blog.credence.run/gamifying-truth-without-the-casino"
    },
    tier2_mechanics: [
      "<b>5 Score Components</b>: Uptime (30%), Consensus Alignment (25%), Exact Grounding (20%), Subject Reputation (15%), Peer Review (10%).",
      "<b>Instant 50% Slash</b>: Any computer caught making up evidence loses half its reputation score immediately.",
      "<b>Fast Health Checks</b>: Nodes must respond to /health checks in under 850 milliseconds."
    ],
    cli: "credence mesh score <node_id>",
    math_proof: "Q_i = 0.30·U_i + 0.25·C_i + 0.20·G_i + 0.15·R_i + 0.10·P_i where Q_i ∈ [0, 1]. Slashing penalty: Q_i = 0.50·Q_i on hallucination.",
    invariants: ["inv-5factor-node-quality", "inv-empirical-expertise", "inv-verbatim-grounding"],
    links: [
      { label: "📘 Terminology & Ontology Lexicon", url: "https://docs.credence.run/blueprints/terminology-and-ontology-lexicon", desc: "Quality formulations and epoch reward schedules" },
      { label: "📘 Robust Consensus Proofs", url: "https://docs.credence.run/tutorials/08-sybil-cartel-demolition", desc: "Mathematical proofs of cartel resistance and quality convergence" }
    ]
  },

  vitals: {
    title: "Node Health, Memory & Scale-to-Zero Vitals",
    icon: "👤",
    tag: "COMPUTE PLANE",
    tier1_plain_english: `
      <b>In plain words:</b> Keeping our cloud servers fast, lightweight, and low-cost.
      <br><br>
      When no one is using the server, it automatically goes to sleep ($0 cost). When someone requests an audit, it wakes up instantly in under 850 milliseconds with fresh memory.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Taming the 10-Second Cold Start",
      desc: "How we reduced Cloud Run server startup time from 10 seconds down to 850ms.",
      url: "https://blog.credence.run/taming-the-10-second-cold-start-scale-to-zero"
    },
    tier2_mechanics: [
      "<b>Sub-Second Cold Starts</b>: Google Cloud Run Gen 2 container optimization with Startup CPU Boost and precompiled bytecode.",
      "<b>Hermetic Memory Ceilings</b>: Prevents out-of-memory crashes even when processing huge batches of articles.",
      "<b>Direct Execution</b>: Bypasses slow shell scripts to respond to /health checks in <850ms."
    ],
    cli: "credence doctor",
    math_proof: "Cold Start Target: T_germinate < 850ms. Memory Footprint Target: RSS < 180MB at idle.",
    invariants: ["inv-hermetic-testing", "inv-dense-workstation-viewport"],
    links: [
      { label: "📘 Cloud Run Scale-to-Zero Blueprint", url: "https://docs.credence.run/blueprints/cloudrun-scale-to-zero-cold-start-optimization", desc: "Sub-40s deployment, WIF keyless auth, and scale-to-zero tuning" },
      { label: "✍️ From 860MB to 2MB: Sub-40s CI/CD Pipeline", url: "https://blog.credence.run/from-860mb-to-2mb-sub-40s-cicd-pipeline", desc: "Ultra-compact build artifacts and container optimization" }
    ]
  },

  telemetry: {
    title: "Interface Telemetry Loopback Protocol (ITLP-v1)",
    icon: "🩺",
    tag: "TELEMETRY STANDARD",
    tier1_plain_english: `
      <b>In plain words:</b> The dashboard's live pulse monitor.
      <br><br>
      Every few seconds, the dashboard asks the node for a tiny status update (<500 bytes) checking memory, CPU, and network health—without relying on heavy third-party monitoring tools.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Interface Telemetry Loopback",
      desc: "Designing resilient, zero-dependency telemetry for decentralized edge nodes.",
      url: "https://blog.credence.run/interface-telemetry-loopback"
    },
    tier2_mechanics: [
      "<b>Ultra-Lightweight Polling</b>: Standard HTTP GET /health and /api/telemetry returning <500 bytes.",
      "<b>Continuous Health Monitoring</b>: Tracks memory usage, event loop latency, and database connection pools.",
      "<b>Self-Healing Failover</b>: Switches to local offline cache if upstream servers become unreachable."
    ],
    cli: "credence telemetry",
    math_proof: "Telemetry Envelope: { status: 'HEALTHY', role: 'LOCAL_PRIMARY_ROOT', mode: 'STANDALONE', grounding_quotient: 1.00 }.",
    invariants: ["inv-xml-safety", "inv-dense-workstation-viewport"],
    links: [
      { label: "📘 Node & Mesh Telemetry Blueprint", url: "https://docs.credence.run/blueprints/node-and-mesh-telemetry-dashboard", desc: "Diagnostic schema and real-time dashboard instrumentation" }
    ]
  },

  badges: {
    title: "Dynamic SVG Merit Badges & Manifest",
    icon: "🛡️",
    tag: "ATTESTATION BADGES",
    tier1_plain_english: `
      <b>In plain words:</b> Live truth badges that news websites can put on their pages.
      <br><br>
      Unlike static image badges that anyone could Photoshop, these are dynamic vector graphics linked to genuine cryptographic verification receipts with zero tracking cookies.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Red-Teaming the Truth Badge",
      desc: "Simulating attacks: How vector badges resist spoofing, clickjacking, and cache poisoning.",
      url: "https://blog.credence.run/red-teaming-the-truth-badge"
    },
    tier2_mechanics: [
      "<b>Anti-Tamper SVG Badges</b>: Embeddable Web Components showing real-time trust scores with zero user tracking.",
      "<b>P2P Seed Discovery</b>: Automatically finds peers using decentralized seed lists and DNS records.",
      "<b>Custom Organizations</b>: News organizations can host private badge registries using <code>credence init-org</code>."
    ],
    cli: "credence badge generate --domain reuters.com",
    math_proof: "SVG Signature: Anti-tamper digest embedded directly in SVG DOM comment metadata: <!-- credence-sig: 0x... -->.",
    invariants: ["inv-web-component-zero-clone", "inv-verbatim-grounding"],
    links: [
      { label: "📘 Embeddable Badges & Anti-Tamper Blueprint", url: "https://docs.credence.run/blueprints/embeddable-attestation-badges-and-anti-tamper", desc: "Embeddable HTML5 custom elements and CSP-compliant badges" }
    ]
  },

  seeds: {
    title: "P2P Seed Manifest & Bootstrap Discovery",
    icon: "🌱",
    tag: "PEER DISCOVERY",
    tier1_plain_english: `
      <b>In plain words:</b> How a new computer finds friends on the network.
      <br><br>
      When you start a new Credence node for the first time, it checks a cryptographically signed seed list (<code>peers.json</code>) to connect to initial peers and join the global mesh.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Miracle-Gro for Truth Nodes",
      desc: "How decentralized peer discovery seeds cold networks in seconds.",
      url: "https://blog.credence.run/miracle-gro-for-truth-nodes"
    },
    tier2_mechanics: [
      "<b>Signed Seed Lists</b>: Seed lists are cryptographically signed by root authority keys.",
      "<b>DNS-SRV Backup</b>: Automatically falls back to DNS records if seed server links are down.",
      "<b>Decentralized Mesh Handoff</b>: Once connected, nodes discover new peers and no longer rely on seeds."
    ],
    cli: "credence mesh seeds",
    math_proof: "Seed Verification: Verify(Root_pub, Manifest_bytes, Manifest_sig) == true before accepting peer endpoints.",
    invariants: ["inv-canonical-json-ed25519", "inv-byzantine-cartel-resistance"],
    links: [
      { label: "📘 DNS-SRV Discovery Blueprint", url: "https://docs.credence.run/tutorials/05-mesh-quickstart", desc: "Automating zero-coordinator mesh discovery" }
    ]
  },

  operator_admin: {
    title: "Operator Security Cockpit & Headroom Governor",
    icon: "🛠️",
    tag: "OPERATIONS",
    tier1_plain_english: `
      <b>In plain words:</b> The budget and safety control panel for node operators.
      <br><br>
      It ensures you never get a surprise cloud bill by automatically reserving at least 30% of your daily AI budget for critical emergencies, pausing non-essential background tasks when quota runs low.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: FinOps as Epistemology",
      desc: "Why strict token budgeting and cost controls are essential defenses against spam attacks.",
      url: "https://blog.credence.run/finops-as-epistemology"
    },
    tier2_mechanics: [
      "<b>30% Safety Reserve</b>: Halts low-priority background queues when daily token quota drops below 30% (<code>QUOTA_PRESERVED</code>).",
      "<b>Gemini 3.7 Flash Reference Engine</b>: Uses 4k thinking tokens to balance forensic accuracy with fast, low-cost execution.",
      "<b>Zero Secret Keys in CI/CD</b>: Keyless authentication across Dev and Prod environments."
    ],
    cli: "credence admin status",
    math_proof: "Circuit Breaker Condition: If Headroom(Tokens_daily) < 0.30, BackgroundQueue.halt() -> return QUOTA_PRESERVED.",
    invariants: ["inv-multi-model-sovereignty", "inv-4k-thinking-budget"],
    links: [
      { label: "📘 Operator Security & Workstation Tutorial", url: "https://docs.credence.run/tutorials/14-operator-security-and-admin-workstation", desc: "Managing cost governors, circuit breakers, and administrative tokens" },
      { label: "✍️ The Economics of Epistemic Headroom", url: "https://blog.credence.run/the-economics-of-epistemic-headroom", desc: "Mathematical models for token preservation under adversarial burst traffic" }
    ]
  },

  miracle_gro: {
    title: "Miracle-Gro Seed Germination Engine",
    icon: "🌱",
    tag: "CACHE WARMING",
    tier1_plain_english: `
      <b>In plain words:</b> Pre-loading the database so searches are instant.
      <br><br>
      When a developer sets up a new node, Miracle-Gro automatically audits top news sources (like Reuters and AP) and saves the results locally, so your first search takes 0 milliseconds.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Miracle-Gro for Truth Nodes",
      desc: "Accelerating cold-start cache performance across decentralized node clusters.",
      url: "https://blog.credence.run/miracle-gro-for-truth-nodes"
    },
    tier2_mechanics: [
      "<b>Cold-Start Seeding</b>: Pre-populates clean wire services so searches get instant 0ms cache hits.",
      "<b>Configurable Burst Sizes</b>: Operators configure bursts (1 to 25 articles) to stay strictly within daily spending limits.",
      "<b>Local SQLite Storage</b>: Evaluated receipts are signed and stored locally on disk."
    ],
    cli: "credence seed --burst 10",
    math_proof: "Germination Batch Size: N_burst ∈ [1, 25]. Cache Hit Latency: T_hit < 2ms.",
    invariants: ["inv-4k-thinking-budget", "inv-multi-model-sovereignty"],
    links: [
      { label: "📘 Developer Quickstart Guide", url: "https://docs.credence.run/quickstart", desc: "Seeding local environments with one-command bootstrap" }
    ]
  },

  daemons: {
    title: "Ingestion Stream Daemons & Crawlers",
    icon: "🔄",
    tag: "DAEMON ENGINE",
    tier1_plain_english: `
      <b>In plain words:</b> Background robot assistants that keep the database up to date.
      <br><br>
      They quietly poll RSS news feeds, discover new websites linked in citations, and verify breaking news stories in the background while you work.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Boredom Engine and Expanding Roots",
      desc: "Designing curiosity algorithms that explore outside news echo chambers.",
      url: "https://blog.credence.run/the-boredom-engine-and-expanding-roots"
    },
    tier2_mechanics: [
      "<b>Sifter Daemon</b>: Polls registered RSS/Atom feeds every 15 minutes for new stories.",
      "<b>Roots Crawler</b>: Discovers new publisher websites by checking links cited in verified articles.",
      "<b>Boredom Loop</b>: Automatically explores novel topics when the news cycle becomes repetitive."
    ],
    cli: "credence daemon start --all",
    math_proof: "Polling Cadence: T_sifter = 900s, T_roots = 3600s, T_boredom = 1800s.",
    invariants: ["inv-ssrf-defense", "inv-boredom-root-expansion"],
    links: [
      { label: "📘 Morning Feed Sifter Cookbook", url: "https://docs.credence.run/cookbooks/morning-feed-sifter", desc: "Configuring systemd daemons and headless scrapers" }
    ]
  }
};
