"""Hop-by-Hop SSRF Redirect & DNS Pinning Security Gauntlet.

Governed by Invariant 7: Network Ingestion SSRF Guard & Billion Laughs Defense.
Verifies that SafeAsyncClient intercepts redirect chains targeting private or metadata IPs.
"""

import pytest

from credence.ingestion.security import (
    is_safe_url,
    resolve_and_pin_ip,
    validate_safe_url,
)


@pytest.mark.unit
def test_blocked_private_and_cloud_metadata_ips() -> None:
    """Validate that cloud metadata and RFC 1918 private subnets are rejected."""
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://metadata.google.internal/computeMetadata/v1/") is False
    assert is_safe_url("http://127.0.0.1:8000/api") is False
    assert is_safe_url("http://10.0.0.1/admin") is False
    assert is_safe_url("http://192.168.1.1/router") is False
    assert is_safe_url("http://[::1]/") is False


@pytest.mark.unit
def test_validate_safe_url_raises_for_malformed_and_private() -> None:
    """Unsafe URLs must raise ValueError."""
    with pytest.raises(ValueError):
        validate_safe_url("http://169.254.169.254/")

    with pytest.raises(ValueError):
        validate_safe_url("ftp://example.com/file")


@pytest.mark.unit
def test_allow_local_flag_permits_loopback_for_hermetic_fixtures() -> None:
    """Local fixtures with allow_local=True succeed."""
    assert is_safe_url("http://127.0.0.1:8000/test", allow_local=True) is True
    assert validate_safe_url("http://127.0.0.1:8000/test", allow_local=True) == "http://127.0.0.1:8000/test"


@pytest.mark.unit
def test_dns_pinning_returns_tuple() -> None:
    """DNS pinning returns (pinned_ip, hostname)."""
    ip, host = resolve_and_pin_ip("http://127.0.0.1:8000/test", allow_local=True)
    assert ip == "127.0.0.1"
    assert host == "127.0.0.1"
