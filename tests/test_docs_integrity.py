"""Hermetic verification test suite for credence-docs integrity (Invariant 26).

Validates:
1. Every registered item in app.js (DOCS_REGISTRY) maps to a valid Markdown file.
2. All documentation and blog articles have valid YAML frontmatter (title & description).
3. All interactive playground widget DOM IDs match app.js event listeners.
4. Tutorial and cookbook YAML code blocks are syntactically valid.
5. Zero-npm invariant: no package.json or node_modules in credence-docs.
"""

import re
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def docs_root() -> Path:
    """Return path to credence-docs directory."""
    return Path(__file__).resolve().parent.parent.parent / "credence-docs"


@pytest.mark.unit
def test_zero_npm_invariant(docs_root: Path) -> None:
    """Verify credence-docs strictly follows the zero-npm and zero-build invariant."""
    assert not (docs_root / "package.json").exists(), "credence-docs must not contain package.json"
    assert not (docs_root / "node_modules").exists(), "credence-docs must not contain node_modules"
    assert not (docs_root / "astro.config.mjs").exists(), "credence-docs must not contain Astro config"

    index_html = docs_root / "index.html"
    assert index_html.exists(), "index.html must exist"
    content = index_html.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "app.js" in content
    assert "styles.css" in content


@pytest.mark.unit
def test_docs_registry_parity(docs_root: Path) -> None:
    """Verify all paths in app.js DOCS_REGISTRY exist on disk and are non-empty."""
    app_js = docs_root / "app.js"
    assert app_js.exists(), "app.js must exist"

    content = app_js.read_text(encoding="utf-8")
    # Match all path: "..." in app.js
    paths = re.findall(r'path:\s*["\']([^"\']+)["\']', content)
    assert len(paths) >= 40, f"Expected at least 40 registered docs, found {len(paths)}"

    for rel_path in paths:
        file_path = docs_root / rel_path
        assert file_path.exists(), f"Registered path '{rel_path}' does not exist on disk"
        text = file_path.read_text(encoding="utf-8")
        assert len(text) > 100, f"Document '{rel_path}' is suspiciously small or empty"
        assert text.startswith("---"), f"Document '{rel_path}' is missing YAML frontmatter"
        assert "title:" in text, f"Document '{rel_path}' is missing title in frontmatter"
        assert "description:" in text, f"Document '{rel_path}' is missing description in frontmatter"


@pytest.mark.unit
def test_all_markdown_files_valid_frontmatter(docs_root: Path) -> None:
    """Verify all Markdown files in docs/ and blog/ have valid structure and frontmatter."""
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    assert len(md_files) >= 45, f"Expected at least 45 markdown files, found {len(md_files)}"

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        assert text.startswith("---"), f"File {md_file.name} missing frontmatter marker"

        # Extract frontmatter between --- and ---
        parts = text.split("---", 2)
        assert len(parts) >= 3, f"File {md_file.name} has malformed frontmatter"

        fm_yaml = parts[1]
        data = yaml.safe_load(fm_yaml)
        assert isinstance(data, dict), f"Frontmatter in {md_file.name} is not a valid YAML mapping"
        assert "title" in data, f"Missing 'title' in frontmatter of {md_file.name}"
        assert "description" in data, f"Missing 'description' in frontmatter of {md_file.name}"


@pytest.mark.unit
def test_interactive_playground_contract(docs_root: Path) -> None:
    """Verify playground.md and app.js have consistent DOM element IDs for all 7 widgets."""
    playground_file = docs_root / "docs" / "playground.md"
    assert playground_file.exists(), "playground.md must exist"
    p_content = playground_file.read_text(encoding="utf-8")

    app_js = docs_root / "app.js"
    js_content = app_js.read_text(encoding="utf-8")

    # Widget containers in markdown
    container_ids = [
        "mesh-simulator-widget",
        "simhash-calculator-widget",
        "grounding-tester-widget",
        "saturation-calculator-widget",
        "webcrypto-verifier-widget",
        "taxonomy-explorer-widget",
        "model-comparator-widget",
    ]
    for cid in container_ids:
        assert cid in p_content, f"Widget container '{cid}' missing in playground.md"

    # Interactive elements hooked in app.js
    interactive_ids = [
        "btn-broadcast-gossip",
        "btn-simulate-split",
        "btn-reset-mesh",
        "mesh-svg",
        "mesh-event-log",
        "simhash-text-a",
        "simhash-text-b",
        "btn-calc-simhash",
        "simhash-dh-val",
        "grounding-source-text",
        "grounding-quote-input",
        "btn-test-grounding",
        "grounding-status",
        "calc-violations",
        "calc-severity",
        "calc-confidence",
        "calc-result-score",
        "calc-result-badge",
        "btn-load-sample",
        "btn-verify-crypto",
        "crypto-json-input",
        "crypto-status",
        "taxonomy-search-input",
        "taxonomy-table-body",
        "comp-articles-slider",
        "comp-length-slider",
        "model-cards-container",
    ]

    for elem_id in interactive_ids:
        assert elem_id in p_content, f"Element ID '{elem_id}' missing in playground.md"
        assert elem_id in js_content, f"Element ID '{elem_id}' missing in app.js event handlers"


@pytest.mark.unit
def test_tutorial_yaml_code_blocks_syntax(docs_root: Path) -> None:
    """Verify all fenced YAML code blocks in tutorials and cookbooks are syntactically valid."""
    tutorial_files = list(docs_root.glob("docs/tutorials/*.md")) + list(docs_root.glob("docs/cookbooks/*.md"))

    for tut_file in tutorial_files:
        text = tut_file.read_text(encoding="utf-8")
        # Match ```yaml ... ``` blocks
        yaml_blocks = re.findall(r"```yaml\n([\s\S]*?)```", text)
        for idx, block in enumerate(yaml_blocks):
            try:
                parsed = yaml.safe_load(block)
                assert parsed is not None or len(block.strip()) == 0
            except Exception as e:
                pytest.fail(f"Invalid YAML block #{idx + 1} in {tut_file.name}: {e}")
