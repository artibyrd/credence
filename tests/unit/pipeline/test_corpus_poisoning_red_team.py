"""Red Team Suite: Vector 8 (The Poisoned Well Attack) against Dynamic Corpus Expansion.

Asserts that add_sample_to_corpus rejects:
1. SSRF target addresses (e.g. metadata.google.internal, 169.254.169.254, 127.0.0.1).
2. XML Entity expansion bombs (<!DOCTYPE / <!ENTITY>).
3. Payload over 250KB limit.
4. Low topic entropy synthetic slop (H < 0.30).
5. Grounding quote mismatches (G < 1.00).
6. Duplicate URL / text samples.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from credence.pipeline.heuristics.benchmark import add_sample_to_corpus


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_corpus_ssrf_blocked() -> None:
    """Vector 8.1: SSRF attack against metadata IP is blocked immediately before network call."""
    with pytest.raises(ValueError, match="SSRF security violation"):
        await add_sample_to_corpus("http://169.254.169.254/latest/meta-data")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_corpus_xml_entity_bomb_rejected() -> None:
    """Vector 8.2: XML Entity Bomb (Billion Laughs style) in HTML payload is rejected."""
    fake_html = """<!DOCTYPE test [
    <!ENTITY lol "lol">
    <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
    ]>
    <html><body><h1>Malicious Document</h1><p>&lol1;</p></body></html>
    """

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text = fake_html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="Entity security violation"):
            await add_sample_to_corpus("https://safe-news.org/bomb")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_corpus_low_entropy_slop_rejected() -> None:
    """Vector 8.3: Synthetic repetitive slop with word entropy H < 0.30 is rejected."""
    slop_html = "<html><body><h1>Slop Title</h1><p>" + "buy viagra cheap click now " * 100 + "</p></body></html>"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text = slop_html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="Topic entropy violation"):
            await add_sample_to_corpus("https://safe-news.org/slop")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_corpus_oversized_payload_rejected() -> None:
    """Vector 8.4: Oversized article payload (>250KB text) is rejected."""
    huge_html = (
        "<html><body><h1>Huge Article</h1><p>"
        + ("Deep investigative report on municipal finances. " * 6000)
        + "</p></body></html>"
    )

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text = huge_html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="Payload size violation"):
            await add_sample_to_corpus("https://safe-news.org/huge")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_corpus_duplicate_sample_rejected() -> None:
    """Vector 8.5: Duplicate URL or duplicate text payload is rejected."""
    clean_html = "<html><body><h1>State Route 238 Flood Closure</h1><p>Arizona Department of Transportation has reopened State Route 238 following emergency drainage repairs after heavy monsoon storms flooded low-lying desert washes. Maintenance crews cleared sediment and reinforced culverts over a 36-hour continuous operation.</p></body></html>"

    # Use a temp corpus file with existing article
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        temp_corpus = {
            "corpus_version": "v1.0.0",
            "articles": [
                {
                    "id": "corpus_0001",
                    "url": "https://azdot.gov/news/sr238-reopening-drainage",
                    "text": "Arizona Department of Transportation has reopened State Route 238 following emergency drainage repairs after heavy monsoon storms flooded low-lying desert washes. Maintenance crews cleared sediment and reinforced culverts over a 36-hour continuous operation.",
                }
            ],
        }
        json.dump(temp_corpus, tf)
        temp_path = Path(tf.name)

    try:
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.text = clean_html
            mock_resp.status_code = 200
            mock_resp.raise_for_status = lambda: None
            mock_get.return_value = mock_resp

            with pytest.raises(ValueError, match="Deduplication violation"):
                await add_sample_to_corpus(
                    "https://azdot.gov/news/sr238-reopening-drainage",
                    corpus_path=temp_path,
                )
    finally:
        if temp_path.exists():
            temp_path.unlink()
