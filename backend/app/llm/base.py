"""LLM provider abstraction interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    """Normalized response from an LLM invocation."""

    content: str = Field(..., description="Raw text completion")
    model_name: str = Field(..., description="Model identifier used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Token usage, finish reasons, etc.")


class LLMProvider(ABC):
    """Abstract interface decoupling Relay from specific LLM vendors."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider implementation (e.g. 'mock', 'gemini', 'openai')."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Generate a freeform text response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """Generate a response strictly validated against a Pydantic schema."""
        pass
