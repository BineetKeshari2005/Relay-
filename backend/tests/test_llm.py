"""Test LLM provider abstraction and mock implementation."""

import pytest
from pydantic import BaseModel, Field
from app.llm.base import LLMProvider, LLMResponse
from app.llm.mock import MockLLMProvider


class DiagnosticSchema(BaseModel):
    issue: str = Field(default="E17 High Pressure")
    safe: bool = Field(default=True)


@pytest.mark.asyncio
async def test_mock_llm_generate():
    provider = MockLLMProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.provider_name == "mock-llm"

    response = await provider.generate("What is error E17?")
    assert isinstance(response, LLMResponse)
    assert "E17" in response.content
    assert response.model_name == "mock-model-v1"
    assert response.metadata["mock"] is True


@pytest.mark.asyncio
async def test_mock_llm_structured():
    provider = MockLLMProvider()
    result = await provider.generate_structured(
        prompt="Analyze pressure reading",
        response_model=DiagnosticSchema,
    )
    assert isinstance(result, DiagnosticSchema)
    assert result.issue == "E17 High Pressure"
    assert result.safe is True
