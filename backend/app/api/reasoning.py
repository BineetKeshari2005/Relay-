"""Reasoning API router providing diagnostic analysis endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.retrieval import get_active_provider
from app.config.settings import settings
from app.context.assembled_context import AssembledContext
from app.context.assembler import ContextAssembler
from app.llm.base import LLMProvider
from app.llm.mock import MockLLMProvider
from app.reasoning import (
    LLMReasoningProvider,
    MockReasoningProvider,
    ReasoningProvider,
    ReasoningResult,
    ReasoningService,
    ReasoningValidationReport,
)

router = APIRouter(prefix="/api/reasoning", tags=["Diagnostic Reasoning"])


def get_active_reasoning_provider() -> ReasoningProvider:
    """Instantiate active reasoning provider based on application settings."""
    if settings.llm_provider == "mock":
        return MockReasoningProvider()
    else:
        # LLM backed provider with decoupled abstraction
        llm: LLMProvider = MockLLMProvider()
        return LLMReasoningProvider(llm_provider=llm)


class AnalyzeRequest(BaseModel):
    """Request payload for evidence-grounded technician diagnostic analysis."""

    query: str = Field(..., min_length=1, description="Technician spoken or typed inquiry")
    session_id: Optional[str] = Field(None, description="Optional active session identifier (e.g. sess-017)")
    asset_id: Optional[str] = Field(None, description="Optional explicit equipment asset ID (e.g. ACX-420-017)")
    top_k: int = Field(5, ge=1, le=20, description="Number of knowledge chunks to retrieve")


class AnalyzeResponse(BaseModel):
    """Unified response containing assembled context, reasoning result, and validation audit."""

    context: AssembledContext
    reasoning: ReasoningResult
    validation_report: ReasoningValidationReport


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze Technician Query with Grounded Reasoning",
)
async def analyze_endpoint(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    Execute complete end-to-end decision-support analysis:
    1. Retrieves relevant manuals, service records, and SOPs through decoupled RetrievalProvider.
    2. Assembles strongly typed case file with ContextAssembler.
    3. Executes evidence-grounded reasoning over AssembledContext.
    4. Validates all evidence claims, citations, and safety constraints.
    5. Returns structured diagnostic recommendations with dynamic clarifying questions.
    """
    try:
        # 1. Retrieval & Context Assembly
        retrieval_provider = get_active_provider()
        assembler = ContextAssembler(retrieval_provider=retrieval_provider)
        context = await assembler.assemble(
            query=req.query,
            asset_id=req.asset_id,
            session_id=req.session_id,
            top_k=req.top_k,
        )

        # 2. Reasoning Execution & Quality Validation
        reasoning_provider = get_active_reasoning_provider()
        service = ReasoningService(provider=reasoning_provider)
        reasoning_result, report = await service.analyze(context)

        return AnalyzeResponse(
            context=context,
            reasoning=reasoning_result,
            validation_report=report,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ReasoningAnalysisError", "message": str(e)},
        )
