"""Retrieval API router providing live search and provider health endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.retrieval.mock import MockRetrievalProvider
from app.retrieval.moss import MossConfigurationError, MossRetrievalProvider, MossRuntimeError
from app.data.demo_fixtures import load_demo_knowledge_documents

router = APIRouter(prefix="/api/retrieval", tags=["Knowledge Retrieval"])

# Singleton provider instance managed across requests
_moss_provider: Optional[MossRetrievalProvider] = None
_mock_provider: Optional[MockRetrievalProvider] = None


def get_active_provider():
    """Return the active retrieval provider based on configuration."""
    global _moss_provider, _mock_provider
    if settings.is_moss_configured:
        if _moss_provider is None:
            _moss_provider = MossRetrievalProvider(config=settings)
        return _moss_provider
    else:
        if _mock_provider is None:
            _mock_provider = MockRetrievalProvider(seed_documents=load_demo_knowledge_documents())
        return _mock_provider


class SearchRequest(BaseModel):
    """Retrieval search query parameters."""

    query: str = Field(..., min_length=1, description="Natural language technician query or symptom")
    asset_id: Optional[str] = Field(None, description="Optional asset ID filter (e.g. ACX-420-017)")
    asset_model: Optional[str] = Field(None, description="Optional equipment model filter (e.g. ACX-420)")
    error_code: Optional[str] = Field(None, description="Optional error code filter (e.g. E17)")
    document_type: Optional[str] = Field(None, description="Optional document type filter")
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of chunks to return")
    alpha: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Hybrid search signal mix (1.0 = embedding only, 0.0 = keyword only)",
    )


class SearchResultItem(BaseModel):
    """Structured evidence item returned to technician reasoner."""

    id: str = Field(..., description="Document or chunk identifier")
    text: str = Field(..., description="Evidence content snippet")
    score: Optional[float] = Field(None, description="Relevance similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class SearchAPIResponse(BaseModel):
    """Observed retrieval response payload."""

    provider: str = Field(..., description="Active retrieval provider ('moss' or 'mock-retrieval')")
    status: str = Field(..., description="Provider status ('ready', 'unconfigured', 'error')")
    query: str = Field(..., description="Query executed")
    results: List[SearchResultItem] = Field(default_factory=list, description="Ranked evidence results")
    latency_ms: float = Field(..., description="Actual measured query execution latency in milliseconds")
    result_count: int = Field(..., description="Number of results returned")


class RetrievalHealthResponse(BaseModel):
    """Retrieval system health and index status without credential disclosure."""

    provider: str = Field(..., description="Provider name")
    status: str = Field(..., description="Operational status: ready, loading, unconfigured, error")
    index: str = Field(..., description="Target index name")
    configured: bool = Field(..., description="Whether credentials are provided")
    default_alpha: float = Field(..., description="Default hybrid search alpha")
    error: Optional[str] = Field(None, description="Error message if in error status")


@router.get("/health", response_model=RetrievalHealthResponse, summary="Retrieval Provider Health")
async def get_retrieval_health() -> RetrievalHealthResponse:
    """Check retrieval provider readiness and index status without exposing secrets."""
    provider = get_active_provider()
    if isinstance(provider, MossRetrievalProvider):
        status_info = provider.get_status_dict()
        return RetrievalHealthResponse(
            provider=status_info["provider"],
            status=status_info["status"],
            index=status_info["index"],
            configured=status_info["configured"],
            default_alpha=status_info["default_alpha"],
            error=status_info["error"],
        )
    else:
        return RetrievalHealthResponse(
            provider="mock-retrieval",
            status="ready",
            index="in-memory-demo",
            configured=False,
            default_alpha=0.8,
            error=None,
        )


@router.post("/search", response_model=SearchAPIResponse, summary="Execute Low-Latency Knowledge Search")
async def search_retrieval(req: SearchRequest) -> SearchAPIResponse:
    """
    Execute semantic and hybrid search over technical manuals, SOPs, and service records.
    Returns grounded evidence along with actual wall-clock / Moss-measured latency.
    """
    provider = get_active_provider()

    # Build filters dictionary from request
    filters: Dict[str, Any] = {}
    if req.asset_id:
        filters["asset_id"] = req.asset_id
    if req.asset_model:
        filters["asset_model"] = req.asset_model
    if req.error_code:
        filters["error_code"] = req.error_code
    if req.document_type:
        filters["document_type"] = req.document_type

    try:
        if isinstance(provider, MossRetrievalProvider):
            # Pass alpha if specified
            search_resp = await provider.search(
                query=req.query,
                filters=filters if filters else None,
                limit=req.top_k,
                alpha=req.alpha,
            )
            provider_status = provider.status
        else:
            search_resp = await provider.search(
                query=req.query,
                filters=filters if filters else None,
                limit=req.top_k,
            )
            provider_status = "ready"

        items = [
            SearchResultItem(
                id=res.chunk_id,
                text=res.content,
                score=res.score,
                metadata=res.metadata,
            )
            for res in search_resp.results
        ]

        return SearchAPIResponse(
            provider=search_resp.provider,
            status=provider_status,
            query=req.query,
            results=items,
            latency_ms=search_resp.latency_ms if search_resp.latency_ms is not None else 0.0,
            result_count=len(items),
        )

    except MossConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "MossNotConfigured", "message": str(e)},
        )
    except MossRuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "MossQueryError", "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "RetrievalError", "message": str(e)},
        )
