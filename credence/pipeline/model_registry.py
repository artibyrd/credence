"""Canonical Model Registry & Offline Lifecycle Governance for Credence.

Single source of truth for:
1. Active Antigravity-aligned Gemini 3.8 & Gemini 4 models (`thinking_mode="level"`).
2. Valid multi-provider / Vertex Model Garden / local Ollama models.
3. Deprecated and retired legacy models retained strictly for historical replay and cost attribution.
4. Pricing per 1M tokens (consumed by `governor.py` and `cross_model_benchmark.py` for zero drift).
5. Offline Tier 2 sunset, status, pricing parity, and Antigravity-harness alignment audit gate.
6. Optional live Gemini API catalog drift discovery (`credence models check --live`).
"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Tuple

import httpx

ThinkingMode = Literal["level", "budget", "none"]
ModelStatus = Literal["active", "deprecated", "retired"]
AuditSeverity = Literal["error", "warning"]

VALID_SURFACES: frozenset[str] = frozenset(
    {"gemini-api", "vertex-model-garden", "antigravity-harness", "anthropic", "openai", "ollama", "local"}
)
VALID_THINKING_MODES: frozenset[str] = frozenset({"level", "budget", "none"})
VALID_THINKING_LEVELS: frozenset[str] = frozenset({"minimal", "low", "medium", "high"})
VALID_STATUSES: frozenset[str] = frozenset({"active", "deprecated", "retired"})

GEMINI_MODELS_LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models"

_GEMINI_LEVEL_RE = re.compile(r"^gemini-(?:[4-9](?:[.-]|$)|3\.8(?:[.-]|$))")
_GEMINI_BUDGET_RE = re.compile(r"^gemini-(?:3\.[0-7]|2\.5)(?:[.-]|$)")

_S_GEM_AGY = frozenset({"gemini-api", "vertex-model-garden", "antigravity-harness"})
_S_GEM_VTX = frozenset({"gemini-api", "vertex-model-garden"})
_S_GEM_API = frozenset({"gemini-api"})
_S_CLAUDE_AGY = frozenset({"anthropic", "antigravity-harness"})
_S_CLAUDE = frozenset({"anthropic"})
_S_OAI = frozenset({"openai"})
_S_OAI_AGY = frozenset({"openai", "vertex-model-garden", "antigravity-harness"})
_S_OAI_VTX = frozenset({"vertex-model-garden", "openai"})
_S_VTX = frozenset({"vertex-model-garden"})
_S_OLLAMA = frozenset({"ollama"})
_S_LOCAL = frozenset({"local"})


@dataclass(frozen=True)
class ModelSpec:
    """Canonical lifecycle, capability, surface, and pricing specification for a model."""

    model_id: str
    family: str
    supported_surfaces: frozenset[str]
    thinking_mode: ThinkingMode
    pricing_per_million: Mapping[str, float]
    status: ModelStatus
    sunset_date: Optional[date] = None
    replacement_model: Optional[str] = None


@dataclass(frozen=True)
class ModelAuditIssue:
    """A single lifecycle, sunset, pricing, or harness-alignment issue detected by catalog auditing."""

    severity: AuditSeverity
    code: str
    subject: str
    model_id: str
    message: str
    replacement_model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "subject": self.subject,
            "model_id": self.model_id,
            "message": self.message,
            "replacement_model": self.replacement_model,
        }


@dataclass
class ModelCatalogAuditReport:
    """Structured result of an offline (and optional live) model catalog audit."""

    checked_on: date
    horizon_days: int
    issues: List[ModelAuditIssue] = field(default_factory=list)
    active_profile_models: Dict[str, Dict[str, str]] = field(default_factory=dict)
    default_models: Dict[str, str] = field(default_factory=dict)
    live_api_checked: bool = False
    live_new_models: List[str] = field(default_factory=list)
    live_missing_models: List[str] = field(default_factory=list)
    live_error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Return True when zero error-severity catalog issues exist."""
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checked_on": self.checked_on.isoformat(),
            "horizon_days": self.horizon_days,
            "issues": [i.to_dict() for i in self.issues],
            "active_profile_models": self.active_profile_models,
            "default_models": self.default_models,
            "live_api_checked": self.live_api_checked,
            "live_new_models": self.live_new_models,
            "live_missing_models": self.live_missing_models,
            "live_error": self.live_error,
        }


_DEP: ModelStatus = "deprecated"
_RET: ModelStatus = "retired"
_G38 = "gemini-3.8-flash"

# (model_id, family, surfaces, thinking_mode, prompt, completion, status, sunset_iso, replacement)
_MODEL_ROWS: Tuple[
    Tuple[str, str, frozenset[str], ThinkingMode, float, float, ModelStatus, Optional[str], Optional[str]], ...
] = (
    # Active Antigravity-Aligned Gemini 3.8 & Gemini 4 Lineup
    ("gemini-3.8-flash", "google/gemini-3.8", _S_GEM_AGY, "level", 0.10, 0.40, "active", None, None),
    ("gemini-4-hydrogen", "google/gemini-4", _S_GEM_AGY, "level", 0.15, 0.60, "active", None, None),
    ("gemini-4-argon", "google/gemini-4", _S_GEM_AGY, "level", 0.30, 1.20, "active", None, None),
    ("gemini-4-neon", "google/gemini-4", _S_GEM_AGY, "level", 0.50, 2.00, "active", None, None),
    ("gemini-4-carbon", "google/gemini-4", _S_GEM_AGY, "level", 1.25, 5.00, "active", None, None),
    # Other Valid Active API / Model Garden / Local Models
    ("gemini-3.5-flash-lite", "google/gemini-3.5", _S_GEM_VTX, "budget", 0.075, 0.30, "active", None, None),
    ("claude-sonnet-5-5", "anthropic/claude", _S_CLAUDE_AGY, "none", 3.00, 15.00, "active", None, None),
    ("claude-opus-5-5", "anthropic/claude", _S_CLAUDE_AGY, "none", 15.00, 75.00, "active", None, None),
    ("claude-3-7-sonnet-20250219", "anthropic/claude", _S_CLAUDE, "none", 3.00, 15.00, "active", None, None),
    ("gpt-4o", "openai/gpt", _S_OAI, "none", 2.50, 10.00, "active", None, None),
    ("gpt-oss-120b", "openai/gpt-oss", _S_OAI_AGY, "none", 0.50, 1.50, "active", None, None),
    ("deepseek-chat", "deepseek/deepseek", _S_OAI, "none", 0.27, 1.10, "active", None, None),
    ("deepseek-r1", "deepseek/deepseek", _S_OAI_VTX, "budget", 0.55, 2.19, "active", None, None),
    ("meta/llama-3.3-70b-instruct-maas", "meta/llama", _S_VTX, "none", 0.30, 0.40, "active", None, None),
    ("llama3.3:70b", "meta/llama", _S_OLLAMA, "none", 0.0, 0.0, "active", None, None),
    ("offline-heuristic", "credence/heuristic", _S_LOCAL, "none", 0.0, 0.0, "active", None, None),
    # Legacy / Deprecated / Retired Models (Retained for Historical Replay)
    ("gemini-3.7-flash", "google/gemini-3.7", _S_GEM_VTX, "budget", 0.15, 0.60, _DEP, "2027-03-01", _G38),
    ("gemini-3.6-flash", "google/gemini-3.6", _S_GEM_VTX, "budget", 0.05, 0.20, _DEP, "2026-12-01", _G38),
    ("gemini-3.1-pro", "google/gemini-3.1", _S_GEM_VTX, "budget", 1.25, 5.00, _DEP, "2026-12-01", "gemini-4-neon"),
    ("gemini-2.5-flash-lite", "google/gemini-2.5", _S_GEM_VTX, "budget", 0.075, 0.30, _DEP, "2026-12-01", _G38),
    ("gemini-2.0-flash-lite", "google/gemini-2.0", _S_GEM_API, "none", 0.075, 0.30, _RET, "2026-06-01", _G38),
    ("gemini-2.0-flash", "google/gemini-2.0", _S_GEM_API, "none", 0.10, 0.40, _RET, "2026-06-01", _G38),
    ("gemini-1.5-pro", "google/gemini-1.5", _S_GEM_API, "none", 1.25, 5.00, _RET, "2025-09-24", "gemini-4-carbon"),
)


def _build_registry() -> Dict[str, ModelSpec]:
    return {
        mid: ModelSpec(
            model_id=mid,
            family=fam,
            supported_surfaces=surf,
            thinking_mode=mode,
            pricing_per_million={"prompt": p_in, "completion": p_out, "thinking": p_out},
            status=status,
            sunset_date=date.fromisoformat(sunset) if sunset else None,
            replacement_model=repl,
        )
        for mid, fam, surf, mode, p_in, p_out, status, sunset, repl in _MODEL_ROWS
    }


MODEL_REGISTRY: Dict[str, ModelSpec] = _build_registry()


def normalize_model_id(model_id: str) -> str:
    """Normalize provider/API prefixes (e.g. `google/`, `models/`) to a canonical registry key."""
    clean = model_id.strip()
    if clean in MODEL_REGISTRY:
        return clean
    lowered = clean.lower()
    if lowered in MODEL_REGISTRY:
        return lowered
    for prefix in ("models/", "google/"):
        if lowered.startswith(prefix):
            stripped = clean[len(prefix) :]
            if stripped in MODEL_REGISTRY:
                return stripped
            if stripped.lower() in MODEL_REGISTRY:
                return stripped.lower()
            return stripped
    return clean


def get_model_spec(model_id: str) -> Optional[ModelSpec]:
    """Retrieve a canonical ModelSpec by bare or prefixed model identifier."""
    normalized = normalize_model_id(model_id)
    return MODEL_REGISTRY.get(normalized) or MODEL_REGISTRY.get(normalized.lower())


def get_model_pricing_per_million() -> Dict[str, Dict[str, float]]:
    """Derive the per-million-token USD pricing table directly from MODEL_REGISTRY."""
    return {model_id: dict(spec.pricing_per_million) for model_id, spec in MODEL_REGISTRY.items()}


def compute_thinking_mode(model_name: str) -> ThinkingMode:
    """Resolve the thinking configuration mode (`level`, `budget`, or `none`) for a model."""
    spec = get_model_spec(model_name)
    if spec is not None:
        return spec.thinking_mode

    normalized = normalize_model_id(model_name).lower()
    if _GEMINI_LEVEL_RE.match(normalized):
        return "level"
    if _GEMINI_BUDGET_RE.match(normalized):
        return "budget"
    return "none"


def _audit_single_model_reference(
    *,
    subject: str,
    raw_model_id: str,
    checked_on: date,
    horizon_days: int,
    require_antigravity_harness: bool,
    pricing_table: Mapping[str, Mapping[str, float]],
    issues: List[ModelAuditIssue],
) -> None:
    def _err(code: str, model_id: str, message: str, repl: Optional[str] = None) -> None:
        issues.append(ModelAuditIssue("error", code, subject, model_id, message, repl))

    spec = get_model_spec(normalize_model_id(raw_model_id))
    if spec is None:
        _err("UNREGISTERED_MODEL", raw_model_id, f"{subject} references unregistered model '{raw_model_id}'.")
        return

    if spec.status != "active":
        rep = f" (replace with '{spec.replacement_model}')." if spec.replacement_model else "."
        _err(
            "INACTIVE_MODEL",
            spec.model_id,
            f"{subject} references {spec.status} model '{spec.model_id}'{rep}",
            spec.replacement_model,
        )

    if spec.sunset_date is not None:
        horizon_cutoff = checked_on + timedelta(days=horizon_days)
        if spec.sunset_date <= checked_on:
            _err(
                "SUNSET_EXPIRED",
                spec.model_id,
                f"{subject} references '{spec.model_id}' past sunset date {spec.sunset_date.isoformat()}.",
                spec.replacement_model,
            )
        elif spec.sunset_date <= horizon_cutoff:
            days_left = (spec.sunset_date - checked_on).days
            _err(
                "SUNSET_IMMINENT",
                spec.model_id,
                f"{subject} references '{spec.model_id}' sunsetting in {days_left} days ({spec.sunset_date.isoformat()} <= {horizon_days}-day horizon).",
                spec.replacement_model,
            )

    if require_antigravity_harness and "antigravity-harness" not in spec.supported_surfaces:
        _err(
            "HARNESS_UNALIGNED",
            spec.model_id,
            f"{subject} references '{spec.model_id}' which lacks 'antigravity-harness' surface alignment.",
            spec.replacement_model,
        )

    if spec.model_id not in pricing_table:
        _err(
            "PRICING_MISSING",
            spec.model_id,
            f"{subject} references '{spec.model_id}' missing from MODEL_PRICING_PER_MILLION.",
        )


def _discover_default_models() -> Dict[str, str]:
    from credence.cli.main import build_parser
    from credence.config import settings
    from credence.pipeline.adapters import GeminiProvider

    defaults: Dict[str, str] = {
        "Settings.DEFAULT_SPECIALIST_MODEL": settings.DEFAULT_SPECIALIST_MODEL,
        "Settings.DEFAULT_TRIAGE_MODEL": settings.DEFAULT_TRIAGE_MODEL,
        "Settings.DEFAULT_WORKER_MODEL": settings.DEFAULT_WORKER_MODEL,
    }
    gemini_default = inspect.signature(GeminiProvider.__init__).parameters["model_name"].default
    if isinstance(gemini_default, str):
        defaults["GeminiProvider.default_model"] = gemini_default

    worker_args = build_parser().parse_args(["worker"])
    if isinstance(getattr(worker_args, "model", None), str):
        defaults["CLI.worker.default_model"] = worker_args.model

    return defaults


def audit_model_catalog(
    *,
    as_of: Optional[date] = None,
    horizon_days: int = 30,
    profiles: Optional[Mapping[Any, Any]] = None,
    default_models: Optional[Mapping[str, str]] = None,
    pricing_table: Optional[Mapping[str, Mapping[str, float]]] = None,
) -> ModelCatalogAuditReport:
    """Run the offline lifecycle, sunset, pricing parity, and Antigravity-harness alignment audit."""
    from credence.config import COST_PROFILES, CostProfile
    from credence.pipeline.governor import MODEL_PRICING_PER_MILLION

    checked_on = as_of or date.today()
    active_profiles = COST_PROFILES if profiles is None else profiles
    active_defaults = _discover_default_models() if default_models is None else dict(default_models)
    active_pricing = MODEL_PRICING_PER_MILLION if pricing_table is None else pricing_table

    issues: List[ModelAuditIssue] = []
    profile_summary: Dict[str, Dict[str, str]] = {}

    for prof_key, cfg in active_profiles.items():
        prof_name = prof_key.value if hasattr(prof_key, "value") else str(prof_key)
        is_offline = prof_key == CostProfile.OFFLINE or prof_name == "offline"
        profile_summary[prof_name] = {
            "primary_model": cfg.primary_model,
            "escalation_model": cfg.escalation_model,
            "triage_model": cfg.triage_model,
        }
        for role_attr in ("primary_model", "escalation_model", "triage_model"):
            _audit_single_model_reference(
                subject=f"COST_PROFILES[{prof_name}].{role_attr}",
                raw_model_id=getattr(cfg, role_attr),
                checked_on=checked_on,
                horizon_days=horizon_days,
                require_antigravity_harness=not is_offline,
                pricing_table=active_pricing,
                issues=issues,
            )

    for label, model_id in active_defaults.items():
        _audit_single_model_reference(
            subject=label,
            raw_model_id=model_id,
            checked_on=checked_on,
            horizon_days=horizon_days,
            require_antigravity_harness=True,
            pricing_table=active_pricing,
            issues=issues,
        )

    return ModelCatalogAuditReport(
        checked_on=checked_on,
        horizon_days=horizon_days,
        issues=issues,
        active_profile_models=profile_summary,
        default_models=active_defaults,
    )


async def fetch_live_gemini_models(api_key: str, timeout: float = 15.0) -> List[str]:
    """Query the live Gemini REST API models endpoint and return normalized generative Gemini model IDs."""
    if not api_key:
        raise ValueError("A Gemini API key is required for live model catalog checks.")

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(GEMINI_MODELS_LIST_URL, headers={"x-goog-api-key": api_key})
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini models API error ({resp.status_code}): {resp.text[:200]}")
        payload = resp.json()

    discovered: List[str] = []
    for entry in payload.get("models", []):
        model_id = str(entry.get("name", "")).removeprefix("models/").strip()
        if not model_id.startswith("gemini-"):
            continue
        methods = entry.get("supportedGenerationMethods")
        if methods is not None and "generateContent" not in methods:
            continue
        discovered.append(model_id)
    return sorted(set(discovered))


def compute_live_catalog_drift(
    live_models: Iterable[str],
    profiles: Optional[Mapping[Any, Any]] = None,
) -> Tuple[List[str], List[str]]:
    """Compute newly released and missing active Gemini models relative to the live API catalog."""
    from credence.config import COST_PROFILES, CostProfile

    live_set = {normalize_model_id(m) for m in live_models}
    new_models = sorted(m for m in live_set if m not in MODEL_REGISTRY)

    active_profiles = COST_PROFILES if profiles is None else profiles
    active_gemini_ids = set()
    for prof_key, cfg in active_profiles.items():
        if prof_key == CostProfile.OFFLINE:
            continue
        for role_attr in ("primary_model", "escalation_model", "triage_model"):
            spec = get_model_spec(getattr(cfg, role_attr))
            if spec and "gemini-api" in spec.supported_surfaces:
                active_gemini_ids.add(spec.model_id)

    missing_models = sorted(m for m in active_gemini_ids if m not in live_set)
    return new_models, missing_models


__all__ = [
    "GEMINI_MODELS_LIST_URL",
    "MODEL_REGISTRY",
    "ModelAuditIssue",
    "ModelCatalogAuditReport",
    "ModelSpec",
    "VALID_STATUSES",
    "VALID_SURFACES",
    "VALID_THINKING_LEVELS",
    "VALID_THINKING_MODES",
    "audit_model_catalog",
    "compute_live_catalog_drift",
    "compute_thinking_mode",
    "fetch_live_gemini_models",
    "get_model_pricing_per_million",
    "get_model_spec",
    "normalize_model_id",
]
