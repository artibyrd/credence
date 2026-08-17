# Tutorial 06: The 13-Node Chaos Lab: Watts-Strogatz Lattice & Netsplit Resiliency

Launch the local 13-node Watts-Strogatz small-world mesh cluster, inspect live epidemic gossip diffusion, and simulate Barbell netsplits and Byzantine cartels.

---

## 1. Pre-Flight Check & Cluster Launch

Run the single Just command to pre-flight system RAM/CPU and launch 13 peer containers:

```bash
just mesh-cluster-up
```

### Cluster Topology ($N=13, K=4, \beta=0.15$):
- **Port Range**: `8765` to `8777`
- **Seed Nodes**: Node 1 (`8765`), Node 2 (`8766`), Node 3 (`8767`)
- **Worker Peers**: Nodes 4 through 13

---

## 2. Launching the Textual TUI Workstation

In another terminal window:
```bash
just tui
```

Switch to the **Mesh Cluster** tab to visualize:
- Live WebSocket peer connection graphs.
- Epidemic gossip diffusion latency across all 13 nodes ($< 450\text{ms}$).
- Real-time 5-factor quality scores ($Q_i$) and domain expertise rankings ($E_i$).

---

## 3. Simulating a Barbell Netsplit

To test network partition recovery:
```bash
poetry run pytest tests/test_red_team_cluster_attacks.py -k barbell -v
```

### What Happens:
1. The bridge node between Cluster Alpha and Cluster Beta is severed.
2. Both clusters continue evaluating independent feeds.
3. Upon reconnection, nodes execute dynamic seed reconciliation, resolving divergent findings via **Domain Authority Weighted Medians** without corrupted consensus.
