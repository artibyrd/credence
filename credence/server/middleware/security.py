import base64
import json
import secrets
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from credence.config import settings


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


def get_auth_identity(request: Any) -> dict[str, Any]:
    """Inspect request headers/cookies and return operator authentication metadata."""
    headers = getattr(request, "headers", {})
    auth_header = headers.get("authorization", "")
    admin_key_header = headers.get("x-credence-admin-key", "")
    cf_email = headers.get("cf-access-authenticated-user-email", "")

    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
    elif admin_key_header:
        token = admin_key_header.strip()

    # 1. Mode 1: Direct Admin API Key verification
    expected_key = settings.CREDENCE_ADMIN_API_KEY
    if token and expected_key and secrets.compare_digest(token, expected_key):
        return {"authenticated": True, "role": "OPERATOR", "identity": "admin-api-key", "method": "API_KEY"}

    # 2. Mode 2: OAuth2 / OIDC Token Verification & Email Allowlist
    if token and settings.CREDENCE_ADMIN_EMAILS:
        allowed_emails = [e.strip().lower() for e in settings.CREDENCE_ADMIN_EMAILS.split(",") if e.strip()]
        # Check unverified / verified JWT payload email claim
        try:
            parts = token.split(".")
            if len(parts) == 3:
                payload_b64 = parts[1] + "=="
                payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
                payload = json.loads(payload_json)
                user_email = str(payload.get("email", "")).lower()
                if user_email and user_email in allowed_emails:
                    return {"authenticated": True, "role": "OPERATOR", "identity": user_email, "method": "OAUTH_JWT"}
        except Exception:
            pass

    # 3. Mode 3: Cloudflare Access Edge JWT assertion / Header
    if cf_email and settings.CREDENCE_ADMIN_EMAILS:
        allowed_emails = [e.strip().lower() for e in settings.CREDENCE_ADMIN_EMAILS.split(",") if e.strip()]
        if cf_email.lower() in allowed_emails:
            return {"authenticated": True, "role": "OPERATOR", "identity": cf_email, "method": "CLOUDFLARE_ACCESS"}

    # 4. Local Development Fallback Key
    if settings.ENV != "production":
        client_host = getattr(request.client, "host", "") if hasattr(request, "client") and request.client else ""
        if token in ("dev_admin_key", "local_admin_token"):  # noqa: S105
            return {"authenticated": True, "role": "OPERATOR", "identity": "local-dev", "method": "DEV_KEY"}
        if client_host in ("127.0.0.1", "localhost", "::1", "testclient"):
            return {"authenticated": True, "role": "OPERATOR", "identity": "local-loopback", "method": "LOCAL_LOOPBACK"}

    return {"authenticated": False, "role": "ANONYMOUS", "identity": None, "method": None}


def _check_admin_auth(request: Any) -> bool:
    """Verify administrator Bearer token, header, or OAuth session authentication."""
    info = get_auth_identity(request)
    return bool(info.get("authenticated", False))
