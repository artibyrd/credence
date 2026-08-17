"""Web ingestion, extraction, snapshotting, and hashing modules for Credence."""

from credence.ingestion.extractor import ExtractedContent, extract_clean_content
from credence.ingestion.hasher import compute_content_sha256, compute_simhash, normalize_text, simhash_hamming_distance
from credence.ingestion.snapshot import DualCaptureResult, capture_webpage

__all__ = [
    "ExtractedContent",
    "extract_clean_content",
    "compute_content_sha256",
    "compute_simhash",
    "normalize_text",
    "simhash_hamming_distance",
    "DualCaptureResult",
    "capture_webpage",
]
