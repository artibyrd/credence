"""Dynamic Taxonomy Registry & YAML Loader for Credence.

Loads, validates, hashes, and indexes extensible taxonomy catalogs across:
1. Journalistic Ethics (SPJ)
2. Logical Fallacies (IEP)
3. Deceptive Patterns
4. Domain-specific extensions
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field, field_validator

from credence.config import settings


class RootDomain(str, Enum):
    """Core taxonomy domains for epistemic and interface auditing."""

    JOURNALISTIC_ETHICS = "JOURNALISTIC_ETHICS"
    LOGICAL_FALLACY = "LOGICAL_FALLACY"
    DECEPTIVE_PATTERN = "DECEPTIVE_PATTERN"
    DOMAIN_SPECIFIC = "DOMAIN_SPECIFIC"


class TaxonomyRule(BaseModel):
    """A concrete, verifiable evaluation rule within a taxonomy cluster."""

    rule_id: str = Field(..., description="Unique rule identifier (e.g. SPJ-1.1, FALLACY-1.1, DP-1.1)")
    name: str = Field(..., description="Human-readable rule title")
    severity: int = Field(..., ge=1, le=5, description="Impact severity score from 1 (minor) to 5 (critical)")
    description: str = Field(..., description="Detailed definition of what constitutes a violation")
    detection_signals: List[str] = Field(default_factory=list, description="Concrete textual or visual signals")
    evidence_guidelines: str = Field(..., description="Requirements for grounded excerpt citation")
    mitigations_or_exemptions: Optional[str] = Field(
        default=None, description="Conditions where this rule is excused (e.g., satire/op-ed)"
    )
    namespaced_uri: Optional[str] = Field(
        default=None, description="Full canonical URI: domain:cluster/rule_id@version"
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Severity must be an integer between 1 and 5.")
        return v


class TaxonomyCluster(BaseModel):
    """A thematic cluster of related rules within a taxonomy domain."""

    cluster_id: str = Field(
        ..., description="Cluster identifier (e.g. SEEK_TRUTH_AND_REPORT, RELEVANCE_AND_PERSONAL_ATTACKS)"
    )
    name: str = Field(..., description="Cluster display name")
    description: str = Field(..., description="Scope of the cluster")
    rules: List[TaxonomyRule] = Field(default_factory=list, description="Rules belonging to this cluster")


class TaxonomyCatalog(BaseModel):
    """A complete versioned taxonomy catalog containing clusters and rules."""

    catalog_id: str = Field(..., description="Catalog identifier (e.g. spj_ethics, iep_fallacies)")
    domain: str = Field(..., description="Root domain (JOURNALISTIC_ETHICS, LOGICAL_FALLACY, DECEPTIVE_PATTERN, etc.)")
    version: str = Field(default="1.0.0", description="Semantic version string")
    description: str = Field(..., description="Catalog overview")
    default_weight: float = Field(default=1.0, ge=0.0, description="Domain weight multiplier for scoring")
    clusters: List[TaxonomyCluster] = Field(default_factory=list, description="Clusters in this catalog")
    catalog_hash: Optional[str] = Field(default=None, description="SHA-256 checksum of canonical JSON representation")

    def populate_namespaced_uris(self) -> None:
        """Assign full namespaced URIs (<domain>:<cluster_id>/<rule_id>@<version>) to all child rules."""
        domain_clean = self.domain.lower().replace("_", "-")
        for cluster in self.clusters:
            cluster_clean = cluster.cluster_id.lower().replace("_", "-")
            for rule in cluster.rules:
                rule.namespaced_uri = f"{domain_clean}:{cluster_clean}/{rule.rule_id}@v{self.version}"

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash of canonical catalog contents."""
        self.populate_namespaced_uris()
        catalog_dict = self.model_dump(exclude={"catalog_hash"})
        canonical_json = json.dumps(catalog_dict, sort_keys=True, separators=(",", ":"))
        hasher = hashlib.sha256(canonical_json.encode("utf-8"))
        self.catalog_hash = f"sha256:{hasher.hexdigest()}"
        return self.catalog_hash


class TaxonomyRegistry:
    """Registry that dynamically discovers, validates, indexes, and serves taxonomy catalogs."""

    def __init__(self, directory: Optional[Path] = None) -> None:
        self.directory: Path = directory or settings.TAXONOMY_DIR
        self.catalogs: Dict[str, TaxonomyCatalog] = {}
        self.rules_by_uri: Dict[str, TaxonomyRule] = {}
        self.rules_by_id: Dict[str, TaxonomyRule] = {}

    def load_from_yaml(self, file_path: Path) -> TaxonomyCatalog:
        """Load and validate a single YAML taxonomy catalog file."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        catalog = TaxonomyCatalog.model_validate(raw_data)
        catalog.populate_namespaced_uris()
        catalog.compute_hash()

        self.catalogs[catalog.catalog_id] = catalog

        for cluster in catalog.clusters:
            for rule in cluster.rules:
                if rule.namespaced_uri:
                    self.rules_by_uri[rule.namespaced_uri] = rule
                self.rules_by_id[rule.rule_id] = rule

        return catalog

    def load_all(self) -> None:
        """Discover and load all .yaml and .yml files in the registry directory."""
        if not self.directory.exists():
            return

        for yaml_file in sorted(self.directory.glob("*.yaml")) + sorted(self.directory.glob("*.yml")):
            self.load_from_yaml(yaml_file)

    def get_catalog(self, catalog_id: str) -> Optional[TaxonomyCatalog]:
        """Retrieve a loaded catalog by catalog_id."""
        if not self.catalogs:
            self.load_all()
        return self.catalogs.get(catalog_id)

    def get_rule(self, rule_id_or_uri: str) -> Optional[TaxonomyRule]:
        """Lookup a rule by either its short rule_id (e.g. SPJ-1.1) or full namespaced URI."""
        if not self.catalogs:
            self.load_all()
        if rule_id_or_uri in self.rules_by_uri:
            return self.rules_by_uri[rule_id_or_uri]
        return self.rules_by_id.get(rule_id_or_uri)

    def list_catalogs(self) -> List[TaxonomyCatalog]:
        """Return list of all registered catalogs."""
        if not self.catalogs:
            self.load_all()
        return list(self.catalogs.values())

    def list_rules(self) -> List[TaxonomyRule]:
        """Return list of all registered rules."""
        if not self.catalogs:
            self.load_all()
        return list(self.rules_by_uri.values())

    def get_catalog_hashes(self) -> Dict[str, str]:
        """Return dictionary of {catalog_id: catalog_hash} for mesh attestation exchange."""
        if not self.catalogs:
            self.load_all()
        return {cat_id: cat.catalog_hash or "" for cat_id, cat in self.catalogs.items()}

    def get_composite_catalog_hash(self) -> str:
        """Compute deterministic SHA-256 root hash over all loaded catalogs in canonical order."""
        if not self.catalogs:
            self.load_all()
        sorted_items = sorted(self.catalogs.items(), key=lambda x: x[0])
        payload = {cat_id: cat.catalog_hash or "" for cat_id, cat in sorted_items}
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        hasher = hashlib.sha256(canonical_json.encode("utf-8"))
        return f"sha256:{hasher.hexdigest()}"

    def get_granular_evaluation_clusters(self, max_rules_per_cluster: int = 6) -> List[TaxonomyCluster]:
        """Return bounded semantic clusters across all registered catalogs (<= max_rules_per_cluster)."""
        if not self.catalogs:
            self.load_all()
        clusters: List[TaxonomyCluster] = []
        for cat in sorted(self.catalogs.values(), key=lambda c: c.catalog_id):
            for cluster in cat.clusters:
                if len(cluster.rules) <= max_rules_per_cluster:
                    clusters.append(cluster)
                else:
                    for i in range(0, len(cluster.rules), max_rules_per_cluster):
                        sub_rules = cluster.rules[i : i + max_rules_per_cluster]
                        sub_id = f"{cluster.cluster_id}_P{(i // max_rules_per_cluster) + 1}"
                        sub_name = f"{cluster.name} (Part {(i // max_rules_per_cluster) + 1})"
                        clusters.append(
                            TaxonomyCluster(
                                cluster_id=sub_id,
                                name=sub_name,
                                description=cluster.description,
                                rules=sub_rules,
                            )
                        )
        return clusters

    def get_catalog_deltas(self, previous_taxonomies: Dict[str, str]) -> List[TaxonomyCluster]:
        """Identify clusters belonging to new or modified catalogs relative to previous audit state."""
        if not self.catalogs:
            self.load_all()
        delta_clusters: List[TaxonomyCluster] = []
        for cat_id, cat in self.catalogs.items():
            prev_hash = previous_taxonomies.get(cat_id)
            if prev_hash != cat.catalog_hash:
                delta_clusters.extend(cat.clusters)
        return delta_clusters

    def is_audit_stale(
        self, audit_taxonomies: Dict[str, str], audit_root_hash: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Check if an audit was performed under an outdated taxonomy state, returning delta reasons."""
        if not self.catalogs:
            self.load_all()
        reasons: List[str] = []
        current_root = self.get_composite_catalog_hash()

        if audit_root_hash and audit_root_hash != current_root:
            audit_short = audit_root_hash[:16]
            curr_short = current_root[:16]
            reasons.append(f"Root hash mismatch: audit={audit_short}... vs current={curr_short}...")
        elif not audit_root_hash:
            reasons.append("Audit missing taxonomy root hash (legacy evaluation)")

        for cat_id, cat in self.catalogs.items():
            prev_hash = audit_taxonomies.get(cat_id)
            if prev_hash is None:
                reasons.append(f"New catalog added: '{cat_id}' (v{cat.version})")
            elif prev_hash != cat.catalog_hash:
                prev_short = prev_hash[:16]
                curr_short = (cat.catalog_hash or "")[:16]
                reasons.append(f"Catalog '{cat_id}' updated: was {prev_short}..., now {curr_short}...")

        is_stale = len(reasons) > 0
        return is_stale, reasons

    def generate_prompt_checklist(self, catalog_id: str) -> str:
        """Generate a clean, structured text checklist of rules for LLM subagent prompts."""
        catalog = self.get_catalog(catalog_id)
        if not catalog:
            raise ValueError(f"Catalog '{catalog_id}' not found in registry.")

        lines = [
            f"# Evaluation Checklist: {catalog.description}",
            f"Domain: {catalog.domain} | Version: v{catalog.version} | Base Weight: {catalog.default_weight}",
            "",
        ]

        for cluster in catalog.clusters:
            lines.append(f"## Cluster: {cluster.name} (`{cluster.cluster_id}`)")
            lines.append(f"{cluster.description}\n")
            for rule in cluster.rules:
                lines.append(f"- **[{rule.rule_id}] {rule.name}** (Severity: {rule.severity}/5)")
                lines.append(f"  URI: `{rule.namespaced_uri}`")
                lines.append(f"  Description: {rule.description}")
                if rule.detection_signals:
                    lines.append("  Signals:")
                    for sig in rule.detection_signals:
                        lines.append(f"    * {sig}")
                lines.append(f"  Evidence Requirement: {rule.evidence_guidelines}")
                if rule.mitigations_or_exemptions:
                    lines.append(f"  Mitigations / Exemptions: {rule.mitigations_or_exemptions}")
                lines.append("")

        return "\n".join(lines)


# Singleton default registry instance
registry = TaxonomyRegistry()
