"""Tests for Phase 7 Voice Interaction, Spoken Response Generation, and Safety Prioritization."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.knowledge import KnowledgeMetadata
from app.reasoning.models import (
    EscalationAssessment,
    EvidenceClaim,
    ReasoningCitation,
    ReasoningMetadata,
    ReasoningResult,
    RecommendedNextStep,
)
from app.reasoning.service import ReasoningService
from app.reasoning.provider import MockReasoningProvider
from app.retrieval.mock import MockRetrievalProvider
from app.context.assembler import ContextAssembler
from app.voice.formatter import SpokenResponseFormatter


def test_voice_response_standard_fault():
    """Verify that standard diagnostic results yield concise assessment and actionable next step."""
    result = ReasoningResult(
        status="completed",
        issue_summary="Blower vibration on unit ACX-420-017",
        what_we_know=["Unit model ACX-420", "Vibration reported"],
        assessment="Excessive blower housing vibration indicates potential bearing wear or unseated wheel assembly. Motor mount tension should be verified.",
        evidence_claims=[
            EvidenceClaim(
                claim="Blower vibration requires bearing inspection",
                evidence_ids=["doc-1"],
                support_level="direct",
            )
        ],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Inspect blower wheel set screws and verify bearing play",
                evidence_ids=["doc-1"],
                rationale="Isolate mechanical balance issues",
                safety_constraints=["Verify unit is de-energized"],
            )
        ],
        safety_considerations=[],
        expected_observations=["Less than 1mm radial play"],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[
            ReasoningCitation(
                evidence_id="doc-1",
                source="ACX-420 Manual",
                document_type="manual",
                relevant_excerpt="Check blower set screws annually.",
            )
        ],
        reasoning_metadata=ReasoningMetadata(
            provider="mock",
            latency_ms=1.5,
            retrieval_latency_ms=2.0,
        ),
    )

    spoken = SpokenResponseFormatter.format(result)

    # Must contain assessment
    assert "Excessive blower housing vibration indicates potential bearing wear" in spoken
    # Must contain next step
    assert "Recommended next step: Inspect blower wheel set screws and verify bearing play." in spoken
    # Must NOT contain verbose citation or document type
    assert "ACX-420 Manual" not in spoken
    assert "doc-1" not in spoken


def test_voice_response_safety_prioritization():
    """Verify that safety constraints (e.g. LOTO, high pressure) are spoken FIRST."""
    result = ReasoningResult(
        status="completed",
        issue_summary="E17 high pressure on unit 017",
        what_we_know=["Pressure is 195 PSI"],
        assessment="High discharge pressure fault E17 active on unit ACX-420-017.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Inspect condenser coil for surface blockages",
                evidence_ids=["e17-troubleshooting"],
                rationale="Clear airflow path",
                safety_constraints=["Mandatory LOTO before touching electrical components"],
            )
        ],
        safety_considerations=[
            "DANGER: System pressure (195.0 PSI) exceeds safety threshold (190.0 PSI). Mandatory Lockout/Tagout (LOTO) required before inspection."
        ],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[],
        reasoning_metadata=ReasoningMetadata(
            provider="mock",
            latency_ms=1.0,
            retrieval_latency_ms=1.5,
        ),
    )

    spoken = SpokenResponseFormatter.format(result)

    # Safety warning MUST be at the very beginning of the spoken response
    assert spoken.startswith("DANGER: System pressure (195.0 PSI) exceeds safety threshold (190.0 PSI).")
    # Followed by assessment and next step
    assert "High discharge pressure fault E17" in spoken
    assert "Recommended next step: Inspect condenser coil for surface blockages." in spoken


def test_voice_response_clarifying_questions():
    """Verify that when status is needs_information, clarifying questions are spoken."""
    result = ReasoningResult(
        status="needs_information",
        issue_summary="Vague complaint",
        what_we_know=[],
        assessment="Insufficient information to diagnose.",
        evidence_claims=[],
        recommended_next_steps=[],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[
            "Which equipment unit identifier are you inspecting?",
            "What specific symptom or error code is displayed?",
        ],
        certainty_level="insufficient_evidence",
        citations=[],
        reasoning_metadata=ReasoningMetadata(
            provider="mock",
            latency_ms=0.5,
            retrieval_latency_ms=1.0,
        ),
    )

    spoken = SpokenResponseFormatter.format(result)

    # Must speak the clarifying questions
    assert "To assist you:" in spoken
    assert "Which equipment unit identifier are you inspecting" in spoken
    assert "what specific symptom or error code is displayed" in spoken


def test_voice_response_non_authoritative_contribution():
    """Verify that when a technician contribution is cited, a non-authoritative notice is spoken."""
    result = ReasoningResult(
        status="completed",
        issue_summary="Intermittent freeze-up",
        what_we_know=["Freeze-up reported"],
        assessment="Unit may be experiencing condensate drain trap blockage based on field reports.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Inspect P-trap cleanout for biological sludge",
                evidence_ids=["contrib-001"],
                rationale="Check drain flow",
            )
        ],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="partially_supported",
        citations=[
            ReasoningCitation(
                evidence_id="contrib-001",
                source="Field Note: P-trap algae",
                document_type="technician_contribution",
                relevant_excerpt="Algae clogged trap.",
                metadata={
                    "provenance_type": "TECHNICIAN_CONTRIBUTION",
                    "verification_status": "PENDING_REVIEW",
                },
            )
        ],
        reasoning_metadata=ReasoningMetadata(
            provider="mock",
            latency_ms=1.0,
            retrieval_latency_ms=1.0,
        ),
    )

    spoken = SpokenResponseFormatter.format(result)

    assert "Note: this guidance references pending field observations." in spoken


def test_voice_response_empty_fields_graceful():
    """Verify that formatting empty or minimal results handles gracefully without crashing."""
    result = ReasoningResult(
        status="completed",
        issue_summary="Minimal test",
        what_we_know=[],
        assessment="Operating nominally.",
        evidence_claims=[],
        recommended_next_steps=[],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[],
        reasoning_metadata=ReasoningMetadata(
            provider="mock",
            latency_ms=0.2,
            retrieval_latency_ms=0.5,
        ),
    )

    spoken = SpokenResponseFormatter.format(result)
    assert spoken == "Operating nominally."


@pytest.mark.asyncio
async def test_end_to_end_reasoning_populates_spoken_response():
    """Verify that ReasoningService.analyze() automatically populates spoken_response."""
    assembler = ContextAssembler(retrieval_provider=MockRetrievalProvider())
    context = await assembler.assemble(
        query="Unit 017 is reporting E17 with pressure around 195 PSI.",
        session_id="sess-017",
    )

    service = ReasoningService(provider=MockReasoningProvider())
    result, report = await service.analyze(context)

    assert report.is_valid is True
    assert result.spoken_response is not None
    assert len(result.spoken_response) > 10
    # Must prioritize safety for E17 > 190 PSI
    assert "DANGER:" in result.spoken_response or "Warning:" in result.spoken_response


def test_api_reasoning_analyze_returns_spoken_response():
    """Verify that POST /api/reasoning/analyze includes spoken_response in HTTP response."""
    client = TestClient(app)

    response = client.post(
        "/api/reasoning/analyze",
        json={
            "query": "Unit 017 is reporting E17 with pressure around 195 PSI.",
            "session_id": "sess-017",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "reasoning" in data
    assert "spoken_response" in data["reasoning"]
    spoken = data["reasoning"]["spoken_response"]
    assert spoken is not None
    assert isinstance(spoken, str)
    assert len(spoken) > 0


def test_voice_session_continuity_across_turns():
    """Verify that consecutive voice turns preserve session_id, asset_id, and context continuity."""
    client = TestClient(app)

    # Turn 1: Initial complaint about vibration
    resp1 = client.post(
        "/api/reasoning/analyze",
        json={
            "query": "Unit 017 is vibrating heavily after startup.",
            "session_id": "sess-017",
            "asset_id": "ACX-420-017",
        },
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["context"]["session_id"] == "sess-017"
    assert data1["context"]["asset_id"] == "ACX-420-017"
    assert data1["reasoning"]["spoken_response"] is not None

    # Turn 2: Follow-up question continuing the exact same session
    resp2 = client.post(
        "/api/reasoning/analyze",
        json={
            "query": "The vibration started after yesterday's maintenance. What should I inspect next?",
            "session_id": "sess-017",
            "asset_id": "ACX-420-017",
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["context"]["session_id"] == "sess-017"
    assert data2["context"]["asset_id"] == "ACX-420-017"
    assert data2["reasoning"]["spoken_response"] is not None
    assert len(data2["reasoning"]["spoken_response"]) > 0

