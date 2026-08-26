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


async def capture_webpage_fastpath(
    url: str,
    output_dir: Optional[Path] = None,
    save_artifacts: bool = True,
    force_playwright: bool = False,
    timeout_ms: Optional[int] = None,
) -> DualCaptureResult:
    """Capture webpage using Trafilatura fast-path (50ms), falling back to Playwright if needed."""
    from credence.ingestion.security import validate_safe_url
    from credence.storage.base import get_blob_storage

    is_local_file = url.startswith("file://") or url.startswith("text://")
    clean_url = validate_safe_url(url, allow_local=is_local_file)

    # If force_playwright requested or local file, use Playwright engine
    if force_playwright or is_local_file:
        return await capture_webpage(url, output_dir=output_dir, save_artifacts=save_artifacts, timeout_ms=timeout_ms)

    # 1. Fast-Path HTTP GET via Safe Async Client
    raw_html: Optional[str] = None
    try:
        from credence.ingestion.security import create_safe_async_client

        async with create_safe_async_client(
            timeout=10.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 (Credence/2.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        ) as client:
            resp = await client.get(clean_url)
            if resp.status_code == 200:
                raw_html = resp.text
    except Exception:
        raw_html = None

    # 2. Check if Fast-Path succeeded with substantive content (>50 words)
    if raw_html:
        extracted = extract_clean_content(raw_html, url=clean_url)
        word_count = len(extracted.clean_text.split())
        if word_count >= 50:
            content_hash = compute_content_sha256(extracted.clean_text)
            simhash_hex = compute_simhash(extracted.clean_text)

            dom_path: Optional[str] = None
            if save_artifacts:
                storage = get_blob_storage()
                cas_key = f"cas/sha256/{content_hash}.html"
                dom_path = await storage.put_blob(
                    cas_key, raw_html.encode("utf-8"), content_type="text/plain; charset=utf-8"
                )

            return DualCaptureResult(
                url=clean_url,
                content_sha256=content_hash,
                simhash_64=simhash_hex,
                raw_html=raw_html,
                extracted=extracted,
                dom_file_path=dom_path,
                screenshot_file_path=None,
                screenshot_bytes=None,
            )

    # 3. Fallback to full Playwright Chromium capture
    return await capture_webpage(url, output_dir=output_dir, save_artifacts=save_artifacts, timeout_ms=timeout_ms)


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
    from credence.storage.base import get_blob_storage

    is_local_file = url.startswith("file://") or url.startswith("text://")
    clean_url = validate_safe_url(url, allow_local=is_local_file)
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
                locale="en-US",
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Credence/1.4"
                ),
            )
            page = await context.new_page()

            try:
                try:
                    await page.goto(clean_url, wait_until="domcontentloaded", timeout=target_timeout)
                except Exception:
                    # Retry once on transient network or protocol glitches
                    await page.wait_for_timeout(500)
                    await page.goto(clean_url, wait_until="load", timeout=target_timeout)

                # Wait briefly for client-side hydration / rendering
                await page.wait_for_timeout(1000)

                raw_html = await page.content()
                try:
                    screenshot_bytes = await page.screenshot(full_page=True, type="png", timeout=10000)
                except Exception:
                    try:
                        screenshot_bytes = await page.screenshot(full_page=False, type="png", timeout=5000)
                    except Exception:
                        screenshot_bytes = b""
            finally:
                await context.close()
                await browser.close()

    # Extract clean text and calculate hashes
    extracted = extract_clean_content(raw_html, url=clean_url)
    content_hash = compute_content_sha256(extracted.clean_text)
    simhash_hex = compute_simhash(extracted.clean_text)

    dom_path: Optional[str] = None
    screenshot_path: Optional[str] = None

    if save_artifacts:
        storage = get_blob_storage()
        clean_hex = content_hash.removeprefix("sha256:")
        cas_html_key = f"cas/sha256/{clean_hex}.html"
        dom_path = await storage.put_blob(
            cas_html_key, raw_html.encode("utf-8"), content_type="text/plain; charset=utf-8"
        )

        if screenshot_bytes:
            cas_png_key = f"cas/sha256/{clean_hex}.png"
            screenshot_path = await storage.put_blob(cas_png_key, screenshot_bytes, content_type="image/png")

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
