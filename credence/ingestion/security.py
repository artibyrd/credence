"""Security, URI Validation & SSRF Guard for Network Ingestion.

Ensures that arbitrary URL inputs provided to the evaluation pipeline, feed parser,
or Playwright dual-capture engine cannot be abused to perform Server-Side Request Forgery
(SSRF) attacks against private infrastructure or cloud metadata endpoints (e.g. 169.254.169.254).

Governed by Invariant 7 (Network Ingestion SSRF Guard & Billion Laughs Defense).
"""

from __future__ import annotations

import ipaddress
import re
import socket
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
    "local",
    "internal",
    "0.0.0.0",  # noqa: S104
    "::",
    "::1",
    "0",
}

_VALID_DOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
MAX_INGESTION_PAYLOAD_BYTES = 10_485_760  # 10 MB maximum payload cap


def is_blocked_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address is private, loopback, link-local, unspecified, or reserved.

    Args:
        ip_obj: The IPv4 or IPv6 address object to evaluate.

    Returns:
        True if the IP falls into a restricted/private network range, False otherwise.
    """
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or ip_obj.is_multicast
        or ip_obj.is_unspecified
    )


def is_safe_domain(hostname: str, require_resolvable: bool = False) -> bool:
    """Resolve and validate a domain name against SSRF blocklists.

    Args:
        hostname: The domain hostname string to evaluate.
        require_resolvable: If True, forces active DNS resolution check.

    Returns:
        True if hostname resolves safely to public IPs, False otherwise.
    """
    # Reject raw numeric, hex, or octal hostnames mimicking IPs (e.g., 2130706433, 0x7f000001, 0177.0.0.1)
    if hostname.isdigit() or hostname.startswith(("0x", "0X")) or re.match(r"^0\d+", hostname):
        return False

    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if is_blocked_ip(ip):
                return False
        return True
    except (socket.gaierror, OSError):
        if require_resolvable:
            return False
        return bool(_VALID_DOMAIN_REGEX.match(hostname))


def is_safe_url(url: str, allow_local: bool = False, require_resolvable: bool = False) -> bool:
    """Validate whether a candidate URL is safe for network ingestion.

    Args:
        url: The candidate URL string to evaluate.
        allow_local: If True, permits loopback/private IPs (used in hermetic test fixtures).
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
        return not is_blocked_ip(ip)
    except ValueError:
        return is_safe_domain(lower_host, require_resolvable=require_resolvable)


def validate_safe_url(url: str, allow_local: bool = False, require_resolvable: bool = False) -> str:
    """Validate URL safety, returning the sanitized URL or raising ValueError.

    Args:
        url: The candidate URL string.
        allow_local: If True, permits loopback/private IPs for mock testing.
        require_resolvable: If True, requires active DNS resolution.

    Returns:
        The stripped, validated URL string.

    Raises:
        ValueError: If the URL is unsafe, malformed, or resolves to a blocked address.
    """
    if not is_safe_url(url, allow_local=allow_local, require_resolvable=require_resolvable):
        raise ValueError(f"Target URL '{url}' is unsafe or resolves to a blocked private/metadata network address.")
    return url.strip()


def resolve_and_pin_ip(url: str, allow_local: bool = False) -> Tuple[str, str]:
    """Perform single-resolution DNS pinning to prevent DNS rebinding attacks.

    Args:
        url: Target URL string to resolve and pin.
        allow_local: If True, permits loopback/private IPs.

    Returns:
        A tuple of (pinned_ip_address, original_hostname).

    Raises:
        ValueError: If hostname cannot be resolved or resolves to an unsafe network.
    """
    clean_url = validate_safe_url(url, allow_local=allow_local)
    parsed = urlparse(clean_url)
    hostname = parsed.hostname or ""

    if allow_local and hostname in ("localhost", "127.0.0.1", "::1"):
        return "127.0.0.1", hostname

    addr_info = socket.getaddrinfo(
        hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP
    )
    for _, _, _, _, sockaddr in addr_info:
        ip_str = str(sockaddr[0])
        ip = ipaddress.ip_address(ip_str)
        if not allow_local and is_blocked_ip(ip):
            raise ValueError(f"Resolved IP '{ip_str}' for host '{hostname}' is in a blocked network range.")
        return ip_str, hostname

    raise ValueError(f"Unable to resolve host '{hostname}' to a safe IP address.")


def create_safe_async_client(
    timeout: float = 10.0,
    allow_local: bool = False,
    headers: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """Create an AsyncClient with hop-by-hop redirect SSRF interception hooks.

    Args:
        timeout: Request timeout in seconds.
        allow_local: If True, permits local/private IPs.
        headers: Default HTTP headers.
        **kwargs: Additional parameters forwarded to httpx.AsyncClient.

    Returns:
        Configured httpx.AsyncClient with SSRF event hooks.
    """

    async def _on_request(request: httpx.Request) -> None:
        validate_safe_url(str(request.url), allow_local=allow_local)

    async def _on_response(response: httpx.Response) -> None:
        if response.is_redirect or response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            if location:
                resolved_target = str(response.url.join(location))
                validate_safe_url(resolved_target, allow_local=allow_local)

    event_hooks = kwargs.pop("event_hooks", {})
    request_hooks = event_hooks.get("request", []) + [_on_request]
    response_hooks = event_hooks.get("response", []) + [_on_response]

    client_headers = headers or {"User-Agent": "Credence-Security-Ingester/2.0"}

    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers=client_headers,
        event_hooks={"request": request_hooks, "response": response_hooks},
        **kwargs,
    )
