"""Strongly-typed data models for the complete Assembled Troubleshooting Context."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.models.asset import Asset
from app.models.service_record import ServiceRecord
from app.models.session import ConversationTurn

# Deterministic evidence classifications
EvidenceClassification = Literal[
    "service_history",
    "maintenance_history",
    "troubleshooting",
    "technical_manual",
    "safety_procedure",
    "general_reference",
    "technician_contribution",
]


class EvidenceItem(BaseModel):
    """
    Structured evidence item preserved from Moss retrieval for citation and grounding.
    Preserves original text, metadata, and relevance score without premature summarization.
    """

    document_id: str = Field(..., description="Unique deterministic document identifier in Moss")
    source: str = Field(..., description="Source file or origin identifier")
    document_type: str = Field(..., description="Original metadata document_type attribute")
    classification: EvidenceClassification = Field(
        ...,
        description="Deterministic classification category (e.g. troubleshooting, safety_procedure, technician_contribution)",
    )
    text: str = Field(..., description="Complete original source text preserved for citation")
    score: Optional[float] = Field(None, description="Similarity or relevance score from Moss")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary from index")
    safety_level: Optional[str] = Field(None, description="Safety criticality: standard, warning, high_pressure, critical")
    version: Optional[str] = Field(None, description="Document revision version")
    date: Optional[str] = Field(None, description="Publication or record date")
    applicability: Dict[str, Any] = Field(
        default_factory=dict,
        description="Determined applicability tags (e.g. {'matches_error_code': True, 'matches_model': True})",
    )
    provenance_type: str = Field(
        default="VERIFIED_COMPANY_DOCUMENT",
        description="Explicit provenance origin (VERIFIED_COMPANY_DOCUMENT, TECHNICIAN_CONTRIBUTION, etc.)",
    )
    verification_status: str = Field(
        default="VERIFIED",
        description="Verification lifecycle status (PENDING_REVIEW, VERIFIED, REJECTED)",
    )
    is_technician_contribution: bool = Field(
        default=False,
        description="True if this evidence chunk originated from a field technician contribution",
    )


class RetrievalMetadata(BaseModel):
    """Preserved metadata from the underlying retrieval execution."""

    provider: str = Field(..., description="Name of the retrieval provider (e.g. 'moss' or 'mock-retrieval')")
    status: str = Field(..., description="Provider status ('ready', 'unconfigured', 'error')")
    latency_ms: float = Field(..., description="Actual measured query execution latency in milliseconds")
    result_count: int = Field(..., description="Number of evidence chunks retrieved")
    query: str = Field(..., description="Raw search query string submitted to retrieval")


class UncertaintyModel(BaseModel):
    """Explicitly tracks missing parameters, ambiguity, and diagnostic boundary conditions."""

    missing_asset: bool = Field(False, description="True if equipment asset cannot be resolved")
    missing_error_code: bool = Field(False, description="True if no diagnostic trouble code is identified")
    missing_measurement: bool = Field(False, description="True if required sensor measurement is absent")
    insufficient_evidence: bool = Field(False, description="True if retrieved knowledge base lacks coverage")
    conflicting_evidence: bool = Field(False, description="True if conflicting documents or records are detected")
    ambiguous_query: bool = Field(False, description="True if technician query is too vague to resolve")
    stale_history: bool = Field(False, description="True if service records are outdated or not recent")
    unresolved_asset_reference: Optional[str] = Field(
        None,
        description="Mentioned asset name/unit that could not be mapped to known assets",
    )
    unverified_safety_threshold: bool = Field(
        False,
        description="True if a measurement was evaluated without a verified knowledge threshold",
    )


class DetectedConflict(BaseModel):
    """Identified contradiction between multiple documents or records."""

    conflict_type: str = Field(..., description="Category: version_mismatch, data_contradiction, etc.")
    sources: List[str] = Field(..., description="List of conflicting source document IDs or records")
    description: str = Field(..., description="Deterministic explanation of the detected discrepancy")


class SafetyWarningItem(BaseModel):
    """
    Structured advisory safety warning with grounded provenance.
    Links each warning to its source standard or identifies it as a heuristic rule.
    """

    warning: str = Field(..., description="Actionable warning text")
    provenance_type: Literal["VERIFIED_FROM_KNOWLEDGE", "DEMO_RULE"] = Field(
        ...,
        description="Origin classification: VERIFIED_FROM_KNOWLEDGE if backed by indexed SOP, DEMO_RULE if heuristic",
    )
    source_document_id: Optional[str] = Field(None, description="Document ID defining this threshold or constraint")
    source_reference: Optional[str] = Field(None, description="Specific section, step, or SOP reference")
    threshold_applied: Optional[str] = Field(None, description="Threshold rule evaluated (e.g. '> 190.0 PSI')")


class SafetyContext(BaseModel):
    """Safety-relevant constraints and standard operating procedures identified for this interaction."""

    safety_level: str = Field("standard", description="Overall highest safety severity detected")
    safety_documents: List[str] = Field(default_factory=list, description="IDs of retrieved safety SOP documents")
    safety_warnings: List[str] = Field(default_factory=list, description="Deterministic advisory safety warnings")
    warning_items: List[SafetyWarningItem] = Field(
        default_factory=list,
        description="Structured safety warnings with explicit provenance",
    )
    threshold_sources: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of threshold metric to document/SOP source",
    )
    safety_evidence_ids: List[str] = Field(default_factory=list, description="All evidence items flagged as safety-critical")
    mandatory_loto: bool = Field(False, description="True if Lockout/Tagout is required before physical access")
    high_pressure_hazard: bool = Field(False, description="True if elevated or emergency pressure is detected")


class ExtractedQueryFacts(BaseModel):
    """Structured facts extracted deterministically from technician utterance."""

    raw_query: str = Field(..., description="Original technician utterance")
    asset_reference: Optional[str] = Field(None, description="Explicit asset reference string (e.g. 'unit 017')")
    asset_model: Optional[str] = Field(None, description="Explicit model mentioned (e.g. 'ACX-420')")
    error_code: Optional[str] = Field(None, description="Extracted diagnostic trouble code (e.g. 'E17')")
    measurements: Dict[str, Any] = Field(default_factory=dict, description="Extracted numerical readings with units")
    is_repeat_issue: bool = Field(False, description="True if query indicates recurrence ('again', 'repeat')")
    observations: List[str] = Field(default_factory=list, description="Explicitly stated physical symptoms")


class AssembledContext(BaseModel):
    """
    Unified Case File assembled for future diagnostic reasoning.

    CRITICAL INVARIANT:
    This model contains facts, evidence, and uncertainty only.
    It does NOT contain final diagnoses, root-cause decisions, or recommended actions.
    """

    session_id: Optional[str] = Field(None, description="Session identifier if associated with an active dialogue")
    technician_query: str = Field(..., description="Raw query from the technician")
    query_facts: ExtractedQueryFacts = Field(..., description="Deterministic facts extracted from query")
    asset: Optional[Asset] = Field(None, description="Structured asset specification if resolved")
    asset_id: Optional[str] = Field(None, description="Resolved equipment identifier (e.g. 'ACX-420-017')")
    asset_model: Optional[str] = Field(None, description="Equipment model (e.g. 'ACX-420')")
    error_code: Optional[str] = Field(None, description="Active trouble code")
    measurements: Dict[str, Any] = Field(default_factory=dict, description="Live sensor and instrument readings")
    measurement_provenance: Dict[str, str] = Field(
        default_factory=dict,
        description="Source origin of each measurement: 'technician_query' vs 'session_telemetry:<session_id>'",
    )
    observations: List[str] = Field(default_factory=list, description="Observed equipment symptoms")
    relevant_service_history: List[ServiceRecord] = Field(
        default_factory=list,
        description="Structured historical work orders for this asset",
    )
    conversation_context: List[ConversationTurn] = Field(
        default_factory=list,
        description="Recent conversation history window",
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Ranked evidence chunks retrieved from Moss knowledge base",
    )
    safety_context: SafetyContext = Field(
        default_factory=SafetyContext,
        description="Grounded safety constraints and warnings",
    )
    uncertainty: UncertaintyModel = Field(
        default_factory=UncertaintyModel,
        description="Explicitly flagged information gaps and ambiguities",
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Human-readable list of missing parameters required for future reasoning",
    )
    conflicts: List[DetectedConflict] = Field(
        default_factory=list,
        description="List of detected version or data contradictions across evidence",
    )
    retrieval_metadata: RetrievalMetadata = Field(
        ...,
        description="Observability and timing metadata from the retrieval layer",
    )
