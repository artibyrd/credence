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
        assert payload["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 4096
        assert "systemInstruction" in payload


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
