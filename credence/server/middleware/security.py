"""Security & Cache-Control Middleware for Credence Server."""

from __future__ import annotations

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce security headers and zero-cache policies across API responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


def _check_admin_auth(request: Any) -> bool:
    """Verify administrator Bearer token authentication or local development exemption."""
    import secrets

    from credence.config import settings

    client_host = getattr(request.client, "host", "") if hasattr(request, "client") and request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1") and settings.ENV != "production":
        return True
    auth_header = getattr(request, "headers", {}).get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        expected = settings.CREDENCE_ADMIN_API_KEY
        if expected and secrets.compare_digest(token, expected):
            return True
    return False
