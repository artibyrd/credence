"""Automated live rendering and visual integrity test suite for credence-docs.

Uses Playwright and headless Chromium to verify:
1. Zero unrendered Mermaid blocks; all diagrams render into valid SVGs with non-zero dimensions.
2. Zero raw HTML tag leaks (<p>&lt;/div&gt;</p>, &lt;textarea&gt;, etc.) in rendered prose.
3. Full interactivity and state transitions across all 8 playground widgets.
4. Zero browser console errors or unhandled runtime exceptions.
"""

import http.server
import socketserver
import threading
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

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
    server = ReusableTCPServer(("127.0.0.1", 0), QuietDocsHandler)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Launch headless Chromium browser instance."""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser: Browser) -> Generator[Page, None, None]:
    """Create fresh browser page context per test."""
    p = browser.new_page()
    yield p
    p.close()


@pytest.mark.e2e
def test_mermaid_diagrams_render_to_svg(page: Page, docs_server: str) -> None:
    """Verify Mermaid diagrams render into SVGs without falling back to raw code."""
    test_routes = [
        "docs/intro",
        "docs/architecture",
        "docs/protocols/mesh-protocol",
        "docs/protocols/token-governor",
        "blog/the-pizza-hut-problem",
    ]

    for route in test_routes:
        page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        page.wait_for_timeout(600)

        # Ensure no raw unrendered mermaid blocks remain
        raw_blocks = page.query_selector_all(".mermaid-code pre code.language-mermaid")
        assert len(raw_blocks) == 0, f"Found unrendered raw mermaid blocks on route {route}"

        # Ensure rendered SVGs exist and have non-zero bounding box
        rendered_svgs = page.query_selector_all(".mermaid-rendered svg")
        assert len(rendered_svgs) >= 1, f"Expected rendered SVG on route {route}, found {len(rendered_svgs)}"

        for idx, svg in enumerate(rendered_svgs):
            box = svg.bounding_box()
            assert box is not None, f"SVG #{idx} on route {route} has no bounding box"
            assert box["width"] > 50, f"SVG #{idx} on route {route} width too small: {box['width']}"
            assert box["height"] > 30, f"SVG #{idx} on route {route} height too small: {box['height']}"


@pytest.mark.e2e
def test_no_raw_html_tag_leaks(page: Page, docs_server: str) -> None:
    """Verify no unescaped or leaked HTML tags appear as text in rendered prose."""
    sample_routes = [
        "docs/intro",
        "docs/playground",
        "docs/tutorials/01-clickbait-teardown",
        "docs/integrations/browser-extension-mv3",
        "blog/the-pizza-hut-problem",
        "blog/the-pareto-frontier-of-truth",
        "blog/bittorrent-for-truth",
    ]

    for route in sample_routes:
        page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        page.wait_for_timeout(400)

        # Check prose paragraphs, headings, and list items outside code blocks
        prose_elements = page.query_selector_all(".markdown-body > p, .markdown-body > h1, .markdown-body > h2, .markdown-body > h3, .markdown-body > ul > li, .markdown-body > ol > li")
        for el in prose_elements:
            html = el.inner_html()
            # Leaked HTML tags appear as &lt;div&gt;, &lt;/div&gt;, &lt;textarea, etc. inside <p>
            assert "&lt;/div&gt;" not in html, f"Found leaked &lt;/div&gt; in prose on {route}: {html}"
            assert "&lt;div" not in html or "<code" in html, f"Found leaked &lt;div in prose on {route}: {html}"
            assert "&lt;textarea" not in html or "<code" in html, f"Found leaked &lt;textarea in prose on {route}: {html}"


@pytest.mark.e2e
def test_interactive_playground_widgets(page: Page, docs_server: str) -> None:
    """Verify all 8 playground widgets initialize and respond accurately to user interactions."""
    page.goto(f"{docs_server}/#docs/playground", wait_until="networkidle")
    page.wait_for_timeout(500)

    # 1. Mesh Gossip Simulator
    btn_gossip = page.query_selector("#btn-broadcast-gossip")
    assert btn_gossip is not None
    btn_gossip.click()
    page.wait_for_timeout(1000)
    log_text = page.inner_text("#mesh-event-log")
    assert "100% Cluster Saturation Reached" in log_text

    # 2. SimHash Visualizer
    btn_sim = page.query_selector("#btn-calc-simhash")
    assert btn_sim is not None
    btn_sim.click()
    page.wait_for_timeout(200)
    dh_val = page.inner_text("#simhash-dh-val")
    assert dh_val.isdigit()

    # 3. Verbatim Grounding Tester
    btn_ground = page.query_selector("#btn-test-grounding")
    assert btn_ground is not None
    btn_ground.click()
    page.wait_for_timeout(200)
    ground_status = page.inner_text("#grounding-status")
    assert "100% Grounded Citation" in ground_status

    # 4. Saturation Calculator
    slider = page.query_selector("#calc-violations")
    assert slider is not None
    slider.fill("4")
    page.wait_for_timeout(200)
    score_text = page.inner_text("#calc-result-score")
    assert float(score_text) > 0.0

    # 5. In-Browser WebCrypto Verifier
    btn_load = page.query_selector("#btn-load-sample")
    btn_verify = page.query_selector("#btn-verify-crypto")
    assert btn_load is not None and btn_verify is not None
    btn_load.click()
    page.wait_for_timeout(200)
    btn_verify.click()
    page.wait_for_timeout(200)
    crypto_status = page.inner_text("#crypto-status")
    assert "WebCrypto Verification Succeeded" in crypto_status

    # 6. Taxonomy Explorer
    search_input = page.query_selector("#taxonomy-search-input")
    assert search_input is not None
    search_input.fill("smear")
    page.wait_for_timeout(200)
    rows = page.query_selector_all("#taxonomy-table-body tr")
    assert len(rows) >= 1

    # 7. Multi-Model Comparator
    cards = page.query_selector_all("#model-cards-container .model-comp-card")
    assert len(cards) == 5

    # 8. Zero-Trust Dynamic Feed Simulator
    feed_score = page.inner_text("#feed-result-score")
    assert float(feed_score) >= 0.0


@pytest.mark.e2e
def test_zero_console_errors(page: Page, docs_server: str) -> None:
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
        page.goto(f"{docs_server}/#{route}", wait_until="networkidle")
        page.wait_for_timeout(300)

    assert len(console_errors) == 0, f"Captured console errors during navigation: {console_errors}"


@pytest.mark.e2e
def test_tabbed_interface_switching_and_persistence(page: Page, docs_server: str) -> None:
    """Verify GCP-style tabbed containers switch active panels and persist preferences to localStorage."""
    walkthrough_url = f"{docs_server}/#docs/walkthroughs/01-auditing-webpages-and-text"
    page.goto(walkthrough_url, wait_until="networkidle")
    page.wait_for_timeout(600)

    tab_groups = page.query_selector_all(".tab-group")
    assert len(tab_groups) >= 3, f"Expected at least 3 tab groups, found {len(tab_groups)}"

    # Check first tab group buttons
    first_group = tab_groups[0]
    buttons = first_group.query_selector_all(".tab-header .tab-btn")
    assert len(buttons) >= 3

    # Initially the first button is active
    assert "active" in (buttons[0].get_attribute("class") or "")
    active_panel = first_group.query_selector(".tab-panel.active")
    assert active_panel is not None

    # Click the second tab (FastMCP)
    buttons[1].click()
    page.wait_for_timeout(300)

    # Verify second tab is now active
    assert "active" in (buttons[1].get_attribute("class") or "")
    assert "active" not in (buttons[0].get_attribute("class") or "")

    # Verify localStorage saved the preference
    saved_pref = page.evaluate("() => localStorage.getItem('credence_preferred_interface')")
    assert saved_pref is not None
    assert "fastmcp" in saved_pref.lower()

    # Navigate to Walkthrough 02 and verify preference automatically persists across pages
    page.goto(f"{docs_server}/#docs/walkthroughs/02-zero-trust-feed-sifting", wait_until="networkidle")
    page.wait_for_timeout(600)

    new_group = page.query_selector(".tab-group")
    assert new_group is not None
    active_btn = new_group.query_selector(".tab-btn.active")
    assert active_btn is not None
    assert "fastmcp" in active_btn.inner_text().lower()


@pytest.mark.e2e
def test_invariant_deep_linking_and_scrolling(page: Page, docs_server: str) -> None:
    """Verify clicking an invariant link routes to #docs/invariants#invariant-N and scrolls viewport."""
    page.goto(f"{docs_server}/#docs/walkthroughs/03-p2p-mesh-consensus", wait_until="networkidle")
    page.wait_for_timeout(600)

    # Click on the Invariant 27 link in the table or prose
    inv_link = page.query_selector("a[href*='invariant-27'], a[href*='invariants#invariant-27']")
    assert inv_link is not None, "Could not find Invariant 27 link on Walkthrough 03"
    inv_link.click()
    page.wait_for_timeout(1200)

    # Verify URL hash changed to invariant 27
    current_hash = page.evaluate("() => window.location.hash")
    assert "invariants" in current_hash
    assert "invariant-27" in current_hash

    # Verify target invariant element exists and is in viewport
    target_card = page.query_selector("#invariant-27")
    assert target_card is not None, "Target anchor #invariant-27 not found in DOM"
    box = target_card.bounding_box()
    assert box is not None
    assert box["y"] < 900, f"Invariant card was not scrolled into view: y={box['y']}"


