"""Taxonomy and Subject tree builders for Credence TUI."""

from __future__ import annotations

from textual.widgets import Tree

from credence.taxonomy_loader import registry


def populate_taxonomy_tree(tree: Tree) -> None:
    """Build nested catalog and cluster tree nodes."""
    tree.clear()
    root = tree.root
    root.label = "Taxonomy Catalogs"
    root.expand()

    for cat_id, cat in registry.catalogs.items():
        cat_node = root.add(f"📚 {cat.description} ({cat_id})", expand=False)
        for cluster in cat.clusters:
            cl_node = cat_node.add(f"📁 {cluster.name} ({cluster.cluster_id})", expand=False)
            for r in cluster.rules:
                cl_node.add_leaf(f"• [{r.rule_id}] {r.evidence_guidelines or r.detection_signals}")


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
