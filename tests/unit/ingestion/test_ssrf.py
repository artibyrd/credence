"""Unit tests for Network SSRF Security Guard."""

import pytest

from credence.ingestion.security import is_safe_url, validate_safe_url


@pytest.mark.unit
def test_ssrf_blocking_metadata_and_loopback():
    """Verify that dangerous private and cloud metadata endpoints are blocked."""
    # Cloud metadata endpoints
    assert is_safe_url("http://169.254.169.254/latest/meta-data/", allow_local=False) is False
    assert is_safe_url("http://metadata.google.internal/computeMetadata/v1/", allow_local=False) is False
    assert is_safe_url("http://instance-data/latest/meta-data/", allow_local=False) is False

    # Loopback addresses
    assert is_safe_url("http://127.0.0.1:8000/secret", allow_local=False) is False
    assert is_safe_url("http://localhost:5432/admin", allow_local=False) is False
    assert is_safe_url("http://[::1]:8080/internal", allow_local=False) is False

    # Private RFC 1918 subnets
    assert is_safe_url("http://10.0.0.1/admin", allow_local=False) is False
    assert is_safe_url("http://172.16.0.5:8080/dashboard", allow_local=False) is False
    assert is_safe_url("http://192.168.1.1/router", allow_local=False) is False

    # Invalid schemes
    assert is_safe_url("ftp://ftp.example.com/file", allow_local=False) is False
    assert is_safe_url("file:///etc/passwd", allow_local=False) is False
    assert is_safe_url("gopher://example.com", allow_local=False) is False


@pytest.mark.unit
def test_ssrf_validate_safe_url_raises():
    """Verify validate_safe_url raises ValueError on unsafe URLs."""
    with pytest.raises(ValueError, match="unsafe or resolves to a blocked"):
        validate_safe_url("http://169.254.169.254/secret", allow_local=False)


@pytest.mark.unit
def test_safe_public_urls_allowed():
    """Verify valid public URLs and synthetic text:// schemes are accepted."""
    assert is_safe_url("https://apiculture-daily.org/article", allow_local=False) is True
    assert is_safe_url("http://example.com/rss.xml", allow_local=False) is True
    assert is_safe_url("text://inline", allow_local=False) is True
