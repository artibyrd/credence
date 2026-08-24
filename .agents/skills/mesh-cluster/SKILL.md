---
name: mesh-cluster
description: Dynamic P2P mesh peering (N >= 1, f = floor((N-1)/3)), local 13-node Watts-Strogatz benchmark testing, Byzantine Sybil cartel isolation (3f+1), and playground chaos simulation.
---

# P2P Mesh Cluster & Peering Orchestration Skill

Use this skill when orchestrating, monitoring, or testing the decentralized P2P mesh network topology.

## Architectural Boundary
- **Live Production Telemetry**: Reflects actual dynamic nodes ($N \ge 1$) from `PeerMetricRecord` and local node identity. When $N=1$, operates in `STANDALONE` mode ($f=0$). Byzantine quorum activates dynamically when $N \ge 4$ ($f = \lfloor (N-1)/3 \rfloor$). Never expose mock data or simulation buttons on production consoles.
- **Node Naming & Multi-Environment Identity**: Nodes resolve authoritative aliases (`Settings.effective_node_alias`):
  - **Production (`ENV=production`)**: `credence-prod-us-central1`
  - **Development (`ENV=development`)**: `credence-dev-us-central1`
  - **Local Default**: `credence-local-anchor` (or custom `--name` / `--alias` CLI flag).
- **Multi-Node Vitals Inspection**: Nexus NOC (`credence.nexus`) supports interactive node click-through on both topology canvas and leaderboard rows, switching to Tab 3 ("Node Vitals") with a dynamic Inspected Node Selector to inspect local daemon metrics vs remote peer validator stats.
- **Chaos Playground (`playground.md`)**: Dedicated 5-scenario 13-node Watts-Strogatz chaos simulation engine (Normal, Barbell Split, 3f+1 Sybil Eclipse, Genesis Seed Failover, Epidemic Burst) for interactive exploration and training.
- **Local Test Benchmark**: Canonical 13-node Watts-Strogatz lattice ($N=13, d=4, \beta=0.20, f=4$) used for hermetic pytest execution (`test_mesh_cluster.py`).

## Core Commands
- `just mesh-cluster-up`: Launch 13-node cluster with `hardware_guard.py` memory pre-flight.
- `just test -k mesh_cluster`: Execute hermetic cluster tests in pytest.
- `credence serve --name my-custom-anchor`: Start server engine with custom node alias.
- `credence mesh --port 8765 --seed wss://relay.credence.nexus:8765`: Start an interactive relay node.
- `credence stats --mesh`: Inspect live swarm peering health and dynamic Byzantine quorum state.

## Network Topology Invariants
- **Benchmark Topology**: Watts-Strogatz small-world lattice ($N = 13$, degree $d = 4$, rewiring $\beta = 0.20$).
- **Byzantine Resilience**: $N \ge 3f + 1$ ($N = 13, f = 4$) cartels isolated.
- **Resource Constraints**: Hard `mem_limit: 128m` Docker cgroups per container; hardware guard throttles on $<2\text{GB}$ RAM hosts.
- **Pathological Scenarios**: Linear Daisy Chain TTL exhaustion, Barbell Netsplit partition recovery, Sybil Eclipse attack isolation, and Star topology flood control.

## Concurrent Swarm Testing Best Practices
- **Session Isolation**: When executing concurrent node tasks (`asyncio.gather(*tasks)`), always provision independent `AsyncSession` instances per node using `async_sessionmaker(bind=engine)` to prevent session flush race conditions.
- **Rendezvous Verification**: Verify that concurrent swarm nodes prioritize distinct feeds by asserting non-overlapping feed polling sequences across heterogeneous node pubkeys (`compute_feed_affinity(node_pubkey, feed_url)`).
- **P2P Cross-Adoption**: Verify that newly audited articles in node bursts are gossiped via `MeshGossipRelay.broadcast_attestation` and adopted by peer nodes at $0.00 token cost via `check_mesh_effort_avoidance`.

## Standards Governance Red-Team Testing (`test_mesh_rfc_redteam.py`)
- **Quorum Consensus ($N=13$)**: Tests 13 honest nodes reaching $\ge 66.7\%$ Byzantine Quorum or $\ge 70.0\%$ Domain-Weighted Quorum.
- **Byzantine Cartel Attack Defense**: Simulates 4 colluding Byzantine nodes ($f=4, 3f+1=13$) attempting to force-ratify malicious/overbroad rules. 9 honest nodes reject and protect Content-Addressed Storage ($30.77\% < 66.7\%$).
- **Headroom Floor Circuit Breaker**: Nodes operating under quota pressure ($<40\%$ token headroom) reject shadow trial canaries with `QUOTA_PRESERVED`.
- **Temporal Trajectory DAG Immutability**: Verifies that upgrading standards (e.g. `v1.0.0` $\to$ `v2.0.0`) preserves bit-for-bit cryptographic verification of historical receipts under original CAS digests.

