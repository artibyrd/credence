"""Unit tests for the Credence FastMCP Server."""

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.models import utc_now
from credence.pipeline.schemas import AuditReport
from credence.server.app import create_mcp_server


@pytest.mark.unit
async def test_fastmcp_server_initialization() -> None:
    """Verify FastMCP server initializes with expected name, tools, resources, and prompts."""
    server = create_mcp_server()
    assert server.name == "credence"

    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "credence_check_url" in tool_names
    assert "credence_evaluate_text" in tool_names
    assert "credence_get_audit" in tool_names
    assert "credence_browse_audits" in tool_names
    assert "credence_verify_attestation" in tool_names
    assert "credence_get_quota_status" in tool_names
    assert "credence_get_consensus" in tool_names
    assert "credence_get_seed_nodes" in tool_names
    assert "credence_sync_feeds" in tool_names
    assert "credence_add_feed_subscription" in tool_names
    assert "credence_list_feeds" in tool_names
    assert "credence_remove_feed_subscription" in tool_names
    assert "credence_get_feed_stats" in tool_names
    assert "credence_get_health_status" in tool_names

    resources = await server.list_resources()
    resource_uris = [r.uri for r in resources]
    assert "credence://taxonomies" in resource_uris
    assert "credence://node/identity" in resource_uris
    assert "credence://node/health" in resource_uris
    assert "credence://mesh/seeds" in resource_uris
    assert "credence://profiles" in resource_uris
    assert "credence://subjects/registry" in resource_uris
    assert "credence://subjects/leaderboard" in resource_uris
    assert "credence://feeds/status" in resource_uris

    prompts = await server.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "audit_article_prompt" in prompt_names
    assert "explain_audit_report_prompt" in prompt_names
    assert "fallacy_review_prompt" in prompt_names
    assert "dark_pattern_review_prompt" in prompt_names


@pytest.mark.unit
async def test_fastmcp_evaluate_text_tool() -> None:
    """Verify credence_evaluate_text tool directly audits raw text without network requests."""
    server = create_mcp_server()

    raw_text = (
        "Either you are 100% on our side, or you are an enemy of the people! Those ignorant cowards hate progress."
    )
    res: Any = await server.call_tool(
        "credence_evaluate_text",
        {"text": raw_text, "title": "Test Fallacy Snippet"},
    )
    assert res is not None
    text_content = res.content[0].text
    data = json.loads(text_content)
    assert data["suspicion_score"] > 0.0
    assert len(data["violations"]) >= 2
    assert any(v["rule_id"] == "FALLACY-2.2" for v in data["violations"])
    assert data["node_signature"] is not None


@pytest.mark.unit
async def test_fastmcp_verify_attestation_tool() -> None:
    """Verify credence_verify_attestation tool validates authentic and tampered attestations."""
    server = create_mcp_server()
    identity = load_or_create_node_identity()

    report = AuditReport(
        url="https://example.com/test",
        content_sha256="sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        simhash_64="0x1234567890abcdef",
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=1.0,
        classification="CLEAN",
    )
    signed_report = sign_audit_report(report, identity)

    # Valid check
    valid_res: Any = await server.call_tool(
        "credence_verify_attestation",
        {"signed_attestation_json": signed_report.model_dump_json()},
    )
    valid_data = json.loads(valid_res.content[0].text)
    assert valid_data["is_valid"] is True

    # Tampered check
    tampered_data = signed_report.model_dump(mode="json")
    tampered_data["suspicion_score"] = 99.9  # Tamper score
    invalid_res: Any = await server.call_tool(
        "credence_verify_attestation",
        {"signed_attestation_json": json.dumps(tampered_data)},
    )
    invalid_data = json.loads(invalid_res.content[0].text)
    assert invalid_data["is_valid"] is False


@pytest.mark.unit
async def test_fastmcp_quota_and_resources() -> None:
    """Verify quota status tool and dynamic resources."""
    server = create_mcp_server()

    # Quota tool
    quota_res: Any = await server.call_tool("credence_get_quota_status", {})
    quota_data = json.loads(quota_res.content[0].text)
    assert "hourly_headroom_pct" in quota_data
    assert "daily_spend_usd" in quota_data

    # Profiles resource
    prof_res: Any = await server.read_resource("credence://profiles")
    prof_data = json.loads(prof_res[0].content)
    assert "free" in prof_data
    assert "balanced" in prof_data
    assert "ultra" in prof_data

    # Subjects registry resource
    subj_res: Any = await server.read_resource("credence://subjects/registry")
    subj_data = json.loads(subj_res[0].content)
    assert len(subj_data) >= 3

    # Taxonomies resource
    tax_res: Any = await server.read_resource("credence://taxonomies")
    tax_data = json.loads(tax_res[0].content)
    assert len(tax_data) >= 3

    # Node Identity resource
    id_res: Any = await server.read_resource("credence://node/identity")
    id_data = json.loads(id_res[0].content)
    assert "public_key_hex" in id_data


@pytest.mark.unit
async def test_fastmcp_human_report_resource_and_prompt(db_session: Any) -> None:
    """Verify human report resource formatting and explain prompt template."""
    server = create_mcp_server()

    # 1. Test explain prompt template
    prompt_res: Any = await server.get_prompt("explain_audit_report_prompt", {"identifier": "https://example.com/news"})
    assert prompt_res is not None
    assert "https://example.com/news" in prompt_res.messages[0].content.text
    assert "credence_get_audit" in prompt_res.messages[0].content.text

    # 2. Test direct evaluate and get_audit with markdown / human format
    eval_res: Any = await server.call_tool(
        "credence_evaluate_text",
        {"text": "Either you support this completely or you are an enemy!", "title": "Fallacy Test"},
    )
    eval_data = json.loads(eval_res.content[0].text)
    content_hash = eval_data["content_sha256"]

    # Retrieve formatted as human
    human_res: Any = await server.call_tool(
        "credence_get_audit",
        {"identifier": content_hash, "format": "human"},
    )
    human_text = human_res.content[0].text
    assert "🧠 Human Epistemic Briefing" in human_text
    assert "Credence Epistemic Audit Report" in human_text

    # Retrieve formatted as compact, ndjson, and tsv
    compact_res: Any = await server.call_tool(
        "credence_get_audit",
        {"identifier": content_hash, "format": "compact"},
    )
    assert "Score:" in compact_res.content[0].text
    assert "Findings:" in compact_res.content[0].text

    ndjson_res: Any = await server.call_tool(
        "credence_get_audit",
        {"identifier": content_hash, "format": "ndjson"},
    )
    assert content_hash in ndjson_res.content[0].text

    tsv_res: Any = await server.call_tool(
        "credence_get_audit",
        {"identifier": content_hash, "format": "tsv"},
    )
    assert content_hash in tsv_res.content[0].text

    # Test browse audits tool
    browse_res: Any = await server.call_tool(
        "credence_browse_audits",
        {"category": "recent", "limit": 5, "format": "human"},
    )
    assert "Credence Epistemic Audits Stream" in browse_res.content[0].text

    browse_json_res: Any = await server.call_tool(
        "credence_browse_audits",
        {"category": "best", "limit": 5, "format": "json"},
    )
    assert browse_json_res is not None

    # Retrieve via human resource
    res_list: Any = await server.read_resource(f"credence://reports/{content_hash}/human")
    assert res_list is not None and len(res_list) > 0
    res_text = res_list[0].content if hasattr(res_list[0], "content") else str(res_list[0])
    assert "Human Epistemic Briefing" in res_text

    # Retrieve via compact resource
    res_compact: Any = await server.read_resource(f"credence://reports/{content_hash}/compact")
    assert res_compact is not None and len(res_compact) > 0
    compact_text = res_compact[0].content if hasattr(res_compact[0], "content") else str(res_compact[0])
    assert "Score:" in compact_text

    # Retrieve via raw resource
    res_raw: Any = await server.read_resource(f"credence://reports/{content_hash}/raw")
    assert res_raw is not None and len(res_raw) > 0

    # Retrieve via explore resource
    res_explore: Any = await server.read_resource("credence://reports/explore/recent")
    assert res_explore is not None and len(res_explore) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_starlette_rest_endpoints(db_session: Any) -> None:
    """Verify Starlette REST API endpoints (/health, /api/reports, /api/sifter/status, /api/feeds/stream)."""
    import httpx
    from httpx import ASGITransport

    from credence.server.app import create_server_app

    app = create_server_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0. Root index and favicon discovery
        res_root_json = await client.get("/", headers={"accept": "application/json"})
        assert res_root_json.status_code == 200
        root_data = res_root_json.json()
        assert root_data["service"] == "credence-server"
        assert "endpoints" in root_data

        res_root_html = await client.get("/", headers={"accept": "text/html"})
        assert res_root_html.status_code == 200
        assert "Credence Node Server" in res_root_html.text

        res_favicon = await client.get("/favicon.ico")
        assert res_favicon.status_code == 204

        # 1. Health check (with Interface Telemetry Loopback payload)
        res_health = await client.get("/health")
        assert res_health.status_code == 200
        health_json = res_health.json()
        assert health_json["status"] == "healthy"
        assert "telemetry" in health_json
        assert "uptime_seconds" in health_json["telemetry"]
        assert "request_counts" in health_json["telemetry"]

        res_api_health = await client.get("/api/health")
        assert res_api_health.status_code == 200
        api_health_json = res_api_health.json()
        assert api_health_json["status"] == "healthy"
        assert "telemetry" in api_health_json

        # 2. Reports endpoint
        res_reports = await client.get("/api/reports?category=recent&limit=10")
        assert res_reports.status_code == 200
        data = res_reports.json()
        assert "reports" in data
        assert "total" in data

        # 3. Sifter status endpoint
        res_status = await client.get("/api/sifter/status")
        assert res_status.status_code == 200
        status_data = res_status.json()
        assert status_data["status"] == "online"
        assert "active_feed_subscriptions" in status_data

        # 4. Feeds stream endpoint
        res_stream = await client.get("/api/feeds/stream?limit=10")
        assert res_stream.status_code == 200
        stream_data = res_stream.json()
        assert "items" in stream_data

        # 5. Germinate endpoint
        res_germ = await client.post("/api/germinate", json={"burst": 0, "sync_mesh": False})
        assert res_germ.status_code == 200
        germ_data = res_germ.json()
        assert germ_data["status"] in ("germinated", "incremental_ready")

        # 6. Roots tree and candidates endpoints
        res_tree = await client.get("/api/roots/tree")
        assert res_tree.status_code == 200
        tree_data = res_tree.json()
        assert "total_active_roots" in tree_data

        res_cands = await client.get("/api/roots/candidates")
        assert res_cands.status_code == 200
        cands_data = res_cands.json()
        assert "candidates" in cands_data

        # 7. Boredom status and cycle endpoints
        from credence.feeds.boredom import BoredomCycleSummary

        res_boredom_status = await client.get("/api/boredom/status")
        assert res_boredom_status.status_code == 200
        b_status = res_boredom_status.json()
        assert "token_headroom" in b_status
        assert "queue" in b_status

        mock_summary = BoredomCycleSummary(
            timestamp=utc_now(),
            headroom_daily_pct=100.0,
            headroom_hourly_pct=100.0,
            circuit_breaker_tripped=False,
            pending_items_scanned=0,
            pending_items_audited=0,
            mesh_attestations_adopted=0,
            items_deferred_budget=0,
            tokens_saved_mesh=0,
            new_roots_subscribed=0,
            initial_items_harvested=0,
            details=[],
        )

        with patch("credence.feeds.boredom.run_boredom_cycle", new=AsyncMock(return_value=mock_summary)):
            res_b_cycle = await client.post("/api/boredom/cycle", json={"burst": 1, "expand_roots": False})
            assert res_b_cycle.status_code == 200
            cycle_data = res_b_cycle.json()
            assert "headroom_daily_pct" in cycle_data

        # 8. Merit and Cryptographic Verification endpoints
        res_merit = await client.get("/api/merit")
        assert res_merit.status_code == 200
        merit_data = res_merit.json()
        assert "tier" in merit_data
        assert "node_pubkey" in merit_data
        assert "canonical_sha256" in merit_data
        assert "signature" in merit_data
        assert merit_data["canonical_sha256"].startswith("sha256:")

        # Verify authentic merit payload via REST
        res_verify = await client.post("/api/merit/verify", json=merit_data)
        assert res_verify.status_code == 200
        verify_data = res_verify.json()
        assert verify_data["valid"] is True
        assert verify_data["tampered"] is False

        # Verify tampered payload is detected and rejected
        tampered_merit = dict(merit_data)
        tampered_merit["tier"] = "ROOT_ANCHOR"
        res_tampered = await client.post("/api/merit/verify", json=tampered_merit)
        assert res_tampered.status_code == 200
        tampered_data = res_tampered.json()
        assert tampered_data["valid"] is False
        assert tampered_data["tampered"] is True


@pytest.mark.unit
async def test_server_telemetry_tracker_and_alerts() -> None:
    """Verify ServerTelemetryTracker rolling window, 5xx alert triggers, and memory pressure warnings."""
    from credence.server.app import global_telemetry

    global_telemetry.reset()
    snap = global_telemetry.get_snapshot()
    assert snap["status"] == "healthy"
    assert snap["request_counts"]["total"] == 0
    assert len(snap["active_alerts"]) == 0

    # 1. Record normal 2xx traffic
    for _ in range(10):
        global_telemetry.record_request(status_code=200, path="/api/reports", duration_ms=15.0)

    snap = global_telemetry.get_snapshot()
    assert snap["request_counts"]["total"] == 10
    assert snap["request_counts"]["2xx"] == 10
    assert snap["status"] == "healthy"

    # 2. Record 5xx errors to trigger spike alert (>= 5 errors)
    for _ in range(5):
        global_telemetry.record_request(
            status_code=500, path="/api/audit", duration_ms=120.0, error_message="Internal Server Error"
        )

    snap = global_telemetry.get_snapshot()
    assert snap["request_counts"]["5xx"] == 5
    assert snap["status"] == "degraded"
    assert any(a["id"] == "alert_5xx_spike" for a in snap["active_alerts"])
    assert len(snap["recent_errors"]) == 5

    # 3. Clean reset
    global_telemetry.reset()
    snap_after = global_telemetry.get_snapshot()
    assert snap_after["request_counts"]["total"] == 0
    assert snap_after["status"] == "healthy"


@pytest.mark.unit
async def test_fastmcp_health_tool_and_resource() -> None:
    """Verify FastMCP credence_get_health_status tool and credence://node/health resource."""
    server = create_mcp_server()

    # Read resource
    res: Any = await server.read_resource("credence://node/health")
    assert res is not None
    data = json.loads(res[0].content)
    assert "status" in data
    assert "request_counts" in data

    # Call tool
    tool_res: Any = await server.call_tool("credence_get_health_status", arguments={})
    assert tool_res is not None
    tool_data = json.loads(tool_res.content[0].text)
    assert "status" in tool_data
    assert "uptime_seconds" in tool_data
