"""Hermetic unit tests for credence audit-docs command."""

import pytest

from credence.cli.commands.docs_audit import parse_markdown_frontmatter, update_markdown_frontmatter

pytestmark = pytest.mark.unit


def test_parse_frontmatter():
    md = """---
title: Sample Page
description: A sample description
verified_version: v2.0.0
---

# Headline
Prose body.
"""
    fm, body = parse_markdown_frontmatter(md)
    assert fm["title"] == "Sample Page"
    assert fm["description"] == "A sample description"
    assert "Headline" in body


def test_update_frontmatter():
    md = """---
title: Sample Page
---
Body text."""
    updated = update_markdown_frontmatter(md, {"verified_version": "v2.14.0"})
    assert "verified_version: v2.14.0" in updated
    assert "last_verified:" in updated


def test_docs_audit_dynamic_version():
    from credence import __version__
    from credence.cli.commands.docs_audit import CURRENT_VERSION

    assert CURRENT_VERSION == f"v{__version__}"


def test_audit_single_doc_receipt_generation(tmp_path):
    from credence import __version__
    from credence.cli.commands.docs_audit import audit_single_doc
    from credence.identity import load_or_create_node_identity

    test_md = tmp_path / "test_page.md"
    test_md.write_text(
        """---
title: Test Page Title
description: Test Page Description
---

# Test Page

This is a test documentation page for epistemic integrity.
""",
        encoding="utf-8",
    )

    identity = load_or_create_node_identity(tmp_path / "node.key")
    result = audit_single_doc(test_md, identity, update_frontmatter=True)

    assert result["title"] == "Test Page Title"
    assert result["suspicion_score"] == 0.0
    assert result["classification"] == "PRISTINE"
    assert "receipt" in result
    assert result["receipt"]["verified_version"] == f"v{__version__}"
    assert result["receipt"]["node_pubkey"] == identity.public_key_hex
    assert len(result["receipt"]["node_signature"]) == 128
