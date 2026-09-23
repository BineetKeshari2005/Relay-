"""Mock retrieval provider for local development, CI, and testing."""

import time
from typing import Any, Dict, List, Optional

from app.models.knowledge import KnowledgeDocument
from app.retrieval.base import RetrievalProvider, SearchResponse, SearchResult

STOP_WORDS = {
    "a", "about", "after", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during", "each",
    "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
    "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more",
    "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
}


class MockRetrievalProvider(RetrievalProvider):
    """
    In-memory mock retrieval provider for local testing and offline development.

    CRITICAL NOTE:
    - This provider is explicitly identified as 'mock-retrieval'.
    - It does NOT pretend to be Moss.
    - It measures actual execution time of its in-memory scan (does not synthesize fake latencies).
    - Supports dynamic ingestion of technician contributions.
    """

    def __init__(self, seed_documents: Optional[List[KnowledgeDocument]] = None):
        self._documents: List[KnowledgeDocument] = list(seed_documents or [])

    @property
    def name(self) -> str:
        return "mock-retrieval"

    def set_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Update in-memory documents index."""
        self._documents = list(documents)

    async def add_document(self, doc: KnowledgeDocument) -> bool:
        """
        Dynamically ingest a new knowledge document or technician contribution.
        Idempotent: replaces existing document if same ID is provided.
        """
        # Remove existing document with same ID if present
        self._documents = [d for d in self._documents if d.document_id != doc.document_id]
        self._documents.append(doc)
        return True

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> SearchResponse:
        """Perform simple deterministic in-memory match over seed documents."""
        start_time = time.perf_counter()
        raw_terms = [t.lower().strip(".,!?:;'\"") for t in query.split()]
        query_terms = [t for t in raw_terms if t and t not in STOP_WORDS]
        matches: List[SearchResult] = []

        filters = filters or {}

        for doc in self._documents:
            # Apply metadata filters if specified
            meta_dict = doc.metadata.model_dump()
            matches_filter = True
            for k, v in filters.items():
                if meta_dict.get(k) != v:
                    matches_filter = False
                    break
            if not matches_filter:
                continue

            # Compute term overlap score
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()
            score = 0.0

            for term in query_terms:
                if term in title_lower:
                    score += 2.0
                if term in content_lower:
                    score += 1.0

            # Include if there's any query match or if query was empty (filter-only search)
            if score > 0 or not query_terms:
                matches.append(
                    SearchResult(
                        chunk_id=doc.document_id,
                        document_id=doc.document_id,
                        title=doc.title,
                        content=doc.content,
                        metadata=meta_dict,
                        score=score if query_terms else 1.0,
                        source=doc.metadata.document_type,
                        provenance_type=meta_dict.get("provenance_type", "VERIFIED_COMPANY_DOCUMENT"),
                        verification_status=meta_dict.get("verification_status", "VERIFIED"),
                    )
                )

        # Sort by score descending
        matches.sort(key=lambda x: x.score or 0.0, reverse=True)
        paginated_matches = matches[:limit]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return SearchResponse(
            provider=self.name,
            query=query,
            results=paginated_matches,
            total_count=len(matches),
            latency_ms=round(elapsed_ms, 3),
        )
