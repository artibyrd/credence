"""Unit tests for Text Normalization, SHA-256 Hashing, and SimHash."""

import pytest

from credence.ingestion.hasher import (
    compute_content_sha256,
    compute_simhash,
    normalize_text,
    simhash_hamming_distance,
    simhash_similarity,
)


@pytest.mark.unit
def test_normalize_text_whitespace_invariance() -> None:
    """Verify normalize_text collapses whitespace, tabs, and excess newlines."""
    text1 = "Breaking  News:\n\n\nScientists discover   new renewable storage.\t\t"
    text2 = "Breaking News:\n\nScientists discover new renewable storage."

    assert normalize_text(text1) == normalize_text(text2)


@pytest.mark.unit
def test_normalize_text_unicode_nfkc() -> None:
    """Verify Unicode NFKC normalization and zero-width character stripping."""
    # Text with zero-width space (\u200B) and full-width characters
    dirty_text = "Scientific\u200b Analysis： １００％ verified."
    clean_text = normalize_text(dirty_text)

    assert "\u200b" not in clean_text
    assert "100%" in clean_text


@pytest.mark.unit
def test_content_sha256_reproducibility() -> None:
    """Verify identical text produces identical SHA-256 hash."""
    text = "Independent reporting on climate change policy."
    hash1 = compute_content_sha256(text)
    hash2 = compute_content_sha256("  Independent reporting on   climate change policy.  \n")

    assert hash1 == hash2
    assert hash1.startswith("sha256:")
    assert len(hash1) == 71


@pytest.mark.unit
def test_simhash_identical_content() -> None:
    """Verify identical text produces 0 Hamming distance and 1.0 similarity."""
    text = "The quick brown fox jumps over the lazy dog in the sunny morning meadow."
    sh1 = compute_simhash(text)
    sh2 = compute_simhash(text)

    assert sh1 == sh2
    assert simhash_hamming_distance(sh1, sh2) == 0
    assert simhash_similarity(sh1, sh2) == 1.0


@pytest.mark.unit
def test_simhash_near_duplicate_detection() -> None:
    """Verify minor typographical edits result in high similarity score."""
    text1 = (
        "Global installations of solar photovoltaic and offshore wind systems expanded by 24 percent "
        "over the prior fiscal year according to researchers. Plummeting battery storage costs drove "
        "adoption across international power grids."
    )
    text2 = (
        "Global installations of solar photovoltaic and offshore wind systems grew by 24 percent "
        "over the prior fiscal year according to researchers. Plummeting battery storage costs drove "
        "adoption across international electrical grids."
    )

    sh1 = compute_simhash(text1)
    sh2 = compute_simhash(text2)

    distance = simhash_hamming_distance(sh1, sh2)
    similarity = simhash_similarity(sh1, sh2)

    # Near-duplicates should have distance <= 12 and similarity >= 0.80
    assert distance <= 12
    assert similarity >= 0.80


@pytest.mark.unit
def test_simhash_distinct_content() -> None:
    """Verify completely unrelated texts produce large Hamming distance."""
    text1 = "Quantum computing algorithms utilize entanglement and superposition for prime factorization."
    text2 = "Bake the chocolate chip cookies at 350 degrees Fahrenheit for twelve minutes until golden brown."

    sh1 = compute_simhash(text1)
    sh2 = compute_simhash(text2)

    distance = simhash_hamming_distance(sh1, sh2)
    similarity = simhash_similarity(sh1, sh2)

    assert distance > 12
    assert similarity < 0.80
