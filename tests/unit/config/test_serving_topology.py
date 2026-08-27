"""Unit tests for production serving topology and environment defaults.

Governed by: inv-hermetic-unit-tests, inv-sovereign-config-decoupling
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from credence.config import ExhaustionStrategy, NodeRole, Settings


@pytest.mark.unit
def test_production_environment_defaults_to_serving_mode() -> None:
    """Verify that production environments default strictly to SERVING role and SERVING_MODE strategy."""
    with patch.dict(os.environ, {"ENV": "production", "GOOGLE_CLOUD_PROJECT": "credence-prod-505902"}, clear=False):
        # Remove any explicit role overrides
        os.environ.pop("CREDENCE_NODE_ROLE", None)
        os.environ.pop("CREDENCE_EXHAUSTION_STRATEGY", None)
        os.environ.pop("CREDENCE_SENTINEL_ENABLED", None)

        prod_settings = Settings(ENV="production")
        assert prod_settings.CREDENCE_NODE_ROLE == NodeRole.SERVING
        assert prod_settings.CREDENCE_EXHAUSTION_STRATEGY == ExhaustionStrategy.SERVING_MODE
        assert prod_settings.CREDENCE_SENTINEL_ENABLED is False


@pytest.mark.unit
def test_development_environment_enables_hybrid_and_sentinel() -> None:
    """Verify that development environments default to HYBRID role, HEURISTIC_FALLBACK, and active sentinels."""
    with patch.dict(os.environ, {"ENV": "development", "GOOGLE_CLOUD_PROJECT": "credence-dev-495173"}, clear=False):
        os.environ.pop("CREDENCE_NODE_ROLE", None)
        os.environ.pop("CREDENCE_EXHAUSTION_STRATEGY", None)
        os.environ.pop("CREDENCE_SENTINEL_ENABLED", None)

        dev_settings = Settings(ENV="development")
        assert dev_settings.CREDENCE_NODE_ROLE == NodeRole.HYBRID
        assert dev_settings.CREDENCE_EXHAUSTION_STRATEGY == ExhaustionStrategy.HEURISTIC_FALLBACK
        assert dev_settings.CREDENCE_SENTINEL_ENABLED is True


@pytest.mark.unit
def test_explicit_env_var_overrides_take_precedence() -> None:
    """Verify that explicit environment variable overrides take absolute precedence over environment defaults."""
    with patch.dict(
        os.environ,
        {
            "ENV": "production",
            "CREDENCE_NODE_ROLE": "evaluator",
            "CREDENCE_EXHAUSTION_STRATEGY": "defer",
            "CREDENCE_SENTINEL_ENABLED": "true",
        },
        clear=False,
    ):
        custom_settings = Settings(ENV="production")
        assert custom_settings.CREDENCE_NODE_ROLE == NodeRole.EVALUATOR
        assert custom_settings.CREDENCE_EXHAUSTION_STRATEGY == ExhaustionStrategy.DEFER
        assert custom_settings.CREDENCE_SENTINEL_ENABLED is True
