"""Automated live rendering and visual integrity test suite for credence-docs.

Uses async Playwright and headless Chromium to verify:
1. Zero unrendered Mermaid blocks; all diagrams render into valid SVGs with non-zero dimensions.
2. Zero raw HTML tag leaks (<p>&lt;/div&gt;</p>, &lt;textarea&gt;, etc.) in rendered prose.
3. Full interactivity and state transitions across all 8 playground widgets.
4. Zero browser console errors or unhandled runtime exceptions.
"""

from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from playwright.async_api import Page, async_playwright

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "credence-docs"


class QuietDocsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def log_message(self, format, *args):
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


@pytest.fixture(scope="session")
def docs_server() -> Generator[str, None, None]:
    """Start local zero-build HTTP server on ephemeral port for Playwright tests."""
    if not DOCS_DIR.exists():
        pytest.skip("credence-docs directory not present in standalone repository checkout")
    server = ReusableTCPServer(("127.0.0.1", 0), QuietDocsHandler)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


@pytest.fixture
async def page() -> AsyncGenerator[Page, None]:
    """Launch headless Chromium browser and fresh page context per async test."""
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
            ],
        )
        p_obj = await b.new_page(viewport={"width": 1280, "height": 800})
        yield p_obj
        await p_obj.close()
        await b.close()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mermaid_diagrams_render_to_svg(page: Page, docs_server: str) -> None:
    """Verify Mermaid diagrams render into SVGs without falling back to raw code."""
    test_routes = [
        "docs/intro",
        "docs/architecture",
        "docs/protocols/mesh-protocol",
        "docs/protocols/token-governor",
        "blog/the-pizza-hut-problem",
    ]

    for route in test_routes:
        await page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        await page.wait_for_timeout(600)

        # Ensure no raw unrendered mermaid blocks remain
        raw_blocks = await page.query_selector_all(".mermaid-code pre code.language-mermaid")
        assert len(raw_blocks) == 0, f"Found unrendered raw mermaid blocks on route {route}"

        # Ensure framed window containers exist with accessibility role
        windows = await page.query_selector_all(".mermaid-window")
        assert len(windows) >= 1, f"Expected .mermaid-window container on route {route}, found {len(windows)}"

        headers = await page.query_selector_all(".mermaid-window-header")
        assert len(headers) >= 1, f"Expected .mermaid-window-header on route {route}, found {len(headers)}"

        # Ensure rendered SVGs exist and have non-zero bounding box
        rendered_svgs = await page.query_selector_all(".mermaid-rendered svg")
        assert len(rendered_svgs) >= 1, f"Expected rendered SVG on route {route}, found {len(rendered_svgs)}"

        for idx, svg in enumerate(rendered_svgs):
            box = await svg.bounding_box()
            assert box is not None, f"SVG #{idx} on route {route} has no bounding box"
            assert box["width"] > 50, f"SVG #{idx} on route {route} width too small: {box['width']}"
            assert box["height"] > 30, f"SVG #{idx} on route {route} height too small: {box['height']}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_no_raw_html_tag_leaks(page: Page, docs_server: str) -> None:
    """Verify no unescaped or leaked HTML tags appear as text in rendered prose."""
    sample_routes = [
        "docs/intro",
        "docs/playground",
        "docs/tutorials/01-clickbait-teardown",
        "docs/integrations/browser-extension-mv3",
        "docs/portability/local-llm-airgap",
        "docs/feature-parity",
        "docs/walkthroughs/04-morning-digest-briefings",
        "docs/roadmap",
        "docs/changelog",
        "docs/invariants",
        "blog/conflict-of-pun-terest",
        "blog/the-pizza-hut-problem",
        "blog/the-pareto-frontier-of-truth",
        "blog/bittorrent-for-truth",
    ]

    for route in sample_routes:
        await page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        await page.wait_for_timeout(400)

        # Check prose paragraphs, headings, and list items outside code blocks
        prose_elements = await page.query_selector_all(
            ".markdown-body > p, .markdown-body > h1, .markdown-body > h2, .markdown-body > h3, .markdown-body > ul > li, .markdown-body > ol > li, .live-monitor-callout"
        )
        for el in prose_elements:
            html = await el.inner_html()
            # Leaked HTML tags appear as &lt;div&gt;, &lt;/div&gt;, &lt;textarea, &lt;a href=, etc. inside <p>
            assert "&lt;/div&gt;" not in html, f"Found leaked &lt;/div&gt; in prose on {route}: {html}"
            assert "&lt;div" not in html or "<code" in html, f"Found leaked &lt;div in prose on {route}: {html}"
            assert "&lt;a href" not in html or "<code" in html, f"Found leaked &lt;a href in prose on {route}: {html}"
            assert "&lt;textarea" not in html or "<code" in html, (
                f"Found leaked &lt;textarea in prose on {route}: {html}"
            )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_interactive_playground_widgets(page: Page, docs_server: str) -> None:
    """Verify all 12 playground widgets initialize and respond accurately to user interactions."""
    await page.goto(f"{docs_server}/#docs/playground", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # 1. Mesh Gossip Simulator & Node Inspector
    btn_gossip = await page.query_selector("#btn-broadcast-gossip")
    assert btn_gossip is not None
    await btn_gossip.click()
    await page.wait_for_timeout(1000)
    log_text = await page.inner_text("#mesh-event-log")
    assert "100% Cluster Saturation Reached" in log_text

    # Node Inspector Click
    await page.evaluate("window.__selectMeshNode(1)")
    await page.wait_for_timeout(150)
    inspector_text = await page.inner_text("#mesh-node-inspector")
    assert "Node 1" in inspector_text

    # 2. SimHash Visualizer & 64-Bit Differential Grid
    btn_sim = await page.query_selector("#btn-calc-simhash")
    assert btn_sim is not None
    await btn_sim.click()
    await page.wait_for_timeout(200)
    dh_val = await page.inner_text("#simhash-dh-val")
    assert dh_val.isdigit()
    bit_tiles = await page.query_selector_all("#simhash-bitdiff-grid .bit-tile")
    assert len(bit_tiles) == 64

    # Preset button interaction
    btn_preset_plagiarism = await page.query_selector("#btn-preset-plagiarism")
    if btn_preset_plagiarism:
        await btn_preset_plagiarism.click()
        await page.wait_for_timeout(200)
        dh_new = await page.inner_text("#simhash-dh-val")
        assert int(dh_new) > 0

    # 3. Verbatim Grounding Tester & DOM Highlighting
    btn_ground = await page.query_selector("#btn-test-grounding")
    assert btn_ground is not None
    await btn_ground.click()
    await page.wait_for_timeout(200)
    ground_status = await page.inner_text("#grounding-status")
    assert "100% Grounded Citation" in ground_status
    match_span = await page.query_selector("#grounding-preview-display .highlight-match")
    assert match_span is not None

    # 4. Saturation Calculator & SVG Curve Plot
    slider = await page.query_selector("#calc-violations")
    assert slider is not None
    await slider.fill("4")
    await page.wait_for_timeout(200)
    score_text = await page.inner_text("#calc-result-score")
    assert float(score_text) > 0.0
    curve_polyline = await page.query_selector("#calc-curve-svg polyline")
    assert curve_polyline is not None

    # 5. In-Browser WebCrypto Verifier & Tamper Detection
    btn_load = await page.query_selector("#btn-load-sample")
    btn_tamper = await page.query_selector("#btn-tamper-sample")
    btn_verify = await page.query_selector("#btn-verify-crypto")
    assert btn_load is not None and btn_tamper is not None and btn_verify is not None
    await btn_load.click()
    await page.wait_for_timeout(200)
    await btn_verify.click()
    await page.wait_for_timeout(200)
    crypto_status = await page.inner_text("#crypto-status")
    assert "WebCrypto Verification Succeeded" in crypto_status

    # Tamper test
    await btn_tamper.click()
    await page.wait_for_timeout(150)
    await btn_verify.click()
    await page.wait_for_timeout(150)
    tamper_status = await page.inner_text("#crypto-status")
    assert "Verification Failed" in tamper_status or "Signature Mismatch" in tamper_status

    # 6. Taxonomy Explorer & Category Chips
    chip_spj = await page.query_selector("#chip-tax-spj")
    assert chip_spj is not None
    await chip_spj.click()
    await page.wait_for_timeout(200)
    cards = await page.query_selector_all("#taxonomy-cards-container .taxonomy-rule-card")
    assert len(cards) >= 1

    search_input = await page.query_selector("#taxonomy-search-input")
    assert search_input is not None
    await search_input.fill("assertion")
    await page.wait_for_timeout(200)
    filtered_cards = await page.query_selector_all("#taxonomy-cards-container .taxonomy-rule-card")
    assert len(filtered_cards) >= 1

    # 7. Multi-Model Comparator
    cards = await page.query_selector_all("#model-cards-container .model-comp-card")
    assert len(cards) == 5

    # 8. Zero-Trust Dynamic Feed Simulator & Astroturfing Preset
    feed_score = await page.inner_text("#feed-result-score")
    assert float(feed_score) >= 0.0
    btn_astro = await page.query_selector("#btn-preset-astroturf")
    if btn_astro:
        await btn_astro.click()
        await page.wait_for_timeout(200)
        astro_status = await page.inner_text("#feed-astroturf-status")
        assert "HIGH RISK" in astro_status or "Astroturfing" in astro_status

    # 9. The Galileo Rule Consensus Simulator
    galileo_score = await page.inner_text("#galileo-consensus-score")
    assert float(galileo_score) == 75.0
    btn_toggle_gal = await page.query_selector("#btn-toggle-galileo")
    assert btn_toggle_gal is not None
    await btn_toggle_gal.click()
    await page.wait_for_timeout(200)
    naive_score = await page.inner_text("#galileo-consensus-score")
    assert float(naive_score) < 75.0
    # Toggle back on
    await btn_toggle_gal.click()
    await page.wait_for_timeout(150)

    # 10. Epistemic Heuristic Text Scanner
    scanner_score = await page.inner_text("#scanner-heuristic-score")
    assert float(scanner_score) > 0.0
    spans = await page.query_selector_all("#scanner-highlight-output .epistemic-span")
    assert len(spans) >= 1

    # 11. Schema.org ClaimReview & RFC 8785 Receipt Generator
    cr_output = await page.inner_text("#cr-json-output")
    assert "ClaimReview" in cr_output or "schema.org" in cr_output
    btn_tab_rfc = await page.query_selector("#btn-tab-rfc8785")
    assert btn_tab_rfc is not None
    await btn_tab_rfc.click()
    await page.wait_for_timeout(200)
    rfc_output = await page.inner_text("#cr-json-output")
    assert "content_sha256" in rfc_output or "classification" in rfc_output

    # 12. Token Governor & 30% Headroom Circuit Breaker
    headroom_text = await page.inner_text("#gov-headroom-pct")
    assert "%" in headroom_text
    gov_badge = await page.inner_text("#gov-state-badge")
    assert "QUOTA_PRESERVED" in gov_badge or "ACTIVE_THINKING" in gov_badge


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_zero_console_errors(page: Page, docs_server: str) -> None:
    """Verify navigation across critical documentation surfaces triggers zero console errors."""
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))

    key_routes = [
        "docs/intro",
        "docs/quickstart",
        "docs/architecture",
        "docs/playground",
        "blog/the-pizza-hut-problem",
        "blog/the-pareto-frontier-of-truth",
    ]

    for route in key_routes:
        await page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        await page.wait_for_timeout(300)

    assert len(console_errors) == 0, f"Captured console errors during navigation: {console_errors}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_tabbed_interface_switching_and_persistence(page: Page, docs_server: str) -> None:
    """Verify GCP-style tabbed containers switch active panels and persist preferences to localStorage."""
    walkthrough_url = f"{docs_server}/#docs/walkthroughs/01-auditing-webpages-and-text"
    await page.goto(walkthrough_url, wait_until="networkidle")
    await page.wait_for_timeout(600)

    tab_groups = await page.query_selector_all(".tab-group")
    assert len(tab_groups) >= 3, f"Expected at least 3 tab groups, found {len(tab_groups)}"

    # Check first tab group buttons
    first_group = tab_groups[0]
    buttons = await first_group.query_selector_all(".tab-header .tab-btn")
    assert len(buttons) >= 3

    # Initially the first button is active
    assert "active" in (await buttons[0].get_attribute("class") or "")
    active_panel = await first_group.query_selector(".tab-panel.active")
    assert active_panel is not None

    # Click the second tab (FastMCP)
    await buttons[1].click()
    await page.wait_for_timeout(300)

    # Verify second tab is now active
    assert "active" in (await buttons[1].get_attribute("class") or "")
    assert "active" not in (await buttons[0].get_attribute("class") or "")

    # Verify localStorage saved the preference
    saved_pref = await page.evaluate("() => localStorage.getItem('credence_preferred_interface')")
    assert saved_pref is not None
    assert "fastmcp" in saved_pref.lower()

    # Navigate to Walkthrough 02 and verify preference automatically persists across pages
    await page.goto(f"{docs_server}/#docs/walkthroughs/02-zero-trust-feed-sifting", wait_until="networkidle")
    await page.wait_for_timeout(600)

    new_group = await page.query_selector(".tab-group")
    assert new_group is not None
    active_btn = await new_group.query_selector(".tab-btn.active")
    assert active_btn is not None
    assert "fastmcp" in (await active_btn.inner_text()).lower()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_invariant_deep_linking_and_scrolling(page: Page, docs_server: str) -> None:
    """Verify clicking an invariant link routes to #docs/invariants#invariant-N and scrolls viewport."""
    await page.goto(f"{docs_server}/#docs/walkthroughs/03-p2p-mesh-consensus", wait_until="networkidle")
    await page.wait_for_timeout(600)

    # Click on the Invariant 27 link in the table or prose
    inv_link = await page.query_selector("a[href*='invariant-27'], a[href*='invariants#invariant-27']")
    assert inv_link is not None, "Could not find Invariant 27 link on Walkthrough 03"
    await inv_link.click()
    await page.wait_for_timeout(1200)

    # Verify URL hash changed to invariant 27
    current_hash = await page.evaluate("() => window.location.hash")
    assert "invariants" in current_hash
    assert "invariant-27" in current_hash

    # Verify target invariant element exists and is in viewport
    target_card = await page.query_selector("#invariant-27")
    assert target_card is not None, "Target anchor #invariant-27 not found in DOM"
    box = await target_card.bounding_box()
    assert box is not None
    assert box["y"] < 900, f"Invariant card was not scrolled into view: y={box['y']}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_tui_vector_svg_rendering(page: Page, docs_server: str) -> None:
    """Verify all embedded TUI vector SVGs render with valid geometry and natural dimensions."""
    test_pages = [
        "docs/quickstart",
        "docs/integrations/tui-workstation",
        "docs/walkthroughs/01-auditing-webpages-and-text",
        "docs/feature-parity",
    ]

    for route in test_pages:
        await page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        await page.wait_for_timeout(500)

        # Activate any TUI tab buttons in tab groups on the page
        tab_groups = await page.query_selector_all(".tab-group")
        for group in tab_groups:
            tui_btn = await group.query_selector('.tab-btn[data-tab-name*="TUI"], .tab-btn[data-tab-name*="Textual"]')
            if tui_btn:
                await tui_btn.click()
                await page.wait_for_timeout(150)

        # Query all TUI images
        tui_imgs = await page.query_selector_all('img[src*="assets/tui/"]')
        assert len(tui_imgs) >= 1, f"Expected at least 1 TUI image on route {route}, found {len(tui_imgs)}"

        for idx, img in enumerate(tui_imgs):
            # Verify image loaded successfully
            is_loaded = await img.evaluate("(el) => el.complete && el.naturalWidth > 0")
            assert is_loaded, f"TUI image #{idx} on route {route} failed to load or has 0 naturalWidth"

            natural_w = await img.evaluate("(el) => el.naturalWidth")
            natural_h = await img.evaluate("(el) => el.naturalHeight")
            assert natural_w >= 100, f"TUI image #{idx} on route {route} naturalWidth too small: {natural_w}"
            assert natural_h >= 50, f"TUI image #{idx} on route {route} naturalHeight too small: {natural_h}"

            # If visible, verify non-zero bounding box
            if await img.is_visible():
                box = await img.bounding_box()
                assert box is not None, f"Visible TUI image #{idx} on route {route} has no bounding box"
                assert box["width"] > 100, f"TUI image #{idx} bounding box width too small: {box['width']}"
                assert box["height"] > 50, f"TUI image #{idx} bounding box height too small: {box['height']}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_anti_scrollbox_and_natural_flow_invariant(page: Page, docs_server: str) -> None:
    """Verify Invariant 38: No nested vertical scrollboxes or trapped containers exist in reading prose."""
    key_pages = [
        "docs/playground",
        "blog/conflict-of-pun-terest",
        "blog/the-pizza-hut-problem",
        "docs/invariants",
        "docs/architecture",
    ]

    for route in key_pages:
        await page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        await page.wait_for_timeout(500)

        # Check for any element inside #doc-content with an active vertical scrollbar
        scroll_violations = await page.evaluate(
            """() => {
            const container = document.getElementById('doc-content');
            if (!container) return [];
            const elements = container.querySelectorAll('*');
            const violations = [];
            for (const el of elements) {
                // Ignore code blocks with horizontal overflow or textareas used for active input
                if (el.tagName === 'PRE' || el.tagName === 'TEXTAREA' || el.tagName === 'TABLE') continue;
                const style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                    if (el.scrollHeight > el.clientHeight + 10) {
                        violations.push({
                            tag: el.tagName,
                            className: el.className,
                            id: el.id,
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight
                        });
                    }
                }
            }
            return violations;
        }"""
        )
        assert len(scroll_violations) == 0, (
            f"Found nested vertical scrollbox violations on route {route}: {scroll_violations}"
        )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_latex_math_rendering_and_zero_macro_leaks(page: Page, docs_server: str) -> None:
    """Verify Invariant 37: Mathematical formulas parse cleanly into Unicode math without raw LaTeX backslash leaks."""
    math_routes = [
        "docs/mathematics/economics-of-truth",
        "docs/mathematics/robust-consensus-proofs",
        "blog/conflict-of-pun-terest",
        "docs/invariants",
    ]

    for route in math_routes:
        await page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        await page.wait_for_timeout(500)

        # Verify math elements are present
        math_elements = await page.query_selector_all(".math-inline, .math-block")
        assert len(math_elements) >= 3, f"Expected rendered math elements on {route}, found {len(math_elements)}"

        # Check prose and math elements for unrendered raw LaTeX macros (excluding literal code blocks)
        prose_texts = await page.evaluate(
            """() => {
            const container = document.getElementById('doc-content');
            if (!container) return [];
            const clone = container.cloneNode(true);
            // Remove code and pre elements so code examples explaining LaTeX syntax are not flagged
            clone.querySelectorAll('pre, code').forEach(el => el.remove());
            return clone.innerText;
        }"""
        )
        raw_macros = ["\\frac{", "\\mathbb{", "\\min_{", "\\sum_{", "\\tau_{", "\\pm ", "\\left(", "\\right)"]
        for macro in raw_macros:
            assert macro not in prose_texts, f"Found unrendered raw LaTeX macro '{macro}' in prose on route {route}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_taxonomy_rule_explorer_full_catalog_and_filtering(page: Page, docs_server: str) -> None:
    """Verify Widget 6: Renders 46 authentic taxonomy rules with zero scrollbars, multi-filtering, and pagination."""
    await page.goto(f"{docs_server}/#docs/playground", wait_until="networkidle")
    await page.wait_for_timeout(600)

    # 1. Total Rules Count
    visible_count = await page.inner_text("#tax-visible-count")
    assert visible_count == "46", f"Expected 46 total rules, got {visible_count}"

    # 2. Category Chips Verification
    # SPJ Journalism
    await page.click("#chip-tax-spj")
    await page.wait_for_timeout(200)
    assert await page.inner_text("#tax-visible-count") == "12"

    # IEP Fallacies
    await page.click("#chip-tax-iep")
    await page.wait_for_timeout(200)
    assert await page.inner_text("#tax-visible-count") == "21"

    # Deceptive UI
    await page.click("#chip-tax-deceptive")
    await page.wait_for_timeout(200)
    assert await page.inner_text("#tax-visible-count") == "9"

    # Domain Specific
    await page.click("#chip-tax-domain")
    await page.wait_for_timeout(200)
    assert await page.inner_text("#tax-visible-count") == "4"

    # Reset to All
    await page.click("#chip-tax-all")
    await page.wait_for_timeout(200)

    # 3. Severity Dropdown Filter
    await page.select_option("#taxonomy-severity-filter", "5")
    await page.wait_for_timeout(200)
    sev5_count = int(await page.inner_text("#tax-visible-count"))
    assert sev5_count >= 4, f"Expected at least 4 Sev 5 rules, found {sev5_count}"

    await page.select_option("#taxonomy-severity-filter", "ALL")
    await page.wait_for_timeout(200)

    # 4. Instant Search Filter
    search_input = page.locator("#taxonomy-search-input")
    await search_input.fill("ad hominem")
    await page.wait_for_timeout(200)
    assert int(await page.inner_text("#tax-visible-count")) >= 1

    await search_input.fill("")
    await page.wait_for_timeout(200)

    # 5. Pagination
    assert "Page 1" in await page.inner_text("#tax-page-indicator")
    await page.click("#tax-next-btn")
    await page.wait_for_timeout(200)
    assert "Page 2" in await page.inner_text("#tax-page-indicator")

    # 6. Show All Toggle
    await page.click("#tax-show-all-btn")
    await page.wait_for_timeout(200)
    all_cards = await page.query_selector_all("#taxonomy-cards-container .taxonomy-rule-card")
    assert len(all_cards) == 46, f"Expected all 46 rule cards visible, found {len(all_cards)}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_cross_domain_consistent_navigation_and_footers(page: Page, docs_server: str) -> None:
    """Verify that all pages across all domains have a consistent header, 4-column footer,

    and an accessible master sitemap.
    """
    # 1. Test docs portal sitemap route
    await page.goto(f"{docs_server}/#docs/sitemap", wait_until="networkidle")
    await page.wait_for_selector("#doc-content h1", timeout=5000)

    title = await page.inner_text("#doc-content h1")
    assert "Ecosystem Master Sitemap" in title

    # Verify sitemap contents
    content_text = await page.inner_text("#doc-content")
    assert "credence.run" in content_text
    assert "credence.report" in content_text
    assert "credence.nexus" in content_text
    assert "credence.foundation" in content_text
    assert "12 Zero-Build Interactive Playgrounds" in content_text or "12 Zero-Build Playgrounds" in content_text
    assert "The Invariant Bible" in content_text

    # 2. Check header navigation links in live docs portal
    nav_links = await page.eval_on_selector_all(
        ".credence-nav .nav-links a",
        "elements => elements.map(e => ({ text: e.innerText.trim(), href: e.getAttribute('href') }))",
    )
    link_texts = [item["text"] for item in nav_links]
    assert len(link_texts) == 5, f"Expected exactly 5 header nav items, found {len(link_texts)}: {link_texts}"
    for required_item in ["Home", "Docs", "Reports", "Nexus", "Foundation"]:
        assert any(required_item.lower() == t.lower() for t in link_texts), (
            f"Missing nav item: {required_item} in {link_texts}"
        )

    # 3. Check 4-column ecosystem footer rendered in article view
    footer_cols = await page.eval_on_selector_all(
        ".credence-footer .footer-col h4", "elements => elements.map(e => e.innerText.trim())"
    )
    assert len(footer_cols) == 4, f"Expected 4 footer columns, found {len(footer_cols)}: {footer_cols}"

    # 4. Verify all 5 domain static HTML entrypoints maintain consistent headers and footers
    web_dir = Path(__file__).parent.parent / "web"
    domain_files = [
        web_dir / "credence.run" / "index.html",
        web_dir / "credence.report" / "index.html",
        web_dir / "credence.report" / "viewer.html",
        web_dir / "credence.nexus" / "index.html",
        web_dir / "credence.foundation" / "index.html",
    ]

    for f in domain_files:
        assert f.exists(), f"Domain entrypoint missing: {f}"
        text = f.read_text(encoding="utf-8")
        assert 'class="credence-nav"' in text or "class='credence-nav'" in text, f"Missing .credence-nav in {f.name}"
        assert 'class="credence-footer"' in text or "class='credence-footer'" in text, (
            f"Missing .credence-footer in {f.name}"
        )
        assert "footer-grid" in text, f"Missing .footer-grid in {f.name}"
