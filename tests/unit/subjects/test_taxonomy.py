"""Unit tests for Taxonomy Registry and YAML Catalog Loading."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from credence.taxonomy_loader import RootDomain, TaxonomyRegistry, TaxonomyRule


@pytest.mark.unit
def test_taxonomy_catalogs_load_successfully(test_registry: TaxonomyRegistry) -> None:
    """Verify standard taxonomy catalogs load and contain expected clusters and rules."""
    catalogs = test_registry.list_catalogs()
    assert len(catalogs) >= 3

    catalog_ids = {c.catalog_id for c in catalogs}
    assert "spj_ethics" in catalog_ids
    assert "iep_fallacies" in catalog_ids
    assert "deceptive_patterns" in catalog_ids


@pytest.mark.unit
def test_namespaced_uris_populated(test_registry: TaxonomyRegistry) -> None:
    """Verify every loaded rule has a valid namespaced URI."""
    rules = test_registry.list_rules()
    assert len(rules) > 0

    for rule in rules:
        assert rule.namespaced_uri is not None
        assert ":" in rule.namespaced_uri
        assert "@v" in rule.namespaced_uri

    # Test specific lookup
    spj_rule = test_registry.get_rule("SPJ-1.1")
    assert spj_rule is not None
    assert spj_rule.name == "Unsourced Factual Assertion"
    assert spj_rule.severity == 3
    assert "journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0" == spj_rule.namespaced_uri

    # Test lookup by full URI
    lookup_by_uri = test_registry.get_rule(spj_rule.namespaced_uri)
    assert lookup_by_uri is not None
    assert lookup_by_uri.rule_id == "SPJ-1.1"


@pytest.mark.unit
def test_catalog_hash_determinism(test_registry: TaxonomyRegistry) -> None:
    """Verify catalog SHA-256 hashes are deterministic across separate loads."""
    reg2 = TaxonomyRegistry()
    reg2.load_all()

    hashes1 = test_registry.get_catalog_hashes()
    hashes2 = reg2.get_catalog_hashes()

    assert hashes1 == hashes2
    for _cat_id, cat_hash in hashes1.items():
        assert cat_hash.startswith("sha256:")
        assert len(cat_hash) == 71  # "sha256:" (7) + 64 hex chars


@pytest.mark.unit
def test_rule_severity_validation() -> None:
    """Verify severity must be between 1 and 5."""
    with pytest.raises(ValidationError):
        TaxonomyRule(
            rule_id="INVALID-1",
            name="Invalid Rule",
            severity=0,  # Invalid: < 1
            description="Test description",
            evidence_guidelines="Test evidence",
        )

    with pytest.raises(ValidationError):
        TaxonomyRule(
            rule_id="INVALID-2",
            name="Invalid Rule",
            severity=6,  # Invalid: > 5
            description="Test description",
            evidence_guidelines="Test evidence",
        )


@pytest.mark.unit
def test_dynamic_custom_domain_extension(tmp_path: Path) -> None:
    """Verify a new domain-specific YAML catalog can be hot-loaded dynamically."""
    custom_yaml = """
catalog_id: medical_claims
domain: DOMAIN_SPECIFIC
version: "1.0.0"
description: "Medical and epidemiological claim verification standards."
default_weight: 1.8

clusters:
  - cluster_id: CLINICAL_EVIDENCE
    name: "Clinical Evidence"
    description: "Standards for citing peer-reviewed clinical trials."
    rules:
      - rule_id: MED-1.1
        name: "Unverified Miracle Cure Claim"
        severity: 5
        description: "Promoting an unapproved compound as a definitive cure for serious illnesses."
        detection_signals:
          - "Claims of 100% cure rate without Phase 3 clinical trial citation."
        evidence_guidelines: "Quote the specific medical efficacy claim."
"""
    custom_file = tmp_path / "medical_claims.yaml"
    custom_file.write_text(custom_yaml, encoding="utf-8")

    custom_registry = TaxonomyRegistry(directory=tmp_path)
    custom_registry.load_all()

    med_catalog = custom_registry.get_catalog("medical_claims")
    assert med_catalog is not None
    assert med_catalog.domain == RootDomain.DOMAIN_SPECIFIC
    assert med_catalog.default_weight == 1.8

    med_rule = custom_registry.get_rule("MED-1.1")
    assert med_rule is not None
    assert med_rule.namespaced_uri == "domain-specific:clinical-evidence/MED-1.1@v1.0.0"
    assert med_rule.severity == 5


@pytest.mark.unit
def test_generate_prompt_checklist(test_registry: TaxonomyRegistry) -> None:
    """Verify subagent checklist generation formatting."""
    checklist = test_registry.generate_prompt_checklist("spj_ethics")
    assert "# Evaluation Checklist:" in checklist
    assert "SPJ-1.1" in checklist
    assert "Evidence Requirement:" in checklist


@pytest.mark.unit
def test_composite_catalog_root_hash(test_registry: TaxonomyRegistry) -> None:
    """Verify composite catalog root hash is deterministic and changes upon rule additions."""
    root_hash_1 = test_registry.get_composite_catalog_hash()
    assert root_hash_1.startswith("sha256:")
    assert len(root_hash_1) == 71

    # Reloading yields exact same hash
    reg2 = TaxonomyRegistry()
    reg2.load_all()
    assert reg2.get_composite_catalog_hash() == root_hash_1


@pytest.mark.unit
def test_granular_cluster_partitioning(test_registry: TaxonomyRegistry) -> None:
    """Verify all clusters returned by get_granular_evaluation_clusters are bounded (<= 6 rules)."""
    clusters = test_registry.get_granular_evaluation_clusters(max_rules_per_cluster=6)
    assert len(clusters) >= 8, f"Expected at least 8 granular clusters, got {len(clusters)}"

    for cluster in clusters:
        assert len(cluster.rules) <= 6, f"Cluster {cluster.cluster_id} exceeds 6 rules limit: {len(cluster.rules)}"
        assert len(cluster.rules) > 0


@pytest.mark.unit
def test_staleness_and_catalog_deltas(test_registry: TaxonomyRegistry) -> None:
    """Verify is_audit_stale detects outdated audit taxonomy hashes and catalog deltas."""
    current_hashes = test_registry.get_catalog_hashes()
    current_root = test_registry.get_composite_catalog_hash()

    # 1. Fresh audit is not stale
    is_stale, reasons = test_registry.is_audit_stale(current_hashes, current_root)
    assert is_stale is False
    assert len(reasons) == 0

    # 2. Missing a catalog triggers staleness
    partial_hashes = {k: v for k, v in current_hashes.items() if k != "deceptive_patterns"}
    is_stale, reasons = test_registry.is_audit_stale(partial_hashes, "sha256:outdated_root_hash")
    assert is_stale is True
    assert any("deceptive_patterns" in r for r in reasons)

    # 3. Catalog deltas isolation
    deltas = test_registry.get_catalog_deltas(partial_hashes)
    assert len(deltas) >= 1
    delta_ids = {c.cluster_id for c in deltas}
    assert any("VISUAL" in c_id or "EMOTIONAL" in c_id or "OBSTRUCTION" in c_id for c_id in delta_ids)
