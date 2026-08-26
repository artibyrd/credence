"""Credence Syndicated Feed Pre-Ingestion, Mesh Effort Avoidance, and Generous Defaults."""

from credence.feeds.dedup import (
    MeshAttestationLookupResult,
    check_mesh_effort_avoidance,
)
from credence.feeds.parser import (
    FeedEntry,
    ParsedFeed,
    fetch_and_parse_feed,
    parse_feed_content,
)
from credence.feeds.sentinel import (
    compute_sentinel_poll_due,
    list_sentinel_sources,
    partition_ingestion_burst,
    set_feed_sentinel_mode,
)
from credence.feeds.worker import (
    FeedSyncSummary,
    sync_all_feeds,
    sync_single_feed,
)

__all__ = [
    "FeedEntry",
    "ParsedFeed",
    "fetch_and_parse_feed",
    "parse_feed_content",
    "MeshAttestationLookupResult",
    "check_mesh_effort_avoidance",
    "FeedSyncSummary",
    "sync_single_feed",
    "sync_all_feeds",
    "compute_sentinel_poll_due",
    "list_sentinel_sources",
    "partition_ingestion_burst",
    "set_feed_sentinel_mode",
]
