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


def get_llm_provider(provider_override: Optional[str] = None) -> Optional[BaseLLMProvider]:
    """Resolve and return the appropriate LLM provider based on environment keys and settings."""
    target = provider_override or os.environ.get("CREDENCE_LLM_PROVIDER")

    if target == "anthropic" or (not target and os.environ.get("ANTHROPIC_API_KEY")):
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
