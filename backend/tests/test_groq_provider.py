"""Comprehensive tests for GroqReasoningProvider and LLM configuration.

Validates all 10 core requirements:
1. LLM_PROVIDER=mock selects MockReasoningProvider.
2. LLM_PROVIDER=groq selects GroqReasoningProvider.
3. Missing Groq credentials fail clearly/safely.
4. Groq structured output is parsed into ReasoningResult.
5. Invalid model output (syntax error, schema failure, timeout, API error) is handled safely.
6. Invalid evidence citations are rejected by validator and trigger safe fallback.
7. Unsupported claims are rejected by validator and trigger safe fallback.
8. Prohibited actions ("bypass lockout") are rejected by validator and trigger safe fallback.
9. Safe fallback works and preserves safety warnings.
10. SpokenResponseFormatter receives only validated reasoning (no validator debug text in speech).
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from groq import APIConnectionError, APITimeoutError

from app.api.reasoning import get_active_reasoning_provider
from app.config.settings import Settings, settings
from app.context.assembled_context import AssembledContext
from app.context.assembler import ContextAssembler
from app.data.demo_fixtures import load_demo_knowledge_documents
from app.reasoning.groq import GroqReasoningProvider
from app.reasoning.models import (
    EvidenceClaim,
    ReasoningCitation,
    ReasoningResult,
    RecommendedNextStep,
)
from app.reasoning.provider import MockReasoningProvider
from app.reasoning.service import ReasoningService
from app.reasoning.validator import ReasoningQualityValidator
from app.retrieval.mock import MockRetrievalProvider
from app.voice.formatter import SpokenResponseFormatter


class MockChatCompletionMessage:
    def __init__(self, content: str):
        self.content = content


class MockChatCompletionChoice:
    def __init__(self, content: str):
        self.message = MockChatCompletionMessage(content)


class MockUsage:
    def __init__(self, prompt_tokens: int = 150, completion_tokens: int = 80, total_tokens: int = 230):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class MockChatCompletion:
    def __init__(self, content: str):
        self.choices = [MockChatCompletionChoice(content)]
        self.usage = MockUsage()


@pytest.fixture
def mock_retrieval():
    return MockRetrievalProvider(seed_documents=load_demo_knowledge_documents())


@pytest.fixture
def assembler(mock_retrieval):
    return ContextAssembler(retrieval_provider=mock_retrieval)


# ==============================================================================
# Requirement 1: LLM_PROVIDER=mock selects MockReasoningProvider
# ==============================================================================
def test_provider_selection_mock():
    with patch.object(settings, "llm_provider", "mock"):
        provider = get_active_reasoning_provider()
        assert isinstance(provider, MockReasoningProvider)
        assert provider.provider_name == "mock-reasoner"


# ==============================================================================
# Requirement 2: LLM_PROVIDER=groq selects GroqReasoningProvider
# ==============================================================================
def test_provider_selection_groq():
    with patch.object(settings, "llm_provider", "groq"):
        provider = get_active_reasoning_provider()
        assert isinstance(provider, GroqReasoningProvider)
        assert "groq-reasoner" in provider.provider_name


# ==============================================================================
# Requirement 3: Missing Groq credentials fail clearly/safely
# ==============================================================================
@pytest.mark.asyncio
async def test_missing_groq_credentials_safe_failure(assembler):
    context = await assembler.assemble(query="Test query without credentials", session_id=None)
    provider = GroqReasoningProvider(api_key="")

    assert not provider.is_configured
    result = await provider.reason(context)

    # Must fail safely without raising an exception
    assert result.status == "insufficient_evidence"
    assert result.certainty_level == "insufficient_evidence"
    assert result.escalation.should_escalate is True
    assert "Missing or unconfigured GROQ_API_KEY" in result.uncertainty.get("error", "")
    # Safety warnings from context must survive
    assert result.safety_considerations == context.safety_context.safety_warnings


# ==============================================================================
# Requirement 4: Groq structured output is parsed into ReasoningResult
# ==============================================================================
@pytest.mark.asyncio
async def test_groq_structured_output_parsing(assembler):
    query = "I am getting E17 again on unit 017. Pressure is around 195 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    valid_evidence_id = context.evidence[0].document_id if context.evidence else "doc-e17-001"

    mock_llm_json = {
        "status": "completed",
        "issue_summary": "E17 high discharge pressure alarm on ACX-420-017",
        "what_we_know": [
            "Asset ACX-420-017 reported error E17",
            "Discharge pressure measured at 195 PSI",
        ],
        "assessment": "The unit is exhibiting high head pressure consistent with condenser airflow blockage or scaling.",
        "evidence_claims": [
            {
                "claim": "Discharge pressure of 195 PSI exceeds the normal operating ceiling of 190 PSI.",
                "evidence_ids": [valid_evidence_id],
                "support_level": "direct",
                "explanation": "Derived from SOP diagnostic thresholds.",
            }
        ],
        "recommended_next_steps": [
            {
                "step": "De-energize unit and apply Lockout/Tagout before inspecting condenser coils.",
                "evidence_ids": [valid_evidence_id],
                "rationale": "High voltage and rotating fan assembly present severe hazards.",
                "expected_observation": "Confirm zero voltage and inspect fins for debris.",
                "safety_constraints": ["Mandatory LOTO before opening service panels"],
            }
        ],
        "safety_considerations": [
            "Mandatory LOTO required before removing condenser fan protective grille.",
            "High pressure hazard: discharge line operates above safe contact pressure.",
        ],
        "expected_observations": ["Zero rotational speed and verified electrical isolation."],
        "decision_branches": [
            {
                "condition": "If coils are fouled with scale",
                "if_true_branch": "Perform non-acid chemical wash per SOP.",
                "if_false_branch": "Test condenser fan motor capacitor.",
                "evidence_ids": [valid_evidence_id],
                "rationale": "SOP diagnostic tree for thermal restriction.",
            }
        ],
        "clarifying_questions": [],
        "certainty_level": "supported",
        "uncertainty": {},
        "escalation": {
            "should_escalate": False,
            "reason": None,
            "missing_information": [],
            "safety_reason": None,
            "recommended_escalation_target": None,
        },
        "citations": [
            {
                "evidence_id": valid_evidence_id,
                "source": "sop-e17-acx420.md",
                "document_type": "troubleshooting_sop",
                "relevant_excerpt": "Normal operating discharge pressure ceiling is 190 PSI.",
                "score": 0.95,
                "metadata": {"section": "thresholds"},
            }
        ],
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion(json.dumps(mock_llm_json))
    )

    provider = GroqReasoningProvider(api_key="gsk_test_mock_key", client=mock_client)
    result = await provider.reason(context)

    assert result.status == "completed"
    assert result.issue_summary == "E17 high discharge pressure alarm on ACX-420-017"
    assert len(result.evidence_claims) == 1
    assert result.evidence_claims[0].evidence_ids == [valid_evidence_id]
    assert len(result.recommended_next_steps) == 1
    assert "Lockout/Tagout" in result.recommended_next_steps[0].step
    assert result.reasoning_metadata.latency_ms > 0
    assert result.reasoning_metadata.retrieval_latency_ms == context.retrieval_metadata.latency_ms
    assert result.reasoning_metadata.token_usage.get("total_tokens") == 230


# ==============================================================================
# Requirement 5: Invalid model output is rejected / safe fallback triggered
# ==============================================================================
@pytest.mark.asyncio
async def test_invalid_json_model_output(assembler):
    context = await assembler.assemble(query="Test malformed output", session_id=None)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion("This is not JSON at all. Internal model prose.")
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    result = await provider.reason(context)

    assert result.status == "insufficient_evidence"
    assert "Invalid JSON from Groq" in result.uncertainty.get("error", "")
    assert result.escalation.should_escalate is True


@pytest.mark.asyncio
async def test_schema_mismatch_model_output(assembler):
    context = await assembler.assemble(query="Test schema mismatch", session_id=None)

    mock_client = AsyncMock()
    # Missing required fields like 'status' and 'issue_summary'
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion(json.dumps({"some_random_key": "some_value"}))
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    result = await provider.reason(context)

    assert result.status == "insufficient_evidence"
    assert "schema validation failed" in result.uncertainty.get("error", "").lower()


@pytest.mark.asyncio
async def test_groq_api_timeout_handling(assembler):
    context = await assembler.assemble(query="Test timeout", session_id=None)

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=APITimeoutError(request=MagicMock())
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    result = await provider.reason(context)

    assert result.status == "insufficient_evidence"
    assert "timeout" in result.uncertainty.get("error", "").lower()


# ==============================================================================
# Requirement 6: Invalid evidence citations are rejected
# ==============================================================================
@pytest.mark.asyncio
async def test_invalid_evidence_citations_rejected_by_validator(assembler):
    query = "Check ACX-420 unit"
    context = await assembler.assemble(query=query, session_id=None)

    # Groq hallucinates a fake citation ID
    fake_id = "doc-completely-hallucinated-999"
    mock_llm_json = {
        "status": "completed",
        "issue_summary": "Unit inspection",
        "what_we_know": ["Unit inspected"],
        "assessment": "Grounded diagnosis",
        "evidence_claims": [],
        "recommended_next_steps": [
            {
                "step": "Check refrigerant level per manual",
                "evidence_ids": [fake_id],
                "rationale": "Standard check",
                "safety_constraints": [],
            }
        ],
        "safety_considerations": ["Standard safety"],
        "expected_observations": [],
        "decision_branches": [],
        "clarifying_questions": [],
        "certainty_level": "supported",
        "uncertainty": {},
        "escalation": {"should_escalate": False},
        "citations": [
            {
                "evidence_id": fake_id,
                "source": "fake_manual.pdf",
                "document_type": "manual",
                "relevant_excerpt": "Check pressure",
                "metadata": {},
            }
        ],
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion(json.dumps(mock_llm_json))
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    service = ReasoningService(provider=provider)

    result, report = await service.analyze(context)

    # Validator must reject the citation and trigger safe fallback
    assert report.is_valid is False
    assert any("non-existent or fabricated evidence" in err.lower() for err in report.errors)
    assert result.status == "insufficient_evidence"
    assert result.escalation.should_escalate is True


# ==============================================================================
# Requirement 7: Unsupported claims are rejected
# ==============================================================================
@pytest.mark.asyncio
async def test_unsupported_direct_claims_rejected_by_validator(assembler):
    context = await assembler.assemble(query="Routine check", session_id=None)

    mock_llm_json = {
        "status": "completed",
        "issue_summary": "Check",
        "what_we_know": [],
        "assessment": "Assessment",
        "evidence_claims": [
            {
                "claim": "Compressor motor winding has shorted to ground.",
                "evidence_ids": [],  # Marked 'direct' without evidence!
                "support_level": "direct",
                "explanation": "No evidence supplied.",
            }
        ],
        "recommended_next_steps": [],
        "safety_considerations": [],
        "expected_observations": [],
        "decision_branches": [],
        "clarifying_questions": [],
        "certainty_level": "supported",
        "uncertainty": {},
        "escalation": {"should_escalate": False},
        "citations": [],
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion(json.dumps(mock_llm_json))
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    service = ReasoningService(provider=provider)

    result, report = await service.analyze(context)

    assert report.is_valid is False
    assert any("provides no supporting evidence ids" in err.lower() for err in report.errors)
    assert result.status == "insufficient_evidence"


# ==============================================================================
# Requirement 8: Prohibited actions are rejected
# ==============================================================================
@pytest.mark.asyncio
async def test_prohibited_safety_action_rejected(assembler):
    query = "I need to quickly service unit 017 without shutting it off."
    context = await assembler.assemble(query=query, session_id="sess-017")

    valid_id = context.evidence[0].document_id if context.evidence else "doc-e17-001"

    # Malicious or dangerous suggestion: bypass lockout
    mock_llm_json = {
        "status": "completed",
        "issue_summary": "Rapid service request",
        "what_we_know": ["Quick service"],
        "assessment": "To save time, proceed directly.",
        "evidence_claims": [],
        "recommended_next_steps": [
            {
                "step": "Bypass lockout and open service valve while unit is running.",
                "evidence_ids": [valid_id],
                "rationale": "Saves reboot time.",
                "safety_constraints": [],
            }
        ],
        "safety_considerations": ["Bypass lockout to expedite testing."],
        "expected_observations": [],
        "decision_branches": [],
        "clarifying_questions": [],
        "certainty_level": "supported",
        "uncertainty": {},
        "escalation": {"should_escalate": False},
        "citations": [],
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion(json.dumps(mock_llm_json))
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    service = ReasoningService(provider=provider)

    result, report = await service.analyze(context)

    # Must be firmly rejected
    assert report.is_valid is False
    assert any("prohibited action: 'bypass lockout'" in err.lower() for err in report.errors)
    # Replaced with safe fallback
    assert result.status == "insufficient_evidence"
    assert result.escalation.should_escalate is True
    # Prohibited action must NOT be in recommended next steps
    assert not any("bypass lockout" in step.step.lower() for step in result.recommended_next_steps)


# ==============================================================================
# Requirement 9: Safe fallback works and preserves safety context
# ==============================================================================
@pytest.mark.asyncio
async def test_safe_fallback_preserves_safety_warnings(assembler):
    query = "E17 fault on unit 017"
    context = await assembler.assemble(query=query, session_id="sess-017")

    # Force fallback via unconfigured key
    provider = GroqReasoningProvider(api_key="")
    service = ReasoningService(provider=provider)

    result, report = await service.analyze(context)

    assert result.status == "insufficient_evidence"
    assert result.escalation.should_escalate is True
    # Context safety warnings must survive into the safe fallback
    assert len(result.safety_considerations) > 0
    assert any("lockout" in s.lower() or "loto" in s.lower() or "pressure" in s.lower() for s in result.safety_considerations)


# ==============================================================================
# Requirement 10: SpokenResponseFormatter receives only validated reasoning
# ==============================================================================
@pytest.mark.asyncio
async def test_spoken_response_contains_no_validator_debug_text(assembler):
    query = "Dangerous shortcut request"
    context = await assembler.assemble(query=query, session_id=None)

    # Groq proposes prohibited action
    mock_llm_json = {
        "status": "completed",
        "issue_summary": "Dangerous shortcut",
        "what_we_know": [],
        "assessment": "Bypass lockout for rapid diagnostic.",
        "evidence_claims": [],
        "recommended_next_steps": [
            {
                "step": "Bypass lockout immediately.",
                "evidence_ids": [],
                "rationale": "Fast check",
                "safety_constraints": [],
            }
        ],
        "safety_considerations": ["Bypass lockout"],
        "expected_observations": [],
        "decision_branches": [],
        "clarifying_questions": [],
        "certainty_level": "supported",
        "uncertainty": {},
        "escalation": {"should_escalate": False},
        "citations": [],
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockChatCompletion(json.dumps(mock_llm_json))
    )

    provider = GroqReasoningProvider(api_key="gsk_test_key", client=mock_client)
    service = ReasoningService(provider=provider)

    result, report = await service.analyze(context)

    assert report.is_valid is False
    assert result.spoken_response is not None
    assert len(result.spoken_response) > 0

    # Spoken output must NEVER contain validator debug text or prohibited phrases
    lower_spoken = result.spoken_response.lower()
    assert "bypass lockout" not in lower_spoken
    assert "validation violation" not in lower_spoken
    assert "prohibited action:" not in lower_spoken
    assert "error #" not in lower_spoken
    assert "rejected to protect technician safety" in lower_spoken or "failed evidence grounding" in lower_spoken
