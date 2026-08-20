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
    updated = update_markdown_frontmatter(md, {"verified_version": "v2.1.0"})
    assert "verified_version: v2.1.0" in updated
    assert "last_verified:" in updated
