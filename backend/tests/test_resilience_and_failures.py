"""Failure Simulation and Resilience Tests for Relay Reasoning & Safety.

Verifies:
1. Rejection of prohibited safety actions ('bypass lockout', 'bypass loto').
2. Rejection of fabricated or unretrieved citation IDs.
3. Safe fallback generation upon validation rejection (escalation flagged, safe voice advice).
4. Prevention of pending technician contributions being promoted to official standards.
5. Graceful handling of retrieval failures.
"""

import pytest

from app.context.assembled_context import (
    AssembledContext,
    EvidenceItem,
    ExtractedQueryFacts,
    RetrievalMetadata,
    SafetyContext,
    UncertaintyModel,
)
from app.reasoning.base import ReasoningProvider
from app.reasoning.models import (
    EvidenceClaim,
    ReasoningCitation,
    ReasoningMetadata,
    ReasoningResult,
    RecommendedNextStep,
)
from app.reasoning.service import ReasoningService
from app.reasoning.validator import ReasoningQualityValidator


class FaultyReasoningProvider(ReasoningProvider):
    """Test stub simulating a rogue or hallucinating reasoning model."""

    def __init__(self, faulty_result: ReasoningResult):
        self._faulty_result = faulty_result

    @property
    def provider_name(self) -> str:
        return "faulty-test-reasoner"

    async def reason(self, context: AssembledContext) -> ReasoningResult:
        return self._faulty_result


def create_minimal_context(mandatory_loto: bool = True) -> AssembledContext:
    return AssembledContext(
        technician_query="Check unit 017",
        query_facts=ExtractedQueryFacts(raw_query="Check unit 017"),
        evidence=[
            EvidenceItem(
                document_id="valid-doc-1",
                source="sop_01.md",
                document_type="troubleshooting",
                classification="troubleshooting",
                text="Standard inspection sequence.",
                score=0.9,
            )
        ],
        safety_context=SafetyContext(
            safety_level="critical" if mandatory_loto else "standard",
            safety_warnings=["Lockout required before opening cabinet."] if mandatory_loto else [],
            mandatory_loto=mandatory_loto,
        ),
        uncertainty=UncertaintyModel(),
        retrieval_metadata=RetrievalMetadata(
            provider="mock",
            status="ready",
            latency_ms=1.0,
            result_count=1,
            query="Check unit 017",
        ),
    )


@pytest.mark.asyncio
async def test_prohibited_action_rejection_and_safe_fallback():
    """Verify that a prohibited action ('bypass lockout') is caught and transformed into a safe fallback."""
    rogue_result = ReasoningResult(
        status="completed",
        issue_summary="Rogue plan",
        what_we_know=[],
        assessment="Fast check: bypass lockout to save time and inspect immediately.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Step 1: Bypass lockout and inspect coil with power on.",
                evidence_ids=["valid-doc-1"],
                rationale="Fast check",
            )
        ],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[
            ReasoningCitation(
                evidence_id="valid-doc-1",
                source="sop_01.md",
                document_type="troubleshooting",
                relevant_excerpt="Standard inspection.",
            )
        ],
        reasoning_metadata=ReasoningMetadata(provider="test", latency_ms=1.0, retrieval_latency_ms=0.5),
    )

    context = create_minimal_context(mandatory_loto=True)
    service = ReasoningService(provider=FaultyReasoningProvider(rogue_result))

    final_result, report = await service.analyze(context)

    # 1. Validation report must record error
    assert report.is_valid is False
    assert any("prohibited action" in err for err in report.errors)

    # 2. Result returned to user must be safe fallback
    assert final_result.status == "insufficient_evidence"
    assert "rejected to protect technician safety" in final_result.assessment
    assert final_result.escalation.should_escalate is True
    assert final_result.spoken_response is not None
    assert "bypass lockout" not in final_result.spoken_response.lower()


@pytest.mark.asyncio
async def test_fabricated_citation_rejection():
    """Verify that citations to unretrieved document IDs are rejected."""
    hallucinated_result = ReasoningResult(
        status="completed",
        issue_summary="Hallucination test",
        what_we_know=[],
        assessment="Assessment based on imaginary manual.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Step 1: Check imaginary valve per SOP-999.",
                evidence_ids=["imaginary-doc-999"],
                rationale="Imaginary procedure",
            )
        ],
        safety_considerations=["Lockout and shutdown required."],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[
            ReasoningCitation(
                evidence_id="imaginary-doc-999",
                source="imaginary_sop.md",
                document_type="troubleshooting",
                relevant_excerpt="Does not exist.",
            )
        ],
        reasoning_metadata=ReasoningMetadata(provider="test", latency_ms=1.0, retrieval_latency_ms=0.5),
    )

    context = create_minimal_context(mandatory_loto=True)
    service = ReasoningService(provider=FaultyReasoningProvider(hallucinated_result))

    final_result, report = await service.analyze(context)

    assert report.is_valid is False
    assert any("fabricated evidence ID" in err for err in report.errors)
    assert final_result.status == "insufficient_evidence"


@pytest.mark.asyncio
async def test_pending_contribution_promotion_rejection():
    """Verify that a reasoning step claiming a pending contribution is an 'approved manufacturer standard' is rejected."""
    context = AssembledContext(
        technician_query="Algae in drain",
        query_facts=ExtractedQueryFacts(raw_query="Algae in drain"),
        evidence=[
            EvidenceItem(
                document_id="contrib-algae-01",
                source="P-trap observation",
                document_type="technician_contribution",
                classification="technician_contribution",
                text="Field observation about algae.",
                provenance_type="TECHNICIAN_CONTRIBUTION",
                verification_status="PENDING_REVIEW",
                is_technician_contribution=True,
            )
        ],
        safety_context=SafetyContext(),
        uncertainty=UncertaintyModel(),
        retrieval_metadata=RetrievalMetadata(
            provider="mock",
            status="ready",
            latency_ms=1.0,
            result_count=1,
            query="Algae in drain",
        ),
    )

    bad_result = ReasoningResult(
        status="completed",
        issue_summary="Bad promotion",
        what_we_know=[],
        assessment="Follow official procedure.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Step 1: Apply approved procedure from field notes.",
                evidence_ids=["contrib-algae-01"],
                rationale="This is an official SOP for clearing drain lines.",
            )
        ],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[],
        reasoning_metadata=ReasoningMetadata(provider="test", latency_ms=1.0, retrieval_latency_ms=0.5),
    )

    service = ReasoningService(provider=FaultyReasoningProvider(bad_result))
    final_result, report = await service.analyze(context)

    assert report.is_valid is False
    assert any("asserts that pending technician contribution" in err for err in report.errors)
    assert final_result.status == "insufficient_evidence"
