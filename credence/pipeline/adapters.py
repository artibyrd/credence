"""Decoupled Multi-Model LLM Adapter Subsystem for Credence.

Provides unified interface across:
1. Google Gemini REST API (gemini-3.7-flash with thinkingConfig)
2. Anthropic Claude Messages API
3. OpenAI Chat Completions API
4. Local Ollama / vLLM API
5. Deterministic Offline Heuristic Provider

Governed by Invariant 7 (Multi-Model Sovereignty & Token Budget).
"""

from __future__ import annotations

import abc
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from credence.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response container from any LLM provider."""

    text: str
    prompt_tokens: int
    completion_tokens: int
    thinking_tokens: int = 0
    provider_name: str = "unknown"
    model_name: str = "unknown"


class BaseLLMProvider(abc.ABC):
    """Abstract base class for LLM inference providers."""

    model_name: str = "unknown"

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Generate content from LLM provider."""
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini REST API Provider supporting 3.7 Flash thinking budgets."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.7-flash"):
        self.api_key = (
            api_key
            or settings.CREDENCE_GEMINI_API_KEY
            or settings.GEMINI_API_KEY
            or os.environ.get("GEMINI_API_KEY", "")
        )
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 4096,
        temperature: float = 0.1,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Gemini API key is required for GeminiProvider.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        gen_config: Dict[str, Any] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }
        if thinking_budget > 0:
            gen_config["thinkingConfig"] = {"thinkingBudget": thinking_budget}

        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_config,
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text[:200]}")

            data = resp.json()
            candidates = data.get("candidates", [])
            text = ""
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                text = "".join(p.get("text", "") for p in parts)

            usage = data.get("usageMetadata", {})
            in_tok = usage.get("promptTokenCount", len(prompt) // 4)
            out_tok = usage.get("candidatesTokenCount", len(text) // 4)
            think_tok = usage.get("thoughtsTokenCount", 0)

            return LLMResponse(
                text=text,
                prompt_tokens=in_tok,
                completion_tokens=out_tok,
                thinking_tokens=think_tok,
                provider_name="gemini",
                model_name=self.model_name,
            )


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude Messages API Provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-3-7-sonnet-20250219"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key is required for ClaudeProvider.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            payload["system"] = system_instruction

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Claude API error ({resp.status_code}): {resp.text[:200]}")

            data = resp.json()
            content = data.get("content", [])
            text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
            usage = data.get("usage", {})
            in_tok = usage.get("input_tokens", len(prompt) // 4)
            out_tok = usage.get("output_tokens", len(text) // 4)

            return LLMResponse(
                text=text,
                prompt_tokens=in_tok,
                completion_tokens=out_tok,
                thinking_tokens=0,
                provider_name="anthropic",
                model_name=self.model_name,
            )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Chat Completions API Provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is required for OpenAIProvider.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text[:200]}")

            data = resp.json()
            choices = data.get("choices", [])
            text = choices[0]["message"]["content"] if choices else ""
            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", len(prompt) // 4)
            out_tok = usage.get("completion_tokens", len(text) // 4)

            return LLMResponse(
                text=text,
                prompt_tokens=in_tok,
                completion_tokens=out_tok,
                thinking_tokens=0,
                provider_name="openai",
                model_name=self.model_name,
            )


class OllamaProvider(BaseLLMProvider):
    """Local Ollama / vLLM Provider for 100% offline self-hosted inference."""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.3:70b"):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url).rstrip("/")
        self.model_name = os.environ.get("OLLAMA_MODEL", model_name)

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system_instruction:
            payload["system"] = system_instruction

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama error ({resp.status_code}): {resp.text[:200]}")

            data = resp.json()
            text = data.get("response", "")
            in_tok = data.get("prompt_eval_count", len(prompt) // 4)
            out_tok = data.get("eval_count", len(text) // 4)

            return LLMResponse(
                text=text,
                prompt_tokens=in_tok,
                completion_tokens=out_tok,
                thinking_tokens=0,
                provider_name="ollama",
                model_name=self.model_name,
            )


class VertexModelGardenProvider(BaseLLMProvider):
    """Google Cloud Vertex AI Model Garden Provider (Model-as-a-Service / MaaS).

    Supports:
    - Meta Llama 3.3 70B Instruct
    - DeepSeek-R1
    - Mistral Large 2
    - Alibaba Qwen 2.5 72B
    - Google Gemma 2 27B
    - AI21 Jamba 1.5 Mini

    Uses GCP Project ID and OAuth2 Bearer token (via gcloud or google-auth).
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "meta/llama-3.3-70b-instruct-maas",
        access_token: Optional[str] = None,
        max_output_tokens: int = 1024,
    ):
        self.project_id = (
            project_id
            or os.environ.get("CLOUDSDK_CORE_PROJECT")
            or os.environ.get("GCP_PROJECT_ID")
            or "credence-dev-495173"
        )
        self.location = location or os.environ.get("CLOUDSDK_COMPUTE_REGION") or "us-central1"
        self.model_name = model_name
        self.access_token = access_token or os.environ.get("VERTEX_BEARER_TOKEN") or ""
        self.max_output_tokens = max_output_tokens

    def _get_bearer_token(self) -> str:
        if self.access_token:
            return self.access_token
        try:
            import google.auth
            from google.auth.transport.requests import Request

            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            credentials.refresh(Request())
            if credentials.token:
                return str(credentials.token)
        except Exception:
            pass

        import shutil
        import subprocess

        gcloud_bin = shutil.which("gcloud")
        if gcloud_bin:
            try:
                res = subprocess.run(  # noqa: S603
                    [gcloud_bin, "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0:
                    token = res.stdout.strip()
                    if token:
                        return token
            except Exception:
                pass
        return ""

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        token = self._get_bearer_token()
        if not token:
            raise ValueError(
                "GCP OAuth2 Bearer token is required for VertexModelGardenProvider. Run 'gcloud auth login' or set VERTEX_BEARER_TOKEN."
            )

        url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/{self.model_name}:rawPredict"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "max_tokens": self.max_output_tokens,
            "temperature": temperature,
        }
        if system_instruction:
            payload["system"] = system_instruction

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Vertex Model Garden API error ({resp.status_code}): {resp.text[:200]}")
            data = resp.json()
            text = ""
            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0].get("message", {}).get("content", "") or data["choices"][0].get("text", "")
            elif "output" in data:
                text = data["output"]
            elif "text" in data:
                text = data["text"]
            else:
                text = str(data)

            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", len(prompt) // 4)
            out_tok = usage.get("completion_tokens", len(text) // 4)
            return LLMResponse(
                text=text,
                prompt_tokens=in_tok,
                completion_tokens=out_tok,
                thinking_tokens=thinking_budget if "r1" in self.model_name else 0,
                provider_name="vertex_model_garden",
                model_name=self.model_name,
            )


def get_llm_provider(provider_override: Optional[str] = None) -> Optional[BaseLLMProvider]:
    """Resolve and return the appropriate LLM provider based on environment keys and settings."""
    target = provider_override or os.environ.get("CREDENCE_LLM_PROVIDER")

    if target == "vertex" or os.environ.get("VERTEX_BEARER_TOKEN"):
        return VertexModelGardenProvider()
    elif target == "anthropic" or (not target and os.environ.get("ANTHROPIC_API_KEY")):
        return ClaudeProvider()
    elif target == "openai" or (not target and os.environ.get("OPENAI_API_KEY")):
        return OpenAIProvider()
    elif target == "ollama" or (not target and os.environ.get("OLLAMA_BASE_URL")):
        return OllamaProvider()
    elif (
        target == "gemini"
        or settings.CREDENCE_GEMINI_API_KEY
        or settings.GEMINI_API_KEY
        or os.environ.get("GEMINI_API_KEY")
    ):
        api_key = settings.CREDENCE_GEMINI_API_KEY or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if api_key:
            return GeminiProvider(api_key=api_key)

    return None
