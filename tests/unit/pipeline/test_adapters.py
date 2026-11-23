"""Hermetic unit tests for Credence multi-model pipeline adapters.

Invariant:
- Hermetic Unit Test Isolation: in-memory mocking, zero network, <35s execution.
- 500 LOC Ceiling Law: file length <= 500 LOC.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from credence.pipeline.adapters import (
    ClaudeProvider,
    GeminiProvider,
    LLMResponse,
    OllamaProvider,
    OpenAIProvider,
    VertexModelGardenProvider,
    compute_thinking_config,
    get_llm_provider,
)


@pytest.mark.unit
def test_llm_response_dataclass_initialization():
    resp = LLMResponse(
        text='{"verdict": "CLEAN"}',
        prompt_tokens=100,
        completion_tokens=20,
        thinking_tokens=50,
        provider_name="test_provider",
        model_name="test_model",
    )
    assert resp.text == '{"verdict": "CLEAN"}'
    assert resp.prompt_tokens == 100
    assert resp.completion_tokens == 20
    assert resp.thinking_tokens == 50
    assert resp.provider_name == "test_provider"
    assert resp.model_name == "test_model"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gemini_provider_generate_success():
    provider = GeminiProvider(api_key="fake-gemini-key", model_name="gemini-3.7-flash")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"result": "success"}'}]}}],
        "usageMetadata": {
            "promptTokenCount": 150,
            "candidatesTokenCount": 35,
            "thoughtsTokenCount": 40,
        },
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate(
            prompt="Analyze this article text",
            system_instruction="You are a strict journalism auditor.",
            thinking_budget=4096,
        )

        assert res.text == '{"result": "success"}'
        assert res.prompt_tokens == 150
        assert res.completion_tokens == 35
        assert res.thinking_tokens == 40
        assert res.provider_name == "gemini"
        assert res.model_name == "gemini-3.7-flash"

        # Verify thinkingConfig and systemInstruction in request payload
        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 4096}
        assert "thinkingLevel" not in payload["generationConfig"]["thinkingConfig"]
        assert "systemInstruction" in payload


@pytest.mark.unit
def test_gemini_provider_defaults_to_gemini_3_8_flash():
    provider = GeminiProvider(api_key="fake-gemini-key")
    assert provider.model_name == "gemini-3.8-flash"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("model_name", "thinking_budget", "thinking_level", "expected"),
    [
        # Gemini 3.8 & Gemini 4 deterministic integer-budget -> thinkingLevel mapping
        ("gemini-3.8-flash", 0, None, {"thinkingLevel": "minimal"}),
        ("gemini-3.8-flash", 512, None, {"thinkingLevel": "low"}),
        ("gemini-3.8-flash", 1024, None, {"thinkingLevel": "low"}),
        ("gemini-3.8-flash", 1025, None, {"thinkingLevel": "medium"}),
        ("gemini-3.8-flash", 4096, None, {"thinkingLevel": "medium"}),
        ("gemini-3.8-flash", 4097, None, {"thinkingLevel": "high"}),
        ("gemini-3.8-flash", 16384, None, {"thinkingLevel": "high"}),
        # Explicit thinking_level overrides budget and strictly excludes thinkingBudget
        ("gemini-4-hydrogen", 4096, "low", {"thinkingLevel": "low"}),
        ("gemini-4-argon", None, "medium", {"thinkingLevel": "medium"}),
        ("gemini-4-neon", None, None, {"thinkingLevel": "medium"}),
        ("gemini-4-carbon", 512, "HIGH", {"thinkingLevel": "high"}),
        # Legacy Gemini 2.5 / 3.7 budget mode preserved when no thinking_level is set
        ("gemini-3.7-flash", 4096, None, {"thinkingBudget": 4096}),
        ("gemini-2.5-flash-lite", 512, None, {"thinkingBudget": 512}),
        ("gemini-3.7-flash", 0, None, None),
        ("gemini-3.7-flash", None, None, None),
        # Budget-only models map explicit thinking_level back to thinkingBudget (never emit thinkingLevel)
        ("gemini-3.7-flash", 4096, "low", {"thinkingBudget": 1024}),
        ("gemini-3.5-flash-lite", None, "minimal", None),
        ("gemini-3.5-flash-lite", None, "low", {"thinkingBudget": 1024}),
        ("gemini-3.5-flash-lite", None, "medium", {"thinkingBudget": 4096}),
        ("gemini-2.5-flash-lite", None, "high", {"thinkingBudget": 8192}),
        # Non-thinking legacy models emit no thinkingConfig
        ("gemini-2.0-flash-lite", 4096, None, None),
        ("gemini-1.5-pro", 4096, "high", None),
    ],
)
def test_compute_thinking_config_contract(model_name, thinking_budget, thinking_level, expected):
    cfg = compute_thinking_config(model_name, thinking_budget=thinking_budget, thinking_level=thinking_level)
    assert cfg == expected
    if cfg is not None:
        assert not ("thinkingLevel" in cfg and "thinkingBudget" in cfg)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_evaluator_passes_profile_thinking_levels_to_level_and_budget_models():
    """Verify evaluate_snapshot forwards profile triage/default thinking_level cleanly for both level and budget models."""
    from credence.config import COST_PROFILES, CostProfile
    from credence.ingestion.extractor import ExtractedContent
    from credence.ingestion.hasher import compute_content_sha256, compute_simhash
    from credence.ingestion.snapshot import DualCaptureResult
    from credence.pipeline.evaluator import evaluate_snapshot

    text = "City officials announced a routine water main inspection on Tuesday morning."
    snapshot = DualCaptureResult(
        url="https://example.org/civic-notice",
        content_sha256=compute_content_sha256(text),
        simhash_64=compute_simhash(text),
        raw_html=f"<html><body><p>{text}</p></body></html>",
        extracted=ExtractedContent(
            url="https://example.org/civic-notice",
            title="Civic Notice",
            byline="Staff",
            clean_text=text,
            word_count=len(text.split()),
        ),
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"is_satire": false, "violations": []}'}]}}],
        "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 10, "thoughtsTokenCount": 5},
    }

    # 1. Gemini 4 level model under ULTRA (triage='low', default='high')
    ultra_provider = GeminiProvider(api_key="fake-key", model_name="gemini-4-neon")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        await evaluate_snapshot(
            snapshot,
            sign_result=False,
            profile_override=COST_PROFILES[CostProfile.ULTRA],
            provider=ultra_provider,
        )
        assert mock_post.await_count >= 2
        payloads = [c.kwargs["json"]["generationConfig"]["thinkingConfig"] for c in mock_post.call_args_list]
        assert payloads[0] == {"thinkingLevel": "low"}
        assert all(p == {"thinkingLevel": "high"} for p in payloads[1:])
        assert all("thinkingBudget" not in p for p in payloads)

    # 2. Budget-only model under BALANCED (triage='minimal' -> omitted, default='medium' -> thinkingBudget: 4096)
    budget_provider = GeminiProvider(api_key="fake-key", model_name="gemini-3.5-flash-lite")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        await evaluate_snapshot(
            snapshot,
            sign_result=False,
            profile_override=COST_PROFILES[CostProfile.BALANCED],
            provider=budget_provider,
        )
        assert mock_post.await_count >= 2
        gen_configs = [c.kwargs["json"]["generationConfig"] for c in mock_post.call_args_list]
        assert "thinkingConfig" not in gen_configs[0]
        assert all(gc["thinkingConfig"] == {"thinkingBudget": 4096} for gc in gen_configs[1:])
        assert all("thinkingLevel" not in gc.get("thinkingConfig", {}) for gc in gen_configs)


@pytest.mark.unit
def test_compute_thinking_config_validation_errors():
    with pytest.raises(ValueError, match="thinking_budget must be >= 0"):
        compute_thinking_config("gemini-3.8-flash", thinking_budget=-1)
    with pytest.raises(ValueError, match="Unsupported thinking_level"):
        compute_thinking_config("gemini-4-neon", thinking_level="extreme")


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_name", "thinking_level", "thinking_budget", "expected_level"),
    [
        ("gemini-3.8-flash", "minimal", None, "minimal"),
        ("gemini-3.8-flash", None, 1024, "low"),
        ("gemini-4-hydrogen", "low", 4096, "low"),
        ("gemini-4-argon", "medium", None, "medium"),
        ("gemini-4-neon", "high", None, "high"),
        ("gemini-4-carbon", None, 8192, "high"),
    ],
)
async def test_gemini_provider_modern_models_emit_only_thinking_level(
    model_name, thinking_level, thinking_budget, expected_level
):
    provider = GeminiProvider(api_key="fake-gemini-key", model_name=model_name)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"violations": []}'}]}}],
        "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 15},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        res = await provider.generate(
            prompt="Audit this article",
            thinking_budget=thinking_budget,
            thinking_level=thinking_level,
        )
        assert res.model_name == model_name
        _, kwargs = mock_post.call_args
        thinking_cfg = kwargs["json"]["generationConfig"]["thinkingConfig"]
        assert thinking_cfg == {"thinkingLevel": expected_level}
        assert "thinkingBudget" not in thinking_cfg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gemini_provider_legacy_25_flash_lite_emits_thinking_budget():
    provider = GeminiProvider(api_key="fake-gemini-key", model_name="gemini-2.5-flash-lite")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"violations": []}'}]}}],
        "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 10},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        await provider.generate(prompt="Replay legacy audit", thinking_budget=512)
        _, kwargs = mock_post.call_args
        thinking_cfg = kwargs["json"]["generationConfig"]["thinkingConfig"]
        assert thinking_cfg == {"thinkingBudget": 512}
        assert "thinkingLevel" not in thinking_cfg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gemini_provider_missing_key_error():
    provider = GeminiProvider(api_key="", model_name="gemini-3.7-flash")
    provider.api_key = ""
    with pytest.raises(ValueError, match="Gemini API key is required"):
        await provider.generate("test prompt")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_claude_provider_generate_success():
    provider = ClaudeProvider(api_key="fake-anthropic-key", model_name="claude-3-7-sonnet-20250219")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"type": "text", "text": '{"violations": []}'}],
        "usage": {"input_tokens": 200, "output_tokens": 45},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate(
            prompt="Audit text",
            system_instruction="Journalism ethics system prompt",
        )

        assert res.text == '{"violations": []}'
        assert res.prompt_tokens == 200
        assert res.completion_tokens == 45
        assert res.provider_name == "anthropic"

        _, kwargs = mock_post.call_args
        headers = kwargs["headers"]
        assert headers["x-api-key"] == "fake-anthropic-key"
        assert headers["anthropic-version"] == "2023-06-01"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_claude_provider_missing_key_error():
    provider = ClaudeProvider(api_key="")
    with pytest.raises(ValueError, match="Anthropic API key is required"):
        await provider.generate("test prompt")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_openai_provider_generate_success():
    provider = OpenAIProvider(api_key="fake-openai-key", model_name="gpt-4o")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"score": 10.5}'}}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 25},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate(prompt="Check this text")

        assert res.text == '{"score": 10.5}'
        assert res.prompt_tokens == 120
        assert res.completion_tokens == 25
        assert res.provider_name == "openai"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ollama_provider_generate_success():
    provider = OllamaProvider(base_url="http://localhost:11434", model_name="llama3.3:70b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": '{"classification": "CLEAN"}',
        "prompt_eval_count": 85,
        "eval_count": 15,
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate(prompt="Local prompt")

        assert res.text == '{"classification": "CLEAN"}'
        assert res.prompt_tokens == 85
        assert res.completion_tokens == 15
        assert res.provider_name == "ollama"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_vertex_model_garden_provider_success():
    provider = VertexModelGardenProvider(
        project_id="credence-dev-test",
        location="us-central1",
        model_name="meta/llama-3.3-70b-instruct-maas",
        access_token="fake-oauth2-bearer-token",
        max_output_tokens=1024,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"model_garden": "verified"}'}}],
        "usage": {"prompt_tokens": 300, "completion_tokens": 60},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate(prompt="Test prompt on Vertex")

        assert res.text == '{"model_garden": "verified"}'
        assert res.prompt_tokens == 300
        assert res.completion_tokens == 60
        assert res.provider_name == "vertex_model_garden"

        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer fake-oauth2-bearer-token"
        assert kwargs["json"]["max_tokens"] == 1024


@pytest.mark.unit
@pytest.mark.asyncio
async def test_vertex_model_garden_provider_missing_token_error():
    provider = VertexModelGardenProvider(access_token="")
    with patch.object(provider, "_get_bearer_token", return_value=""):
        with pytest.raises(ValueError, match="GCP OAuth2 Bearer token is required"):
            await provider.generate("test prompt")


@pytest.mark.unit
def test_get_llm_provider_resolution():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
        p = get_llm_provider("anthropic")
        assert isinstance(p, ClaudeProvider)

    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
        p = get_llm_provider("openai")
        assert isinstance(p, OpenAIProvider)

    with patch.dict("os.environ", {"VERTEX_BEARER_TOKEN": "test-token"}, clear=True):
        p = get_llm_provider("vertex")
        assert isinstance(p, VertexModelGardenProvider)

    with patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://test:11434"}, clear=True):
        p = get_llm_provider("ollama")
        assert isinstance(p, OllamaProvider)
