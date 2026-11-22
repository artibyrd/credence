"""Shared base interfaces and credential helpers for Credence multi-model LLM adapters."""

from __future__ import annotations

import abc
import os
from dataclasses import dataclass
from typing import Optional


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

    def has_credentials(self) -> bool:
        """Return True if this provider has active credentials or a local endpoint."""
        return True

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


def resolve_provider_key(
    explicit: Optional[str],
    *env_names: str,
    setting_fallbacks: tuple[Optional[str], ...] = (),
) -> str:
    """Resolve an API key from explicit arg, Settings fallbacks, or environment variables."""
    if explicit is not None:
        return explicit
    for val in setting_fallbacks:
        if val:
            return val
    for name in env_names:
        env_val = os.environ.get(name)
        if env_val:
            return env_val
    return ""
