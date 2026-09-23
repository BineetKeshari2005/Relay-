"""Comprehensive tests for the Phase 3 Context Assembly Engine."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.context.assembler import ContextAssembler
from app.context.quality_validator import ContextQualityValidator
from app.context.query_extractor import QueryContextExtractor
from app.data.demo_fixtures import load_demo_knowledge_documents
from app.main import app
from app.retrieval.mock import MockRetrievalProvider


@pytest.fixture
def mock_assembler():
    docs = load_demo_knowledge_documents()
    provider = MockRetrievalProvider(seed_documents=docs)
    return ContextAssembler(retrieval_provider=provider)


# --- 1. Query Fact Extraction Tests ---

def test_query_fact_extraction_e17_scenario():
    extractor = QueryContextExtractor()
    facts = extractor.extract("I'm getting E17 again on unit 017. Pressure is around 195 PSI.")
    assert facts.error_code == "E17"
    assert facts.asset_reference == "unit 017"
    assert facts.measurements.get("pressure_psi") == 195.0
    assert facts.is_repeat_issue is True
    assert "elevated_pressure_reported" in facts.observations


def test_query_fact_extraction_no_hallucination():
    extractor = QueryContextExtractor()
    facts = extractor.extract("Machine is making a strange humming sound.")
    assert facts.error_code is None
    assert facts.asset_reference is None
    assert facts.measurements == {}
    assert facts.is_repeat_issue is False


# --- 2. Asset Resolution Tests ---

def test_asset_resolution(mock_assembler):
    facts_known = mock_assembler.query_extractor.extract("E17 on unit 017")
    asset, aid, resolved = mock_assembler.resolve_asset(None, facts_known)
    assert resolved is True
    assert aid == "ACX-420-017"
    assert asset is not None
    assert asset.model == "ACX-420"

    facts_unknown = mock_assembler.query_extractor.extract("E17 on compressor 99")
    asset2, aid2, resolved2 = mock_assembler.resolve_asset(None, facts_unknown)
    assert resolved2 is False
    assert aid2 is None
    assert asset2 is None


# --- 3. Deterministic Evidence Classification Tests ---

def test_evidence_classification(mock_assembler):
    assert mock_assembler.classify_evidence("service_record", "standard") == "service_history"
    assert mock_assembler.classify_evidence("maintenance_history", "standard") == "maintenance_history"
    assert mock_assembler.classify_evidence("troubleshooting_procedure", "high_pressure") == "troubleshooting"
    assert mock_assembler.classify_evidence("technical_manual", "standard") == "technical_manual"
    assert mock_assembler.classify_evidence("safety_sop", "critical") == "safety_procedure"
    assert mock_assembler.classify_evidence("other_doc", "standard") == "general_reference"


# --- 4. Complete E17 Context Assembly Scenario ---

@pytest.mark.asyncio
async def test_complete_e17_scenario_assembly(mock_assembler):
    query = "I'm getting E17 again on unit 017. Pressure is around 195 PSI."
    ctx = await mock_assembler.assemble(
        query=query,
        session_id="sess-017",
    )

    # Core Facts
    assert ctx.technician_query == query
    assert ctx.asset_id == "ACX-420-017"
    assert ctx.asset_model == "ACX-420"
    assert ctx.error_code == "E17"
    assert ctx.measurements["pressure_psi"] == 195.0

    # Structured Service History separation
    assert len(ctx.relevant_service_history) >= 1
    assert ctx.relevant_service_history[0].record_id == "SR-2026-0814-017"

    # Evidence preservation & classification
    assert len(ctx.evidence) > 0
    doc_ids = [e.document_id for e in ctx.evidence]
    assert any("e17" in did or "017" in did for did in doc_ids)

    # Safety Context
    assert ctx.safety_context.high_pressure_hazard is True
    assert ctx.safety_context.mandatory_loto is True
    assert len(ctx.safety_context.safety_warnings) > 0

    # Uncertainty
    assert ctx.uncertainty.missing_asset is False
    assert ctx.uncertainty.missing_error_code is False
    assert ctx.uncertainty.missing_measurement is False

    # Retrieval Metadata
    assert ctx.retrieval_metadata.latency_ms >= 0.0

    # Strict Invariant: No final diagnosis / treatment recommendation
    report = ContextQualityValidator().validate(ctx)
    assert report.valid is True
    assert len(report.errors) == 0


# --- 5. Follow-up Query Context Test ---

@pytest.mark.asyncio
async def test_followup_query_assembly(mock_assembler):
    query = "The pressure sensor was already replaced last month. What should I check next?"
    ctx = await mock_assembler.assemble(
        query=query,
        asset_id="ACX-420-017",
    )

    assert ctx.asset_id == "ACX-420-017"
    assert len(ctx.relevant_service_history) >= 1
    # Check that it extracted past sensor replacement observation
    assert "past_sensor_replacement_referenced" in ctx.observations
    # Check that it flags missing error code or measurements since they were not in the query
    assert ctx.uncertainty.missing_error_code is True

    # Validates cleanly
    report = ContextQualityValidator().validate(ctx)
    assert report.valid is True


# --- 6. Safety Query Context Test ---

@pytest.mark.asyncio
async def test_safety_query_assembly(mock_assembler):
    query = "What safety procedure applies before checking the pressure system?"
    ctx = await mock_assembler.assemble(query=query)

    # Evidence includes safety SOP
    has_safety_evidence = any(e.classification == "safety_procedure" for e in ctx.evidence)
    assert has_safety_evidence is True
    assert ctx.safety_context.mandatory_loto is True


# --- 7. Missing Information and Uncertainty Detection ---

@pytest.mark.asyncio
async def test_missing_information_detection(mock_assembler):
    # Vague query without asset or measurements
    query = "Unit has tripped."
    ctx = await mock_assembler.assemble(query=query)

    assert ctx.uncertainty.missing_asset is True
    assert ctx.uncertainty.missing_error_code is True
    assert len(ctx.missing_information) >= 2


# --- 8. Context Quality Validator Tests ---

def test_quality_validator_catches_invalid_context():
    validator = ContextQualityValidator()
    # Create empty mock context
    docs = load_demo_knowledge_documents()
    assembler = ContextAssembler(retrieval_provider=MockRetrievalProvider(seed_documents=docs))
    
    # Assembly with empty query should fail validation
    import asyncio
    ctx = asyncio.run(assembler.assemble(query="   "))
    report = validator.validate(ctx)
    assert report.valid is False
    assert any("Technician query is missing or empty" in e for e in report.errors)


# --- 9. Conflict Detection and Retrieval Metadata Tests ---

def test_conflict_detection_version_mismatch(mock_assembler):
    from app.context.assembled_context import EvidenceItem
    evidence = [
        EvidenceItem(
            document_id="doc-v1",
            source="manual_v1.md",
            document_type="manual",
            classification="technical_manual",
            text="Operating limit 185 PSI",
            version="1.0",
        ),
        EvidenceItem(
            document_id="doc-v2",
            source="manual_v2.md",
            document_type="manual",
            classification="technical_manual",
            text="Operating limit 190 PSI",
            version="2.0",
        ),
    ]
    conflicts = mock_assembler.detect_conflicts(evidence)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "version_mismatch"
    assert "doc-v1" in conflicts[0].sources
    assert "doc-v2" in conflicts[0].sources


@pytest.mark.asyncio
async def test_retrieval_metadata_preservation(mock_assembler):
    ctx = await mock_assembler.assemble("E17 high pressure")
    assert ctx.retrieval_metadata.provider == "mock-retrieval"
    assert ctx.retrieval_metadata.status == "ready"
    assert ctx.retrieval_metadata.latency_ms >= 0.0
    assert ctx.retrieval_metadata.result_count == len(ctx.evidence)
    assert ctx.retrieval_metadata.query == "E17 high pressure"


# --- 10. REST API Endpoint Tests ---

@pytest.mark.asyncio
async def test_api_context_assemble_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "query": "I'm getting E17 again on unit 017. Pressure is around 195 PSI.",
            "session_id": "sess-017",
            "top_k": 3,
        }
        resp = await client.post("/api/context/assemble", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert "context" in data
        assert "quality_report" in data
        assert data["quality_report"]["valid"] is True

        ctx = data["context"]
        assert ctx["asset_id"] == "ACX-420-017"
        assert ctx["error_code"] == "E17"
        assert ctx["measurements"]["pressure_psi"] == 195.0
        assert len(ctx["relevant_service_history"]) >= 1
        assert len(ctx["evidence"]) <= 3
        assert ctx["safety_context"]["high_pressure_hazard"] is True
        assert "project_key" not in str(data)
        assert "api_key" not in str(data)


