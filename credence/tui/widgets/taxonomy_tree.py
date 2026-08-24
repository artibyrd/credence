"""Taxonomy and Subject tree builders for Credence TUI."""

from __future__ import annotations

from textual.widgets import Tree

from credence.taxonomy_loader import registry


def populate_taxonomy_tree(tree: Tree) -> None:
    """Build nested 3-tier standards and catalog tree nodes with RFC status badges."""
    tree.clear()
    root = tree.root
    root.label = "⚖️ Epistemic Standards & Taxonomies"
    root.expand()

    from credence.pipeline.rfc import rfc_registry, StandardTier

    # 1. Tier 0: Universal General
    tier0_node = root.add("🏛️ Tier 0: Universal General Standards", expand=True)
    # 2. Tier 1: Domain Specialist
    tier1_node = root.add("🔬 Tier 1: Domain Specialist Catalogs", expand=True)
    # 3. Tier 2: Sovereign Niche
    tier2_node = root.add("🏢 Tier 2: Sovereign Org & Niche Rules", expand=True)

    for proposal in rfc_registry.list_proposals():
        target_tier_node = (
            tier0_node
            if proposal.tier == StandardTier.UNIVERSAL_GENERAL
            else tier1_node
            if proposal.tier == StandardTier.DOMAIN_SPECIALIST
            else tier2_node
        )

        stage_badge = f"[{proposal.stage.value}]"
        prop_node = target_tier_node.add(
            f"📜 {proposal.rfc_id}: {proposal.title} {stage_badge}", expand=False
        )

        from credence.pipeline.rfc import validate_catalog_yaml

        _, _, catalog = validate_catalog_yaml(proposal.catalog_yaml)
        if catalog:
            for cluster in catalog.clusters:
                cl_node = prop_node.add(f"📁 {cluster.name} ({cluster.cluster_id})", expand=False)
                for r in cluster.rules:
                    cl_node.add_leaf(f"• [{r.rule_id}] {r.name} (Sev {r.severity}/5)")


def populate_subjects_tree(tree: Tree) -> None:
    """Build subject domain tree nodes."""
    tree.clear()
    root = tree.root
    root.label = "Subject Registries"
    root.expand()
    root.add_leaf("• journalistic.news")
    root.add_leaf("• science.medicine")
    root.add_leaf("• financial.equities")
    root.add_leaf("• technology.software")

