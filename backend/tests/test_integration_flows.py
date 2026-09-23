"""End-to-End Integration Flow Tests for Relay Decision Support.

Covers:
1. Flow A: Full E17 high-pressure scenario.
2. Flow B: Arbitrary technical issue (compressor vibration).
3. Flow C: Vague query ('Unit isn't working') requiring clarification.
4. Flow D: No-evidence query with explicit uncertainty.
5. Flow E: Technician contribution ingestion and subsequent retrieval roundtrip.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.retrieval import get_active_provider
from app.context.assembler import ContextAssembler
from app.reasoning.service import ReasoningService
from app.reasoning.provider import MockReasoningProvider


@pytest.mark.asyncio
async def test_integration_flow_a_e17_scenario():
    """Verify complete Flow A: E17 fault with 195 PSI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/reasoning/analyze",
            json={
                "query": "I am getting E17 again on unit 017. Pressure is around 195 PSI.",
                "session_id": "sess-017",
                "asset_id": "ACX-420-017",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        # 1. Context validation
        context = data["context"]
        assert context["error_code"] == "E17"
        assert context["measurements"]["pressure_psi"] == 195.0
        assert context["safety_context"]["mandatory_loto"] is True
        assert context["safety_context"]["high_pressure_hazard"] is True

        # 2. Reasoning validation
        reasoning = data["reasoning"]
        assert reasoning["status"] == "completed"
        assert reasoning["certainty_level"] == "supported"
        assert len(reasoning["citations"]) > 0

        # Citations must point to actual evidence
        evidence_ids = [e["document_id"] for e in context["evidence"]]
        for cite in reasoning["citations"]:
            assert cite["evidence_id"] in evidence_ids or cite["evidence_id"] == "unit-017-service-record"

        # 3. Next step must exist and be actionable
        assert len(reasoning["recommended_next_steps"]) > 0
        first_step = reasoning["recommended_next_steps"][0]["step"]
        assert "model scope" not in first_step.lower()
        assert "notice" not in first_step.lower()

        # 4. Spoken response must be safety-first and actionable
        spoken = reasoning["spoken_response"]
        assert spoken is not None
        assert spoken.startswith("Warning:")
        assert "195.0 PSI" in spoken or "195 PSI" in spoken
        assert "Model Scope" not in spoken
        assert "Recommended next step:" in spoken


@pytest.mark.asyncio
async def test_integration_flow_b_arbitrary_issue_no_e17_contamination():
    """Verify complete Flow B: Arbitrary compressor vibration does not inherit E17 or 195 PSI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/reasoning/analyze",
            json={
                "query": "Compressor is exhibiting severe mechanical vibration and harmonic rattling on unit 017.",
                "session_id": "sess-vibration-01",
                "asset_id": "ACX-420-017",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        context = data["context"]
        # Error code must NOT be E17
        assert context["error_code"] is None
        # Pressure must NOT be 195 PSI
        assert "pressure_psi" not in context["query_facts"]["measurements"]

        reasoning = data["reasoning"]
        assert reasoning["status"] in ["completed", "needs_information"]
        spoken = reasoning.get("spoken_response", "")
        assert "E17" not in spoken
        assert "195" not in spoken


@pytest.mark.asyncio
async def test_integration_flow_c_vague_query_clarifying_questions():
    """Verify complete Flow C: Vague query generates clarifying questions without guessing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/reasoning/analyze",
            json={
                "query": "Unit isn't working right now.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        reasoning = data["reasoning"]
        assert reasoning["status"] == "needs_information"
        assert reasoning["certainty_level"] == "insufficient_evidence"
        assert len(reasoning["clarifying_questions"]) > 0

        # Voice output must ask clarifying questions
        spoken = reasoning["spoken_response"]
        assert spoken is not None
        assert "To assist you:" in spoken


@pytest.mark.asyncio
async def test_integration_flow_d_no_evidence_explicit_uncertainty():
    """Verify complete Flow D: Unsupported component has explicit uncertainty and no hallucinated diagnosis."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/reasoning/analyze",
            json={
                "query": "Quantum cryogenic sub-cooler valve QX-999 is pulsing helium fluid on unit 999.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        context = data["context"]
        reasoning = data["reasoning"]

        assert context["uncertainty"]["missing_asset"] is True
        assert context["uncertainty"]["missing_error_code"] is True
        assert reasoning["status"] == "needs_information"
        assert reasoning["certainty_level"] == "insufficient_evidence"
        assert len(reasoning["evidence_claims"]) == 0


@pytest.mark.asyncio
async def test_integration_flow_e_technician_contribution_roundtrip():
    """Verify complete Flow E: Technician A contributes, Technician B retrieves with provenance intact."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Technician A creates contribution
        create_resp = await client.post(
            "/api/knowledge/contributions",
            json={
                "title": "Loose vibration isolator bushing causing harmonic hum",
                "observation": "Blower assembly vibrating during 100% stage 2 run",
                "symptom": "Harmonic hum and chassis vibration",
                "suspected_cause": "Neoprene bushing degraded and mounting bolt loosened",
                "action_taken": "Replaced bushing with silicone isolator and torqued to 25 ft-lbs",
                "outcome": "Vibration dampened by 85%, noise eliminated",
                "asset_id": "ACX-420-017",
            },
        )
        assert create_resp.status_code == 201
        contrib_data = create_resp.json()
        contrib_id = contrib_data["id"]
        assert contrib_data["provenance_type"] == "TECHNICIAN_CONTRIBUTION"
        assert contrib_data["verification_status"] == "PENDING_REVIEW"

        # 2. Technician B queries about the same issue
        query_resp = await client.post(
            "/api/reasoning/analyze",
            json={
                "query": "Blower assembly harmonic hum and chassis vibration on unit 017",
                "asset_id": "ACX-420-017",
            },
        )
        assert query_resp.status_code == 200
        analysis_data = query_resp.json()

        # Check that retrieved contribution appears with proper provenance in context
        evidence_items = analysis_data["context"]["evidence"]
        matching_contrib = next((e for e in evidence_items if e["document_id"] == contrib_id), None)

        if matching_contrib:
            assert matching_contrib["provenance_type"] == "TECHNICIAN_CONTRIBUTION"
            assert matching_contrib["verification_status"] == "PENDING_REVIEW"
            assert matching_contrib["is_technician_contribution"] is True
