"""Tests for SSRF Multi-Environment Ingestion Guards."""

import pytest

from credence.ingestion.security import is_safe_url, validate_safe_url


@pytest.mark.unit
def test_allow_local_flag_in_development():
    """Verify that allow_local=True permits localhost/loopback in dev environments."""
    assert is_safe_url("http://127.0.0.1:8000/fixture.html", allow_local=True) is True
    assert is_safe_url("http://localhost:8000/fixture.html", allow_local=True) is True
    assert (
        validate_safe_url("http://127.0.0.1:8000/fixture.html", allow_local=True)
        == "http://127.0.0.1:8000/fixture.html"
    )


@pytest.mark.unit
def test_strict_ssrf_blocking_in_production():
    """Verify that allow_local=False strictly blocks loopback and cloud metadata in production."""
    assert is_safe_url("http://127.0.0.1:8000/secret.txt", allow_local=False) is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/", allow_local=False) is False
    assert is_safe_url("http://10.0.0.1/internal-admin", allow_local=False) is False

    with pytest.raises(ValueError, match="is unsafe or resolves to a blocked"):
        validate_safe_url("http://127.0.0.1:8000/secret.txt", allow_local=False)

    with pytest.raises(ValueError, match="is unsafe or resolves to a blocked"):
        validate_safe_url("http://169.254.169.254/latest/meta-data/", allow_local=False)
