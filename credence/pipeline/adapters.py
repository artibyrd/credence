"""Decoupled Multi-Model LLM Adapter Subsystem for Credence.

Provides unified interface across:
1. Google Gemini REST API (gemini-3.7-flash with thinkingConfig)
2. Anthropic Claude Messages API
3. OpenAI Chat Completions API
4. OpenAI-Compatible & DeepSeek APIs
5. Local Ollama / vLLM API
6. Google Cloud Vertex AI Model Garden (via adapters_vertex)

Governed by Invariant 7 (Multi-Model Sovereignty & Token Budget).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

from credence.config import settings
from credence.pipeline.adapters_base import BaseLLMProvider, LLMResponse, resolve_provider_key
from credence.pipeline.adapters_vertex import VertexModelGardenProvider

logger = logging.getLogger(__name__)

__all__ = [
    "BaseLLMProvider",
    "ClaudeProvider",
    "GeminiProvider",
    "LLMResponse",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "OpenAIProvider",
    "VertexModelGardenProvider",
    "get_llm_provider",
]


class GeminiProvider(BaseLLMProvider):
    """Google Gemini REST API Provider supporting 3.7 Flash thinking budgets."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.7-flash"):
        self.api_key = resolve_provider_key(
            api_key,
            "CREDENCE_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "CREDENCE_MODEL_API_KEY",
            setting_fallbacks=(
                settings.CREDENCE_GEMINI_API_KEY,
                settings.GEMINI_API_KEY,
                settings.CREDENCE_MODEL_API_KEY,
            ),
        )
        self.model_name = model_name

    def has_credentials(self) -> bool:
        return bool(self.api_key)

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 4096,
        temperature: float = 0.1,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Gemini API key is required for GeminiProvider.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
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
            resp = await client.post(url, headers=headers, json=payload)
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
        self.api_key = resolve_provider_key(
            api_key,
            "ANTHROPIC_API_KEY",
            "CREDENCE_MODEL_API_KEY",
            setting_fallbacks=(settings.ANTHROPIC_API_KEY, settings.CREDENCE_MODEL_API_KEY),
        )
        self.model_name = model_name

    def has_credentials(self) -> bool:
        return bool(self.api_key)

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

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        base_url: Optional[str] = None,
        provider_name: str = "openai",
    ):
        self.api_key = resolve_provider_key(
            api_key,
            "OPENAI_API_KEY",
            "CREDENCE_MODEL_API_KEY",
            setting_fallbacks=(settings.OPENAI_API_KEY, settings.CREDENCE_MODEL_API_KEY),
        )
        self.model_name = model_name
        effective_base = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.base_url = effective_base.rstrip("/")
        self.provider_name = provider_name

    def has_credentials(self) -> bool:
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            return True
        return bool(self.api_key and self.api_key != "none")

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        if not self.has_credentials():
            raise ValueError("OpenAI API key is required for OpenAIProvider.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key or 'none'}",
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
                raise RuntimeError(f"{self.provider_name} API error ({resp.status_code}): {resp.text[:200]}")

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
                provider_name=self.provider_name,
                model_name=self.model_name,
            )


class OpenAICompatibleProvider(OpenAIProvider):
    """Universal OpenAI-compatible API provider for custom, local, and open-weights endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "custom-model",
    ):
        target_base = (
            base_url
            or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or "http://localhost:8000/v1"
        )
        target_key = (
            resolve_provider_key(
                api_key,
                "OPENAI_COMPATIBLE_API_KEY",
                "DEEPSEEK_API_KEY",
                "OPENAI_API_KEY",
                "CREDENCE_MODEL_API_KEY",
                setting_fallbacks=(
                    settings.DEEPSEEK_API_KEY,
                    settings.OPENAI_API_KEY,
                    settings.CREDENCE_MODEL_API_KEY,
                ),
            )
            or "none"
        )
        target_model = (
            model_name if model_name != "custom-model" else (os.environ.get("OPENAI_COMPATIBLE_MODEL") or model_name)
        )
        super().__init__(
            api_key=target_key,
            model_name=target_model,
            base_url=target_base,
            provider_name="openai_compatible",
        )


class OllamaProvider(BaseLLMProvider):
    """Local Ollama / vLLM Provider for 100% offline self-hosted inference."""

    def __init__(self, base_url: Optional[str] = None, model_name: str = "llama3.3:70b"):
        resolved_base = (
            base_url
            or os.environ.get("OLLAMA_HOST")
            or os.environ.get("OLLAMA_BASE_URL")
            or settings.OLLAMA_HOST
            or settings.OLLAMA_BASE_URL
            or "http://localhost:11434"
        )
        self.base_url = resolved_base.rstrip("/")
        self.model_name = model_name if model_name != "llama3.3:70b" else (os.environ.get("OLLAMA_MODEL") or model_name)

    def has_credentials(self) -> bool:
        return bool(self.base_url)

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


def get_llm_provider(provider_override: Optional[str] = None) -> Optional[BaseLLMProvider]:
    """Resolve and return the appropriate LLM provider based on environment keys and settings."""
    target = (
        provider_override or os.environ.get("CREDENCE_LLM_PROVIDER") or settings.CREDENCE_LLM_PROVIDER or ""
    ).lower()

    if target in ("openai_compatible", "custom") or (not target and os.environ.get("OPENAI_COMPATIBLE_BASE_URL")):
        return OpenAICompatibleProvider()
    if target == "deepseek" or (not target and (settings.DEEPSEEK_API_KEY or os.environ.get("DEEPSEEK_API_KEY"))):
        return OpenAICompatibleProvider(
            base_url="https://api.deepseek.com/v1",
            api_key=resolve_provider_key(
                None,
                "DEEPSEEK_API_KEY",
                "CREDENCE_MODEL_API_KEY",
                setting_fallbacks=(settings.DEEPSEEK_API_KEY, settings.CREDENCE_MODEL_API_KEY),
            ),
            model_name=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        )
    if target == "vertex" or os.environ.get("VERTEX_BEARER_TOKEN"):
        return VertexModelGardenProvider()
    if target == "anthropic" or (not target and (settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY"))):
        return ClaudeProvider()
    if target == "openai" or (not target and (settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY"))):
        return OpenAIProvider()
    if target == "ollama" or (
        not target
        and (
            settings.OLLAMA_HOST
            or settings.OLLAMA_BASE_URL
            or os.environ.get("OLLAMA_HOST")
            or os.environ.get("OLLAMA_BASE_URL")
        )
    ):
        return OllamaProvider()

    gemini_key = resolve_provider_key(
        None,
        "CREDENCE_GEMINI_API_KEY",
        "GEMINI_API_KEY",
        "CREDENCE_MODEL_API_KEY",
        setting_fallbacks=(
            settings.CREDENCE_GEMINI_API_KEY,
            settings.GEMINI_API_KEY,
            settings.CREDENCE_MODEL_API_KEY,
        ),
    )
    if target == "gemini" or gemini_key:
        if gemini_key:
            return GeminiProvider(api_key=gemini_key)

    return None
