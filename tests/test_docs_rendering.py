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
    rows = await page.query_selector_all("#taxonomy-table-body tr")
    assert len(rows) >= 1

    search_input = await page.query_selector("#taxonomy-search-input")
    assert search_input is not None
    await search_input.fill("smear")
    await page.wait_for_timeout(200)
    filtered_rows = await page.query_selector_all("#taxonomy-table-body tr")
    assert len(filtered_rows) >= 1

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
    cr_output = await page.input_value("#cr-json-output")
    assert "ClaimReview" in cr_output or "schema.org" in cr_output
    btn_tab_rfc = await page.query_selector("#btn-tab-rfc8785")
    assert btn_tab_rfc is not None
    await btn_tab_rfc.click()
    await page.wait_for_timeout(200)
    rfc_output = await page.input_value("#cr-json-output")
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
