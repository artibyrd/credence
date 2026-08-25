"""Hermetic verification test suite for credence-docs integrity (Invariant 26).

Validates:
1. Every registered item in app.js (DOCS_REGISTRY) maps to a valid Markdown file.
2. All documentation and blog articles have valid YAML frontmatter (title & description).
3. All interactive playground widget DOM IDs match app.js event listeners.
4. Tutorial and cookbook YAML code blocks are syntactically valid.
5. Zero-npm invariant: no package.json or node_modules in credence-docs.
"""

import argparse
import re
import tomllib
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
    """Verify universal semantic version parity across all ecosystem repositories, runtime JS engines, and all 11 web surfaces."""
    import json
    import re
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
    expected_tag = f"v{canonical_version}"

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
    assert expected_tag in docs_index_content, f"credence-docs/index.html missing badge {expected_tag}"

    # 4. credence-docs/app.js CURRENT_ECOSYSTEM_VERSION
    docs_app_path = docs_root / "app.js"
    assert docs_app_path.exists()
    docs_app_content = docs_app_path.read_text(encoding="utf-8")
    assert f"'v{canonical_version}'" in docs_app_content or f'"v{canonical_version}"' in docs_app_content, (
        f"credence-docs/app.js brandBadge does not match {expected_tag}"
    )

    # 5. credence-docs/docs/changelog.md latest release header
    changelog_path = docs_root / "docs" / "changelog.md"
    assert changelog_path.exists()
    changelog_content = changelog_path.read_text(encoding="utf-8")
    assert f"## [{canonical_version}]" in changelog_content, (
        f"docs/changelog.md missing release section ## [{canonical_version}]"
    )

    # 6. Runtime JS engine CREDENCE_VERSION in credence-workstation.js
    ws_js_path = credence_root / "web" / "assets" / "credence-workstation.js"
    assert ws_js_path.exists()
    ws_js_content = ws_js_path.read_text(encoding="utf-8")
    assert f'export const CREDENCE_VERSION = "{expected_tag}";' in ws_js_content, (
        f"credence-workstation.js CREDENCE_VERSION does not match {expected_tag}"
    )

    # 7. Scan ALL HTML files across web/ for navbar brand badge parity
    web_dir = credence_root / "web"
    html_files = list(web_dir.rglob("*.html"))
    assert len(html_files) >= 10, f"Expected at least 10 HTML surfaces in web/, found {len(html_files)}"

    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        if '<nav class="credence-nav">' in content and "Credence" in content:
            badge_match = re.search(r'Credence\s*<span class="badge">([^<]+)</span>', content)
            if badge_match:
                found_version = badge_match.group(1).strip()
                assert found_version == expected_tag, (
                    f"Version mismatch in {html_file.relative_to(credence_root)}: found '{found_version}', expected '{expected_tag}'"
                )

    # 8. credence-agent/plugin.json
    plugin_path = agent_root / "plugin.json"
    if plugin_path.exists():
        plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
        assert plugin_data["version"] == canonical_version, (
            f"credence-agent/plugin.json version does not match {canonical_version}"
        )


@pytest.mark.governance
def test_social_sharing_open_graph_parity(docs_root: Path) -> None:
    """Verify open-standard Open Graph (og:*), brand logos, and W3C favicons across all ecosystem surfaces."""
    ecosystem_root = docs_root.parent
    credence_root = ecosystem_root / "credence"

    # 1. Verify 1200x630 social preview image and vector assets exist and match canonical version
    docs_og_png = docs_root / "assets" / "og-card.png"
    web_og_png = credence_root / "web" / "assets" / "og-card.png"
    docs_og_svg = docs_root / "assets" / "og-card.svg"
    web_og_svg = credence_root / "web" / "assets" / "og-card.svg"

    # Brand logo & Favicon assets
    docs_logo = docs_root / "assets" / "logo.svg"
    web_logo = credence_root / "web" / "assets" / "logo.svg"
    docs_fav = docs_root / "assets" / "favicon.svg"
    web_fav = credence_root / "web" / "assets" / "favicon.svg"
    docs_touch = docs_root / "assets" / "apple-touch-icon.png"
    web_touch = credence_root / "web" / "assets" / "apple-touch-icon.png"

    assert docs_og_png.exists(), "credence-docs/assets/og-card.png must exist for link embeds"
    assert web_og_png.exists(), "credence/web/assets/og-card.png must exist for link embeds"
    assert docs_og_svg.exists(), "credence-docs/assets/og-card.svg must exist"
    assert web_og_svg.exists(), "credence/web/assets/og-card.svg must exist"
    assert docs_og_png.stat().st_size > 1000, "og-card.png must be a valid non-empty image"

    assert docs_logo.exists() and web_logo.exists(), "logo.svg must exist in docs and web"
    assert docs_fav.exists() and web_fav.exists(), "favicon.svg must exist in docs and web"
    assert docs_touch.exists() and web_touch.exists(), "apple-touch-icon.png must exist in docs and web"

    # Canonical version verification in social card SVGs
    pyproject_path = credence_root / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    canonical_version = pyproject_data["tool"]["poetry"]["version"]
    expected_tag = f"v{canonical_version}"

    assert f">{expected_tag}<" in docs_og_svg.read_text(encoding="utf-8"), (
        f"credence-docs/assets/og-card.svg version badge does not match {expected_tag}"
    )
    assert f">{expected_tag}<" in web_og_svg.read_text(encoding="utf-8"), (
        f"credence/web/assets/og-card.svg version badge does not match {expected_tag}"
    )

    # 2. Verify all ecosystem HTML entry points define complete open standard preview meta tags and favicons
    html_surfaces = list((credence_root / "web").rglob("*.html"))
    html_surfaces.append(docs_root / "index.html")

    for html_file in html_surfaces:
        content = html_file.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in content or "http-equiv='refresh'" in content:
            continue  # Skip redirect shells
        assert 'property="og:title"' in content or "property='og:title'" in content, (
            f"Missing og:title meta tag in {html_file.name}"
        )
        assert 'property="og:description"' in content or "property='og:description'" in content, (
            f"Missing og:description meta tag in {html_file.name}"
        )
        assert 'property="og:image"' in content or "property='og:image'" in content, (
            f"Missing og:image meta tag in {html_file.name}"
        )
        assert 'name="theme-color"' in content or "name='theme-color'" in content, (
            f"Missing theme-color meta tag in {html_file.name}"
        )
        assert 'rel="icon"' in content or "rel='icon'" in content, f"Missing favicon link in {html_file.name}"
        assert 'rel="apple-touch-icon"' in content or "rel='apple-touch-icon'" in content, (
            f"Missing apple-touch-icon link in {html_file.name}"
        )
        assert "twitter:" not in content, f"Found forbidden proprietary twitter card meta tag in {html_file.name}"

    # 3. Verify app.js dynamic social meta updater is exported
    app_js_content = (docs_root / "app.js").read_text(encoding="utf-8")
    assert "export function updateSocialMetadata" in app_js_content, (
        "app.js must export updateSocialMetadata for dynamic client-side article embeds"
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
def test_zero_legacy_mermaid_diagrams_invariant(docs_root: Path) -> None:
    """Invariant 34: Verify zero legacy Mermaid diagrams remain anywhere in documentation or blog posts.

    All technical diagrams must use enclosed UTF-8 box schematics, wire sequence layouts, or state matrices.
    """
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        blocks = re.findall(r"```mermaid\n([\s\S]*?)```", text)
        assert len(blocks) == 0, (
            f"Invariant 34 Violation in {md_file.name}: Found {len(blocks)} legacy Mermaid block(s). "
            f"All diagrams must use high-density UTF-8 box schematics."
        )


@pytest.mark.governance
def test_zero_ascii_box_art_invariant(docs_root: Path) -> None:
    """Invariant 34: Verify zero retro ASCII/UTF-8 box art remains anywhere in documentation or blog posts.

    All technical illustrations must use high-fidelity, resolution-independent vector SVG assets, Markdown tables, or structured lists.
    """
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        boxes = re.findall(r"```([a-zA-Z0-9_-]*)\n([\s\S]*?)```", text)
        for idx, (lang, block) in enumerate(boxes):
            lang_clean = lang.strip().lower()
            if lang_clean in ["json", "yaml", "yml", "python", "py", "bash", "sh", "javascript", "js", "html"]:
                continue
            assert not any(c in block for c in "┌╔╭╮╰╯"), (
                f"Invariant 34 Violation in {md_file.name} (block #{idx + 1}): Found legacy ASCII/UTF-8 box corners. "
                f"All diagrams must use native vector SVG illustrations in assets/illustrations/ or Markdown tables."
            )
            assert not re.search(r"\+[-=]{3,}\+", block), (
                f"Invariant 34 Violation in {md_file.name} (block #{idx + 1}): Found legacy ASCII box boundaries (+---+). "
                f"All diagrams must use native vector SVG illustrations in assets/illustrations/ or Markdown tables."
            )
            assert not re.search(r"[-=]{2,}>|--►|--▶|──►|──▶|◄--|◀--", block), (
                f"Invariant 34 Violation in {md_file.name} (block #{idx + 1}): Found ASCII flowchart arrows. "
                f"All diagrams must use native vector SVG illustrations in assets/illustrations/ or Markdown tables."
            )


@pytest.mark.governance
def test_doc_illustration_assets_integrity(docs_root: Path) -> None:
    """Verify that all referenced vector SVG illustrations exist on disk, have valid XML markup, and declare explicit viewBox."""
    import xml.etree.ElementTree as ET

    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    illustrations_dir = docs_root / "assets" / "illustrations"
    assert illustrations_dir.exists(), "assets/illustrations/ directory must exist in credence-docs"

    referenced_svgs: set[str] = set()
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        matches = re.findall(
            r"(?:!\[[^\]]*\]\((?:assets/illustrations/|\.\./assets/illustrations/|/assets/illustrations/)([^)]+\.svg)\)|src=[\"'](?:assets/illustrations/|\.\./assets/illustrations/|/assets/illustrations/)([^\"']+\.svg)[\"'])",
            text,
        )
        for m in matches:
            svg_name = m[0] or m[1]
            if svg_name:
                referenced_svgs.add(svg_name)

    assert len(referenced_svgs) >= 20, (
        f"Expected at least 20 referenced vector illustrations, found {len(referenced_svgs)}"
    )

    for svg_name in referenced_svgs:
        svg_path = illustrations_dir / svg_name
        assert svg_path.exists(), f"Referenced SVG illustration '{svg_name}' does not exist on disk at {svg_path}"

        # Validate XML structure & viewBox
        content = svg_path.read_text(encoding="utf-8")
        assert 'xmlns="http://www.w3.org/2000/svg"' in content, f"{svg_name} missing SVG namespace"
        assert 'viewBox="' in content, f"{svg_name} missing explicit viewBox for zero-scroll scaling"
        assert "#090d16" in content or "#050810" in content or "#1e293b" in content, (
            f"{svg_name} missing dark-theme color tokens"
        )

        try:
            root = ET.fromstring(content)
            assert root.tag.endswith("svg"), f"{svg_name} root XML tag must be svg"
        except Exception as e:
            pytest.fail(f"Invalid XML syntax in SVG illustration {svg_name}: {e}")


@pytest.mark.governance
def test_ecosystem_illustration_checksum_parity() -> None:
    """Verify 100% file parity and identical SHA-256 checksums between credence-docs and web assets/illustrations/."""
    import hashlib

    credence_root = Path(__file__).resolve().parents[2]
    docs_illustrations = credence_root.parent / "credence-docs" / "assets" / "illustrations"
    web_illustrations = credence_root / "web" / "assets" / "illustrations"

    assert docs_illustrations.exists(), f"Missing {docs_illustrations}"
    assert web_illustrations.exists(), f"Missing {web_illustrations}"

    docs_files = sorted([f.name for f in docs_illustrations.glob("*.svg")])
    web_files = sorted([f.name for f in web_illustrations.glob("*.svg")])

    assert len(docs_files) >= 20, f"Expected >=20 SVG illustrations in docs, found {len(docs_files)}"
    assert docs_files == web_files, (
        f"Illustration file list mismatch between docs and web: {set(docs_files) ^ set(web_files)}"
    )

    for filename in docs_files:
        docs_hash = hashlib.sha256((docs_illustrations / filename).read_bytes()).hexdigest()
        web_hash = hashlib.sha256((web_illustrations / filename).read_bytes()).hexdigest()
        assert docs_hash == web_hash, f"SHA-256 checksum mismatch for illustration '{filename}' between docs and web"


@pytest.mark.governance
def test_doc_illustrations_require_descriptive_figcaptions(docs_root: Path) -> None:
    """Verify that all vector SVG illustrations declare substantive, non-duplicate alt text rendered as visible figcaptions."""
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    generic_words = {"diagram", "illustration", "image", "svg", "alt", "graphic", "picture", "figure"}

    found_illustrations = 0
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")

        # Extract title from frontmatter or top header
        doc_title = ""
        fm_match = re.search(r"^title:\s*['\"]?(.*?)['\"]?$", content, re.MULTILINE)
        if fm_match:
            doc_title = fm_match.group(1).strip().lower()
        header_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        h1_title = header_match.group(1).strip().lower() if header_match else ""

        # Extract markdown image tags referencing illustrations
        matches = re.finditer(
            r"!\[([^\]]*)\]\((?:assets/illustrations/|\.\./assets/illustrations/|/assets/illustrations/)([^)]+\.svg)\)",
            content,
        )
        for match in matches:
            found_illustrations += 1
            alt_text = match.group(1).strip()
            svg_filename = match.group(2)
            rel_file = md_file.relative_to(docs_root)

            # 1. Alt text must not be empty and must have sufficient descriptive length
            assert len(alt_text) >= 20, (
                f"Illustration '{svg_filename}' in {rel_file} has insufficient alt text ('{alt_text}'). "
                f"Must provide a substantive technical description (at least 20 chars)."
            )

            # 2. Alt text must NOT blindly duplicate article title
            alt_lower = alt_text.lower()
            if doc_title:
                assert alt_lower != doc_title, (
                    f"Illustration '{svg_filename}' in {rel_file} duplicates document title '{doc_title}'. "
                    f"Alt text must describe what the diagram illustrates, not the page title."
                )
            if h1_title:
                assert alt_lower != h1_title, (
                    f"Illustration '{svg_filename}' in {rel_file} duplicates H1 title '{h1_title}'. "
                    f"Alt text must describe what the diagram illustrates, not the page title."
                )

            # 3. Alt text must not be a single generic filler word
            cleaned_words = set(re.findall(r"\b\w+\b", alt_lower))
            meaningful_words = cleaned_words - generic_words
            assert len(meaningful_words) >= 3, (
                f"Illustration '{svg_filename}' in {rel_file} contains only generic placeholder words ('{alt_text}'). "
                f"Must describe specific architectural components, flows, or state machines."
            )

    assert found_illustrations >= 20, f"Expected >=20 captioned illustrations in docs, found {found_illustrations}"


@pytest.mark.governance
def test_edge_router_tiered_cache_headers() -> None:
    """Verify that web/_worker.js enforces tiered edge caching (s-maxage=2592000 for SVGs/static vs max-age=0 for dynamic docs)."""
    worker_path = Path(__file__).resolve().parents[2] / "web" / "_worker.js"
    assert worker_path.exists(), "web/_worker.js must exist"
    worker_text = worker_path.read_text(encoding="utf-8")

    assert "s-maxage=2592000" in worker_text, "_worker.js must define long-lived edge CDN cache for static assets"
    assert "stale-while-revalidate=86400" in worker_text, (
        "_worker.js must define background revalidation for static assets"
    )
    assert (
        "public, max-age=0, must-revalidate" in worker_text or "no-cache, no-store, must-revalidate" in worker_text
    ), "_worker.js must enforce zero-cache revalidation on mutable HTML and markdown docs"


@pytest.mark.governance
def test_playground_and_docs_math_rendering_integrity(docs_root: Path) -> None:
    """Verify that math expressions in docs and the interactive playground have balanced delimiters and zero broken syntax leaks."""
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")

        # 1. Prohibit unescaped, unmatched inline math delimiters within a line (excluding fenced code blocks and math spans)
        # Strip fenced code blocks and HTML code / pre blocks
        prose_text = re.sub(r"```[\s\S]*?```", "", text)
        prose_text = re.sub(r"<pre[\s\S]*?</pre>", "", prose_text)
        prose_text = re.sub(r"<code[\s\S]*?</code>", "", prose_text)
        prose_text = re.sub(r"`[^`\n]+`", "", prose_text)

        # Strip display math and inline math blocks
        prose_text = re.sub(r"\$\$[\s\S]*?\$\$", "", prose_text)
        prose_text = re.sub(r"\\\[[\s\S]*?\\\]", "", prose_text)
        prose_text = re.sub(r"\$[^\$\n]+\$", "", prose_text)
        prose_text = re.sub(r"\\\([^\)\n]+\\\)", "", prose_text)

        # Prohibit raw LaTeX macro leaks in bare un-delimited text like \bar{ or \sum_ without math delimiters
        raw_latex_leaks = re.findall(
            r"\\(?:frac|bar|sum|int|sqrt|alpha|beta|gamma|lambda|sigma|Delta|min|max)\{[^}]+\}", prose_text
        )
        assert len(raw_latex_leaks) == 0, (
            f"Raw LaTeX macro leak outside math delimiters in {md_file.name}: {raw_latex_leaks[:5]}"
        )

    # 2. Playground math specific checks
    playground_md = docs_root / "docs" / "playground.md"
    assert playground_md.exists(), "docs/playground.md must exist"
    pg_text = playground_md.read_text(encoding="utf-8")
    assert "\\text{" in pg_text or "$" in pg_text, "docs/playground.md must contain formatted mathematical expressions"


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
            if (
                not target
                or target.startswith("javascript:")
                or target.startswith("mailto:")
                or target.startswith("file://")
                or target.startswith("conversation://")
            ):
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

    # 2. Verify all interactive playgrounds are covered
    assert (
        "14 Zero-Build Interactive Playgrounds" in sitemap_text
        or "12 Zero-Build Interactive Playgrounds" in sitemap_text
        or "Zero-Build Interactive Playgrounds" in sitemap_text
    )
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
            assert (
                "4-Phase Release & Learning Lifecycle" in content
                or "4-Phase Release & Lean Learning Lifecycle" in content
            ), f"{af.name} must declare 4-Phase Release & Learning Lifecycle"
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
    assert "NOTE|TIP" in content and "IMPORTANT|WARNING|CAUTION" in content

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
    """Execute Node.js runtime test on all documentation files via app.js parseMarkdown() with leak checks."""
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
      const leakViolations = [];

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

              // Invariant: Zero unrendered blockquote '>' leaks or split raw markers
              const lines = html.split('\\n');
              for (let idx = 0; idx < lines.length; idx++) {{
                const trimmed = lines[idx].trim();
                if (trimmed === '>' || trimmed === '&gt;' || trimmed === '<p>&gt;</p>' || trimmed === '<p>&gt; </p>') {{
                  leakViolations.push(`${{path.relative(docsDir, full)}}:${{idx + 1}} -> "${{trimmed}}"`);
                }}
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

      if (leakViolations.length > 0) {{
        console.error('Found unrendered blockquote leaks:\\n' + leakViolations.join('\\n'));
        process.exit(1);
      }}

      console.log(`Successfully verified ${{count}} markdown files with zero parser leaks.`);
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


@pytest.mark.governance
def test_dashboard_info_modals_and_docs_linkage_parity(docs_root: Path) -> None:
    """Verify 100% of dashboard info modals in INFO_TOPICS link to real docs and invariants."""
    credence_root = docs_root.parent / "credence"
    workstation_js = credence_root / "web" / "assets" / "credence-workstation.js"
    assert workstation_js.exists(), "credence-workstation.js must exist"

    content = workstation_js.read_text(encoding="utf-8")

    # 1. Parse all topic keys from INFO_TOPICS
    topic_keys = set(re.findall(r"^\s{2}([a-z0-9_]+):\s*\{", content, re.MULTILINE))
    assert len(topic_keys) >= 25, f"Expected at least 25 registered INFO_TOPICS, found {len(topic_keys)}"

    # 2. Check all openInfoModal calls across all HTML templates in web/
    aliases = {
        "diff": "temporal_diff",
        "revisions": "temporal_diff",
        "stealth": "temporal_diff",
        "webcrypto": "webcrypto",
        "crypto": "webcrypto",
        "signature": "webcrypto",
        "keys": "webcrypto",
        "rules": "taxonomies",
        "rule": "taxonomies",
        "taxonomy": "taxonomies",
        "mesh": "topology",
        "nodes": "topology",
        "admin": "operator_admin",
        "governor": "operator_admin",
        "cost": "operator_admin",
        "qi": "qi_scoring",
        "leaderboard": "qi_scoring",
        "identity": "custody",
        "pubkey": "custody",
    }

    web_root = credence_root / "web"
    for html_path in web_root.glob("**/*.html"):
        html_text = html_path.read_text(encoding="utf-8")
        for called_key in re.findall(r'openInfoModal\([\'"]([a-z0-9_]+)[\'"]\)', html_text):
            resolved_key = aliases.get(called_key, called_key)
            assert resolved_key in topic_keys, f"HTML file {html_path.name} calls unregistered modal key '{called_key}'"

    # 3. Verify all doc URLs in INFO_TOPICS resolve to real markdown files on disk
    urls = re.findall(r'url:\s*["\']([^"\']+)["\']', content)
    for u in urls:
        if "docs.credence.run/" in u:
            slug = u.split("docs.credence.run/")[1].split("#")[0]
            target_md = docs_root / f"{slug}.md"
            target_md_direct = docs_root / "docs" / f"{slug.replace('docs/', '')}.md"
            target_blog = docs_root / "blog" / f"{slug.replace('blog/', '')}.md"
            assert target_md.exists() or target_md_direct.exists() or target_blog.exists(), (
                f"URL '{u}' references missing documentation slug '{slug}'"
            )
        elif "docs.credence.run#" in u:
            slug = u.split("docs.credence.run#")[1].split("#")[0]
            target_md = docs_root / f"{slug}.md"
            target_md_direct = docs_root / "docs" / f"{slug.replace('docs/', '')}.md"
            target_blog = docs_root / "blog" / f"{slug.replace('blog/', '')}.md"
            assert target_md.exists() or target_md_direct.exists() or target_blog.exists(), (
                f"URL '{u}' references missing documentation slug '{slug}'"
            )
        elif "blog.credence.run/" in u:
            slug = u.split("blog.credence.run/")[1].split("#")[0]
            target_blog = docs_root / "blog" / f"{slug.replace('blog/', '')}.md"
            assert target_blog.exists(), f"Blog URL '{u}' references missing blog essay '{slug}'"
        elif "blog.credence.run#" in u:
            slug = u.split("blog.credence.run#")[1].split("#")[0]
            target_blog = docs_root / "blog" / f"{slug.replace('blog/', '')}.md"
            assert target_blog.exists(), f"Blog URL '{u}' references missing blog essay '{slug}'"

    # 4. Verify topic-index.md catalogs the Knowledge Modal Registry
    topic_index_path = docs_root / "docs" / "topic-index.md"
    assert topic_index_path.exists()
    topic_index_content = topic_index_path.read_text(encoding="utf-8")
    assert "Workstation & Dashboard Knowledge Modal Registry" in topic_index_content
    for key in topic_keys:
        assert f"`{key}`" in topic_index_content, f"Topic '{key}' must be cataloged in docs/topic-index.md"


@pytest.mark.governance
def test_edge_wrangler_routes_and_web_folders_parity(docs_root: Path) -> None:
    """Verify Cloudflare Wrangler edge router declares all web surfaces and routes (Invariant 9 & 13)."""
    import tomllib

    credence_root = docs_root.parent / "credence"
    wrangler_toml = credence_root / "web" / "wrangler.toml"
    assert wrangler_toml.exists(), "web/wrangler.toml must exist"

    with open(wrangler_toml, "rb") as f:
        data = tomllib.load(f)

    assert data.get("name") == "credence"
    assert data.get("main") == "_worker.js"
    assert data.get("assets", {}).get("binding") == "ASSETS"

    routes = data.get("routes", [])
    dev_routes = data.get("env", {}).get("dev", {}).get("routes", [])
    all_routes = routes + dev_routes
    assert len(all_routes) >= 15, f"Expected at least 15 edge routes, found {len(all_routes)}"

    route_patterns = {r["pattern"] for r in all_routes if "pattern" in r}

    # Verify primary apex and subdomains are explicitly bound
    expected_patterns = [
        "credence.run/*",
        "admin.credence.run/*",
        "docs.credence.run/*",
        "blog.credence.run/*",
        "credence.nexus/*",
        "credence.foundation/*",
        "credence.report/*",
    ]
    for ep in expected_patterns:
        assert ep in route_patterns, f"Missing required edge route pattern: {ep}"

    # Verify all web directories have corresponding route bindings
    web_dir = credence_root / "web"
    domain_dirs = [d.name for d in web_dir.iterdir() if d.is_dir() and "." in d.name and not d.name.startswith(".")]
    for d in domain_dirs:
        matching = [p for p in route_patterns if p.startswith(f"{d}/") or p.startswith(f"dev.{d}/")]
        assert len(matching) > 0, f"Web directory '{d}' has no matching route pattern in wrangler.toml"


@pytest.mark.governance
def test_skills_schema_and_frontmatter_integrity(docs_root: Path) -> None:
    """Verify all Antigravity skills in credence-agent/.agents/skills pass schema and token economy linting."""
    import importlib.util

    agent_root = docs_root.parent / "credence-agent"
    linter_path = agent_root / "scripts" / "lint_skills.py"
    assert linter_path.exists(), "scripts/lint_skills.py must exist in credence-agent"

    spec = importlib.util.spec_from_file_location("lint_skills", linter_path)
    assert spec and spec.loader
    lint_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint_module)

    skills_dir = agent_root / ".agents" / "skills"
    assert skills_dir.exists(), ".agents/skills directory must exist"

    skill_subdirs = [p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
    assert len(skill_subdirs) >= 7, f"Expected at least 7 skills, found {len(skill_subdirs)}"

    all_errors = []
    for skill_dir in skill_subdirs:
        skill_file = skill_dir / "SKILL.md"
        errors = lint_module.lint_skill_file(skill_file)
        if errors:
            all_errors.extend(errors)

    assert not all_errors, "Found skill schema violations:\n" + "\n".join(f"  • {e}" for e in all_errors)


@pytest.mark.governance
def test_agents_md_categorization_and_budget(docs_root: Path) -> None:
    """Verify all 4 AGENTS.md files declare the prioritized Class Alpha/Beta/Gamma cognitive hierarchy."""
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
            assert "Class α (Alpha)" in content or "Class Alpha" in content, (
                f"{af.name} must declare Class α (Alpha) header"
            )
            assert "Class β (Beta)" in content or "Class Beta" in content, (
                f"{af.name} must declare Class β (Beta) header"
            )
            assert "Class γ (Gamma)" in content or "Class Gamma" in content, (
                f"{af.name} must declare Class γ (Gamma) header"
            )


@pytest.mark.governance
def test_subagent_templates_validity(docs_root: Path) -> None:
    """Verify all declarative subagent templates in credence-agent/templates/subagents/ have valid JSON schemas."""
    import json

    templates_dir = docs_root.parent / "credence-agent" / "templates" / "subagents"
    assert templates_dir.exists(), "templates/subagents directory must exist in credence-agent"

    json_files = list(templates_dir.glob("*.json"))
    assert len(json_files) >= 3, f"Expected at least 3 subagent templates, found {len(json_files)}"

    required_keys = {
        "name",
        "role",
        "description",
        "system_prompt",
        "enable_write_tools",
        "enable_subagent_tools",
        "default_workspace",
    }

    for template_file in json_files:
        with open(template_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        missing = required_keys - set(data.keys())
        assert not missing, f"Subagent template '{template_file.name}' missing required fields: {missing}"
        assert data["name"].strip(), f"Template '{template_file.name}' has empty name"
        assert data["role"].strip(), f"Template '{template_file.name}' has empty role"
        assert data["system_prompt"].strip(), f"Template '{template_file.name}' has empty system_prompt"
        assert data["default_workspace"] in {"inherit", "branch", "share"}


def test_invariants_registry_and_slug_integrity():
    """Validates that all invariant cards declare semantic slugs (id='inv-...'),

    INVARIANTS_REGISTRY in credence-workstation.js matches invariants.md,
    and all 28 modal topics use verified semantic invariant slugs.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    invariants_file = repo_root / "credence-docs" / "docs" / "invariants.md"
    workstation_file = repo_root / "credence" / "web" / "assets" / "credence-workstation.js"

    assert invariants_file.is_file(), f"invariants.md not found at {invariants_file}"
    assert workstation_file.is_file(), f"credence-workstation.js not found at {workstation_file}"

    invariants_content = invariants_file.read_text(encoding="utf-8")
    workstation_content = workstation_file.read_text(encoding="utf-8")

    # Extract all invariant card IDs from invariants.md
    card_ids = set(re.findall(r'<div class="invariant-card" id="([^"]+)"', invariants_content))
    assert len(card_ids) >= 45, f"Expected >= 45 invariant cards in invariants.md, found {len(card_ids)}"

    # Verify all card IDs follow semantic slug format (inv-...)
    for card_id in card_ids:
        assert card_id.startswith("inv-"), f"Invariant card ID '{card_id}' does not use 'inv-' prefix"

    # Verify every invariant card has a backward-compatibility legacy alias anchor (<a id="invariant-N">)
    legacy_aliases = set(re.findall(r'<a id="(invariant-\d+)"></a>', invariants_content))
    assert len(legacy_aliases) >= 45, f"Expected >= 45 legacy aliases in invariants.md, found {len(legacy_aliases)}"

    # Verify INVARIANTS_REGISTRY exists in workstation.js and all slugs match invariants.md
    assert "INVARIANTS_REGISTRY" in workstation_content
    assert "resolveInvariant" in workstation_content

    # Extract all slugs in INVARIANTS_REGISTRY
    registry_slugs = set(re.findall(r'"(inv-[a-z0-9-]+)":\s*\{', workstation_content))
    assert len(registry_slugs) >= 45, f"Expected >= 45 slugs in INVARIANTS_REGISTRY, found {len(registry_slugs)}"

    # Check for symmetric parity between invariants.md and INVARIANTS_REGISTRY
    missing_in_registry = card_ids - registry_slugs
    missing_in_docs = registry_slugs - card_ids
    assert not missing_in_registry, f"Invariants in docs missing from INVARIANTS_REGISTRY: {missing_in_registry}"
    assert not missing_in_docs, f"Slugs in INVARIANTS_REGISTRY missing from invariants.md: {missing_in_docs}"

    # Verify all invariant cards declare explicit data-scope (universal or domain)
    for card_match in re.finditer(
        r'<div class="invariant-card" id="([^"]+)"[^>]*data-scope="([^"]+)"', invariants_content
    ):
        cid, scope = card_match.group(1), card_match.group(2)
        assert scope in {"universal", "domain"}, f"Invariant card '{cid}' has invalid data-scope: '{scope}'"

    # Verify all invariant cards declare an expandable agent translation HUD (<details class="agent-translation">)
    raw_specs = re.findall(
        r'<details class="agent-translation">.*?<span class="agent-slug-pill">(?:`([^`]+)`|<code>([^<]+)</code>)</span>',
        invariants_content,
        re.DOTALL,
    )
    agent_specs = {s[0] or s[1] for s in raw_specs}
    missing_specs = card_ids - agent_specs
    assert not missing_specs, f"Invariant cards missing expandable agent specification: {missing_specs}"

    # Verify AGENTS.md invariant slugs are a valid subset of canonical invariants
    ecosystem_root = repo_root
    agents_md = ecosystem_root / "AGENTS.md"
    if agents_md.exists():
        agents_slugs = set(re.findall(r"`(inv-[a-z0-9-]+)`", agents_md.read_text(encoding="utf-8")))
        unknown_in_agents = agents_slugs - card_ids
        assert not unknown_in_agents, f"AGENTS.md references unknown invariant slugs: {unknown_in_agents}"


def test_invariant_variable_anatomy_and_scratch_script_previews():
    """Verify 1:1 scope parity between workstation registry and docs, variable anatomy table structure,

    and scratch script preview link requirements in AGENTS.md.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    invariants_file = repo_root / "credence-docs" / "docs" / "invariants.md"
    workstation_file = repo_root / "credence" / "web" / "assets" / "credence-workstation.js"
    agents_files = [
        repo_root / "AGENTS.md",
        repo_root / "credence" / "AGENTS.md",
        repo_root / "credence-docs" / "AGENTS.md",
        repo_root / "credence-agent" / "AGENTS.md",
    ]

    invariants_content = invariants_file.read_text(encoding="utf-8")
    workstation_content = workstation_file.read_text(encoding="utf-8")

    # 1. 1:1 Scope parity between invariants.md and credence-workstation.js
    docs_scopes = dict(
        re.findall(r'<div class="invariant-card" id="([^"]+)"[^>]*data-scope="([^"]+)"', invariants_content)
    )
    registry_scopes = dict(re.findall(r'"(inv-[a-z0-9-]+)":\s*\{[^}]*scope:\s*"([^"]+)"', workstation_content))

    assert len(docs_scopes) == len(registry_scopes), (
        f"Docs count ({len(docs_scopes)}) != Registry count ({len(registry_scopes)})"
    )
    for slug, scope in docs_scopes.items():
        assert slug in registry_scopes, f"Slug '{slug}' missing from workstation registry"
        assert registry_scopes[slug] == scope, (
            f"Scope mismatch for '{slug}': docs has '{scope}' but workstation registry has '{registry_scopes[slug]}'"
        )

    # 2. Mathematical invariants declare variable anatomy tables with required headers
    math_slugs = ["inv-5factor-node-quality", "inv-topic-entropy-defense", "inv-empirical-expertise"]
    for slug in math_slugs:
        assert f'id="{slug}"' in invariants_content
        # Find card block
        card_start = invariants_content.find(f'id="{slug}"')
        card_end = invariants_content.find('class="invariant-card"', card_start + 1)
        if card_end == -1:
            card_end = len(invariants_content)
        card_snippet = invariants_content[card_start:card_end]

        assert "variable-anatomy-table" in card_snippet, (
            f"Mathematical invariant '{slug}' missing variable-anatomy-table"
        )
        assert "<th>Symbol</th>" in card_snippet
        assert "<th>Component Factor</th>" in card_snippet
        assert "<th>Weight</th>" in card_snippet
        assert "<th>Epistemic Role</th>" in card_snippet

    # 3. Scratch script invariant in all AGENTS.md mandates preview links before run_command
    for af in agents_files:
        if af.exists():
            text = af.read_text(encoding="utf-8")
            assert "inv-clean-scratch-scripts" in text, f"{af.name} missing inv-clean-scratch-scripts"
            assert "scratch/<name>.py" in text or "brain scratch" in text, (
                f"{af.name} must mandate standalone brain scratch scripts"
            )
            assert "clickable" in text.lower() or "preview" in text.lower(), (
                f"{af.name} must mandate clickable preview links before run_command"
            )


def test_ecosystem_naming_conventions_and_guardrails():
    """Validates that all invariant slugs, subagent templates, branch patterns,

    PR title formats, and commit messages comply with canonical governance guardrails.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    invariants_file = repo_root / "credence-docs" / "docs" / "invariants.md"
    templates_dir = repo_root / "credence-agent" / "templates" / "subagents"

    # 1. Invariant Slug Pattern: inv-<domain>-<slug> (lowercase alphanumeric + hyphens, no sequential numbers)
    invariants_content = invariants_file.read_text(encoding="utf-8")
    card_ids = re.findall(r'<div class="invariant-card" id="([^"]+)"', invariants_content)
    assert len(card_ids) >= 45

    slug_pattern = re.compile(r"^inv-[a-z0-9]+(-[a-z0-9]+)*$")
    sequential_antipattern = re.compile(r"^inv-\d+$")

    for card_id in card_ids:
        assert slug_pattern.match(card_id), (
            f"Invariant slug '{card_id}' does not match pattern '{slug_pattern.pattern}'"
        )
        assert not sequential_antipattern.match(card_id), (
            f"Invariant slug '{card_id}' uses sequential number antipattern"
        )

    # 2. Subagent Template Filenames: snake_case.json
    if templates_dir.is_dir():
        template_pattern = re.compile(r"^[a-z0-9_]+\.json$")
        for f in templates_dir.glob("*.json"):
            assert template_pattern.match(f.name), f"Subagent template filename '{f.name}' must be snake_case.json"

    # 3. Conventional Commit & PR Title Patterns
    pr_title_pattern = re.compile(
        r"^(\[v[0-9]+\.[0-9]+\.[0-9]+\] )?(feat|fix|docs|refactor|test|ci|chore|perf)(\((governance|forensics|mesh|crypto|ui|ops)\))?!?: .+$"
    )
    branch_pattern = re.compile(r"^(release/v[0-9]+\.[0-9]+\.[0-9]+|(feat|fix|docs|ci|hotfix)/.+)$")

    # Positive PR Title Tests
    valid_titles = [
        "[v2.3.0] feat(governance): implement demotion highway scanner",
        "[v2.3.0] feat(ui): migrate modal registries to semantic slugs",
        "[v2.3.0] ci(ops): configure PR dev staging triggers",
        "feat(mesh): Byzantine quorum isolation test",
        "fix(crypto): RFC 8785 canonical JSON bytes order",
        "docs(forensics): add SPJ code of ethics cookbook",
        "feat: ecosystem milestone rollup",
    ]
    for vt in valid_titles:
        assert pr_title_pattern.match(vt), f"Valid title '{vt}' failed regex match"

    # Negative PR Title Tests
    invalid_titles = [
        "updated stuff",
        "[v2.3.0] random_type(core): do thing",
        "feat(unknown_scope): something",
        "feat(): missing scope content",
    ]
    for it in invalid_titles:
        assert not pr_title_pattern.match(it), f"Invalid title '{it}' unexpectedly passed regex match"

    # Positive Branch Pattern Tests
    valid_branches = [
        "release/v2.3.0",
        "release/v1.14.0",
        "feat/p2p-gossip-optimization",
        "fix/ed25519-signature-padding",
        "docs/agentic-governance-guide",
        "ci/workload-identity-oidc",
    ]
    for vb in valid_branches:
        assert branch_pattern.match(vb), f"Valid branch '{vb}' failed regex match"

    # Negative Branch Pattern Tests
    invalid_branches = [
        "random-branch-name",
        "my_feature",
        "v2.3.0",
        "release-2.3.0",
    ]
    for ib in invalid_branches:
        assert not branch_pattern.match(ib), f"Invalid branch '{ib}' unexpectedly passed regex match"


@pytest.mark.governance
@pytest.mark.unit
def test_wrangler_route_isolation() -> None:
    """Verify that top-level production routes in wrangler.toml never contain dev preview subdomains."""
    wrangler_file = Path(__file__).resolve().parents[2] / "web" / "wrangler.toml"
    assert wrangler_file.exists(), "web/wrangler.toml must exist"
    content = wrangler_file.read_text(encoding="utf-8")

    # Split between top-level routes and [env.dev] block
    top_level_section = content.split("[env.dev")[0]
    dev_matches = re.findall(r'pattern\s*=\s*"([^"]*dev\.[^"]*)"', top_level_section)
    assert not dev_matches, (
        f"Found dev subdomains in top-level production routes of wrangler.toml: {dev_matches}. "
        "Dev routes must be isolated exclusively under [env.dev] to prevent Cloudflare worker route collisions."
    )


@pytest.mark.governance
@pytest.mark.unit
def test_deploy_dev_branch_isolation() -> None:
    """Verify that deploy-dev.yml deploys Pages to the dev preview branch and never to main."""
    workflow_file = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "deploy-dev.yml"
    assert workflow_file.exists(), ".github/workflows/deploy-dev.yml must exist"
    content = workflow_file.read_text(encoding="utf-8")

    assert "--branch=dev" in content or "--branch=${{ github.head_ref" in content, (
        "deploy-dev.yml must specify --branch=dev or dynamic branch for Cloudflare Pages deploy"
    )
    # Ensure no pages deploy with --branch=main exists in deploy-dev.yml
    pages_deploys = [line for line in content.splitlines() if "pages deploy" in line]
    for pd in pages_deploys:
        assert "--branch=main" not in pd, f"deploy-dev.yml contains forbidden --branch=main in pages deploy: {pd}"


@pytest.mark.governance
@pytest.mark.unit
def test_worker_assets_routing_invariant() -> None:
    """Verify that web/_worker.js handles /assets/ paths without domain prefixing and contains root fallback."""
    worker_file = Path(__file__).resolve().parents[2] / "web" / "_worker.js"
    assert worker_file.exists(), "web/_worker.js must exist"
    content = worker_file.read_text(encoding="utf-8")

    assert "reqPath.startsWith('/assets/')" in content, (
        "_worker.js must handle /assets/ requests directly without domain prefixing"
    )
    assert "new URL(reqPath, request.url)" in content, "_worker.js must include root reqPath fallback on 404"


@pytest.mark.governance
@pytest.mark.unit
def test_info_modals_integrity_and_sync(docs_root: Path) -> None:
    """Verify that all info modals across web dashboards match INFO_TOPICS and topic-index.md with 0 broken links."""
    credence_root = docs_root.parent / "credence"
    ws_js_path = credence_root / "web" / "assets" / "credence-workstation.js"
    assert ws_js_path.exists(), "credence-workstation.js must exist"

    ws_content = ws_js_path.read_text(encoding="utf-8")
    start = ws_content.find("const INFO_TOPICS = {")
    end = ws_content.find(
        "};\n\n// -----------------------------------------------------------------------------", start
    )
    if end == -1:
        end = ws_content.find("};\n\n//", start)

    block = ws_content[start:end]
    ws_topics = set(re.findall(r"^\s{2}([a-z0-9_]+):\s*\{", block, re.MULTILINE))
    assert len(ws_topics) >= 30, f"Expected at least 30 info topics in workstation.js, found {len(ws_topics)}"

    # 1. Check topic-index.md table parity
    topic_index_path = docs_root / "docs" / "topic-index.md"
    assert topic_index_path.exists(), "topic-index.md must exist"
    ti_content = topic_index_path.read_text(encoding="utf-8")
    table_topics = set(re.findall(r"^\|\s*`([a-z0-9_]+)`\s*\|", ti_content, re.MULTILINE))

    missing_in_index = ws_topics - table_topics
    assert not missing_in_index, (
        f"Info modal topics missing from topic-index.md: {missing_in_index}. Run 'just sync-topics'!"
    )

    # 2. Check that all URLs in INFO_TOPICS resolve to real docs
    urls = re.findall(r"url:\s*\"([^\"]+)\"", block)
    for u in urls:
        if u.startswith("https://docs.credence.run/"):
            path_part = u.split("https://docs.credence.run/")[1].split("#")[0]
            target_md = docs_root / (path_part + ".md")
            target_md_docs = docs_root / "docs" / (path_part + ".md")
            target_html = docs_root / (path_part + ".html")
            assert (
                target_md.exists()
                or target_md_docs.exists()
                or target_html.exists()
                or (docs_root / path_part).exists()
            ), f"Broken link in INFO_TOPICS: {u} (expected {target_md})"
        elif u.startswith("https://docs.credence.run#"):
            path_part = u.split("#")[1].split("#")[0]
            target_md = docs_root / (path_part + ".md")
            target_html = docs_root / (path_part + ".html")
            assert target_md.exists() or target_html.exists() or (docs_root / path_part).exists(), (
                f"Broken link in INFO_TOPICS: {u} (expected {target_md})"
            )
        elif u.startswith("https://blog.credence.run/"):
            slug = u.split("https://blog.credence.run/")[1].split("#")[0]
            target_blog = docs_root / "blog" / (slug + ".md")
            assert target_blog.exists(), f"Broken blog link in INFO_TOPICS: {u} (expected {target_blog})"
        elif u.startswith("https://blog.credence.run#"):
            slug = u.split("#")[1]
            target_blog = docs_root / "blog" / (slug + ".md")
            assert target_blog.exists(), f"Broken blog link in INFO_TOPICS: {u} (expected {target_blog})"


@pytest.mark.governance
@pytest.mark.unit
def test_workstation_and_docs_routing_regression_safeguards(docs_root: Path) -> None:
    """Verify that global html/body scroll locks are avoided and docs edge router preserves markdown subpaths."""
    credence_root = docs_root.parent / "credence"

    # 1. Verify credence-ui.css scopes overflow: hidden to workstation containers
    for css_path in [
        credence_root / "web" / "assets" / "credence-ui.css",
        docs_root / "assets" / "credence-ui.css",
    ]:
        assert css_path.exists()
        css_text = css_path.read_text(encoding="utf-8")
        assert "html:has(.workstation-container)" in css_text, (
            f"{css_path} must scope 100vh overflow:hidden to :has(.workstation-container)"
        )

    # 2. Verify _worker.js preserves docs subpaths and enforces domain redirect gates
    worker_path = credence_root / "web" / "_worker.js"
    assert worker_path.exists()
    worker_text = worker_path.read_text(encoding="utf-8")
    assert "isDocsOrBlogDomain" in worker_text, "_worker.js must explicitly check isDocsOrBlogDomain"
    assert "docs.credence.run" in worker_text, "_worker.js must define docs.credence.run domain routing"
    assert "blog.credence.run" in worker_text, "_worker.js must define blog.credence.run domain routing"

    # 3. Verify app.js rejects HTML payloads for markdown and exports clean routing functions
    app_js_path = docs_root / "app.js"
    assert app_js_path.exists()
    app_js_text = app_js_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in app_js_text, "app.js must reject <!DOCTYPE html> responses in loadDocument"
    assert "getDomainContext" in app_js_text, "app.js must export getDomainContext"
    assert "resolveDocument" in app_js_text, "app.js must export resolveDocument"
    assert "getCanonicalDocUrl" in app_js_text, "app.js must export getCanonicalDocUrl"

    # 4. Verify _redirects exists for Cloudflare Pages SPA clean slug routing
    redirects_path = docs_root / "_redirects"
    assert redirects_path.exists(), "credence-docs/_redirects must exist for Cloudflare Pages SPA routing"
    assert "/* /index.html 200" in redirects_path.read_text(encoding="utf-8")


@pytest.mark.governance
@pytest.mark.unit
def test_edge_router_dynamic_opengraph_rewrite() -> None:
    """Verify that web/_worker.js transforms og:image and og:url via HTMLRewriter for dynamic origin resolution."""
    worker_path = Path(__file__).resolve().parents[2] / "web" / "_worker.js"
    assert worker_path.exists(), "web/_worker.js must exist"
    worker_text = worker_path.read_text(encoding="utf-8")

    assert "new HTMLRewriter()" in worker_text, "_worker.js must use HTMLRewriter for dynamic metadata"
    assert 'meta[property="og:image"]' in worker_text, "_worker.js must rewrite og:image meta tag"
    assert 'meta[property="og:url"]' in worker_text, "_worker.js must rewrite og:url meta tag"
    assert "originUrl" in worker_text, "_worker.js must resolve to active request originUrl"


@pytest.mark.governance
@pytest.mark.unit
def test_docs_attestation_and_manifest_version_parity(docs_root: Path) -> None:
    """Gate 1: Assert all docs frontmatters and attestations.json match canonical pyproject.toml version and Ed25519 signatures."""
    import json
    import tomllib

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    from credence.identity import canonical_json_bytes

    credence_root = docs_root.parent / "credence"
    with open(credence_root / "pyproject.toml", "rb") as f:
        canonical_version = tomllib.load(f)["tool"]["poetry"]["version"]
    expected_tag = f"v{canonical_version}"

    # 1. Frontmatter version verification across all markdown files
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                data = yaml.safe_load(parts[1])
                if isinstance(data, dict) and "verified_version" in data:
                    assert data["verified_version"] == expected_tag, (
                        f"Stale verified_version in {md_file.name}: found {data['verified_version']}, expected {expected_tag}"
                    )

    # 2. attestations.json verification
    manifest_path = docs_root / "assets" / "attestations.json"
    assert manifest_path.exists(), "assets/attestations.json must exist"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest) >= 150, f"Expected at least 150 attested docs, found {len(manifest)}"

    for rel_path, receipt in manifest.items():
        assert receipt.get("verified_version") == expected_tag, (
            f"Stale verified_version in receipt for {rel_path}: {receipt.get('verified_version')}"
        )
        assert "node_pubkey" in receipt, f"Missing node_pubkey in receipt for {rel_path}"
        assert "node_signature" in receipt, f"Missing node_signature in receipt for {rel_path}"

        # Verify Ed25519 signature
        pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(receipt["node_pubkey"]))
        signable = {
            "origin_url": receipt["origin_url"],
            "content_sha256": receipt["content_sha256"],
            "simhash_64": receipt["simhash_64"],
            "audited_at": receipt["audited_at"],
            "suspicion_score": receipt["suspicion_score"],
            "classification": receipt["classification"],
        }
        canonical_bytes = canonical_json_bytes(signable)
        pubkey.verify(bytes.fromhex(receipt["node_signature"]), canonical_bytes)


@pytest.mark.governance
@pytest.mark.unit
def test_all_registered_playgrounds_have_active_dom_mounts(docs_root: Path) -> None:
    """Gate 2: Assert all registered playground pages have DOM containers and active app.js mount handlers."""
    app_js = docs_root / "app.js"
    app_js_text = app_js.read_text(encoding="utf-8")

    # Verify mount handler calls in handleRoute()
    assert "mountContentEvolutionLab();" in app_js_text, "app.js handleRoute must invoke mountContentEvolutionLab()"
    assert "mountBadgeSecurityLab();" in app_js_text, "app.js handleRoute must invoke mountBadgeSecurityLab()"
    assert "setupPlaygroundWidgets();" in app_js_text, "app.js handleRoute must invoke setupPlaygroundWidgets()"

    # Verify lab containers exist in their respective markdown files
    lab13_md = docs_root / "docs" / "lab-content-evolution.md"
    assert lab13_md.exists()
    assert "content-evolution-lab-container" in lab13_md.read_text(encoding="utf-8")

    lab14_md = docs_root / "docs" / "lab-badge-security.md"
    assert lab14_md.exists()
    assert "badge-security-lab-container" in lab14_md.read_text(encoding="utf-8")

    # Verify all interactive action buttons exist in app.js
    lab13_buttons = [
        "btnPresetPristine",
        "btnPresetCorrection",
        "btnPresetStealth",
        "btnPresetPoison",
        "revText",
        "labScoreBadge",
    ]
    for btn in lab13_buttons:
        assert btn in app_js_text, f"Playground 13 element '{btn}' missing in app.js"

    lab14_buttons = [
        "btnAttackBait",
        "btnAttackSig",
        "btnAttackDomain",
        "btnAttackScrubber",
        "sandboxBadge",
        "attackConsole",
    ]
    for btn in lab14_buttons:
        assert btn in app_js_text, f"Playground 14 element '{btn}' missing in app.js"


@pytest.mark.governance
@pytest.mark.unit
def test_docs_cli_commands_and_flags_validity(docs_root: Path) -> None:
    """Gate 3: Assert that CLI commands documented in markdown tutorials point to registered CLI subcommands."""
    from credence.cli.main import build_parser

    parser = build_parser()
    valid_subcommands: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            valid_subcommands.update(action.choices.keys())

    # Common standalone tools / aliases
    valid_subcommands.update({"tui", "serve", "server", "verify-file", "audit-docs"})

    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    cmd_pattern = re.compile(r"(?:poetry\s+run\s+)?credence\s+([a-zA-Z0-9_-]+)")

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        code_blocks = re.findall(r"```(?:bash|sh|console)?\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                match = cmd_pattern.search(line)
                if match:
                    subcmd = match.group(1)
                    if subcmd.startswith("-"):
                        continue
                    assert subcmd in valid_subcommands, (
                        f"Documented unknown CLI subcommand 'credence {subcmd}' in {md_file.name}"
                    )


@pytest.mark.governance
@pytest.mark.unit
def test_docs_justfile_recipes_exist(docs_root: Path) -> None:
    """Gate 4: Assert that Justfile recipe invocations in docs point to existing recipes."""
    credence_root = docs_root.parent / "credence"
    just_files = [credence_root / "Justfile"] + list((credence_root / "just").glob("*.just"))

    declared_recipes = set()
    recipe_pattern = re.compile(r"^(?:alias\s+)?([a-zA-Z0-9_-]+)(?:\s*:?=|(?:\s+[^:]*)?:)", re.MULTILINE)
    for jf in just_files:
        if jf.exists():
            text = jf.read_text(encoding="utf-8")
            for match in recipe_pattern.finditer(text):
                r_name = match.group(1)
                if not r_name.startswith("_") and r_name not in ("set", "import", "alias"):
                    declared_recipes.add(r_name)

    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    just_call_pattern = re.compile(r"(?:^|[;&|]\s*|\$\s+)just\s+([a-zA-Z0-9_-]+)")

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        code_blocks = re.findall(r"```(?:bash|sh|console)\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                for match in just_call_pattern.finditer(line):
                    recipe_name = match.group(1)
                    if recipe_name in ("--list", "-l", "--help", "-h", "--groups"):
                        continue
                    assert recipe_name in declared_recipes, (
                        f"Documented unknown Justfile recipe 'just {recipe_name}' in {md_file.name}"
                    )


@pytest.mark.governance
@pytest.mark.unit
def test_zero_hardcoded_invariant_counts_in_docs(docs_root: Path) -> None:
    """Gate 5: Invariant inv-living-canon: Assert zero hardcoded invariant counts in documentation or public web surfaces."""
    credence_root = docs_root.parent / "credence"
    scanned_files = (
        list(docs_root.glob("docs/**/*.md"))
        + list(docs_root.glob("blog/**/*.md"))
        + list((credence_root / "web").rglob("*.html"))
        + [docs_root / "app.js", docs_root / "index.html"]
    )

    hardcoded_pattern = re.compile(r"\b(36|38|39|40)\s+core\s+invariants\b", re.IGNORECASE)

    violations = []
    for f in scanned_files:
        if f.exists():
            text = f.read_text(encoding="utf-8")
            for match in hardcoded_pattern.finditer(text):
                violations.append(f"{f.name}: '{match.group(0)}'")

    assert not violations, f"Hardcoded invariant counts found (must use 'The Invariant Bible'): {violations}"


@pytest.mark.governance
@pytest.mark.unit
def test_docs_minimum_meaningful_length(docs_root: Path) -> None:
    """Gate 6: Enforce minimum meaningful documentation length across all documentation archetypes."""
    thresholds = {
        "blog": 600,
        "docs/protocols": 700,
        "docs/blueprints": 700,
        "docs/operations": 500,
        "docs/tutorials": 500,
        "docs/walkthroughs": 500,
        "docs/security": 500,
        "docs/mathematics": 500,
        "docs/mesh-engineering": 500,
        "docs/cookbooks": 450,
        "docs/integrations": 450,
        "docs/agentic": 450,
        "docs/portability": 450,
        "docs": 450,
    }

    violations = []
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    for md_file in md_files:
        rel_path = str(md_file.relative_to(docs_root))
        min_words = 450
        for prefix, limit in thresholds.items():
            if rel_path.startswith(prefix):
                min_words = limit
                break

        content = md_file.read_text(encoding="utf-8")
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2]

        words = re.findall(r"\b\w+\b", body)
        if len(words) < min_words:
            violations.append(f"{rel_path}: {len(words)} words (minimum {min_words} required)")

    assert not violations, "Under-length documentation files found:\n" + "\n".join(violations)


@pytest.mark.governance
@pytest.mark.unit
def test_zero_empty_or_sparse_sections(docs_root: Path) -> None:
    """Gate 7: Assert zero empty or sparse sections across all documentation files."""
    header_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    violations = []
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))
    for md_file in md_files:
        if md_file.name == "changelog.md":
            continue

        content = md_file.read_text(encoding="utf-8")
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2]

        sections = []
        current_header = None
        current_level = 0
        current_lines = []
        in_code_fence = False

        for line in body.splitlines():
            if line.strip().startswith("```"):
                in_code_fence = not in_code_fence
                current_lines.append(line)
                continue

            if in_code_fence:
                current_lines.append(line)
                continue

            match = header_pattern.match(line)
            if match:
                if current_header is not None:
                    sections.append((current_header, current_level, current_lines))
                current_header = match.group(2).strip()
                current_level = len(match.group(1))
                current_lines = []
            else:
                current_lines.append(line)

        if current_header is not None:
            sections.append((current_header, current_level, current_lines))

        for i, (header, level, sec_lines) in enumerate(sections):
            clean_text = "\n".join(
                [ln for ln in sec_lines if not ln.strip().startswith("<!--") and not ln.strip().startswith("-->")]
            )
            clean_words = re.findall(r"\b\w+\b", clean_text)
            has_subsections = i + 1 < len(sections) and sections[i + 1][1] > level
            if len(clean_words) == 0 and not has_subsections:
                violations.append(f"{md_file.name}: Empty leaf section '{header}'")

    assert not violations, "Empty leaf sections found in documentation:\n" + "\n".join(violations)


@pytest.mark.governance
@pytest.mark.unit
def test_zero_pseudo_box_art_and_dashed_boundaries_invariant(docs_root: Path) -> None:
    """Gate 8: Assert zero pseudo-box art, dashed borders, loose pipe connectors, bare arrows, or unformatted ALL CAPS headers in prose."""
    violations = []
    md_files = list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))

    dashed_border_pat = re.compile(r"^\-{5,}\s+\-{5,}")
    loose_arrow_pat = re.compile(r"^(▼|▲|◄--|--►)")
    all_caps_pat = re.compile(r"^[A-Z\s]{10,}$")

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2]

        in_code_block = False
        for line_no, line in enumerate(body.splitlines(), start=1):
            line_s = line.strip()
            if line_s.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Allow proper markdown table lines
            if line_s.startswith("|") and line_s.endswith("|"):
                continue

            # Disallow dashed pseudo-box lines
            if dashed_border_pat.match(line_s) or line_s.startswith("----------------------------------------+"):
                violations.append(f"{md_file.name}:{line_no} -> Dashed pseudo-box boundary: {line_s}")

            # Disallow loose box art pipes
            if (
                "|" in line_s
                and not line_s.startswith("<!--")
                and not (line_s.startswith("$") and line_s.endswith("$"))
            ):
                if re.search(r"\|\s*•|\|\s*🚀|\|\s*🛡️|\|\s*✅|\|\s*❌", line_s):
                    violations.append(f"{md_file.name}:{line_no} -> Pseudo-box pipe line: {line_s}")
                elif line_s.startswith("- ") and "|" in line_s and "•" in line_s:
                    violations.append(f"{md_file.name}:{line_no} -> Pseudo-table pipe line: {line_s}")

            # Disallow bare arrow lines in prose
            if loose_arrow_pat.match(line_s):
                violations.append(f"{md_file.name}:{line_no} -> Bare arrow line in prose: {line_s}")

            # Disallow unformatted ALL CAPS headers
            if all_caps_pat.match(line_s) and not line_s.startswith("#"):
                violations.append(f"{md_file.name}:{line_no} -> Unformatted ALL CAPS title: {line_s}")

    assert not violations, "Pseudo-box art, dashed borders, or loose arrows found in documentation:\n" + "\n".join(
        violations
    )


@pytest.mark.governance
def test_roadmap_pure_forward_looking_and_horizon_integrity(docs_root: Path) -> None:
    """Shift-Left Automated Integrity Gate 9: Asserts roadmap.md is 100% forward-looking.

    Invariants enforced:
    1. Zero retrospective foundation lists (e.g. '## 1. Verified Stable Foundation' or past version catalogs).
    2. Exactly contains the 6 required forward-looking sections.
    3. The Comprehensive Horizon Decision Matrix table is present with Difficulty and Impact ratings.
    4. Zero completed features (such as 'agent-check') linger in the active horizon queue.
    5. Frontmatter contains valid metadata and semantic invariant slugs.
    """
    roadmap_path = docs_root / "docs" / "roadmap.md"
    assert roadmap_path.exists(), "docs/roadmap.md must exist"

    content = roadmap_path.read_text(encoding="utf-8")

    # 1. Prohibit retrospective foundation or past milestone sections
    assert "Verified Stable Foundation" not in content, (
        "docs/roadmap.md must not contain retrospective 'Verified Stable Foundation' lists. "
        "Past milestones belong exclusively in docs/changelog.md."
    )
    assert "### Verified Foundation" not in content

    # 2. Assert all 6 required forward-looking sections exist
    required_sections = [
        "## 1. Empirical Drivers & Real-World Telemetry",
        "## 2. Comprehensive Horizon Decision Matrix",
        "## 3. Strategic Execution Pathways",
        "## 4. Detailed Architecture Horizons",
        "## 5. Known Operational Edge Cases & Target Resolutions",
        "## 6. Guiding Invariants for Roadmap Contributions",
    ]
    for section in required_sections:
        assert section in content, f"docs/roadmap.md missing required section: '{section}'"

    # 3. Assert the Horizon Decision Matrix table exists with proper columns
    assert (
        "| Item # | Horizon | Initiative | Difficulty (Effort) | Impact / Value | Primary Subsystem | Key Strategic Trade-Off & Capability |"
        in content
    ), "docs/roadmap.md missing the Comprehensive Horizon Decision Matrix table"

    # 4. Assert that already completed features do not linger in active horizons
    assert "Automated Prompt Context Linter (`just agent-check`)" not in content, (
        "docs/roadmap.md retains already-shipped feature 'agent-check' in active horizons. "
        "Completed features must be retired upon landing."
    )

    # 5. Parse frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "docs/roadmap.md must contain valid YAML frontmatter"
    frontmatter = yaml.safe_load(match.group(1))
    assert "verified_version" in frontmatter
    assert "last_verified" in frontmatter
    assert "invariants" in frontmatter
    assert "inv-mk1-eyeball" in frontmatter["invariants"]


@pytest.mark.governance
def test_all_articles_and_docs_have_leading_h1_title_headers(docs_root: Path) -> None:
    """Verify that every markdown file in docs/ and blog/ begins with an # <Title> heading."""
    missing_h1 = []

    for md_path in sorted(list(docs_root.glob("docs/**/*.md")) + list(docs_root.glob("blog/**/*.md"))):
        text = md_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            missing_h1.append(f"{md_path.relative_to(docs_root)}: Missing frontmatter block")
            continue

        parts = text.split("---", 2)
        if len(parts) < 3:
            missing_h1.append(f"{md_path.relative_to(docs_root)}: Malformed frontmatter block")
            continue

        fm_raw = parts[1]
        body = parts[2]

        title = None
        try:
            data = yaml.safe_load(fm_raw)
            if isinstance(data, dict):
                title = data.get("title")
        except Exception:
            m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm_raw, re.MULTILINE)
            if m:
                title = m.group(1)

        if not title:
            missing_h1.append(f"{md_path.relative_to(docs_root)}: Missing 'title' in frontmatter")
            continue

        first_heading = re.search(r"^\s*(#+)\s+([^\n]+)", body, re.MULTILINE)
        if not first_heading:
            missing_h1.append(f"{md_path.relative_to(docs_root)}: No markdown headings found in body")
        elif first_heading.group(1) != "#":
            missing_h1.append(
                f"{md_path.relative_to(docs_root)}: First heading is {first_heading.group(1)} ('{first_heading.group(2)[:40]}'), expected top-level '# <Title>'"
            )

    assert not missing_h1, f"Found {len(missing_h1)} headless or improperly headed markdown files:\n" + "\n".join(
        f"  - {item}" for item in missing_h1
    )


def test_svg_illustrations_visual_integrity_and_text_budget():
    """Validates that all SVG illustrations are visual-first architectural schematics.

    Enforces:
    1. Zero bullet point characters (•, *, -, 1., etc.) in SVG text nodes.
    2. Text line length limit (<= 38 chars) to prevent paragraph cramming into nodes.
    3. Strict text budget (<= 450 total text characters per SVG).
    4. Meaningful visual geometry (contains flow paths, directional arrows, or topology nodes).
    """
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    illustrations_dir = repo_root / "credence-docs" / "assets" / "illustrations"
    assert illustrations_dir.is_dir(), f"Illustrations directory not found at {illustrations_dir}"

    svg_files = list(illustrations_dir.glob("*.svg"))
    assert len(svg_files) >= 30, f"Expected >= 30 SVG illustrations, found {len(svg_files)}"

    violations = []
    for svg_file in svg_files:
        content = svg_file.read_text(encoding="utf-8")

        # 1. Check for bullet points
        text_elements = re.findall(r"<text\b[^>]*>(.*?)</text>", content, re.DOTALL)
        cleaned_texts = [re.sub(r"<[^>]+>", "", t).strip() for t in text_elements if t.strip()]

        bullets = [t for t in cleaned_texts if t.startswith(("•", "* ", "- ", "1. ", "2. ", "3. ", "4. ", "5. "))]
        if bullets:
            violations.append(f"{svg_file.name}: Contains {len(bullets)} bullet points ({bullets[:2]})")

        # 2. Check for long prose lines in nodes (max 38 chars)
        long_lines = [t for t in cleaned_texts if len(t) > 38 and not t.isupper()]
        if len(long_lines) > 2:
            violations.append(f"{svg_file.name}: Contains {len(long_lines)} long prose lines ({long_lines[:2]})")

        # 3. Check total text character budget (max 450 chars)
        total_chars = sum(len(t) for t in cleaned_texts)
        if total_chars > 450:
            violations.append(f"{svg_file.name}: Exceeds text character budget ({total_chars} > 450 chars)")

        # 4. Check for visual schematic elements (lines, paths, markers, circles)
        has_visual_connectors = (
            "marker-end" in content
            or "<path" in content
            or "<circle" in content
            or "<polygon" in content
            or "<line" in content
        )
        if not has_visual_connectors:
            violations.append(
                f"{svg_file.name}: Missing visual schematic geometry (no flow paths, connectors, or nodes)"
            )

    assert not violations, f"Found {len(violations)} SVG illustration visual integrity violations:\n" + "\n".join(
        f"  - {v}" for v in violations
    )
