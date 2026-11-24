"""Hermetic unit tests and offline Tier 2 gate for the Canonical Model Registry.

Validates:
1. Canonical ModelSpec schema completeness across active and legacy replay models.
2. Offline sunset horizon (30 days), active status, pricing parity, and Antigravity-harness alignment gate.
3. Negative detection of expired, imminent-sunset, inactive, unaligned, and unpriced models.
4. `credence models check` CLI (offline default, --json, and mocked --live drift discovery).
"""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from credence.cli.commands.models import run_models_check_command, run_models_list_command
from credence.cli.main import build_parser
from credence.config import COST_PROFILES, CostProfile, CostProfileConfig, settings
from credence.pipeline.governor import MODEL_PRICING_PER_MILLION
from credence.pipeline.model_registry import (
    MODEL_REGISTRY,
    VALID_STATUSES,
    VALID_SURFACES,
    VALID_THINKING_MODES,
    audit_model_catalog,
    compute_thinking_mode,
    get_model_pricing_per_million,
    get_model_spec,
    normalize_model_id,
)


@pytest.mark.unit
def test_model_registry_schema_and_active_gemini4_catalog() -> None:
    """Verify every registered model has valid metadata and the active Gemini 3.8 / 4 lineup is present."""
    assert len(MODEL_REGISTRY) >= 12

    for model_id, spec in MODEL_REGISTRY.items():
        assert spec.model_id == model_id
        assert spec.family
        assert spec.supported_surfaces
        assert spec.supported_surfaces.issubset(VALID_SURFACES)
        assert spec.thinking_mode in VALID_THINKING_MODES
        assert spec.status in VALID_STATUSES
        for key in ("prompt", "completion", "thinking"):
            assert key in spec.pricing_per_million
            assert spec.pricing_per_million[key] >= 0.0

    # Active Antigravity-aligned Gemini 3.8 & Gemini 4 lineup
    active_gemini = [
        "gemini-3.8-flash",
        "gemini-4-hydrogen",
        "gemini-4-argon",
        "gemini-4-neon",
        "gemini-4-carbon",
    ]
    for model_id in active_gemini:
        active_spec = get_model_spec(model_id)
        assert active_spec is not None, f"Missing active model {model_id}"
        assert active_spec.status == "active"
        assert active_spec.thinking_mode == "level"
        assert "antigravity-harness" in active_spec.supported_surfaces
        assert "gemini-api" in active_spec.supported_surfaces


@pytest.mark.unit
def test_legacy_models_retained_for_historical_replay() -> None:
    """Verify legacy models remain in model_registry.py as deprecated/retired with pricing preserved."""
    legacy_models = [
        "gemini-3.7-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
    ]
    for model_id in legacy_models:
        spec = get_model_spec(model_id)
        assert spec is not None, f"Legacy model {model_id} missing from registry"
        assert spec.status in ("deprecated", "retired")
        assert spec.replacement_model is not None
        assert get_model_spec(spec.replacement_model) is not None
        assert model_id in MODEL_PRICING_PER_MILLION


@pytest.mark.unit
def test_normalize_model_id_and_thinking_mode_resolution() -> None:
    """Verify provider/API prefixes normalize cleanly and thinking modes resolve deterministically."""
    assert normalize_model_id("google/gemini-3.8-flash") == "gemini-3.8-flash"
    assert normalize_model_id("models/gemini-4-neon") == "gemini-4-neon"
    assert normalize_model_id("meta/llama-3.3-70b-instruct-maas") == "meta/llama-3.3-70b-instruct-maas"

    assert compute_thinking_mode("google/gemini-3.8-flash") == "level"
    assert compute_thinking_mode("gemini-4-carbon") == "level"
    assert compute_thinking_mode("gemini-4.5-pro") == "level"
    assert compute_thinking_mode("gemini-3.7-flash") == "budget"
    assert compute_thinking_mode("gemini-2.5-flash-lite") == "budget"
    assert compute_thinking_mode("gemini-2.0-flash-lite") == "none"
    assert compute_thinking_mode("gemini-1.5-pro") == "none"


@pytest.mark.unit
def test_model_catalog_freshness_and_sunset_dates() -> None:
    """Offline Tier 2 Governance Gate: active presets & defaults must be active, unexpired, priced, and harness-aligned."""
    report = audit_model_catalog(horizon_days=30)
    errors = [i for i in report.issues if i.severity == "error"]
    assert report.passed, f"Model catalog freshness gate failed: {errors}"

    # Verify pricing table is derived directly from model_registry.py with zero drift
    registry_pricing = get_model_pricing_per_million()
    assert MODEL_PRICING_PER_MILLION == registry_pricing

    # Verify every active LLM profile model declares antigravity-harness and has pricing parity
    for profile in (CostProfile.FREE, CostProfile.ECONOMY, CostProfile.BALANCED, CostProfile.ULTRA):
        cfg = COST_PROFILES[profile]
        for model_id in (cfg.primary_model, cfg.escalation_model, cfg.triage_model):
            spec = get_model_spec(model_id)
            assert spec is not None
            assert spec.status == "active"
            assert "antigravity-harness" in spec.supported_surfaces
            assert model_id in MODEL_PRICING_PER_MILLION

    # Verify Settings defaults are active and harness-aligned
    for default_model in (
        settings.DEFAULT_SPECIALIST_MODEL,
        settings.DEFAULT_TRIAGE_MODEL,
        settings.DEFAULT_WORKER_MODEL,
    ):
        spec = get_model_spec(default_model)
        assert spec is not None
        assert spec.status == "active"
        assert "antigravity-harness" in spec.supported_surfaces


@pytest.mark.unit
def test_audit_catches_expired_imminent_inactive_unaligned_and_unpriced_models() -> None:
    """Negative gate checks: audit_model_catalog catches sunset, status, harness, and pricing violations."""
    base_cfg = COST_PROFILES[CostProfile.ECONOMY]

    # 1. Imminent sunset (gemini-2.5-flash-lite sunsets 2026-12-01; checking as of 2026-11-23 is 8 days away)
    imminent_profiles = {
        CostProfile.ECONOMY: base_cfg.model_copy(update={"triage_model": "gemini-2.5-flash-lite"}),
    }
    rep_imminent = audit_model_catalog(
        as_of=date(2026, 11, 23),
        horizon_days=30,
        profiles=imminent_profiles,
        default_models={},
    )
    assert not rep_imminent.passed
    codes = {i.code for i in rep_imminent.issues}
    assert "SUNSET_IMMINENT" in codes
    assert "INACTIVE_MODEL" in codes

    # 2. Already-expired sunset (gemini-2.0-flash-lite retired 2026-06-01)
    expired_profiles = {
        CostProfile.FREE: COST_PROFILES[CostProfile.FREE].model_copy(update={"primary_model": "gemini-2.0-flash-lite"}),
    }
    rep_expired = audit_model_catalog(
        as_of=date(2026, 11, 23),
        horizon_days=30,
        profiles=expired_profiles,
        default_models={},
    )
    assert not rep_expired.passed
    assert any(i.code == "SUNSET_EXPIRED" for i in rep_expired.issues)

    # 3. Active API model NOT aligned with antigravity-harness (gemini-3.5-flash-lite)
    unaligned_profiles: dict[CostProfile, CostProfileConfig] = {
        CostProfile.ECONOMY: base_cfg.model_copy(update={"triage_model": "gemini-3.5-flash-lite"}),
    }
    rep_unaligned = audit_model_catalog(
        as_of=date(2026, 11, 23),
        horizon_days=30,
        profiles=unaligned_profiles,
        default_models={},
    )
    assert not rep_unaligned.passed
    assert any(i.code == "HARNESS_UNALIGNED" for i in rep_unaligned.issues)

    # 4. Missing pricing entry
    rep_unpriced = audit_model_catalog(
        as_of=date(2026, 11, 23),
        horizon_days=30,
        profiles={CostProfile.FREE: COST_PROFILES[CostProfile.FREE]},
        default_models={},
        pricing_table={},
    )
    assert not rep_unpriced.passed
    assert any(i.code == "PRICING_MISSING" for i in rep_unpriced.issues)


@pytest.mark.unit
def test_cli_models_parser_shapes() -> None:
    """Verify CLI parser supports `credence models check [--live] [--json]`, `models list`, and `compare <url>`."""
    parser = build_parser()

    args_check = parser.parse_args(["models", "check"])
    assert args_check.command == "models"
    assert args_check.action == "check"
    assert args_check.live is False

    args_live = parser.parse_args(["models", "check", "--live", "--json", "--horizon-days", "45"])
    assert args_live.live is True
    assert args_live.json is True
    assert args_live.horizon_days == 45

    args_list = parser.parse_args(["models", "list"])
    assert args_list.action == "list"

    args_compare = parser.parse_args(["compare", "https://example.com/article"])
    assert args_compare.command == "compare"
    assert args_compare.url == "https://example.com/article"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cli_models_check_offline_and_live_mocked(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify `credence models check` offline default and optional --live Gemini API drift probe."""
    # Offline JSON check passes cleanly with zero network calls
    code_offline = await run_models_check_command(live=False, json_output=True)
    assert code_offline == 0
    out_offline = json.loads(capsys.readouterr().out)
    assert out_offline["passed"] is True
    assert out_offline["live_api_checked"] is False

    # Live check with mocked Gemini API response surfacing a newly released model
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [
            {"name": "models/gemini-3.8-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-4-hydrogen", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-4-argon", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-4-neon", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-4-carbon", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-4.5-krypton", "supportedGenerationMethods": ["generateContent"]},
        ]
    }
    with (
        patch("credence.cli.commands.models.resolve_provider_key", return_value="fake-gemini-key"),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp) as mock_get,
    ):
        code_live = await run_models_check_command(live=True, json_output=True)
        assert code_live == 0
        assert mock_get.await_count == 1
        out_live = json.loads(capsys.readouterr().out)
        assert out_live["live_api_checked"] is True
        assert "gemini-4.5-krypton" in out_live["live_new_models"]
        assert out_live["live_missing_models"] == []

    # Live check without configured API key degrades gracefully without crashing
    with patch("credence.cli.commands.models.resolve_provider_key", return_value=""):
        code_no_key = await run_models_check_command(live=True, json_output=True)
        assert code_no_key == 0
        out_no_key = json.loads(capsys.readouterr().out)
        assert out_no_key["live_api_checked"] is False
        assert out_no_key["live_error"] is not None

    # List command executes cleanly
    assert run_models_list_command(json_output=False) == 0
