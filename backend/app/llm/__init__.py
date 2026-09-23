"""LLM abstraction module."""

from .base import LLMProvider, LLMResponse
from .mock import MockLLMProvider

__all__ = ["LLMProvider", "LLMResponse", "MockLLMProvider"]
