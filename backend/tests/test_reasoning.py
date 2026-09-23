"""Comprehensive tests for Phase 4: Evidence-Grounded Reasoning Engine.

Covers:
1. Known fault reasoning (E17 regression test verifying structural properties)
2. Arbitrary non-E17 reasoning (vibration scenario)
3. Insufficient context without hallucination
4. Dynamic clarifying questions from missing info
5. Evidence citation validation
6. Unsupported claim rejection by validator
7. Safety constraint preservation (high pressure & mandatory LOTO)
8. Conflicting evidence detection and surfacing
9. Iterative context evolution over multiple turns
10. Static AST audit verifying NO hardcoded Q&A mappings
11. Mock provider dynamic execution across varied inputs
12. API endpoint POST /api/reasoning/analyze
13. Invalid reasoning fallback handling
14. Escalation behavior on critical hazards
"""

import ast
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.context.assembled_context import (
    AssembledContext,
    DetectedConflict,
    EvidenceClassification,
    EvidenceItem,
    ExtractedQueryFacts,
    RetrievalMetadata,
    SafetyContext,
    UncertaintyModel,
)
from app.context.assembler import ContextAssembler
from app.main import app
from app.models.session import ConversationTurn
from app.reasoning.models import (
    EvidenceClaim,
    ReasoningCitation,
    ReasoningMetadata,
    ReasoningResult,
    RecommendedNextStep,
)
from app.data.demo_fixtures import load_demo_knowledge_documents
from app.reasoning.provider import MockReasoningProvider
from app.reasoning.service import ReasoningService
from app.reasoning.validator import ReasoningQualityValidator
from app.retrieval.mock import MockRetrievalProvider


@pytest.fixture
def mock_retrieval():
    return MockRetrievalProvider(seed_documents=load_demo_knowledge_documents())


@pytest.fixture
def assembler(mock_retrieval):
    return ContextAssembler(retrieval_provider=mock_retrieval)


@pytest.fixture
def reasoning_service():
    return ReasoningService(provider=MockReasoningProvider())


@pytest.mark.asyncio
async def test_known_fault_reasoning_e17(assembler, reasoning_service):
    """1. Test known fault (E17) structural properties without hardcoded string equality."""
    query = "I'm getting E17 again on unit 017. Pressure is around 195 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    result, report = await reasoning_service.analyze(context)

    assert report.is_valid is True
    assert result.status == "completed"
    assert result.certainty_level in ["supported", "partially_supported"]

    # Must contain evidence claims citing real evidence
    assert len(result.evidence_claims) > 0
    valid_ids = {e.document_id for e in context.evidence} | {r.record_id for r in context.relevant_service_history}
    for claim in result.evidence_claims:
        assert len(claim.evidence_ids) > 0
        for eid in claim.evidence_ids:
            assert eid in valid_ids

    # Safety constraints preserved
    assert len(result.safety_considerations) > 0
    assert any("lockout" in s.lower() or "loto" in s.lower() or "shutdown" in s.lower() for s in result.safety_considerations)

    # Next steps must cite evidence
    assert len(result.recommended_next_steps) > 0
    for step in result.recommended_next_steps:
        assert len(step.evidence_ids) > 0


@pytest.mark.asyncio
async def test_arbitrary_non_e17_reasoning(assembler, reasoning_service):
    """2. Test arbitrary non-E17 query: no E17 assumptions, no invented diagnosis."""
    query = "The unit started vibrating immediately after yesterday's maintenance."
    context = await assembler.assemble(query=query, session_id=None)

    result, report = await reasoning_service.analyze(context)

    assert report.is_valid is True
    # Must NOT assume E17 or high pressure
    assert context.error_code != "E17"
    assert "E17" not in result.issue_summary
    assert context.query_facts.error_code is None


@pytest.mark.asyncio
async def test_insufficient_context_no_fabrication(assembler, reasoning_service):
    """3. Test insufficient context: returns needs_information with 0 fabricated diagnoses."""
    query = "Something is wrong with the machine."
    context = await assembler.assemble(query=query, session_id=None)

    result, report = await reasoning_service.analyze(context)

    assert report.is_valid is True
    assert result.status == "needs_information"
    assert result.certainty_level == "insufficient_evidence"

    # Must NOT fabricate next steps or claims
    assert len(result.evidence_claims) == 0
    assert len(result.recommended_next_steps) == 0
    # Must provide clarifying questions
    assert len(result.clarifying_questions) > 0


@pytest.mark.asyncio
async def test_clarifying_questions_generated_from_missing_info(assembler, reasoning_service):
    """4. Test dynamic clarifying questions directly address missing parameters."""
    query = "Something is wrong with the machine."
    context = await assembler.assemble(query=query, session_id=None)

    result, _ = await reasoning_service.analyze(context)

    questions_text = " ".join(result.clarifying_questions).lower()
    # Missing asset should prompt for asset/unit
    assert "asset" in questions_text or "unit" in questions_text
    # Missing error code should prompt for code/fault
    assert "code" in questions_text or "fault" in questions_text


@pytest.mark.asyncio
async def test_evidence_citation_validation(assembler, reasoning_service):
    """5. Test citations point only to real evidence chunks retrieved."""
    query = "What safety procedure applies before checking the pressure system?"
    context = await assembler.assemble(query=query, session_id=None)

    result, report = await reasoning_service.analyze(context)

    assert report.is_valid is True
    valid_ids = {e.document_id for e in context.evidence}
    assert len(result.citations) > 0
    for citation in result.citations:
        assert citation.evidence_id in valid_ids


@pytest.mark.asyncio
async def test_unsupported_claim_rejection(assembler):
    """6. Test validator rejects reasoning containing fabricated evidence IDs."""
    query = "I'm getting E17 again on unit 017."
    context = await assembler.assemble(query=query, session_id="sess-017")

    validator = ReasoningQualityValidator()

    # Construct invalid reasoning with hallucinated citation and claim
    invalid_result = ReasoningResult(
        status="completed",
        issue_summary="Test issue",
        assessment="Diagnostic assessment",
        evidence_claims=[
            EvidenceClaim(
                claim="Fabricated claim without evidence",
                evidence_ids=["hallucinated-doc-999"],
                support_level="direct",
            )
        ],
        recommended_next_steps=[],
        safety_considerations=["Perform shutdown."],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[
            ReasoningCitation(
                evidence_id="non-existent-chunk-xyz",
                source="fake_manual.md",
                document_type="manual",
                relevant_excerpt="fake excerpt",
            )
        ],
        reasoning_metadata=ReasoningMetadata(
            provider="test",
            latency_ms=1.0,
            retrieval_latency_ms=0.0,
        ),
    )

    report = validator.validate(invalid_result, context)
    assert report.is_valid is False
    assert len(report.errors) >= 2
    assert any("hallucinated-doc-999" in e for e in report.errors)
    assert any("non-existent-chunk-xyz" in e for e in report.errors)


@pytest.mark.asyncio
async def test_safety_constraint_preservation(assembler, reasoning_service):
    """7. Test elevated pressure hazard and mandatory LOTO are preserved in reasoning."""
    query = "I'm getting E17 on unit 017. Pressure is 195 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    result, report = await reasoning_service.analyze(context)

    assert report.is_valid is True
    # Safety constraints in reasoning must mention lockout/shutdown
    safety_text = " ".join(result.safety_considerations).lower()
    assert "lockout" in safety_text or "loto" in safety_text or "de-energiz" in safety_text


@pytest.mark.asyncio
async def test_conflicting_evidence_surfaced(reasoning_service):
    """8. Test conflicting evidence sets certainty to conflicting_evidence and surfaces in assessment."""
    context = AssembledContext(
        technician_query="Check compressor pressure threshold",
        query_facts=ExtractedQueryFacts(raw_query="Check compressor pressure threshold"),
        evidence=[
            EvidenceItem(
                document_id="doc-ver-1",
                source="manual_v1.md",
                document_type="manual",
                classification="technical_manual",
                text="Normal pressure limit is 185 PSI.",
                version="1.0",
            ),
            EvidenceItem(
                document_id="doc-ver-2",
                source="manual_v2.md",
                document_type="manual",
                classification="technical_manual",
                text="Normal pressure limit is 210 PSI.",
                version="2.0",
            ),
        ],
        conflicts=[
            DetectedConflict(
                conflict_type="version_mismatch",
                sources=["doc-ver-1", "doc-ver-2"],
                description="Version mismatch: 1.0 vs 2.0 pressure thresholds.",
            )
        ],
        retrieval_metadata=RetrievalMetadata(
            provider="mock",
            status="ready",
            latency_ms=0.5,
            result_count=2,
            query="Check compressor pressure threshold",
        ),
    )

    result, report = await reasoning_service.analyze(context)

    assert report.is_valid is True
    assert result.status == "conflicting_evidence"
    assert result.certainty_level == "conflicting_evidence"
    assert "conflicting" in result.assessment.lower()
    assert result.escalation.should_escalate is True


@pytest.mark.asyncio
async def test_iterative_context_evolution(assembler, reasoning_service):
    """9. Test iterative context evolution across two conversational turns."""
    # Turn 1: Vague query
    t1_query = "Something is wrong with the machine."
    ctx1 = await assembler.assemble(query=t1_query, session_id=None)
    res1, _ = await reasoning_service.analyze(ctx1)

    assert res1.status == "needs_information"
    assert len(res1.clarifying_questions) > 0

    # Turn 2: Technician provides specific detail and session context
    t2_query = "It started vibrating after maintenance on unit 017."
    ctx2 = await assembler.assemble(query=t2_query, asset_id="ACX-420-017", session_id="sess-017")
    res2, _ = await reasoning_service.analyze(ctx2)

    # Context 2 has resolved asset and history
    assert ctx2.asset_id == "ACX-420-017"
    assert len(ctx2.conversation_context) > 0
    # Status evolves beyond basic needs_information
    assert res2.status in ["completed", "partially_supported", "safety_escalation"]


def test_no_hardcoded_qa_in_reasoning_source():
    """10. Static AST audit of app/reasoning/ verifying NO hardcoded Q&A mappings exist."""
    reasoning_dir = Path(__file__).resolve().parent.parent / "app" / "reasoning"
    assert reasoning_dir.exists()

    py_files = list(reasoning_dir.glob("*.py"))
    assert len(py_files) >= 5

    for file_path in py_files:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        # Check for forbidden pattern: if query == "..." or if error_code == "..."
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test_str = ast.unparse(node.test)
                assert 'query == "E17"' not in test_str, f"Hardcoded query check in {file_path.name}: {test_str}"
                assert 'query == "e17"' not in test_str, f"Hardcoded query check in {file_path.name}: {test_str}"
                assert 'error_code == "E17"' not in test_str, f"Hardcoded error_code branch in {file_path.name}: {test_str}"
                assert 'error_code == "e17"' not in test_str, f"Hardcoded error_code branch in {file_path.name}: {test_str}"


@pytest.mark.asyncio
async def test_mock_reasoning_provider_generic_execution(assembler):
    """11. Test mock reasoning provider on arbitrary random query without crashing."""
    provider = MockReasoningProvider()
    query = "Compressor motor temperature sensor reading intermittent signal."
    context = await assembler.assemble(query=query)

    result = await provider.reason(context)
    assert result is not None
    assert result.issue_summary != ""
    assert result.certainty_level in ["supported", "partially_supported", "insufficient_evidence"]


def test_api_reasoning_analyze_endpoint():
    """12. Test POST /api/reasoning/analyze end-to-end via FastAPI TestClient."""
    client = TestClient(app)
    resp = client.post(
        "/api/reasoning/analyze",
        json={
            "query": "I am getting E17 again on unit 017. Pressure is around 195 PSI.",
            "session_id": "sess-017",
            "top_k": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "context" in data
    assert "reasoning" in data
    assert "validation_report" in data
    assert data["validation_report"]["is_valid"] is True
    assert data["reasoning"]["status"] in ["completed", "safety_escalation"]
    assert len(data["reasoning"]["evidence_claims"]) > 0


@pytest.mark.asyncio
async def test_invalid_reasoning_fallback(assembler):
    """13. Test that when provider produces invalid result, service produces a safe fallback."""
    class BuggyReasoningProvider(MockReasoningProvider):
        async def reason(self, context):
            res = await super().reason(context)
            # Inject a safety violation
            res.assessment += " It is safe to bypass lockout and open service valve under pressure."
            return res

    service = ReasoningService(provider=BuggyReasoningProvider())
    query = "I'm getting E17 on unit 017. Pressure is 195 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    result, report = await service.analyze(context)

    # Quality validator rejected it
    assert report.is_valid is False
    # Service returned safe fallback
    assert result.status == "insufficient_evidence"
    assert "rejected" in result.assessment.lower()
    assert result.escalation.should_escalate is True


@pytest.mark.asyncio
async def test_escalation_behavior(assembler, reasoning_service):
    """14. Test emergency pressure (>250 PSI) triggers safety escalation."""
    query = "Emergency pressure on unit 017 is 275 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    result, _ = await reasoning_service.analyze(context)

    assert result.status == "safety_escalation"
    assert result.escalation.should_escalate is True
    assert result.escalation.safety_reason is not None
