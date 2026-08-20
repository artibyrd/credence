"""CORS Configuration & Headers for Credence Server."""

from __future__ import annotations

from starlette.middleware.cors import CORSMiddleware


def setup_cors(app) -> None:
    """Configure permissive, secure cross-origin headers for zero-build web surfaces."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
