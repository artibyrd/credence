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
    path = Path(__file__).resolve().parent.parent.parent / "credence-docs"
    if not path.exists():
        pytest.skip("credence-docs directory not present in standalone repository checkout")
    return path


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
def test_ecosystem_version_parity(docs_root: Path) -> None:
    """Verify universal semantic version parity across all ecosystem repositories and web surfaces."""
    import json
    import tomllib

    ecosystem_root = docs_root.parent
    credence_root = ecosystem_root / "credence"
    agent_root = ecosystem_root / "credence-agent"

    # 1. Canonical version from pyproject.toml
    pyproject_path = credence_root / "pyproject.toml"
    assert pyproject_path.exists()
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    canonical_version = pyproject_data["tool"]["poetry"]["version"]

    # 2. Python __version__ in credence/__init__.py
    init_path = credence_root / "credence" / "__init__.py"
    assert init_path.exists()
    init_content = init_path.read_text(encoding="utf-8")
    assert f'__version__ = "{canonical_version}"' in init_content, (
        f"credence/__init__.py version does not match {canonical_version}"
    )

    # 3. credence-docs/index.html navbar badge
    docs_index_path = docs_root / "index.html"
    assert docs_index_path.exists()
    docs_index_content = docs_index_path.read_text(encoding="utf-8")
    assert f"v{canonical_version}" in docs_index_content, f"credence-docs/index.html missing badge v{canonical_version}"

    # 4. credence-docs/app.js brandBadge fallback
    docs_app_path = docs_root / "app.js"
    assert docs_app_path.exists()
    docs_app_content = docs_app_path.read_text(encoding="utf-8")
    assert f"'v{canonical_version}'" in docs_app_content or f'"v{canonical_version}"' in docs_app_content, (
        f"credence-docs/app.js brandBadge does not match v{canonical_version}"
    )

    # 5. credence-docs/docs/changelog.md latest release header
    changelog_path = docs_root / "docs" / "changelog.md"
    assert changelog_path.exists()
    changelog_content = changelog_path.read_text(encoding="utf-8")
    assert f"## [{canonical_version}]" in changelog_content, (
        f"docs/changelog.md missing release section ## [{canonical_version}]"
    )

    # 6. credence.run index.html brand & hero badge-pill
    web_run_index = credence_root / "web" / "credence.run" / "index.html"
    if web_run_index.exists():
        web_content = web_run_index.read_text(encoding="utf-8")
        assert f"v{canonical_version}" in web_content, f"web/credence.run/index.html missing badge v{canonical_version}"
        assert f"v{canonical_version} Stable" in web_content, (
            f"web/credence.run/index.html missing hero pill v{canonical_version} Stable"
        )

    # 7. credence-agent/plugin.json
    plugin_path = agent_root / "plugin.json"
    if plugin_path.exists():
        plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
        assert plugin_data["version"] == canonical_version, (
            f"credence-agent/plugin.json version does not match {canonical_version}"
        )


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
    """Verify playground.md and app.js have consistent DOM element IDs for all 8 widgets."""
    playground_file = docs_root / "docs" / "playground.md"
    assert playground_file.exists(), "playground.md must exist"
    p_content = playground_file.read_text(encoding="utf-8")

    app_js = docs_root / "app.js"
    js_content = app_js.read_text(encoding="utf-8")

    # Widget containers in markdown (all 8 widgets)
    container_ids = [
        "mesh-simulator-widget",
        "simhash-calculator-widget",
        "grounding-tester-widget",
        "saturation-calculator-widget",
        "webcrypto-verifier-widget",
        "taxonomy-explorer-widget",
        "model-comparator-widget",
        "feed-simulator-widget",
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
        "feed-suspicion-slider",
        "feed-grounding-slider",
        "feed-entropy-slider",
        "feed-freshness-slider",
        "feed-suspicion-val",
        "feed-grounding-val",
        "feed-entropy-val",
        "feed-freshness-val",
        "feed-result-score",
        "feed-result-badge",
        "feed-astroturf-status",
    ]

    for elem_id in interactive_ids:
        assert elem_id in p_content, f"Element ID '{elem_id}' missing in playground.md"
        assert elem_id in js_content, f"Element ID '{elem_id}' missing in app.js event handlers"


@pytest.mark.unit
def test_mermaid_diagram_syntax_integrity(docs_root: Path) -> None:
    """Verify all fenced mermaid code blocks in documentation have valid diagram headers."""
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    valid_diagram_types = (
        "graph",
        "flowchart",
        "sequencediagram",
        "classdiagram",
        "statediagram",
        "erdiagram",
        "journey",
        "gantt",
        "pie",
        "gitgraph",
        "mindmap",
        "timeline",
    )

    mermaid_count = 0
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        blocks = re.findall(r"```mermaid\n([\s\S]*?)```", text)
        for idx, block in enumerate(blocks):
            mermaid_count += 1
            lines = [
                line.strip()
                for line in block.strip().splitlines()
                if line.strip() and not line.strip().startswith("%%")
            ]
            assert len(lines) > 0, f"Empty Mermaid diagram block #{idx + 1} in {md_file.name}"
            first_token = lines[0].split()[0].lower()
            assert any(first_token.startswith(t) for t in valid_diagram_types), (
                f"Invalid Mermaid diagram type '{first_token}' in {md_file.name} block #{idx + 1}"
            )

    assert mermaid_count >= 24, f"Expected at least 24 Mermaid diagrams, found {mermaid_count}"


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


@pytest.mark.unit
def test_all_invariant_link_anchors_exist(docs_root: Path) -> None:
    """Verify all markdown links pointing to invariant anchors resolve to valid IDs in docs/invariants.md."""
    invariants_file = docs_root / "docs" / "invariants.md"
    assert invariants_file.exists(), "docs/invariants.md must exist"
    inv_text = invariants_file.read_text(encoding="utf-8")

    # Extract all declared invariant anchor IDs in docs/invariants.md
    declared_ids = set(re.findall(r'id=["\']([^"\']+)["\']', inv_text))
    assert len(declared_ids) >= 32, f"Expected at least 32 declared invariant anchors, found {len(declared_ids)}"

    # Scan all markdown files for links to invariants
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    total_inv_links = 0

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        # Match [Text](...invariants.md#anchor) or [Text](...invariants#anchor)
        links = re.findall(r"\[([^\]]+)\]\(([^)]*invariants(?:\.md)?#([^)]+))\)", text)
        for link_text, full_url, anchor in links:
            total_inv_links += 1
            assert anchor in declared_ids, (
                f"Broken invariant anchor '#{anchor}' referenced in {md_file.relative_to(docs_root)} "
                f"via [{link_text}]({full_url}). Valid anchors are: {sorted(declared_ids)[:5]}..."
            )

    assert total_inv_links >= 15, f"Expected at least 15 invariant links across catalog, found {total_inv_links}"
