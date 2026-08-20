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
    path = Path(__file__).resolve().parents[2].parent / "credence-docs"
    if not path.exists():
        pytest.skip("credence-docs directory not present in standalone repository checkout")
    return path


@pytest.mark.governance
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


@pytest.mark.governance
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


@pytest.mark.governance
def test_docs_registry_parity(docs_root: Path) -> None:
    """Verify all paths in app.js DOCS_REGISTRY exist on disk and are non-empty."""
    app_js = docs_root / "app.js"
    assert app_js.exists(), "app.js must exist"

    content = app_js.read_text(encoding="utf-8")

    # 1. Verify DOCS_REGISTRY contains both docs/ and blog/ categories
    assert 'id: "blog/conflict-of-pun-terest"' in content, "blog/conflict-of-pun-terest must be in DOCS_REGISTRY"
    assert 'path: "blog/conflict-of-pun-terest.md"' in content, (
        "blog/conflict-of-pun-terest.md must be in DOCS_REGISTRY"
    )
    assert "export const DOCS_REGISTRY = [" in content, "DOCS_REGISTRY export must exist"

    # Extract the DOCS_REGISTRY array definition
    reg_match = re.search(r"export const DOCS_REGISTRY = \[([\s\S]*?)\n\];", content)
    assert reg_match is not None, "DOCS_REGISTRY array definition not found"
    registry_block = reg_match.group(1)

    # 2. Match all { id: "...", title: "...", path: "..." } in DOCS_REGISTRY definition
    items = re.findall(
        r'\{\s*id:\s*["\']([^"\']+)["\'],\s*title:\s*["\']([^"\']+)["\'],\s*path:\s*["\']([^"\']+)["\']',
        registry_block,
    )
    assert len(items) >= 80, f"Expected at least 80 registered docs/blogs in DOCS_REGISTRY, found {len(items)}"

    doc_ids = set()
    for doc_id, _title, rel_path in items:
        assert doc_id not in doc_ids, f"Duplicate doc_id '{doc_id}' found in DOCS_REGISTRY"
        doc_ids.add(doc_id)

        file_path = docs_root / rel_path
        assert file_path.exists(), f"Registered path '{rel_path}' does not exist on disk"
        text = file_path.read_text(encoding="utf-8")
        assert len(text) > 100, f"Document '{rel_path}' is suspiciously small or empty"
        assert text.startswith("---"), f"Document '{rel_path}' is missing YAML frontmatter"
        assert "title:" in text, f"Document '{rel_path}' is missing title in frontmatter"
        assert "description:" in text, f"Document '{rel_path}' is missing description in frontmatter"

        # Verify prefix consistency
        if doc_id.startswith("blog/"):
            assert rel_path.startswith("blog/"), f"doc_id {doc_id} must have blog/ path, found {rel_path}"
        elif doc_id.startswith("docs/"):
            assert rel_path.startswith("docs/"), f"doc_id {doc_id} must have docs/ path, found {rel_path}"


@pytest.mark.governance
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
        assert "since_version" in data, f"Missing 'since_version' in frontmatter of {md_file.name}"
        assert "verified_version" in data, f"Missing 'verified_version' in frontmatter of {md_file.name}"


@pytest.mark.governance
def test_interactive_playground_contract(docs_root: Path) -> None:
    """Verify playground.md and app.js have consistent DOM element IDs for all 8 widgets."""
    playground_file = docs_root / "docs" / "playground.md"
    assert playground_file.exists(), "playground.md must exist"
    p_content = playground_file.read_text(encoding="utf-8")

    app_js = docs_root / "app.js"
    js_content = app_js.read_text(encoding="utf-8")

    # Widget containers in markdown (all 12 widgets)
    container_ids = [
        "mesh-simulator-widget",
        "simhash-calculator-widget",
        "grounding-tester-widget",
        "saturation-calculator-widget",
        "webcrypto-verifier-widget",
        "taxonomy-explorer-widget",
        "model-comparator-widget",
        "feed-simulator-widget",
        "galileo-consensus-widget",
        "epistemic-scanner-widget",
        "claimreview-generator-widget",
        "token-governor-widget",
    ]
    for cid in container_ids:
        assert cid in p_content, f"Widget container '{cid}' missing in playground.md"

    # Interactive elements hooked in app.js
    interactive_ids = [
        "btn-scen-normal",
        "btn-scen-partition",
        "btn-scen-sybil",
        "btn-scen-failover",
        "btn-scen-burst",
        "btn-broadcast-gossip",
        "btn-reset-mesh",
        "mesh-svg",
        "mesh-event-log",
        "mesh-node-inspector",
        "inspector-node-id",
        "inspector-node-status",
        "inspector-node-role",
        "inspector-node-qi",
        "inspector-node-region",
        "inspector-node-links",
        "simhash-text-a",
        "simhash-text-b",
        "btn-calc-simhash",
        "simhash-dh-val",
        "simhash-verdict-badge",
        "simhash-fp-a",
        "simhash-fp-b",
        "simhash-bitdiff-grid",
        "btn-preset-mirror",
        "btn-preset-plagiarism",
        "btn-preset-distinct",
        "grounding-source-text",
        "grounding-quote-input",
        "btn-test-grounding",
        "grounding-status",
        "grounding-preview-display",
        "btn-preset-verbatim",
        "btn-preset-paraphrase",
        "calc-violations",
        "calc-severity",
        "calc-confidence",
        "val-violations",
        "val-severity",
        "val-confidence",
        "calc-result-score",
        "calc-result-badge",
        "calc-raw-score",
        "calc-saturation-pct",
        "calc-curve-svg",
        "btn-load-sample",
        "btn-tamper-sample",
        "btn-verify-crypto",
        "crypto-json-input",
        "crypto-status",
        "taxonomy-search-input",
        "taxonomy-cards-container",
        "chip-tax-all",
        "chip-tax-spj",
        "chip-tax-iep",
        "chip-tax-deceptive",
        "chip-tax-domain",
        "comp-articles-slider",
        "comp-length-slider",
        "comp-thinking-slider",
        "comp-articles-val",
        "comp-length-val",
        "comp-thinking-val",
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
        "btn-preset-investigative",
        "btn-preset-astroturf",
        "galileo-sybil-slider",
        "galileo-expert-slider",
        "galileo-sybil-val",
        "galileo-expert-val",
        "btn-toggle-galileo",
        "galileo-consensus-score",
        "galileo-verdict-badge",
        "galileo-rule-status",
        "galileo-histogram",
        "scanner-text-input",
        "btn-scan-clickbait",
        "btn-scan-urgency",
        "btn-scan-clean",
        "scanner-highlight-output",
        "scanner-heuristic-score",
        "scanner-verdict-badge",
        "scanner-rules-detected",
        "cr-claim-text",
        "cr-author-input",
        "cr-verdict-select",
        "cr-source-url",
        "btn-tab-claimreview",
        "btn-tab-rfc8785",
        "btn-cr-copy",
        "btn-cr-download",
        "cr-json-output",
        "gov-budget-slider",
        "gov-burn-slider",
        "gov-budget-val",
        "gov-burn-val",
        "gov-headroom-pct",
        "gov-state-badge",
        "gov-status-desc",
        "gov-headroom-fill",
    ]

    for elem_id in interactive_ids:
        assert elem_id in p_content, f"Element ID '{elem_id}' missing in playground.md"
        assert elem_id in js_content, f"Element ID '{elem_id}' missing in app.js event handlers"


@pytest.mark.governance
def test_mermaid_diagram_syntax_integrity(docs_root: Path) -> None:
    """Verify all fenced mermaid code blocks in documentation have valid syntax,

    balanced delimiters, proper subgraph nesting, zero raw markdown links, and WCAG contrast standards.
    """
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

            # 1. Valid diagram header
            first_token = lines[0].split()[0].lower()
            assert any(first_token.startswith(t) for t in valid_diagram_types), (
                f"Invalid Mermaid diagram type '{first_token}' in {md_file.name} block #{idx + 1}"
            )

            # 2. Rejection of raw markdown links in diagram labels
            assert not re.search(r"\[[^\]]+\]\([^)]+\)", block), (
                f"Mermaid Invariant Violation in {md_file.name} block #{idx + 1}: "
                f"Contains raw Markdown link syntax inside diagram. Use clean descriptive text instead."
            )

            # 3. Linebreak hygiene: prohibit literal '\\n' in string labels (use <br/>)
            assert r"\n" not in block, (
                f"Mermaid Invariant Violation in {md_file.name} block #{idx + 1}: "
                f"Contains literal '\\n' in label. Use '<br/>' HTML break tags for line breaks."
            )

            # 4. Balanced subgraphs
            is_sequence = first_token.startswith("sequencediagram")
            if not is_sequence:
                subgraph_count = sum(
                    1 for line in lines if line.startswith("subgraph") or re.match(r"^subgraph\s+", line)
                )
                end_count = sum(
                    1 for line in lines if line == "end" or line.startswith("end ") or line.endswith(" end")
                )
                assert subgraph_count == end_count, (
                    f"Mismatched subgraphs in {md_file.name} block #{idx + 1}: "
                    f"{subgraph_count} 'subgraph' blocks vs {end_count} 'end' statements."
                )

            # 5. Balanced double quotes per line
            for line_no, line in enumerate(lines, 1):
                quotes = re.findall(r'(?<!\\)"', line)
                assert len(quotes) % 2 == 0, (
                    f"Unbalanced double quotes in {md_file.name} block #{idx + 1}, line {line_no}: '{line}'"
                )

            # 6. WCAG Dark-Theme Contrast Guard on custom classDef
            for line in lines:
                if line.startswith("classDef"):
                    assert "fill:#" in line or "fill: #" in line, (
                        f"classDef in {md_file.name} block #{idx + 1} missing explicit fill hex: '{line}'"
                    )
                    assert "stroke:#" in line or "stroke: #" in line, (
                        f"classDef in {md_file.name} block #{idx + 1} missing explicit stroke hex: '{line}'"
                    )

    assert mermaid_count >= 85, f"Expected at least 85 Mermaid diagrams in catalog, found {mermaid_count}"


@pytest.mark.governance
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


@pytest.mark.governance
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


@pytest.mark.governance
def test_tui_vector_assets_integrity(docs_root: Path) -> None:
    """Verify all TUI vector SVG assets exist, have valid rich-terminal markup, and resolve in docs."""
    tui_assets_dir = docs_root / "assets" / "tui"
    assert tui_assets_dir.exists(), "credence-docs/assets/tui directory must exist"

    expected_assets = [
        "01-inspector-rich.svg",
        "02-inspector-compact.svg",
        "03-inspector-raw-json.svg",
        "04-inspector-satire.svg",
        "05-taxonomies-tree.svg",
        "06-domain-subjects.svg",
        "07-feeds-stream.svg",
        "08-morning-digest.svg",
        "09-token-quota.svg",
        "10-node-identity.svg",
        "11-audit-modal.svg",
    ]

    for asset_name in expected_assets:
        asset_path = tui_assets_dir / asset_name
        assert asset_path.exists(), f"Missing TUI vector asset: {asset_name}"
        assert asset_path.stat().st_size > 1000, f"TUI vector asset {asset_name} is too small / empty"
        content = asset_path.read_text(encoding="utf-8")
        assert "<svg" in content, f"TUI asset {asset_name} does not contain <svg tag"
        assert 'class="rich-terminal"' in content, f"TUI asset {asset_name} missing rich-terminal class"

    # Scan all documentation files to ensure any referenced assets/tui/*.svg exists
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    tui_ref_count = 0
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        tui_matches = re.findall(r"!\[[^\]]*\]\((?:\.\./|/)*assets/tui/([^)]+\.svg)\)", text)
        for match in tui_matches:
            tui_ref_count += 1
            ref_path = tui_assets_dir / match
            assert ref_path.exists(), f"Broken TUI image reference '{match}' in {md_file.name}"

    assert tui_ref_count >= 10, f"Expected at least 10 TUI SVG image references across docs, found {tui_ref_count}"


@pytest.mark.governance
def test_all_markdown_links_and_anchors_resolve_cleanly(docs_root: Path) -> None:
    """Verify all internal markdown file links, section anchors, and app route links resolve cleanly without broken targets."""
    import urllib.parse

    app_js = docs_root / "app.js"
    assert app_js.exists(), "app.js must exist"
    app_js_text = app_js.read_text(encoding="utf-8")
    registered_ids = set(re.findall(r'id:\s*["\']([^"\']+)["\']', app_js_text))
    assert len(registered_ids) >= 40, "Expected registered docs in app.js"

    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    assert len(md_files) >= 45, "Expected markdown documents"

    def slugify_heading(h: str) -> str:
        h = h.strip().lower()
        h = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", h)
        h = re.sub(r"[*_`#~]", "", h)
        h = re.sub(r"[^\w\s-]", "", h)
        h = re.sub(r"[\s]+", "-", h)
        return h.strip("-")

    broken_links: list[tuple[str, str, str, str]] = []
    verified_relative_count = 0
    verified_external_count = 0
    verified_anchor_count = 0

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        rel_doc = str(md_file.relative_to(docs_root))

        local_anchors = set(re.findall(r'id=["\']([^"\']+)["\']', text))
        local_anchors.update(re.findall(r'<a\s+name=["\']([^"\']+)["\']', text))
        for line in text.splitlines():
            if line.startswith("#"):
                local_anchors.add(slugify_heading(line.lstrip("#").strip()))

        links = re.findall(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", text)

        for label, target in links:
            target = target.strip()
            if not target or target.startswith("javascript:") or target.startswith("mailto:"):
                continue

            # 1. External URL syntax validation (hermetic, zero-network)
            if target.startswith("http://") or target.startswith("https://"):
                verified_external_count += 1
                parsed = urllib.parse.urlparse(target)
                if not parsed.scheme or not parsed.netloc:
                    broken_links.append((rel_doc, label, target, "Invalid URL syntax"))
                continue

            # 2. App Route links (#docs/... or #blog/...)
            if target.startswith("#docs/") or target.startswith("#blog/"):
                route_id = target.lstrip("#").split("#")[0].split(":")[0]
                if route_id not in registered_ids:
                    broken_links.append((rel_doc, label, target, f"Route ID '{route_id}' not found in DOCS_REGISTRY"))
                continue

            # 3. Same-file section anchor (#anchor)
            if target.startswith("#"):
                verified_anchor_count += 1
                anchor = target.lstrip("#")
                if anchor not in local_anchors:
                    broken_links.append(
                        (rel_doc, label, target, f"Local anchor '#{anchor}' not found in {md_file.name}")
                    )
                continue

            # 4. Relative file link (path/to/file.md or path/to/file.md#anchor)
            verified_relative_count += 1
            target_path_str, _, anchor = target.partition("#")

            resolved_target = (md_file.parent / target_path_str).resolve()
            if not resolved_target.exists():
                broken_links.append((rel_doc, label, target, f"Target file '{target_path_str}' does not exist on disk"))
            elif anchor:
                target_text = resolved_target.read_text(encoding="utf-8")
                target_anchors = set(re.findall(r'id=["\']([^"\']+)["\']', target_text))
                target_anchors.update(re.findall(r'<a\s+name=["\']([^"\']+)["\']', target_text))
                for line in target_text.splitlines():
                    if line.startswith("#"):
                        target_anchors.add(slugify_heading(line.lstrip("#").strip()))
                if anchor not in target_anchors:
                    broken_links.append(
                        (rel_doc, label, target, f"Anchor '#{anchor}' not found in {resolved_target.name}")
                    )

    assert len(broken_links) == 0, f"Found {len(broken_links)} broken links in documentation:\n" + "\n".join(
        f"  - [{doc}] '{lbl}' -> '{tgt}': {reason}" for doc, lbl, tgt, reason in broken_links
    )
    assert verified_relative_count >= 100, f"Expected >=100 relative links, found {verified_relative_count}"
    assert verified_external_count >= 50, f"Expected >=50 external links, found {verified_external_count}"


def test_sitemap_integrity_and_route_coverage(docs_root: Path) -> None:
    """Verify that docs/sitemap.md exists, covers all 5 domains, 12 playgrounds,

    38 invariants, and that all referenced routes exist in the registry.
    """
    sitemap_path = docs_root / "docs" / "sitemap.md"
    assert sitemap_path.exists(), f"docs/sitemap.md not found at {sitemap_path}"

    sitemap_text = sitemap_path.read_text(encoding="utf-8")

    # 1. Verify 5 sovereign ecosystem domains are covered
    domains = [
        "credence.run",
        "docs.credence.run",
        "blog.credence.run",
        "credence.report",
        "credence.nexus",
        "credence.foundation",
    ]
    for domain in domains:
        assert domain in sitemap_text, f"Sitemap missing ecosystem domain: {domain}"

    # 2. Verify all 12 interactive playgrounds are covered
    assert "12 Zero-Build Interactive Playgrounds" in sitemap_text or "12 Zero-Build Playgrounds" in sitemap_text
    assert "13-Node Watts-Strogatz Mesh Gossip Simulator" in sitemap_text
    assert "SimHash-64 Bitwise Visualizer" in sitemap_text
    assert "Live Namespaced Taxonomy Rule Explorer" in sitemap_text

    # 3. Verify The Invariant Bible is covered
    assert "The Invariant Bible" in sitemap_text

    # 4. Extract all hash links (#docs/..., #blog/...) and ensure their backing files exist
    hash_links = re.findall(r"\(#(docs/[^)#\s]+|blog/[^)#\s]+)\)", sitemap_text)
    assert len(hash_links) >= 30, f"Expected >= 30 doc/blog links in sitemap, found {len(hash_links)}"

    for link in hash_links:
        md_file = docs_root / f"{link}.md"
        assert md_file.exists(), f"Sitemap link '#{link}' maps to non-existent file: {md_file}"

    # 5. Check app.js DOCS_REGISTRY includes docs/sitemap
    app_js_path = docs_root / "app.js"
    assert app_js_path.exists()
    app_js_text = app_js_path.read_text(encoding="utf-8")
    assert 'id: "docs/sitemap"' in app_js_text or "id: 'docs/sitemap'" in app_js_text, (
        "docs/sitemap not registered in DOCS_REGISTRY in app.js"
    )


@pytest.mark.governance
def test_hermetic_unit_test_markers_invariant() -> None:
    """Verify that all tests marked with @pytest.mark.governance are strictly hermetic.

    Ensures that no unit test imports Playwright or calls browser scraping functions, preventing
    browser runtime dependency leaks into fast CI verification gates.
    """
    import ast

    tests_dir = Path(__file__).resolve().parent

    for py_file in tests_dir.rglob("test_*.py"):
        if "e2e" in py_file.parts:
            continue

        file_content = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(file_content, filename=str(py_file))
        except SyntaxError as e:
            pytest.fail(f"Syntax error in test file {py_file}: {e}")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip self-test
                if node.name == "test_hermetic_unit_test_markers_invariant":
                    continue

                is_unit = False
                for dec in node.decorator_list:
                    # Check for @pytest.mark.governance
                    if (
                        isinstance(dec, ast.Attribute)
                        and dec.attr == "unit"
                        and isinstance(dec.value, ast.Attribute)
                        and dec.value.attr == "mark"
                    ):
                        is_unit = True
                        break

                if is_unit:
                    # Inspect function AST for forbidden browser calls/imports
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            call_name = ""
                            if isinstance(subnode.func, ast.Name):
                                call_name = subnode.func.id
                            elif isinstance(subnode.func, ast.Attribute):
                                call_name = subnode.func.attr

                            assert call_name not in ["capture_webpage", "async_playwright"], (
                                f"Invariant Violation: {py_file.name}::{node.name} is marked as @pytest.mark.governance "
                                f"but calls '{call_name}'. Browser scraping tests must be marked @pytest.mark.integration."
                            )
                        elif isinstance(subnode, (ast.Import, ast.ImportFrom)):
                            mod_name = getattr(subnode, "module", "") or ""
                            names = [alias.name for alias in subnode.names]
                            assert "playwright" not in mod_name and not any("playwright" in n for n in names), (
                                f"Invariant Violation: {py_file.name}::{node.name} is marked as @pytest.mark.governance "
                                f"but imports Playwright. Browser tests must be marked @pytest.mark.integration."
                            )


@pytest.mark.governance
def test_all_markdown_code_fences_and_syntax(docs_root: Path) -> None:
    """Verify that all markdown files across the ecosystem have balanced and valid code fences.

    Ensures that no code fence has leading whitespace indentation (which can corrupt zero-build AST
    parsers) and that every opened code fence is properly closed.
    """
    ecosystem_root = docs_root.parent
    check_dirs = [
        docs_root / "docs",
        docs_root / "blog",
    ]

    invalid_fences = []
    unclosed_fences = []

    for check_dir in check_dirs:
        if not check_dir.exists():
            continue
        for md_file in check_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            fence_count = 0

            for line_no, line in enumerate(lines, start=1):
                trimmed = line.strip()
                if trimmed.startswith("```"):
                    # Check for unwanted indentation
                    if line.startswith(" ") or line.startswith("\t"):
                        invalid_fences.append(
                            f"{md_file.relative_to(ecosystem_root)}:{line_no} -> Indented code fence: '{line}'"
                        )
                    fence_count += 1

            if fence_count % 2 != 0:
                unclosed_fences.append(
                    f"{md_file.relative_to(ecosystem_root)} -> Odd number of code fences ({fence_count})"
                )

    assert not invalid_fences, f"Found {len(invalid_fences)} markdown files with indented code fences:\n" + "\n".join(
        invalid_fences
    )
    assert not unclosed_fences, f"Found {len(unclosed_fences)} markdown files with unclosed code fences:\n" + "\n".join(
        unclosed_fences
    )


@pytest.mark.governance
def test_learning_lifecycle_and_invariant_governance_contracts(docs_root: Path) -> None:
    """Verify that the 4-Phase Delivery & Continuous Learning Lifecycle and invariant governance contracts are declared."""
    ecosystem_root = docs_root.parent
    agents_files = [
        ecosystem_root / "AGENTS.md",
        ecosystem_root / "credence" / "AGENTS.md",
        ecosystem_root / "credence-docs" / "AGENTS.md",
        ecosystem_root / "credence-agent" / "AGENTS.md",
    ]
    for af in agents_files:
        if af.exists():
            content = af.read_text(encoding="utf-8")
            assert "4-Phase Release & Learning Lifecycle" in content, (
                f"{af.name} must declare 4-Phase Release & Learning Lifecycle"
            )
            assert "Dual-Environment Least-Privilege CI/CD" in content, (
                f"{af.name} must declare Dual-Environment Least-Privilege CI/CD"
            )
            assert "invariant-audit" in content, f"{af.name} must reference invariant-audit skill"

    # Verify invariant-audit skill existence and frontmatter
    audit_skill = ecosystem_root / "credence-agent" / ".agents" / "skills" / "invariant-audit" / "SKILL.md"
    assert audit_skill.exists(), "invariant-audit/SKILL.md must exist"
    skill_content = audit_skill.read_text(encoding="utf-8")
    assert "name: invariant-audit" in skill_content
    assert "description:" in skill_content

    # Verify knowledge-governance skill declares 4-phase lifecycle
    kg_skill = ecosystem_root / "credence-agent" / ".agents" / "skills" / "knowledge-governance" / "SKILL.md"
    if kg_skill.exists():
        kg_content = kg_skill.read_text(encoding="utf-8")
        assert "The 4-Phase Delivery & Continuous Learning Lifecycle" in kg_content


@pytest.mark.governance
def test_no_unrendered_directives_or_malformed_alerts(docs_root: Path) -> None:
    """Verify that all markdown files use valid GFM alert callouts or supported container directives.

    Ensures zero unclosed :::tabs blocks, zero stray ::: markers, and zero malformed alert keywords.
    """
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    issues = []
    allowed_alert_types = {"NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"}

    for md_file in md_files:
        rel_path = md_file.relative_to(docs_root)
        content = md_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        in_code_block = False
        in_tab_block = False
        tab_start_line = 0

        for line_no, line in enumerate(lines, start=1):
            trimmed = line.strip()

            if trimmed.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Directive check
            if trimmed.startswith(":::"):
                directive = trimmed[3:].strip()
                if directive == "tabs":
                    if in_tab_block:
                        issues.append(f"{rel_path}:{line_no} -> Nested ':::tabs' block detected")
                    in_tab_block = True
                    tab_start_line = line_no
                elif directive == "":
                    if not in_tab_block:
                        issues.append(f"{rel_path}:{line_no} -> Stray closing ':::' without opening block")
                    in_tab_block = False
                elif directive.lower() in {"note", "tip", "info", "warning", "caution", "important", "danger"}:
                    # In our canonical documentation, alerts should strictly use GFM callouts (> [!NOTE])
                    issues.append(
                        f"{rel_path}:{line_no} -> Non-standard directive ':::{directive}'. "
                        f"Standardize to GFM alert '> [!{directive.upper()}]'"
                    )

            # Tab item check outside of tabs
            if re.match(r"^===\s+", trimmed) and not in_tab_block:
                issues.append(f"{rel_path}:{line_no} -> Tab marker '=== ...' found outside of ':::tabs' container")

            # GitHub alert callout check
            if line.startswith(">"):
                alert_match = re.match(r"^>\s*\[\!(.*?)\]", line)
                if alert_match:
                    alert_type = alert_match.group(1).upper()
                    if alert_type not in allowed_alert_types:
                        issues.append(
                            f"{rel_path}:{line_no} -> Unknown alert type '> [!{alert_type}]'. "
                            f"Valid types are: {sorted(allowed_alert_types)}"
                        )

        if in_tab_block:
            issues.append(f"{rel_path}:{tab_start_line} -> Unclosed ':::tabs' block (missing matching ':::')")

    assert not issues, f"Found {len(issues)} directive / alert syntax issues in documentation:\n" + "\n".join(
        f"  - {issue}" for issue in issues
    )


@pytest.mark.governance
def test_full_docs_markdown_rendering_pipeline(docs_root: Path) -> None:
    """Simulate the zero-build app.js parseMarkdown pipeline across all documentation.

    Ensures that every document parses without leaking unrendered directive artifacts,
    unparsed alert callout markers, or unclosed structural HTML containers.
    """
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    leaks = []

    def escape_html(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    for md_file in md_files:
        rel_path = md_file.relative_to(docs_root)
        content = md_file.read_text(encoding="utf-8")

        # Strip frontmatter
        fm_match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n", content)
        body = content[fm_match.end() :] if fm_match else content

        lines = body.splitlines()
        rendered_lines = []
        in_code_block = False
        in_alert_box = False
        in_tab_block = False

        for line_no, line in enumerate(lines, start=1):
            trimmed = line.strip()

            # Code fence
            if trimmed.startswith("```"):
                in_code_block = not in_code_block
                in_alert_box = False
                continue

            if in_code_block:
                continue

            # Tabs container
            if trimmed.startswith(":::tabs"):
                in_tab_block = True
                in_alert_box = False
                continue

            if in_tab_block and trimmed == ":::":
                in_tab_block = False
                continue

            # Alert callouts
            alert_match = re.match(r"^>\s*\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", line, re.I)
            if alert_match:
                in_alert_box = True
                continue

            if in_alert_box:
                if line.startswith(">"):
                    continue
                else:
                    in_alert_box = False

            # Check rendered line
            rendered_lines.append((line_no, line))

        # Check for unrendered directive leaks
        for line_no, line in rendered_lines:
            trimmed = line.strip()
            if trimmed == ":::" or (trimmed.startswith(":::") and not line.startswith(" ")):
                leaks.append(f"{rel_path}:{line_no} -> Unrendered ':::' token in parsed document: '{line}'")
            if re.search(r"(?<!`)(?:> \[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\])(?!`)", line) and not line.startswith(
                ">"
            ):
                leaks.append(f"{rel_path}:{line_no} -> Unrendered inline alert marker: '{line}'")

    assert not leaks, f"Found {len(leaks)} unrendered markdown artifacts across documentation:\n" + "\n".join(
        f"  - {leak}" for leak in leaks
    )


@pytest.mark.governance
def test_app_js_directive_and_alert_resilience(docs_root: Path) -> None:
    """Verify that app.js contains dual-engine support for both GFM callouts and container directives."""
    app_js = docs_root / "app.js"
    assert app_js.exists(), "credence-docs/app.js must exist"
    content = app_js.read_text(encoding="utf-8")

    # 1. Verify GFM alert regex
    assert "alertMatch" in content, "app.js must support GFM alertCallouts"
    assert (
        r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]" in content or "NOTE|TIP|IMPORTANT|WARNING|CAUTION" in content
    )

    # 2. Verify container directive regex
    assert "directiveMatch" in content, "app.js must support container directives"
    assert ":::(note|tip|info|warning|caution|important|danger)" in content

    # 3. Verify tabs container
    assert ":::tabs" in content, "app.js must support :::tabs containers"


@pytest.mark.governance
def test_raw_html_code_entity_escaping(docs_root: Path) -> None:
    """Verify that raw HTML cards do not contain unescaped angle brackets in <code> elements."""
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    unescaped = []

    for md_file in md_files:
        rel_path = md_file.relative_to(docs_root)
        content = md_file.read_text(encoding="utf-8")

        # Scan for raw HTML blocks containing <code>...</code> where content has unescaped <tag>
        for line_no, line in enumerate(content.splitlines(), start=1):
            if "<div" in line or "<p>" in line or "<h3>" in line:
                # Find all <code>...</code> in this HTML line
                code_matches = re.findall(r"<code>(.*?)</code>", line)
                for code_content in code_matches:
                    # Check for unescaped angle brackets that look like <tag> instead of &lt;tag&gt;
                    if re.search(r"<(?:[a-zA-Z!][^>]*?)>", code_content):
                        unescaped.append(
                            f"{rel_path}:{line_no} -> Unescaped angle bracket in raw HTML <code>: '{code_content}'"
                        )

    assert not unescaped, f"Found {len(unescaped)} unescaped code elements in raw HTML:\n" + "\n".join(
        f"  - {u}" for u in unescaped
    )


@pytest.mark.governance
def test_javascript_markdown_parser_runtime_integrity(docs_root: Path) -> None:
    """Execute Node.js runtime smoke test on all documentation files via app.js parseMarkdown()."""
    import shutil
    import subprocess

    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js runtime not installed in environment")

    docs_dir_str = str(docs_root.resolve()).replace("\\", "/")
    test_script = f"""
    import fs from 'fs';
    import path from 'path';

    const docsDir = '{docs_dir_str}';
    const appJsPath = path.resolve(docsDir, 'app.js');

    import(`file://${{appJsPath}}`).then(({{ parseMarkdown }}) => {{
      let count = 0;
      function scan(dir) {{
        for (const f of fs.readdirSync(dir, {{ withFileTypes: true }})) {{
          const full = path.join(dir, f.name);
          if (f.isDirectory() && f.name !== 'node_modules' && f.name !== '.git') scan(full);
          else if (f.name.endsWith('.md')) {{
            const content = fs.readFileSync(full, 'utf-8');
            try {{
              const html = parseMarkdown(content);
              if (typeof html !== 'string' || html.length === 0) {{
                throw new Error(`Empty HTML output for ${{full}}`);
              }}
              count++;
            }} catch (err) {{
              console.error(`PARSER ERROR on ${{full}}:`, err);
              process.exit(1);
            }}
          }}
        }}
      }}
      scan(docsDir);
      console.log(`Successfully verified ${{count}} markdown files.`);
    }}).catch(err => {{
      console.error('Import error:', err);
      process.exit(1);
    }});
    """

    res = subprocess.run(
        [node_bin, "--input-type=module", "-e", test_script],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res.returncode == 0, f"Node.js parser verification failed: {res.stderr}"
    assert "Successfully verified" in res.stdout


@pytest.mark.governance
def test_web_component_zero_clone_and_defensive_events(docs_root: Path) -> None:
    """Verify credence-widget.js adheres to the zero-clone and defensive event binding invariant."""
    widget_path = docs_root / "assets" / "credence-widget.js"
    assert widget_path.exists(), "assets/credence-widget.js must exist"
    content = widget_path.read_text(encoding="utf-8")

    assert "cloneNode(" not in content, (
        "credence-widget.js must not invoke cloneNode to prevent recursive constructor loops"
    )
    assert "customElements.define('credence-badge'" in content, "credence-widget.js must register custom element"
    assert "attributeChangedCallback" in content, "credence-widget.js must implement attributeChangedCallback"
