"""Credence Server Application Factory & Router Assembly.

Governed by Invariant 8: Universal 4-Way Feature Parity.
Architecture: Modular Dispatcher (<150 LOC).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.staticfiles import StaticFiles

from credence.server.api.analytics import (
    api_bounties,
    api_get_attestation_badge,
    api_get_badge_svg,
    api_get_merit,
    api_get_publisher_badge,
    api_leaderboard,
    api_list_publishers,
    api_publisher_analytics,
    api_rankings_rules,
    api_verify_merit,
    api_weather,
)
from credence.server.api.audits import api_audit_url, api_get_report, api_reports
from credence.server.api.cost import (
    api_cost_budget,
    api_cost_emergency_stop,
    api_cost_recommendations,
    api_cost_resume,
    api_cost_telemetry,
)
from credence.server.api.database import (
    api_db_backup,
    api_db_export_pack,
    api_db_import_pack,
    api_db_restore,
    api_db_status,
)
from credence.server.api.domains import (
    api_domain_appeal,
    api_domain_quarantine,
    api_domain_reputation,
    api_rankings_domains,
)
from credence.server.api.feeds import (
    api_boredom_cycle,
    api_boredom_status,
    api_feeds_sentinel_toggle,
    api_feeds_sentinels,
    api_feeds_stream,
    api_roots_candidates,
    api_roots_expand,
    api_roots_tree,
    api_sifter_cycle,
    api_sifter_status,
)
from credence.server.api.governance import (
    api_benchmark_rfc,
    api_get_rfc,
    api_list_rfcs,
    api_validate_rfc,
)
from credence.server.api.mesh import api_mesh_network_health, api_mesh_stats
from credence.server.api.system import (
    api_auth_config,
    api_auth_verify,
    api_cron_boredom,
    api_favicon,
    api_germinate,
    api_get_mesh_status,
    api_health,
    api_node_stats,
    api_root_index,
    api_set_operational_profile,
)
from credence.server.api.widget import api_get_badge_data, api_get_history
from credence.server.lifespan import combined_lifespan
from credence.server.mcp.server import create_mcp_server
from credence.server.middleware.rate_limit import ServerRateLimiter
from credence.server.middleware.security import _check_admin_auth
from credence.server.middleware.telemetry import global_telemetry


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Enforce Interface Telemetry Loopback Protocol (ITLP-v1)."""

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        t0 = time.perf_counter()
        status_code = 500
        error_msg = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            global_telemetry.record_request(status_code, request.url.path, dt_ms, error_msg)


def create_server_app(enable_sifter: bool = True, enable_boredom: bool = True) -> Starlette:
    """Instantiate and assemble the full Credence FastMCP + REST Starlette application."""
    mcp = create_mcp_server()
    app = mcp.streamable_http_app()

    rest_routes = [
        Route("/", endpoint=api_root_index, methods=["GET", "OPTIONS"]),
        Route("/favicon.ico", endpoint=api_favicon, methods=["GET", "OPTIONS"]),
        Route("/health", endpoint=api_health, methods=["GET"]),
        Route("/api/health", endpoint=api_health, methods=["GET"]),
        Route("/api/node/stats", endpoint=api_node_stats, methods=["GET", "OPTIONS"]),
        Route("/api/auth/config", endpoint=api_auth_config, methods=["GET", "OPTIONS"]),
        Route("/api/auth/verify", endpoint=api_auth_verify, methods=["GET", "POST", "OPTIONS"]),
        Route("/api/v1/badge/{identifier:path}", endpoint=api_get_badge_data, methods=["GET", "OPTIONS"]),
        Route("/api/badge/data/{identifier:path}", endpoint=api_get_badge_data, methods=["GET", "OPTIONS"]),
        Route("/api/v1/history/{identifier:path}", endpoint=api_get_history, methods=["GET", "OPTIONS"]),
        Route("/api/history/{identifier:path}", endpoint=api_get_history, methods=["GET", "OPTIONS"]),
        Route("/api/v1/mesh/stats", endpoint=api_mesh_stats, methods=["GET", "OPTIONS"]),
        Route("/api/mesh/stats", endpoint=api_mesh_stats, methods=["GET", "OPTIONS"]),
        Route("/api/v1/mesh/status", endpoint=api_get_mesh_status, methods=["GET", "OPTIONS"]),
        Route("/api/mesh/status", endpoint=api_get_mesh_status, methods=["GET", "OPTIONS"]),
        Route("/api/v1/mesh/network-health", endpoint=api_mesh_network_health, methods=["GET", "OPTIONS"]),
        Route("/api/mesh/network-health", endpoint=api_mesh_network_health, methods=["GET", "OPTIONS"]),
        Route("/api/v1/mesh/health", endpoint=api_mesh_network_health, methods=["GET", "OPTIONS"]),
        Route("/api/mesh/health", endpoint=api_mesh_network_health, methods=["GET", "OPTIONS"]),
        Route("/api/v1/config/profile", endpoint=api_set_operational_profile, methods=["POST", "OPTIONS"]),
        Route("/api/config/profile", endpoint=api_set_operational_profile, methods=["POST", "OPTIONS"]),
        Route("/api/reports", endpoint=api_reports, methods=["GET", "OPTIONS"]),
        Route("/api/reports/{identifier:path}", endpoint=api_get_report, methods=["GET", "OPTIONS"]),
        Route("/api/rfcs", endpoint=api_list_rfcs, methods=["GET", "OPTIONS"]),
        Route("/api/rfcs/validate", endpoint=api_validate_rfc, methods=["POST", "OPTIONS"]),
        Route("/api/rfcs/benchmark", endpoint=api_benchmark_rfc, methods=["POST", "OPTIONS"]),
        Route("/api/rfcs/{rfc_id:path}", endpoint=api_get_rfc, methods=["GET", "OPTIONS"]),
        Route("/api/cost/telemetry", endpoint=api_cost_telemetry, methods=["GET", "OPTIONS"]),
        Route("/api/cost/recommendations", endpoint=api_cost_recommendations, methods=["GET", "OPTIONS"]),
        Route("/api/cost/budget", endpoint=api_cost_budget, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/cost/emergency-stop", endpoint=api_cost_emergency_stop, methods=["POST", "OPTIONS"]),
        Route("/api/cost/resume", endpoint=api_cost_resume, methods=["POST", "OPTIONS"]),
        Route("/api/audit", endpoint=api_audit_url, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/germinate", endpoint=api_germinate, methods=["POST", "GET", "OPTIONS"]),
        Route("/cron/boredom", endpoint=api_cron_boredom, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/sifter/status", endpoint=api_sifter_status, methods=["GET", "OPTIONS"]),
        Route("/api/sifter/cycle", endpoint=api_sifter_cycle, methods=["POST", "OPTIONS"]),
        Route("/api/roots/expand", endpoint=api_roots_expand, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/roots/tree", endpoint=api_roots_tree, methods=["GET", "OPTIONS"]),
        Route("/api/roots/candidates", endpoint=api_roots_candidates, methods=["GET", "OPTIONS"]),
        Route("/api/boredom/cycle", endpoint=api_boredom_cycle, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/boredom/status", endpoint=api_boredom_status, methods=["GET", "OPTIONS"]),
        Route("/api/domain/reputation/{domain:path}", endpoint=api_domain_reputation, methods=["GET", "OPTIONS"]),
        Route("/api/domain/quarantine", endpoint=api_domain_quarantine, methods=["GET", "OPTIONS"]),
        Route("/api/domain/appeal/{domain:path}", endpoint=api_domain_appeal, methods=["POST", "OPTIONS"]),
        Route("/api/feeds/stream", endpoint=api_feeds_stream, methods=["GET", "OPTIONS"]),
        Route("/api/feeds/sentinels", endpoint=api_feeds_sentinels, methods=["GET", "OPTIONS"]),
        Route("/api/feeds/sentinel", endpoint=api_feeds_sentinel_toggle, methods=["POST", "GET", "OPTIONS"]),
        Route("/api/leaderboard", endpoint=api_leaderboard, methods=["GET", "OPTIONS"]),
        Route("/api/merit", endpoint=api_get_merit, methods=["GET", "OPTIONS"]),
        Route("/api/merit/verify", endpoint=api_verify_merit, methods=["POST", "OPTIONS"]),
        Route("/api/merit/{identifier:path}", endpoint=api_get_merit, methods=["GET", "OPTIONS"]),
        Route("/api/badge/publisher/{domain:path}", endpoint=api_get_publisher_badge, methods=["GET", "OPTIONS"]),
        Route(
            "/api/badge/attestation/{identifier:path}", endpoint=api_get_attestation_badge, methods=["GET", "OPTIONS"]
        ),
        Route("/api/badge/{badge_id:path}", endpoint=api_get_badge_svg, methods=["GET", "OPTIONS"]),
        Route("/api/rankings/domains", endpoint=api_rankings_domains, methods=["GET", "OPTIONS"]),
        Route("/api/rankings/rules", endpoint=api_rankings_rules, methods=["GET", "OPTIONS"]),
        Route("/api/analytics/publishers", endpoint=api_list_publishers, methods=["GET", "OPTIONS"]),
        Route("/api/analytics/publisher/{domain:path}", endpoint=api_publisher_analytics, methods=["GET", "OPTIONS"]),
        Route("/api/weather", endpoint=api_weather, methods=["GET", "OPTIONS"]),
        Route("/api/bounties", endpoint=api_bounties, methods=["GET", "OPTIONS"]),
        Route("/api/db/backup", endpoint=api_db_backup, methods=["POST", "OPTIONS"]),
        Route("/api/db/restore", endpoint=api_db_restore, methods=["POST", "OPTIONS"]),
        Route("/api/db/status", endpoint=api_db_status, methods=["GET", "OPTIONS"]),
        Route("/api/db/export-pack", endpoint=api_db_export_pack, methods=["GET", "POST", "OPTIONS"]),
        Route("/api/db/import-pack", endpoint=api_db_import_pack, methods=["POST", "OPTIONS"]),
    ]

    for r in reversed(rest_routes):
        app.router.routes.insert(0, r)

    parents = Path(__file__).resolve().parents
    local_web_candidates = [
        Path("/app/web"),
        Path.cwd() / "web",
        parents[2] / "web" if len(parents) > 2 else None,
    ]
    web_dir = next((p for p in local_web_candidates if p and p.exists() and p.is_dir()), None)
    if web_dir:
        if (web_dir / "assets").exists():
            app.mount("/assets", StaticFiles(directory=str(web_dir / "assets")), name="assets")
        if (web_dir / "credence.run").exists():
            app.mount("/credence.run", StaticFiles(directory=str(web_dir / "credence.run"), html=True), name="run")
        if (web_dir / "admin.credence.run").exists():
            app.mount(
                "/admin.credence.run",
                StaticFiles(directory=str(web_dir / "admin.credence.run"), html=True),
                name="admin",
            )
        if (web_dir / "credence.report").exists():
            app.mount(
                "/credence.report", StaticFiles(directory=str(web_dir / "credence.report"), html=True), name="report"
            )
        if (web_dir / "credence.foundation").exists():
            app.mount(
                "/credence.foundation",
                StaticFiles(directory=str(web_dir / "credence.foundation"), html=True),
                name="foundation",
            )
        if (web_dir / "credence.nexus").exists():
            app.mount(
                "/credence.nexus", StaticFiles(directory=str(web_dir / "credence.nexus"), html=True), name="nexus"
            )
        app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(TelemetryMiddleware)

    app.router.lifespan_context = combined_lifespan(app, enable_sifter=enable_sifter, enable_boredom=enable_boredom)
    return app


create_app = create_server_app
mcp_server = create_mcp_server()
app = create_server_app()

__all__ = ["app", "create_app", "_check_admin_auth", "ServerRateLimiter"]
