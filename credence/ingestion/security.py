"""Security, URI Validation & SSRF Guard for Network Ingestion.

Ensures that arbitrary URL inputs provided to the evaluation pipeline, feed parser,
or Playwright dual-capture engine cannot be abused to perform Server-Side Request Forgery
(SSRF) attacks against private infrastructure or cloud metadata endpoints (e.g. 169.254.169.254).
"""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
    "local",
    "internal",
}

_VALID_DOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")


def _is_blocked_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if IP address is private, loopback, link-local, or reserved."""
    return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast


def _is_safe_domain(hostname: str, require_resolvable: bool) -> bool:
    """Resolve and validate a domain name."""
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if _is_blocked_ip(ip):
                return False
        return True
    except (socket.gaierror, OSError):
        if require_resolvable:
            return False
        return bool(_VALID_DOMAIN_REGEX.match(hostname))


def is_safe_url(url: str, allow_local: bool = False, require_resolvable: bool = False) -> bool:
    """Validate whether a target URL is safe for network ingestion.

    Args:
        url: The candidate URL string to evaluate.
        allow_local: If True, allows loopback/private IPs for mock tests.
        require_resolvable: If True, requires active DNS resolution.

    Returns:
        True if URL is safe, False otherwise.
    """
    if not url:
        return False

    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    if scheme == "text":
        return True
    if scheme == "file":
        return allow_local
    if scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False
    if allow_local:
        return True

    lower_host = hostname.lower()
    if lower_host in _BLOCKED_HOSTNAMES or lower_host.endswith(".internal"):
        return False

    try:
        ip = ipaddress.ip_address(hostname)
        return not _is_blocked_ip(ip)
    except ValueError:
        return _is_safe_domain(lower_host, require_resolvable=require_resolvable)


def validate_safe_url(url: str, allow_local: bool = False, require_resolvable: bool = False) -> str:
    """Validate URL and return clean URL or raise ValueError if unsafe."""
    if not is_safe_url(url, allow_local=allow_local, require_resolvable=require_resolvable):
        raise ValueError(f"Target URL '{url}' is unsafe or resolves to a blocked private/metadata network address.")
    return url.strip()
