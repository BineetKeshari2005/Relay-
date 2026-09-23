"""FastAPI router for Technician Knowledge Contributions and Teach Relay workflow."""

import logging
from typing import List, Optional
import uuid
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.retrieval import get_active_provider
from app.models.knowledge import TechnicianContribution
from app.retrieval.contribution_service import KnowledgeIngestionService, get_contribution_storage

logger = logging.getLogger("relay.api.contributions")
router = APIRouter(prefix="/api/knowledge/contributions", tags=["Knowledge Contributions"])


class ContributionCreateRequest(BaseModel):
    """Payload for submitting a technician field contribution."""

    title: str = Field(..., min_length=3, max_length=200, description="Short descriptive title of the finding")
    observation: Optional[str] = Field(None, description="Initial observation of equipment symptom or anomaly")
    symptom: Optional[str] = Field(None, description="Specific symptom exhibited")
    suspected_cause: Optional[str] = Field(None, description="Discovered root cause")
    action_taken: str = Field(..., min_length=3, description="Specific repair or adjustment performed")
    outcome: Optional[str] = Field(default="Resolved in field", description="Verified physical or diagnostic outcome")
    asset_id: Optional[str] = Field(None, description="Target asset ID (e.g. ACX-420-017)")
    session_id: Optional[str] = Field(None, description="Active session ID if associated")
    technician_id: Optional[str] = Field(None, description="Technician identifier")
    source_turn_ids: List[str] = Field(default_factory=list, description="IDs of related dialogue turns")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Referenced official document IDs")


@router.post(
    "",
    response_model=TechnicianContribution,
    status_code=status.HTTP_201_CREATED,
    summary="Create and Ingest Technician Field Knowledge Contribution",
)
async def create_contribution(req: ContributionCreateRequest) -> TechnicianContribution:
    """
    Ingest a new technician observation into the system:
    1. Validates structured fields without fabricating missing data.
    2. Assigns TECHNICIAN_CONTRIBUTION provenance and PENDING_REVIEW verification status.
    3. Normalizes contribution into structured retrieval document.
    4. Indexes into active retrieval provider (Moss / Mock) for future technician retrieval.
    """
    try:
        obs = (req.observation or req.symptom or req.title).strip()
        sym = (req.symptom or req.observation or req.title).strip()
        out = (req.outcome or "Resolved in field").strip()

        contrib_id = f"contrib-{uuid.uuid4().hex[:8]}"
        contribution = TechnicianContribution(
            id=contrib_id,
            title=req.title.strip(),
            observation=obs,
            symptom=sym,
            suspected_cause=req.suspected_cause.strip() if req.suspected_cause else None,
            action_taken=req.action_taken.strip(),
            outcome=out,
            asset_id=req.asset_id.strip() if req.asset_id else None,
            session_id=req.session_id.strip() if req.session_id else None,
            technician_id=req.technician_id.strip() if req.technician_id else None,
            source_turn_ids=req.source_turn_ids,
            supporting_evidence_ids=req.supporting_evidence_ids,
            provenance_type="TECHNICIAN_CONTRIBUTION",
            verification_status="PENDING_REVIEW",
        )

        provider = get_active_provider()
        ingestion_service = KnowledgeIngestionService(retrieval_provider=provider)
        await ingestion_service.ingest(contribution)

        return contribution

    except Exception as e:
        logger.error("Failed to create contribution: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ContributionIngestionError", "message": str(e)},
        )


@router.get(
    "/{contribution_id}",
    response_model=TechnicianContribution,
    summary="Get Technician Knowledge Contribution by ID",
)
async def get_contribution(contribution_id: str) -> TechnicianContribution:
    """Retrieve a single contribution by its unique identifier."""
    storage = get_contribution_storage()
    contrib = storage.get(contribution_id)
    if not contrib:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contribution '{contribution_id}' not found.",
        )
    return contrib


@router.get(
    "",
    response_model=List[TechnicianContribution],
    summary="List Technician Knowledge Contributions",
)
async def list_contributions(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    verification_status: Optional[str] = Query(None, description="Filter by status (e.g. PENDING_REVIEW)"),
) -> List[TechnicianContribution]:
    """List technician knowledge contributions matching optional query parameters."""
    storage = get_contribution_storage()
    return storage.list(asset_id=asset_id, verification_status=verification_status)
