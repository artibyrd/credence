"""Playwright Dual-Capture Ingestion Engine.

Captures:
1. Full visual screenshot (.png) for multimodal UI and deceptive pattern analysis.
2. Full rendered DOM HTML (.html) for structural inspection.
3. Clean extracted markdown and text (via Trafilatura).
4. Deterministic content hashes (SHA-256 and SimHash).

Protected by an asyncio.Semaphore(1) to avoid Chromium OOM crashes in constrained environments.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright
from pydantic import BaseModel, Field

from credence.config import settings
from credence.ingestion.extractor import ExtractedContent, extract_clean_content
from credence.ingestion.hasher import compute_content_sha256, compute_simhash

# Concurrency semaphore to constrain Chromium memory footprint
_SNAPSHOT_SEMAPHORE = asyncio.Semaphore(settings.MAX_CONCURRENT_SNAPSHOTS)


class DualCaptureResult(BaseModel):
    """Result of a dual-capture ingestion pass."""

    url: str = Field(..., description="Target URL")
    content_sha256: str = Field(..., description="SHA-256 hash of normalized text")
    simhash_64: str = Field(..., description="Hex 64-bit SimHash")
    raw_html: str = Field(default="", description="Rendered DOM HTML")
    extracted: ExtractedContent = Field(..., description="Clean text, markdown, and extracted metadata")
    dom_file_path: Optional[str] = Field(default=None, description="Path to saved DOM HTML file")
    screenshot_file_path: Optional[str] = Field(default=None, description="Path to saved visual PNG screenshot")
    screenshot_bytes: Optional[bytes] = Field(default=None, repr=False, description="Raw PNG bytes")


async def capture_webpage(
    url: str,
    output_dir: Optional[Path] = None,
    save_artifacts: bool = True,
    timeout_ms: Optional[int] = None,
) -> DualCaptureResult:
    """Capture full rendered HTML and visual screenshot of a webpage using Playwright.

    Executes under an asyncio Semaphore to enforce strict concurrency limits.
    """
    from credence.ingestion.security import validate_safe_url

    is_local_file = url.startswith("file://") or url.startswith("text://")
    clean_url = validate_safe_url(url, allow_local=is_local_file)
    target_dir = output_dir or settings.SNAPSHOT_DIR
    target_timeout = timeout_ms or settings.PLAYWRIGHT_TIMEOUT_MS

    async with _SNAPSHOT_SEMAPHORE:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-setuid-sandbox",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CredenceBot/0.1"
                ),
            )
            page = await context.new_page()

            try:
                await page.goto(clean_url, wait_until="domcontentloaded", timeout=target_timeout)
                # Wait briefly for client-side hydration / rendering
                await page.wait_for_timeout(1000)

                raw_html = await page.content()
                screenshot_bytes = await page.screenshot(full_page=True, type="png")
            finally:
                await context.close()
                await browser.close()

    # Extract clean text and calculate hashes
    extracted = extract_clean_content(raw_html, url=clean_url)
    content_hash = compute_content_sha256(extracted.clean_text)
    simhash_hex = compute_simhash(extracted.clean_text)

    dom_path: Optional[str] = None
    screenshot_path: Optional[str] = None

    if save_artifacts and target_dir:
        target_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"{content_hash[:16]}"
        dom_file = target_dir / f"{base_name}.html"
        dom_file.write_text(raw_html, encoding="utf-8")
        dom_path = str(dom_file)

        if screenshot_bytes:
            shot_file = target_dir / f"{base_name}.png"
            shot_file.write_bytes(screenshot_bytes)
            screenshot_path = str(shot_file)

    return DualCaptureResult(
        url=clean_url,
        content_sha256=content_hash,
        simhash_64=simhash_hex,
        raw_html=raw_html,
        extracted=extracted,
        dom_file_path=dom_path,
        screenshot_file_path=screenshot_path,
        screenshot_bytes=screenshot_bytes,
    )
