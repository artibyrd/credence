"""Cryptographic and Locality-Sensitive Hashing for Web Snapshots.

Provides:
- Deterministic text normalization (Unicode NFKC, whitespace collapsing).
- SHA-256 content hashing for exact cache hits.
- 64-bit SimHash for fuzzy/near-duplicate detection and Hamming distance comparison.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from simhash import Simhash


def normalize_text(text: str) -> str:
    """Normalize extracted text for deterministic hashing.

    - Applies Unicode NFKC normalization.
    - Removes invisible/zero-width characters.
    - Normalizes line breaks and collapses multiple whitespace characters.
    - Strips leading and trailing whitespace.
    """
    if not text:
        return ""

    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # Remove zero-width and invisible control characters (except standard newlines/tabs)
    normalized = re.sub(r"[\u200B-\u200D\uFEFF\u00A0]", " ", normalized)

    # Standardize CRLF to LF
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse consecutive horizontal whitespace (spaces, tabs)
    normalized = re.sub(r"[ \t]+", " ", normalized)

    # Collapse more than two consecutive newlines to two
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()


def compute_content_sha256(text: str) -> str:
    """Compute deterministic SHA-256 hash of normalized text.

    Returns format: 'sha256:<hexdigest>'
    """
    normalized = normalize_text(text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_simhash(text: str) -> str:
    """Compute 64-bit SimHash of text shingles for fuzzy duplicate detection.

    Returns hex string format: '0x<16-char-hex>'
    """
    normalized = normalize_text(text)
    if not normalized:
        return "0x0000000000000000"

    # Tokenize into word unigrams and bigrams for rich semantic representation
    words = re.findall(r"\w+", normalized.lower())
    if not words:
        return "0x0000000000000000"

    features = words + [f"{words[i]}_{words[i + 1]}" for i in range(len(words) - 1)]
    sh_val = Simhash(features).value
    return f"0x{sh_val:016x}"


def simhash_hamming_distance(hash1_hex: str, hash2_hex: str) -> int:
    """Calculate the Hamming bit distance (0 to 64) between two SimHash hex strings.

    - Distance 0: Identical content.
    - Distance 1-3: Near-duplicate mirror or minor typographical edit.
    - Distance > 10: Substantially distinct content.
    """
    val1 = int(hash1_hex, 16)
    val2 = int(hash2_hex, 16)
    xor_val = val1 ^ val2
    return bin(xor_val).count("1")


def simhash_similarity(hash1_hex: str, hash2_hex: str) -> float:
    """Compute normalized similarity percentage (0.0 to 1.0) based on Hamming distance."""
    distance = simhash_hamming_distance(hash1_hex, hash2_hex)
    return round(max(0.0, 1.0 - (distance / 64.0)), 4)
