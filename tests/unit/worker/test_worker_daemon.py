"""Unit tests for the Volunteer Worker daemon and lease management."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from credence.identity import load_or_create_node_identity
from credence.pipeline.adapters import OpenAICompatibleProvider
from credence.server.app import app
from credence.worker.daemon import run_worker_daemon
from credence.worker.leases import LocalLeaseTracker, compute_backoff_delay, resolve_model_family


def test_resolve_model_family():
    """Verify standard and custom model slug resolution."""
    assert resolve_model_family("google/gemini-3.7-flash") == "google/gemini"
    assert resolve_model_family("anthropic/claude-3-7-sonnet") == "anthropic/claude"
    assert resolve_model_family("openai/gpt-4o") == "openai/gpt"
    assert resolve_model_family("meta/llama-3.3-70b") == "meta/llama"
    assert resolve_model_family("deepseek/deepseek-r1") == "deepseek/deepseek"
    assert resolve_model_family("mistral/mistral-large") == "mistral/mistral"
    assert resolve_model_family("qwen/qwen-2.5-72b") == "qwen/qwen"
    assert resolve_model_family("gemini-1.5-pro") == "google/gemini"
    assert resolve_model_family("claude-instant") == "anthropic/claude"
    assert resolve_model_family("my-custom-org/finetune-v1") == "my-custom-org/finetune"
    assert resolve_model_family("custom-model-2026") == "custom/custom"


def test_compute_backoff_delay():
    """Verify backoff scaling."""
    assert compute_backoff_delay(0) == 2.0
    assert compute_backoff_delay(1) == 3.0
    assert compute_backoff_delay(10) == 30.0  # Cap at max_delay


def test_local_lease_tracker():
    """Verify local lease tracking, expiration checks, and pruning."""
    tracker = LocalLeaseTracker(max_concurrency=2)
    assert tracker.can_claim_more() is True

    # Track 1s lease
    tracker.track_lease("l-1", "job-1", "https://example.com/1", 1)
    assert tracker.is_lease_valid("l-1") is True
    assert tracker.active_lease_count() == 1

    # Track 10s lease
    tracker.track_lease("l-2", "job-2", "https://example.com/2", 10)
    assert tracker.can_claim_more() is False

    tracker.release_lease("l-2")
    assert tracker.can_claim_more() is True


def test_openai_compatible_provider_config():
    """Verify OpenAICompatibleProvider parameter binding."""
    provider = OpenAICompatibleProvider(
        base_url="http://localhost:11434/v1",
        api_key="sk-test",
        model_name="deepseek-r1:70b",
    )
    assert provider.base_url == "http://localhost:11434/v1"
    assert provider.api_key == "sk-test"
    assert provider.model_name == "deepseek-r1:70b"
    assert provider.provider_name == "openai_compatible"


@pytest.mark.asyncio
async def test_worker_daemon_single_job_lifecycle(tmp_path: Path, monkeypatch):
    """Verify worker daemon claims, evaluates with dummy response, and submits."""
    from sqlmodel import delete

    from credence.db import get_async_session, init_db
    from credence.models import AuditJob, WorkerRecord

    await init_db()
    async with get_async_session() as session:
        await session.exec(delete(AuditJob))  # type: ignore[call-overload]
        await session.exec(delete(WorkerRecord))  # type: ignore[call-overload]
        await session.commit()

    key_file = str(tmp_path / "worker.key")
    ident = load_or_create_node_identity(key_file)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Enqueue a job
        res_enq = await client.post(
            "/api/queue/enqueue",
            json={
                "url": "https://example.com/volunteer-test",
                "normalized_text": "A standard benign news article about garden vegetables.",
                "priority": 1,
                "target_quorum": 1,
            },
        )
        assert res_enq.status_code == 200
        assert "job_id" in res_enq.json()

        # Run worker daemon for max_jobs=1
        await run_worker_daemon(
            node_url="http://test",
            model="google/gemini-3.7-flash",
            continuous=False,
            max_jobs=1,
            key_file=key_file,
            client=client,
        )

        # Verify job is no longer pending or has been submitted
        res_stats = await client.get("/api/queue/stats")
        stats = res_stats.json()
        assert stats["depth"] == 0

        # Verify worker record exists
        res_dossier = await client.get(f"/api/worker/{ident.public_key_hex}")
        assert res_dossier.status_code == 200
        data = res_dossier.json()
        assert data["total_completed"] == 1
        assert any(b.get("badge_id") == "first_bounty" for b in data["badges"])
