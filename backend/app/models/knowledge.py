"""Knowledge document and technician contribution models with explicit provenance."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ProvenanceType = Literal[
    "VERIFIED_COMPANY_DOCUMENT",
    "MANUFACTURER_DOCUMENT",
    "HISTORICAL_SERVICE_RECORD",
    "TECHNICIAN_CONTRIBUTION",
    "UNVERIFIED",
    "CONFLICTING",
]

VerificationStatus = Literal[
    "PENDING_REVIEW",
    "VERIFIED",
    "REJECTED",
]


class KnowledgeMetadata(BaseModel):
    """Metadata attributes supporting filtered, scoped, and provenance-tracked retrieval."""

    asset_model: Optional[str] = Field(None, description="Equipment model (e.g. ACX-420)")
    asset_id: Optional[str] = Field(None, description="Specific asset ID if asset-scoped")
    error_code: Optional[str] = Field(None, description="Associated error code (e.g. E17)")
    document_type: str = Field(
        ...,
        description="Type category: manual, procedure, safety_sop, service_history, technician_contribution",
    )
    safety_level: str = Field(
        default="standard",
        description="Safety criticality: standard, warning, high_voltage, high_pressure, critical",
    )
    source: str = Field(..., description="Source document or origin authority")
    version: str = Field(default="1.0", description="Document revision/version")
    date: Optional[str] = Field(None, description="Publication or revision date")
    provenance_type: ProvenanceType = Field(
        default="VERIFIED_COMPANY_DOCUMENT",
        description="Authoritative provenance origin",
    )
    verification_status: VerificationStatus = Field(
        default="VERIFIED",
        description="Verification lifecycle status",
    )


class KnowledgeDocument(BaseModel):
    """Structured knowledge document or chunk available for retrieval."""

    document_id: str = Field(..., description="Unique identifier for the knowledge document/chunk")
    title: str = Field(..., description="Human-readable title")
    document_type: str = Field(..., description="Primary type identifier (manual, procedure, etc.)")
    content: str = Field(..., description="Full text or chunk content")
    metadata: KnowledgeMetadata = Field(..., description="Filtering and provenance metadata")


class TechnicianContribution(BaseModel):
    """
    Structured contribution submitted by a field technician.

    CRITICAL INVARIANT:
    Technician contributions default to PENDING_REVIEW and TECHNICIAN_CONTRIBUTION.
    They are never automatically promoted to authoritative company standards.
    """

    id: str = Field(..., description="Unique contribution identifier (e.g. contrib-...)")
    title: str = Field(..., min_length=3, max_length=200, description="Short descriptive title of the field finding")
    observation: str = Field(..., min_length=5, description="Initial observation of equipment state or anomaly")
    symptom: str = Field(..., min_length=3, description="Specific symptom exhibited by the machinery")
    suspected_cause: Optional[str] = Field(None, description="Root cause discovered or suspected during diagnosis")
    action_taken: str = Field(..., min_length=3, description="Specific repair, adjustment, or inspection performed")
    outcome: str = Field(..., min_length=3, description="Verified physical or diagnostic outcome after action was taken")
    asset_id: Optional[str] = Field(None, description="Target asset ID if known (e.g. ACX-420-017)")
    session_id: Optional[str] = Field(None, description="Associated interaction session ID if applicable")
    technician_id: Optional[str] = Field(None, description="Identifier of contributing technician if provided")
    source_turn_ids: List[str] = Field(default_factory=list, description="IDs of conversation turns leading to this finding")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Referenced official document IDs")
    provenance_type: ProvenanceType = Field(
        default="TECHNICIAN_CONTRIBUTION",
        description="Explicit provenance: always TECHNICIAN_CONTRIBUTION for field submissions",
    )
    verification_status: VerificationStatus = Field(
        default="PENDING_REVIEW",
        description="Review status: defaults to PENDING_REVIEW",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Creation timestamp in ISO 8601 UTC",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Last update timestamp in ISO 8601 UTC",
    )
