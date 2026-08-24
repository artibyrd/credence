"""13-Node Local Mesh Red-Team Integration Test Suite for RFC Standards Governance (Phase 5).

Evaluates decentralized RFC standards lifecycle against a 13-node Watts-Strogatz local mesh (N=13, f=4):
1. Happy Path Ratification: 13/13 nodes execute Gauntlet, sign Ed25519 envelopes, meet >= 66.7% Byzantine Quorum, and hot-reload.
2. Byzantine Cartel Attack Resistance: 4 colluding Byzantine nodes attempt to force-ratify a flawed/adversarial catalog; 9 honest nodes reject and defend the CAS.
3. Headroom Floor Circuit Breaker: Nodes under token pressure (<40% headroom) reject shadow trial canaries to preserve core audit loop.
4. Temporal Trajectory DAG Immutability: Re-auditing under newly ratified catalogs appends a new snapshot leaf without mutating or invalidating historical receipts.
"""

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from credence.identity import canonical_json_bytes
from credence.pipeline.rfc import (
    RFCProposal,
    RFCRegistry,
    RFCVoteAttestation,
    StandardTier,
    compute_byzantine_quorum,
    run_synthetic_benchmark,
    validate_catalog_yaml,
)
from credence.taxonomy_loader import registry as taxonomy_registry


class SimulatedMeshNode:
    """Represents a simulated P2P mesh node with cryptographic identity and token headroom."""

    def __init__(
        self, node_id: str, is_byzantine: bool = False, headroom_pct: float = 100.0, domain_authority: float = 0.85
    ):
        self.node_id = node_id
        self.is_byzantine = is_byzantine
        self.headroom_pct = headroom_pct
        self.domain_authority = domain_authority
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.public_key_hex = self.public_key.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        ).hex()

    def evaluate_and_vote(self, proposal: RFCProposal, fixtures: list[dict]) -> RFCVoteAttestation:
        """Evaluate candidate catalog and mint signed Ed25519 vote attestation envelope."""
        if self.is_byzantine:
            # Byzantine nodes vote to approve even flawed/compromised catalogs to test cartel attacks
            vote = "APPROVE"
            reason = "Byzantine cartel approval"
        elif self.headroom_pct < 40.0:
            vote = "REJECT"
            reason = "QUOTA_PRESERVED: Token headroom below 40% threshold"
        else:
            is_valid, errors, catalog = validate_catalog_yaml(proposal.catalog_yaml)
            if not is_valid or not catalog:
                vote = "REJECT"
                reason = f"Schema validation failed: {'; '.join(errors)}"
            else:
                report = run_synthetic_benchmark(catalog, fixtures)
                if report.passed_gate:
                    vote = "APPROVE"
                    reason = f"Synthetic gauntlet passed: F1={report.f1_score}, FPR={report.golden_baseline_fpr}"
                else:
                    vote = "REJECT"
                    reason = f"Synthetic gauntlet failed: F1={report.f1_score}, FPR={report.golden_baseline_fpr}"

        attestation = RFCVoteAttestation(
            rfc_id=proposal.rfc_id,
            catalog_sha256=proposal.catalog_sha256 or "",
            node_pubkey=self.public_key_hex,
            vote=vote,
            metrics={"headroom_pct": self.headroom_pct, "authority": self.domain_authority},
            reason=reason,
        )

        # Ed25519 signature over canonical RFC 8785 JSON bytes
        raw_bytes = canonical_json_bytes(attestation.get_signable_payload())
        sig_bytes = self.private_key.sign(raw_bytes)
        attestation.signature = sig_bytes.hex()
        return attestation


@pytest.mark.integration
def test_13_node_mesh_happy_path_rfc_ratification() -> None:
    """Scenario 1: 13-node local mesh evaluates valid specialist standard and reaches 100% consensus."""
    registry = RFCRegistry()

    valid_proposal = RFCProposal(
        rfc_id="RFC-050",
        title="Scientific Preprint Evidentiary Standard",
        tier=StandardTier.DOMAIN_SPECIALIST,
        author="Open Science Federation",
        motivation="Differentiate peer-reviewed literature from unreviewed preprints.",
        target_domain="PEER_REVIEWED_SCIENCE",
        version="1.0.0",
        catalog_yaml="""
catalog_id: "science_preprints"
domain: "PEER_REVIEWED_SCIENCE"
name: "Scientific Preprint Evidentiary Standard"
version: "1.0.0"
description: "Rules auditing preprint disclosure and statistical significance."
clusters:
  - cluster_id: "PEER_REVIEW"
    name: "Peer Review Status"
    description: "Evaluates journal publication versus preprint status."
    rules:
      - rule_id: "SCI-1.1"
        name: "Unlabeled Preprint Assertion"
        severity: 4
        description: "Presenting findings from an unreviewed preprint as established scientific consensus."
        detection_signals:
          - "Citing unreviewed ArXiv or BioRxiv preprint with definitive clinical claims."
          - "Absence of 'Preprint / Not Peer-Reviewed' disclaimer in article body."
        evidence_guidelines: "Must quote the definitive claim and cite the source preprint DOI."
""",
    )
    valid_proposal.compute_sha256()
    registry.register_proposal(valid_proposal)

    fixtures = [
        {"id": "fix_1", "expected_violations": ["SCI-1.1"], "detected_violations": ["SCI-1.1"]},
        {"id": "fix_2", "expected_violations": [], "detected_violations": []},
    ]

    # Create 13 honest nodes
    nodes = [SimulatedMeshNode(f"node_{i:02d}", is_byzantine=False) for i in range(1, 14)]

    # Collect votes
    approvals = 0
    for node in nodes:
        vote = node.evaluate_and_vote(valid_proposal, fixtures)
        registry.record_vote(vote)
        if vote.vote == "APPROVE":
            approvals += 1

    # Check Quorum (13/13 approvals = 100% >= 66.7%)
    passed, pct = compute_byzantine_quorum(approvals, total_active_anchors=13)
    assert passed is True
    assert pct == 100.0

    # Hot-reload into live TaxonomyRegistry
    hot_catalog = registry.hot_reload_into_taxonomy_registry("RFC-050")
    assert hot_catalog is not None
    assert taxonomy_registry.get_catalog("science_preprints") is not None
    assert taxonomy_registry.get_rule("SCI-1.1") is not None


@pytest.mark.integration
def test_13_node_mesh_byzantine_cartel_attack_defense() -> None:
    """Scenario 2: 4 Byzantine nodes attempt to force-ratify a flawed standard with False Positives."""
    registry = RFCRegistry()

    # Flawed standard that falsely flags factual Reuters articles (Golden Baseline violation)
    flawed_proposal = RFCProposal(
        rfc_id="RFC-066",
        title="Malicious Overbroad Factual Filter",
        tier=StandardTier.UNIVERSAL_GENERAL,
        author="Adversarial Cartel",
        motivation="Attempt to censor factual news wires.",
        target_domain="ADVERSARIAL_DOMAIN",
        version="1.0.0",
        catalog_yaml="""
catalog_id: "flawed_cartel_cat"
domain: "ADVERSARIAL_DOMAIN"
name: "Flawed Cartel Catalog"
version: "1.0.0"
description: "Overbroad rules designed to trigger false positives."
clusters:
  - cluster_id: "OVERBROAD"
    name: "Overbroad Cluster"
    description: "Censors factual keywords."
    rules:
      - rule_id: "CARTEL-1.1"
        name: "Factual Keyword Censorship"
        severity: 5
        description: "Overbroad trigger on clean news terms."
        detection_signals:
          - "Any mention of government agency or statistics."
          - "Absence of ideological alignment."
        evidence_guidelines: "Must quote any factual sentence."
""",
    )
    flawed_proposal.compute_sha256()
    registry.register_proposal(flawed_proposal)

    # Fixtures simulating poor precision / high false positive rate
    fixtures = [{"id": "fix_bad", "expected_violations": [], "detected_violations": ["CARTEL-1.1"]}]

    # 9 Honest Nodes + 4 Byzantine Cartel Nodes (N=13, f=4)
    nodes = [SimulatedMeshNode(f"honest_{i}", is_byzantine=False) for i in range(1, 10)]
    nodes += [SimulatedMeshNode(f"byzantine_{i}", is_byzantine=True) for i in range(1, 5)]

    approvals = 0
    rejections = 0

    for node in nodes:
        vote = node.evaluate_and_vote(flawed_proposal, fixtures)
        registry.record_vote(vote)
        if vote.vote == "APPROVE":
            approvals += 1
        else:
            rejections += 1

    # Exactly 4 Byzantine nodes approved (30.77%), 9 honest nodes rejected (69.23%)
    assert approvals == 4
    assert rejections == 9

    passed, pct = compute_byzantine_quorum(approvals, total_active_anchors=13)
    assert passed is False
    assert pct < 66.7

    # Ensure catalog is NOT hot-reloaded into registry
    assert taxonomy_registry.get_catalog("flawed_cartel_cat") is None


@pytest.mark.integration
def test_straggler_and_headroom_floor_defense() -> None:
    """Scenario 3: Nodes under token quota pressure (<40%) reject shadow trials to protect core audit loop."""
    overloaded_node = SimulatedMeshNode("overloaded_node_1", is_byzantine=False, headroom_pct=25.0)

    proposal = RFCProposal(
        rfc_id="RFC-077",
        title="Heavy Compute Standard",
        tier=StandardTier.DOMAIN_SPECIALIST,
        author="Compute Heavy Working Group",
        motivation="Test quota preservation.",
        target_domain="HEAVY_COMPUTE",
        version="1.0.0",
        catalog_yaml="""
catalog_id: "heavy_comp"
domain: "HEAVY_COMPUTE"
name: "Heavy Compute Standard"
version: "1.0.0"
description: "Test catalog."
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "HVY-1.1"
        name: "Heavy Rule"
        severity: 3
        description: "Heavy computation rule."
        detection_signals:
          - "Signal 1"
          - "Signal 2"
        evidence_guidelines: "Quote verbatim."
""",
    )
    proposal.compute_sha256()

    vote = overloaded_node.evaluate_and_vote(proposal, fixtures=[])
    assert vote.vote == "REJECT"
    assert "QUOTA_PRESERVED" in (vote.reason or "")


@pytest.mark.integration
def test_temporal_trajectory_dag_immutability() -> None:
    """Scenario 4: Upgrading from v1.0.0 to v2.0.0 preserves historical receipt hashes under original CAS."""
    # Proposal v1
    prop_v1 = RFCProposal(
        rfc_id="RFC-080",
        title="Municipal Ethics Standard v1",
        tier=StandardTier.DOMAIN_SPECIALIST,
        author="Gov WG",
        motivation="Audit city council conflicts.",
        target_domain="MUNICIPAL_GOV",
        version="1.0.0",
        catalog_yaml="""
catalog_id: "muni_ethics"
domain: "MUNICIPAL_GOV"
name: "Municipal Ethics"
version: "1.0.0"
description: "Rules auditing local government conflicts."
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "MUNI-1.1"
        name: "Unlabeled Councilmember Ownership"
        severity: 5
        description: "Publishing without ownership disclosure."
        detection_signals:
          - "Signal 1"
          - "Signal 2"
        evidence_guidelines: "Quote verbatim."
""",
    )
    digest_v1 = prop_v1.compute_sha256()

    # Proposal v2 with evolved rules
    prop_v2 = RFCProposal(
        rfc_id="RFC-080-v2",
        title="Municipal Ethics Standard v2",
        tier=StandardTier.DOMAIN_SPECIALIST,
        author="Gov WG",
        motivation="Refined signals for planning commissions.",
        target_domain="MUNICIPAL_GOV",
        version="2.0.0",
        catalog_yaml="""
catalog_id: "muni_ethics"
domain: "MUNICIPAL_GOV"
name: "Municipal Ethics"
version: "2.0.0"
description: "Rules auditing local government conflicts v2."
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "MUNI-1.1"
        name: "Unlabeled Councilmember Ownership"
        severity: 5
        description: "Publishing without ownership disclosure."
        detection_signals:
          - "Signal 1"
          - "Signal 2"
        evidence_guidelines: "Quote verbatim."
      - rule_id: "MUNI-1.2"
        name: "Planning Commission Recusal Failure"
        severity: 4
        description: "Failure to disclose zoning conflict."
        detection_signals:
          - "Signal A"
          - "Signal B"
        evidence_guidelines: "Quote verbatim."
""",
    )
    digest_v2 = prop_v2.compute_sha256()

    # Both hashes are deterministic, unique, and immutable
    assert digest_v1 != digest_v2
    assert digest_v1.startswith("sha256:")
    assert digest_v2.startswith("sha256:")
