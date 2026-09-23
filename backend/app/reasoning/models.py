"""Strongly-typed data models for the Evidence-Grounded Reasoning Engine."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


SupportLevel = Literal["direct", "inferred", "insufficient"]

CertaintyLevel = Literal[
    "supported",
    "partially_supported",
    "insufficient_evidence",
    "conflicting_evidence",
]

ReasoningStatus = Literal[
    "completed",
    "insufficient_evidence",
    "needs_information",
    "conflicting_evidence",
    "safety_escalation",
]


class EvidenceClaim(BaseModel):
    """
    Substantive technical claim backed by evidence chunks from the knowledge base.
    Prevents unsupported model assertions from appearing as established facts.
    """

    claim: str = Field(..., description="Actionable or diagnostic claim")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Chunk or document IDs directly supporting this claim",
    )
    support_level: SupportLevel = Field(
        ...,
        description="Confidence grounding: direct, inferred, or insufficient",
    )
    explanation: Optional[str] = Field(
        None,
        description="Rationale connecting the evidence chunks to the claim",
    )


class ReasoningCitation(BaseModel):
    """
    Specific citation referencing retrieved documentation or service history.
    Preserves original source metadata and document identity.
    """

    evidence_id: str = Field(..., description="Document or chunk ID in the retrieved knowledge base")
    source: str = Field(..., description="Source file or document name")
    document_type: str = Field(..., description="Document classification (e.g. troubleshooting, manual)")
    relevant_excerpt: str = Field(..., description="Direct verbatim or key excerpt grounded in the text")
    score: Optional[float] = Field(None, description="Retrieval similarity score if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata")


class RecommendedNextStep(BaseModel):
    """
    Actionable next step for field technician troubleshooting.
    MUST be supported by evidence and conform to verified safety constraints.
    """

    step: str = Field(..., description="Concrete physical or diagnostic inspection action")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Document IDs specifying or authorizing this procedure step",
    )
    rationale: str = Field(..., description="Why this step is prioritized based on facts and evidence")
    expected_observation: Optional[str] = Field(
        None,
        description="What the technician should look for or measure during this step",
    )
    safety_constraints: List[str] = Field(
        default_factory=list,
        description="Mandatory precautions (e.g. LOTO, de-energization) before performing this step",
    )


class DecisionBranch(BaseModel):
    """
    Conditional logic branch grounded in standard operating procedures.
    Enables step-by-step diagnostic tree navigation based on technician observations.
    """

    condition: str = Field(..., description="Condition or measurement outcome (e.g. 'If pressure > 190 PSI')")
    if_true_branch: str = Field(..., description="Next diagnostic action if condition holds true")
    if_false_branch: Optional[str] = Field(None, description="Alternative action if condition is false")
    evidence_ids: List[str] = Field(default_factory=list, description="Document IDs defining this branching rule")
    rationale: Optional[str] = Field(None, description="Technical explanation for this diagnostic branch")


class EscalationAssessment(BaseModel):
    """Structured escalation recommendation when technical or safety thresholds require supervisor sign-off."""

    should_escalate: bool = Field(False, description="True if escalation to supervisor or senior engineer is required")
    reason: Optional[str] = Field(None, description="Detailed reason for escalation")
    missing_information: List[str] = Field(
        default_factory=list,
        description="Critical technical parameters missing before work can proceed safely",
    )
    safety_reason: Optional[str] = Field(None, description="Hazard or threshold trigger that mandates escalation")
    recommended_escalation_target: Optional[str] = Field(
        None,
        description="Target team or role (e.g. 'Senior HVAC Technician', 'Facility Safety Supervisor')",
    )


class ReasoningMetadata(BaseModel):
    """Telemetry and timing metadata for reasoning execution."""

    provider: str = Field(..., description="Name of reasoning provider (e.g. 'mock-reasoner', 'llm-reasoner')")
    latency_ms: float = Field(..., description="Reasoning execution latency in milliseconds")
    retrieval_latency_ms: float = Field(..., description="Preserved retrieval latency from Moss")
    model_name: Optional[str] = Field(None, description="Underlying model identifier if LLM backed")
    token_usage: Dict[str, Any] = Field(default_factory=dict, description="Token consumption statistics")


class ReasoningResult(BaseModel):
    """
    Unified Evidence-Grounded Diagnostic Reasoning Result.

    CRITICAL INVARIANT:
    All claims and recommended next steps must be grounded in supplied evidence.
    No ungrounded guesses or fabricated diagnoses are permitted.
    """

    status: ReasoningStatus = Field(
        ...,
        description="Overall diagnostic status: completed, insufficient_evidence, needs_information, etc.",
    )
    issue_summary: str = Field(..., description="Concise summary of what the technician reported")
    what_we_know: List[str] = Field(
        default_factory=list,
        description="Facts directly supported by query, asset telemetry, or service records",
    )
    assessment: str = Field(
        ...,
        description="Evidence-grounded interpretation of the current equipment state",
    )
    evidence_claims: List[EvidenceClaim] = Field(
        default_factory=list,
        description="Substantive claims mapped directly to supporting evidence IDs",
    )
    recommended_next_steps: List[RecommendedNextStep] = Field(
        default_factory=list,
        description="Prioritized, evidence-supported troubleshooting steps",
    )
    safety_considerations: List[str] = Field(
        default_factory=list,
        description="Authoritative safety constraints and hazard warnings",
    )
    expected_observations: List[str] = Field(
        default_factory=list,
        description="Physical indicators or telemetry readings expected during testing",
    )
    decision_branches: List[DecisionBranch] = Field(
        default_factory=list,
        description="Conditional troubleshooting branches supported by SOP evidence",
    )
    clarifying_questions: List[str] = Field(
        default_factory=list,
        description="Dynamic clarifying questions generated when context is insufficient",
    )
    certainty_level: CertaintyLevel = Field(
        ...,
        description="Calibrated confidence level based on evidence completeness",
    )
    uncertainty: Dict[str, Any] = Field(
        default_factory=dict,
        description="Explicitly tracked diagnostic unknowns and information gaps",
    )
    escalation: EscalationAssessment = Field(
        default_factory=EscalationAssessment,
        description="Structured escalation assessment",
    )
    citations: List[ReasoningCitation] = Field(
        default_factory=list,
        description="Explicit source citations referencing retrieved documents",
    )
    reasoning_metadata: ReasoningMetadata = Field(
        ...,
        description="Execution timing and observability metadata",
    )
    spoken_response: Optional[str] = Field(
        None,
        description="Concise, synthesized speech script prioritizing safety, assessment, and next action",
    )
