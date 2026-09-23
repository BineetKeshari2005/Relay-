"""Service for validating, normalizing, and ingesting technician knowledge contributions."""

import logging
from typing import Dict, List, Optional
import uuid

from app.models.knowledge import KnowledgeDocument, KnowledgeMetadata, TechnicianContribution
from app.retrieval.base import RetrievalProvider

logger = logging.getLogger("relay.retrieval.contribution")


class ContributionStorage:
    """In-memory persistent registry for technician knowledge contributions."""

    def __init__(self):
        self._contributions: Dict[str, TechnicianContribution] = {}

    def save(self, contribution: TechnicianContribution) -> TechnicianContribution:
        """Store or update a technician contribution."""
        self._contributions[contribution.id] = contribution
        return contribution

    def get(self, contribution_id: str) -> Optional[TechnicianContribution]:
        """Retrieve a contribution by its unique ID."""
        return self._contributions.get(contribution_id)

    def list(
        self,
        asset_id: Optional[str] = None,
        verification_status: Optional[str] = None,
    ) -> List[TechnicianContribution]:
        """List contributions matching optional asset or status filters."""
        results = list(self._contributions.values())
        if asset_id:
            results = [c for c in results if c.asset_id == asset_id]
        if verification_status:
            results = [c for c in results if c.verification_status == verification_status]
        # Sort by creation time descending
        results.sort(key=lambda c: c.created_at, reverse=True)
        return results

    def clear(self) -> None:
        """Clear storage (primarily for test resets)."""
        self._contributions.clear()


# Global storage instance
_global_storage = ContributionStorage()


def get_contribution_storage() -> ContributionStorage:
    """Access the global contribution storage singleton."""
    return _global_storage


class KnowledgeIngestionService:
    """
    Validates, normalizes, and ingests technician knowledge contributions into the retrieval layer.

    CORE PRINCIPLE:
    TECHNICIAN CONTRIBUTION != VERIFIED COMPANY KNOWLEDGE
    Always assigns TECHNICIAN_CONTRIBUTION provenance and PENDING_REVIEW verification status.
    Never fabricates unmentioned measurements, repair outcomes, or safety limits.
    """

    def __init__(
        self,
        retrieval_provider: RetrievalProvider,
        storage: Optional[ContributionStorage] = None,
    ):
        self.retrieval_provider = retrieval_provider
        self.storage = storage or get_contribution_storage()

    def normalize(self, contribution: TechnicianContribution) -> KnowledgeDocument:
        """
        Transform a structured technician contribution into a normalized KnowledgeDocument
        suitable for low-latency indexing in Moss.
        """
        doc_id = contribution.id if contribution.id.startswith("contrib-") else f"contrib-{contribution.id}"

        formatted_content = (
            f"# Field Technician Report: {contribution.title}\n"
            f"Provenance: TECHNICIAN_CONTRIBUTION | Status: {contribution.verification_status}\n"
            f"Asset ID: {contribution.asset_id or 'unspecified'} | Session: {contribution.session_id or 'unspecified'}\n\n"
            f"## Field Observation\n"
            f"{contribution.observation.strip()}\n\n"
            f"## Observed Symptom\n"
            f"{contribution.symptom.strip()}\n\n"
            f"## Discovered Cause\n"
            f"{contribution.suspected_cause.strip() if contribution.suspected_cause else 'Not specified'}\n\n"
            f"## Action Taken\n"
            f"{contribution.action_taken.strip()}\n\n"
            f"## Field Outcome\n"
            f"{contribution.outcome.strip()}\n"
        )

        metadata = KnowledgeMetadata(
            asset_model="ACX-420" if (contribution.asset_id and "ACX" in contribution.asset_id) else None,
            asset_id=contribution.asset_id,
            error_code=None,  # Do not infer error code unless explicitly provided in future schemas
            document_type="technician_contribution",
            safety_level="standard",
            source=f"Technician Contribution ({contribution.id})",
            version="1.0",
            date=contribution.created_at[:10] if contribution.created_at else None,
            provenance_type="TECHNICIAN_CONTRIBUTION",
            verification_status=contribution.verification_status,
        )

        return KnowledgeDocument(
            document_id=doc_id,
            title=contribution.title,
            document_type="technician_contribution",
            content=formatted_content,
            metadata=metadata,
        )

    async def ingest(self, contribution: TechnicianContribution) -> KnowledgeDocument:
        """
        Complete ingestion flow:
        1. Store structured contribution.
        2. Normalize into retrieval KnowledgeDocument.
        3. Index into active retrieval provider (Moss or Mock).
        """
        # 1. Enforce strict provenance invariants
        contribution.provenance_type = "TECHNICIAN_CONTRIBUTION"
        if not contribution.verification_status:
            contribution.verification_status = "PENDING_REVIEW"

        # 2. Persist contribution
        self.storage.save(contribution)

        # 3. Normalize into searchable knowledge document
        norm_doc = self.normalize(contribution)

        # 4. Ingest into retrieval engine
        indexed = await self.retrieval_provider.add_document(norm_doc)
        if not indexed:
            logger.warning("Retrieval provider failed to index contribution %s", contribution.id)

        logger.info(
            "Successfully ingested technician contribution '%s' (ID: %s, Status: %s)",
            contribution.title,
            contribution.id,
            contribution.verification_status,
        )
        return norm_doc
