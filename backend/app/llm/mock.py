"""Mock LLM provider for local deterministic testing and offline development."""

from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from app.llm.base import LLMProvider, LLMResponse

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider returning predefined or formatted responses.
    Allows testing pipelines without external API costs or latency.
    """

    def __init__(self, default_response: Optional[str] = None):
        self._default_response = default_response or (
            "ISSUE: E17 High-Pressure Protection\n"
            "LIKELY CAUSE: Potential condenser airflow restriction.\n"
            "SAFETY: Shut down compressor before inspecting.\n"
            "NEXT STEPS: Verify shutdown, inspect condenser coil, measure discharge pressure."
        )

    @property
    def provider_name(self) -> str:
        return "mock-llm"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._default_response,
            model_name="mock-model-v1",
            metadata={"mock": True},
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        # Construct an instance of response_model with default or empty fields for mock testing
        # Can be overridden or enriched per test case
        try:
            return response_model.model_validate({})
        except Exception:
            # Fallback if fields are required
            return response_model.model_construct()
