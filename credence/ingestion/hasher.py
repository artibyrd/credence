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


def compute_text_diff(old_text: str, new_text: str) -> dict:
    """Compute structured line and token diff between two normalized texts.

    Returns dict containing:
    - added_lines_count: int
    - removed_lines_count: int
    - added_words_count: int
    - removed_words_count: int
    - diff_summary: str (e.g. '+3 lines, -1 lines')
    - hunks: list of diff hunks with tag ('add', 'remove', 'equal') and content
    """
    norm_old = normalize_text(old_text)
    norm_new = normalize_text(new_text)

    if norm_old == norm_new:
        return {
            "added_lines_count": 0,
            "removed_lines_count": 0,
            "added_words_count": 0,
            "removed_words_count": 0,
            "diff_summary": "Identical content",
            "hunks": [{"tag": "equal", "text": norm_new}],
        }

    import difflib

    old_lines = norm_old.splitlines()
    new_lines = norm_new.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    hunks = []
    added_lines = 0
    removed_lines = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            hunks.append({"tag": "equal", "lines": new_lines[j1:j2]})
        elif tag == "insert":
            hunks.append({"tag": "add", "lines": new_lines[j1:j2]})
            added_lines += j2 - j1
        elif tag == "delete":
            hunks.append({"tag": "remove", "lines": old_lines[i1:i2]})
            removed_lines += i2 - i1
        elif tag == "replace":
            hunks.append({"tag": "remove", "lines": old_lines[i1:i2]})
            hunks.append({"tag": "add", "lines": new_lines[j1:j2]})
            removed_lines += i2 - i1
            added_lines += j2 - j1

    old_words = set(re.findall(r"\w+", norm_old.lower()))
    new_words = set(re.findall(r"\w+", norm_new.lower()))

    added_words = len(new_words - old_words)
    removed_words = len(old_words - new_words)

    summary = f"+{added_lines} lines / -{removed_lines} lines (+{added_words}/-{removed_words} words)"

    return {
        "added_lines_count": added_lines,
        "removed_lines_count": removed_lines,
        "added_words_count": added_words,
        "removed_words_count": removed_words,
        "diff_summary": summary,
        "hunks": hunks,
    }


def compute_token_drift(old_text: str, new_text: str) -> float:
    """Compute normalized semantic token drift ratio (0.0 to 1.0) between two texts.

    - 0.0: Identical normalized text.
    - < 0.05: Minor typographical edit.
    - 0.05 - 0.25: Editorial clarification or section update.
    - > 0.70: Total article overhaul or topic shift.
    """
    norm_old = normalize_text(old_text)
    norm_new = normalize_text(new_text)

    if norm_old == norm_new:
        return 0.0

    sh1 = compute_simhash(norm_old)
    sh2 = compute_simhash(norm_new)
    sim_sim = simhash_similarity(sh1, sh2)

    words1 = set(re.findall(r"\w+", norm_old.lower()))
    words2 = set(re.findall(r"\w+", norm_new.lower()))

    if not words1 or not words2:
        return 1.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)
    jaccard_sim = intersection / union if union > 0 else 0.0

    # Composite similarity (SimHash for shingle order + Jaccard for vocabulary overlap)
    composite_sim = (0.5 * sim_sim) + (0.5 * jaccard_sim)
    drift = round(max(0.0, min(1.0, 1.0 - composite_sim)), 4)
    return drift
