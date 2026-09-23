"""Base abstractions and data contracts for knowledge retrieval."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.knowledge import KnowledgeDocument


class SearchResult(BaseModel):
    """An individual chunk or document match returned by retrieval."""

    chunk_id: str = Field(..., description="Unique chunk or document identifier")
    document_id: str = Field(..., description="Parent document identifier")
    title: str = Field(..., description="Document or section title")
    content: str = Field(..., description="Retrieved textual content or chunk snippet")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Associated metadata (asset_model, error_code, safety_level, etc.)",
    )
    score: Optional[float] = Field(
        None,
        description="Relevance or similarity score if computed by the provider",
    )
    source: str = Field(..., description="Source origin (e.g. 'manual', 'procedure', 'service_history')")
    provenance_type: Optional[str] = Field(
        None,
        description="Explicit knowledge provenance category (e.g. TECHNICIAN_CONTRIBUTION, VERIFIED_COMPANY_DOCUMENT)",
    )
    verification_status: Optional[str] = Field(
        None,
        description="Verification lifecycle status (e.g. PENDING_REVIEW, VERIFIED)",
    )


class SearchResponse(BaseModel):
    """Encapsulates results and observability metrics from a retrieval call."""

    provider: str = Field(..., description="Name of the retrieval provider (e.g. 'moss', 'mock-retrieval')")
    query: str = Field(..., description="Search query string executed")
    results: List[SearchResult] = Field(default_factory=list, description="List of ranked search results")
    total_count: int = Field(0, description="Total matching chunks found")
    latency_ms: Optional[float] = Field(
        None,
        description="Actual measured wall-clock execution time in milliseconds (never synthetic or faked)",
    )


class RetrievalProvider(ABC):
    """
    Abstract interface for knowledge retrieval providers.
    Supports low-latency semantic and keyword retrieval over equipment manuals,
    SOPs, historical repairs, safety guidelines, and ingested technician contributions.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> SearchResponse:
        """
        Execute a search query over indexed technical knowledge.

        Args:
            query: Natural language or keyword query from technician/reasoner
            filters: Optional metadata filters (e.g. {'asset_model': 'ACX-420', 'error_code': 'E17'})
            limit: Maximum number of chunks to return

        Returns:
            SearchResponse containing matching chunks, metadata, and actual latency.
        """
        pass

    @abstractmethod
    async def add_document(self, doc: KnowledgeDocument) -> bool:
        """
        Ingest a normalized knowledge document into the retrieval provider index.

        Args:
            doc: Strongly-typed KnowledgeDocument containing normalized content and metadata.

        Returns:
            True if successfully indexed, False otherwise.
        """
        pass
