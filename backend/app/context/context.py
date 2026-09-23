"""Context abstraction representing the unified state for reasoning and decision-making."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.asset import Asset
from app.models.knowledge import KnowledgeDocument
from app.models.service_record import ServiceRecord
from app.models.session import ConversationTurn


class UncertaintyContext(BaseModel):
    """Tracks ambiguity, missing information, and safety flags."""

    missing_information: List[str] = Field(
        default_factory=list,
        description="List of critical parameters not yet provided (e.g. ['operating_pressure', 'ambient_temperature'])",
    )
    unverified_claims: List[str] = Field(
        default_factory=list,
        description="Assumptions or statements requiring physical technician verification",
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Estimate of reasoning confidence based on retrieved evidence completeness",
    )
    needs_human_escalation: bool = Field(
        default=False,
        description="True if situation exceeds safe automated diagnostic parameters",
    )


class Context(BaseModel):
    """
    Unified context assembled for the reasoning engine.

    Structure:
    Context
    ├── user_query: current user prompt / speech input
    ├── asset: equipment specification and metadata
    ├── issue: reported equipment symptom
    ├── error_code: specific diagnostic trouble code
    ├── measurements: live instrument readings
    ├── conversation: recent dialogue history
    ├── service_history: relevant prior work orders and repairs
    ├── retrieved_evidence: documents and SOP snippets fetched via retrieval
    ├── safety_context: mandatory safety procedures and warnings
    └── uncertainty: missing parameters and ambiguity markers
    """

    user_query: Optional[str] = Field(
        None,
        description="The live utterance or query from the field technician",
    )
    asset: Optional[Asset] = Field(
        None,
        description="Physical asset specifications and identity",
    )
    issue: Optional[str] = Field(
        None,
        description="Current reported malfunction or symptom",
    )
    error_code: Optional[str] = Field(
        None,
        description="Current active error or alarm code (e.g., E17)",
    )
    measurements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current live sensor and gauge readings (e.g., {'pressure_psi': 195})",
    )
    conversation: List[ConversationTurn] = Field(
        default_factory=list,
        description="Recent dialogue turns from the active session",
    )
    service_history: List[ServiceRecord] = Field(
        default_factory=list,
        description="Prior service records pertinent to this asset and problem",
    )
    retrieved_evidence: List[KnowledgeDocument] = Field(
        default_factory=list,
        description="Technical documentation and SOP chunks retrieved from the knowledge layer",
    )
    safety_context: List[str] = Field(
        default_factory=list,
        description="Critical safety requirements, lockout procedures, and hazard warnings",
    )
    uncertainty: UncertaintyContext = Field(
        default_factory=UncertaintyContext,
        description="Diagnostic ambiguity and missing information trackers",
    )


class ContextBuilder:
    """Fluent helper to assemble a Context object across pipeline stages."""

    def __init__(self, initial: Optional[Context] = None):
        self._context = initial or Context()

    def with_query(self, query: str) -> "ContextBuilder":
        self._context.user_query = query
        return self

    def with_asset(self, asset: Asset) -> "ContextBuilder":
        self._context.asset = asset
        return self

    def with_issue(self, issue: str, error_code: Optional[str] = None) -> "ContextBuilder":
        self._context.issue = issue
        if error_code:
            self._context.error_code = error_code
        return self

    def with_measurement(self, key: str, value: Any) -> "ContextBuilder":
        self._context.measurements[key] = value
        return self

    def add_turn(self, turn: ConversationTurn) -> "ContextBuilder":
        self._context.conversation.append(turn)
        return self

    def add_service_record(self, record: ServiceRecord) -> "ContextBuilder":
        self._context.service_history.append(record)
        return self

    def add_evidence(self, doc: KnowledgeDocument) -> "ContextBuilder":
        self._context.retrieved_evidence.append(doc)
        return self

    def add_safety_warning(self, warning: str) -> "ContextBuilder":
        self._context.safety_context.append(warning)
        return self

    def set_uncertainty(
        self,
        missing: Optional[List[str]] = None,
        confidence: float = 1.0,
        escalate: bool = False,
    ) -> "ContextBuilder":
        if missing is not None:
            self._context.uncertainty.missing_information = missing
        self._context.uncertainty.confidence_score = confidence
        self._context.uncertainty.needs_human_escalation = escalate
        return self

    def build(self) -> Context:
        return self._context
