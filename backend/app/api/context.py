"""Context Assembly API router providing endpoints for case file generation."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.retrieval import get_active_provider
from app.context.assembled_context import AssembledContext
from app.context.assembler import ContextAssembler
from app.context.quality_validator import ContextQualityValidator, ContextQualityReport

router = APIRouter(prefix="/api/context", tags=["Context Assembly"])


class AssembleContextRequest(BaseModel):
    """Request payload for context assembly."""

    query: str = Field(..., min_length=1, description="Live technician utterance or issue description")
    asset_id: Optional[str] = Field(None, description="Optional explicit asset identifier (e.g. ACX-420-017)")
    session_id: Optional[str] = Field(None, description="Optional active session identifier (e.g. sess-017)")
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of evidence chunks to retrieve")


class AssembleContextResponse(BaseModel):
    """Assembled case file and quality validation outcome."""

    context: AssembledContext
    quality_report: ContextQualityReport


@router.post(
    "/assemble",
    response_model=AssembleContextResponse,
    summary="Assemble Troubleshooting Context Case File",
)
async def assemble_context_endpoint(req: AssembleContextRequest) -> AssembleContextResponse:
    """
    Assemble the complete structured case file for a technician interaction:
    1. Deterministically extracts facts from technician utterance.
    2. Resolves equipment asset and attaches structured service history.
    3. Retrieves evidence chunks via the low-latency retrieval provider.
    4. Deterministically classifies evidence and tags safety SOPs.
    5. Flags missing information and diagnostic uncertainty.
    6. Validates context quality and ensures zero premature diagnostic claims.
    """
    provider = get_active_provider()
    assembler = ContextAssembler(retrieval_provider=provider)
    validator = ContextQualityValidator()

    try:
        context = await assembler.assemble(
            query=req.query,
            asset_id=req.asset_id,
            session_id=req.session_id,
            top_k=req.top_k,
        )

        report = validator.validate(context)
        if not report.valid:
            # Context assembly produced hard validation errors
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ContextValidationError",
                    "errors": report.errors,
                    "warnings": report.warnings,
                },
            )

        return AssembleContextResponse(
            context=context,
            quality_report=report,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ContextAssemblyError", "message": str(e)},
        )
