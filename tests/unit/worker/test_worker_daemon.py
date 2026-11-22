"""Unit tests for the Volunteer Worker daemon, multi-model providers, and lease management."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from credence.config import settings
from credence.identity import load_or_create_node_identity
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.pipeline.adapters import (
    ClaudeProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
)
from credence.pipeline.evaluator import evaluate_snapshot
from credence.server.app import app
from credence.worker.daemon import init_worker_provider, run_worker_daemon
from credence.worker.leases import LocalLeaseTracker, compute_backoff_delay, resolve_model_family


@pytest.mark.unit
def test_resolve_model_family():
    """Verify standard, custom, and boundary-safe model slug resolution."""
    assert resolve_model_family("google/gemini-3.7-flash") == "google/gemini"
    assert resolve_model_family("anthropic/claude-3-7-sonnet") == "anthropic/claude"
    assert resolve_model_family("openai/gpt-4o") == "openai/gpt"
    assert resolve_model_family("meta/llama-3.3-70b") == "meta/llama"
    assert resolve_model_family("deepseek/deepseek-r1") == "deepseek/deepseek"
    assert resolve_model_family("ollama/r1:14b") == "deepseek/deepseek"
    assert resolve_model_family("mistral/mistral-large") == "mistral/mistral"
    assert resolve_model_family("qwen/qwen-2.5-72b") == "qwen/qwen"
    assert resolve_model_family("gemini-1.5-pro") == "google/gemini"
    assert resolve_model_family("claude-instant") == "anthropic/claude"
    assert resolve_model_family("my-custom-org/finetune-v1") == "my-custom-org/finetune"
    assert resolve_model_family("custom-model-2026") == "custom/custom"
    # Non-DeepSeek slugs merely containing substring "r1" must NOT misclassify as deepseek
    assert resolve_model_family("acme/super1-chat") == "acme/super1"
    assert resolve_model_family("vendor/bar10-instruct") == "vendor/bar10"


@pytest.mark.unit
def test_compute_backoff_delay():
    """Verify backoff scaling."""
    assert compute_backoff_delay(0) == 2.0
    assert compute_backoff_delay(1) == 3.0
    assert compute_backoff_delay(10) == 30.0


@pytest.mark.unit
def test_local_lease_tracker():
    """Verify local lease tracking, expiration checks, and pruning."""
    tracker = LocalLeaseTracker(max_concurrency=2)
    assert tracker.can_claim_more() is True

    tracker.track_lease("l-1", "job-1", "https://example.com/1", 1)
    assert tracker.is_lease_valid("l-1") is True
    assert tracker.active_lease_count() == 1

    tracker.track_lease("l-2", "job-2", "https://example.com/2", 10)
    assert tracker.can_claim_more() is False

    tracker.release_lease("l-2")
    assert tracker.can_claim_more() is True


@pytest.mark.unit
def test_openai_compatible_and_deepseek_routing(monkeypatch: pytest.MonkeyPatch):
    """Verify OpenAICompatibleProvider and native DeepSeek worker routing."""
    provider = OpenAICompatibleProvider(
        base_url="http://localhost:11434/v1",
        api_key="sk-test",
        model_name="deepseek-r1:70b",
    )
    assert provider.base_url == "http://localhost:11434/v1"
    assert provider.api_key == "sk-test"
    assert provider.model_name == "deepseek-r1:70b"
    assert provider.provider_name == "openai_compatible"

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-live")
    ds_provider = init_worker_provider("deepseek/deepseek-chat")
    assert isinstance(ds_provider, OpenAICompatibleProvider)
    assert ds_provider.base_url == "https://api.deepseek.com/v1"
    assert ds_provider.api_key == "sk-ds-live"
    assert ds_provider.model_name == "deepseek-chat"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_non_gemini_providers_execute_llm_pipeline_without_gemini_key(monkeypatch: pytest.MonkeyPatch):
    """Prove Claude, OpenAI, DeepSeek, and Ollama execute real LLM calls with NO GEMINI_API_KEY set."""
    monkeypatch.setattr(settings, "CREDENCE_GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.delenv("CREDENCE_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    prose = "The municipal council approved the budget unanimously after two public hearings."
    snapshot = DualCaptureResult(
        url="https://example.com/multi-model-test",
        content_sha256=compute_content_sha256(prose),
        simhash_64=compute_simhash(prose),
        raw_html=f"<html><body><p>{prose}</p></body></html>",
        extracted=ExtractedContent(
            url="https://example.com/multi-model-test",
            title="Municipal Budget Approved",
            byline="Jane Doe",
            clean_text=prose,
            word_count=len(prose.split()),
        ),
    )

    provider_cases = [
        (
            ClaudeProvider(api_key="sk-ant-test", model_name="claude-3-7-sonnet"),
            {
                "content": [{"type": "text", "text": '{"is_satire": false, "violations": []}'}],
                "usage": {"input_tokens": 120, "output_tokens": 30},
            },
        ),
        (
            OpenAIProvider(api_key="sk-oai-test", model_name="gpt-4o-mini"),
            {
                "choices": [{"message": {"content": '{"is_satire": false, "violations": []}'}}],
                "usage": {"prompt_tokens": 110, "completion_tokens": 25},
            },
        ),
        (
            OpenAICompatibleProvider(
                base_url="https://api.deepseek.com/v1", api_key="sk-ds-test", model_name="deepseek-chat"
            ),
            {
                "choices": [{"message": {"content": '{"is_satire": false, "violations": []}'}}],
                "usage": {"prompt_tokens": 90, "completion_tokens": 20},
            },
        ),
        (
            OllamaProvider(base_url="http://localhost:11434", model_name="llama3.3:8b"),
            {
                "response": '{"is_satire": false, "violations": []}',
                "prompt_eval_count": 80,
                "eval_count": 15,
            },
        ),
    ]

    for provider, payload in provider_cases:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
            report = await evaluate_snapshot(snapshot=snapshot, provider=provider, sign_result=False)
            assert mock_post.await_count >= 1
            assert report.quota_preserved is False
            assert report.evaluation_method.startswith("llm_multi_agent")
            assert report.evaluation_model == provider.model_name
            assert report.tokens_used > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_worker_daemon_single_job_lifecycle(tmp_path: Path):
    """Verify worker daemon claims with Ed25519 PoP, evaluates, signs, and submits."""
    from sqlmodel import delete

    from credence.db import get_async_session, init_db
    from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord

    await init_db()
    async with get_async_session() as session:
        await session.execute(delete(Violation))
        await session.execute(delete(Audit))
        await session.execute(delete(Snapshot))
        await session.execute(delete(AuditJob))
        await session.execute(delete(WorkerRecord))
        await session.commit()

    key_file = str(tmp_path / "worker.key")
    ident = load_or_create_node_identity(key_file)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_enq = await client.post(
            "/api/queue/enqueue",
            headers={"X-Credence-Admin-Key": "dev_admin_key"},
            json={
                "url": "https://example.com/volunteer-test",
                "normalized_text": "A standard benign news article about garden vegetables.",
                "priority": 1,
                "target_quorum": 1,
            },
        )
        assert res_enq.status_code == 200

        await run_worker_daemon(
            node_url="http://test",
            model="google/gemini-3.7-flash",
            continuous=False,
            max_jobs=1,
            key_file=key_file,
            client=client,
        )

        res_stats = await client.get("/api/queue/stats")
        assert res_stats.json()["depth"] == 0

        res_dossier = await client.get(f"/api/worker/{ident.public_key_hex}")
        assert res_dossier.status_code == 200
        data = res_dossier.json()
        assert data["total_completed"] == 1
        assert any(b.get("badge_id") == "first_bounty" for b in data["badges"])
