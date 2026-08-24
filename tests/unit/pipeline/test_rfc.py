"""Unit tests for Autonomous Standards Ratification & RFC Governance Protocol (Phase 1).

Tests:
1. RFCProposal model validation and deterministic RFC 8785 canonical hashing.
2. YAML catalog linter and AST validation rules (<0.3s gate).
3. Byzantine Quorum (>= 66.7%) and Expertise-Weighted Median calculations.
4. Synthetic Benchmark Gauntlet execution with Golden Control Corpus defense (FPR = 0%).
5. RFCRegistry proposal discovery, stage transitions, and hot-reloading into TaxonomyRegistry.
"""

import pytest

from credence.pipeline.golden_baseline import get_golden_control_corpus
from credence.pipeline.rfc import (
    RFCProposal,
    RFCRegistry,
    RFCStage,
    RFCVoteAttestation,
    StandardTier,
    compute_byzantine_quorum,
    compute_domain_weighted_quorum,
    run_synthetic_benchmark,
    validate_catalog_yaml,
)
from credence.taxonomy_loader import registry as taxonomy_registry


@pytest.mark.unit
def test_rfc_proposal_model_and_canonical_hashing() -> None:
    """Verify RFCProposal creation, field validation, and deterministic SHA-256 calculation."""
    proposal = RFCProposal(
        rfc_id="RFC-101",
        title="Clinical Trial Disclosure Standards",
        tier=StandardTier.DOMAIN_SPECIALIST,
        stage=RFCStage.DRAFT,
        author="BioMed Working Group",
        motivation="Establish verifiable standards for auditing pharmaceutical trial claims.",
        target_domain="CLINICAL_MEDICINE",
        version="1.0.0",
        catalog_yaml="""
catalog_id: "clinical_trials"
domain: "CLINICAL_MEDICINE"
name: "Clinical Trial Disclosure Standard"
version: "1.0.0"
description: "Rules auditing medical and pharmaceutical claims."
clusters:
  - cluster_id: "EVIDENCE"
    name: "Evidence Level"
    description: "Evaluates empirical basis of medical assertions."
    rules:
      - rule_id: "MED-1.1"
        name: "Unsubstantiated Clinical Efficacy"
        severity: 4
        description: "Asserting clinical cure without citing peer-reviewed Phase III trial data."
        detection_signals:
          - "Claims of revolutionary clinical cure lacking peer-reviewed journal citation."
          - "Use of anecdotal testimonials in place of double-blind trial results."
        evidence_guidelines: "Must quote the specific unproven clinical claim verbatim."
""",
    )

    digest = proposal.compute_sha256()
    assert digest.startswith("sha256:")
    assert len(digest) == 71  # "sha256:" + 64 hex chars
    assert proposal.catalog_sha256 == digest

    # Determinism check: recomputing on identical content yields identical hash
    digest_again = proposal.compute_sha256()
    assert digest == digest_again


@pytest.mark.unit
def test_validate_catalog_yaml_success() -> None:
    """Verify validate_catalog_yaml correctly parses and approves valid YAML catalogs."""
    valid_yaml = """
catalog_id: "financial_integrity"
domain: "FINANCIAL_DISCLOSURES"
name: "Financial Disclosure Integrity Standard"
version: "1.0.0"
description: "Rules auditing corporate earnings calls and financial disclosures."
clusters:
  - cluster_id: "NON_GAAP"
    name: "Non-GAAP Disclosures"
    description: "Evaluates adjusted non-GAAP metrics."
    rules:
      - rule_id: "FIN-1.1"
        name: "Missing GAAP Reconciliation"
        severity: 4
        description: "Promoting non-GAAP metrics without providing required GAAP reconciliation table."
        detection_signals:
          - "Presentation of adjusted EBITDA with no reconciliation to net income."
          - "Exclusion of standard operating cash expenses from adjusted performance metrics."
        evidence_guidelines: "Must quote the non-GAAP metric and cite the absence of GAAP reconciliation."
"""
    is_valid, errors, catalog = validate_catalog_yaml(valid_yaml)
    assert is_valid is True
    assert len(errors) == 0
    assert catalog is not None
    assert catalog.catalog_id == "financial_integrity"
    assert catalog.catalog_hash is not None
    assert catalog.catalog_hash.startswith("sha256:")
    assert len(catalog.clusters[0].rules) == 1
    assert catalog.clusters[0].rules[0].namespaced_uri == "financial-disclosures:non-gaap/FIN-1.1@v1.0.0"


@pytest.mark.unit
def test_validate_catalog_yaml_rejection_criteria() -> None:
    """Verify validate_catalog_yaml strictly rejects invalid catalogs."""
    # 1. Empty YAML
    is_valid, errors, _ = validate_catalog_yaml("")
    assert is_valid is False
    assert any("empty" in e.lower() for e in errors)

    # 2. Missing required fields
    is_valid, errors, _ = validate_catalog_yaml("name: Test\nversion: 1.0.0")
    assert is_valid is False
    assert any("domain" in e for e in errors)

    # 3. Rule with fewer than 2 detection signals
    invalid_signals_yaml = """
catalog_id: "bad_signals"
domain: "TEST"
name: "Bad Signals"
version: "1.0.0"
description: "Test catalog"
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "BAD-1.1"
        name: "Single Signal Rule"
        severity: 3
        description: "Only one signal provided"
        detection_signals:
          - "Only one signal here"
        evidence_guidelines: "Must quote text verbatim."
"""
    is_valid, errors, _ = validate_catalog_yaml(invalid_signals_yaml)
    assert is_valid is False
    assert any("at least 2 distinct detection_signals" in e for e in errors)

    # 4. Rule with invalid severity (> 5)
    invalid_severity_yaml = """
catalog_id: "bad_sev"
domain: "TEST"
name: "Bad Severity"
version: "1.0.0"
description: "Test catalog"
clusters:
  - cluster_id: "C1"
    name: "Cluster 1"
    description: "Desc"
    rules:
      - rule_id: "BAD-1.2"
        name: "Extreme Severity Rule"
        severity: 9
        description: "Severity out of bounds"
        detection_signals:
          - "Signal 1"
          - "Signal 2"
        evidence_guidelines: "Must quote text verbatim."
"""
    is_valid, errors, _ = validate_catalog_yaml(invalid_severity_yaml)
    assert is_valid is False
    assert any("severity" in e.lower() for e in errors)


@pytest.mark.unit
def test_byzantine_quorum_calculation() -> None:
    """Verify Byzantine Quorum threshold math (>= 66.7% over active anchors)."""
    # 13 nodes, f=4 Byzantine tolerance -> 9 approvals needed (69.2% >= 66.7%)
    passed, pct = compute_byzantine_quorum(approvals=9, total_active_anchors=13)
    assert passed is True
    assert pct >= 66.7

    # 8 approvals out of 13 -> 61.54% < 66.7% -> Fails quorum
    passed, pct = compute_byzantine_quorum(approvals=8, total_active_anchors=13)
    assert passed is False
    assert pct < 66.7

    # Edge cases
    passed, _ = compute_byzantine_quorum(approvals=0, total_active_anchors=13)
    assert passed is False
    passed, _ = compute_byzantine_quorum(approvals=10, total_active_anchors=0)
    assert passed is False


@pytest.mark.unit
def test_domain_weighted_quorum_calculation() -> None:
    """Verify Expertise-Weighted Median consensus for Tier 1 Specialist standards."""
    # 4 high-authority nodes approve, 2 low-authority reject
    votes = [
        ("APPROVE", 0.95),
        ("APPROVE", 0.90),
        ("APPROVE", 0.85),
        ("APPROVE", 0.80),
        ("REJECT", 0.30),
        ("REJECT", 0.20),
    ]
    # Total weight = 4.00, approval weight = 3.50 (87.5% >= 70%)
    passed, pct = compute_domain_weighted_quorum(votes, min_threshold_pct=70.0)
    assert passed is True
    assert pct == 87.5

    # Opposing vote where rejection outweighs approval
    failing_votes = [
        ("APPROVE", 0.40),
        ("REJECT", 0.95),
        ("REJECT", 0.85),
    ]
    passed, pct = compute_domain_weighted_quorum(failing_votes, min_threshold_pct=70.0)
    assert passed is False
    assert pct < 70.0


@pytest.mark.unit
def test_synthetic_benchmark_gauntlet_with_golden_baseline() -> None:
    """Verify Synthetic Benchmark Gauntlet enforces F1 >= 0.87 and Golden FPR = 0.00%."""
    yaml_content = """
catalog_id: "test_gauntlet_cat"
domain: "JOURNALISTIC_ETHICS"
name: "Gauntlet Test Catalog"
version: "1.0.0"
description: "Test catalog for synthetic gauntlet"
clusters:
  - cluster_id: "TRUTH"
    name: "Truth Cluster"
    description: "Accuracy rules"
    rules:
      - rule_id: "TEST-1.1"
        name: "Sensationalized Title"
        severity: 3
        description: "Headline contradicts body"
        detection_signals:
          - "Headline asserts certainty when body reports rumors"
          - "Omission of critical context"
        evidence_guidelines: "Must quote headline and body."
"""
    _, _, catalog = validate_catalog_yaml(yaml_content)
    assert catalog is not None

    # Fixtures with high precision and recall
    fixtures = [
        {
            "id": "fix_01",
            "expected_violations": ["TEST-1.1"],
            "detected_violations": ["TEST-1.1"],
        },
        {
            "id": "fix_02",
            "expected_violations": ["TEST-1.1"],
            "detected_violations": ["TEST-1.1"],
        },
        {
            "id": "fix_03",
            "expected_violations": [],
            "detected_violations": [],
        },
    ]

    report = run_synthetic_benchmark(catalog, fixtures)
    assert report.passed_gate is True
    assert report.f1_score >= 0.87
    assert report.golden_baseline_fpr == 0.00
    assert report.grounding_quotient == 1.00

    # Test False Positive on Golden Baseline triggers failure
    compromised_golden = get_golden_control_corpus()
    compromised_golden[0]["detected_violations"] = ["TEST-1.1"]  # False positive on clean Reuters text!

    failing_report = run_synthetic_benchmark(catalog, fixtures, golden_baseline=compromised_golden)
    assert failing_report.passed_gate is False
    assert failing_report.golden_baseline_fpr > 0.00


@pytest.mark.unit
def test_rfc_registry_lifecycle_and_hot_reload() -> None:
    """Verify RFCRegistry proposal registration, retrieval, and hot-reload into TaxonomyRegistry."""
    registry = RFCRegistry()

    # Verify foundational ratified RFCs exist
    proposals = registry.list_proposals()
    assert len(proposals) >= 3
    rfc_ids = [p.rfc_id for p in proposals]
    assert "RFC-001" in rfc_ids
    assert "RFC-002" in rfc_ids
    assert "RFC-003" in rfc_ids

    # Register new specialist standard
    new_rfc = RFCProposal(
        rfc_id="RFC-009",
        title="Municipal Conflict of Interest Standard",
        tier=StandardTier.DOMAIN_SPECIALIST,
        author="Ecosystem Governance",
        motivation="Audit local government media ownership disclosures.",
        target_domain="LOCAL_GOVERNMENT",
        version="1.0.0",
        catalog_yaml="""
catalog_id: "municipal_gov"
domain: "LOCAL_GOVERNMENT"
name: "Municipal Government Integrity Standard"
version: "1.0.0"
description: "Rules auditing elected official media ownership and zoning conflicts."
clusters:
  - cluster_id: "CONFLICTS"
    name: "Conflicts of Interest"
    description: "Evaluates elected official media ownership."
    rules:
      - rule_id: "MUNI-1.1"
        name: "Unlabeled Councilmember Ownership"
        severity: 5
        description: "Publishing municipal coverage without disclosing elected official ownership."
        detection_signals:
          - "Absence of publisher conflict-of-interest disclosure on council voting stories."
          - "Editorial advocacy for council policies authored by an elected councilmember."
        evidence_guidelines: "Must quote the news story and verify missing ownership disclaimer."
""",
    )

    success, errors = registry.register_proposal(new_rfc)
    assert success is True
    prop = registry.get_proposal("RFC-009")
    assert prop is not None
    assert prop.stage == RFCStage.PROPOSED

    # Record vote
    vote = RFCVoteAttestation(
        rfc_id="RFC-009",
        catalog_sha256=new_rfc.catalog_sha256 or "",
        node_pubkey="node_anchor_1" + "0" * 50,
        vote="APPROVE",
        metrics={"f1": 0.95, "fpr": 0.0},
    )
    registry.record_vote(vote)
    assert len(registry.get_votes("RFC-009")) == 1

    # Hot-reload into live TaxonomyRegistry
    hot_catalog = registry.hot_reload_into_taxonomy_registry("RFC-009")
    assert hot_catalog is not None
    assert hot_catalog.catalog_id == "municipal_gov"
    assert taxonomy_registry.get_catalog("municipal_gov") is not None
    assert taxonomy_registry.get_rule("MUNI-1.1") is not None
