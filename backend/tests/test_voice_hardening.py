"""Regression and hardening test suite for SpokenResponseFormatter.

Specifically verifies:
1. Rejection of metadata lines (e.g. 'Model Scope', 'Document ID', 'NOTICE', 'Target Subsystem').
2. Selection of genuine actionable steps.
3. Safety-first prioritization.
4. Needs-information clarifying questions.
5. Non-authoritative contribution indicator.
6. Zero leakage of file extensions, JSON tokens, or scores into speech.
"""

import pytest
from app.reasoning.models import (
    ReasoningCitation,
    ReasoningMetadata,
    ReasoningResult,
    RecommendedNextStep,
)
from app.voice.formatter import SpokenResponseFormatter


def test_spoken_formatter_rejects_model_scope_and_metadata():
    """Verify that 'Model Scope', 'Document ID', and headers are rejected and a subsequent actionable step is selected."""
    result = ReasoningResult(
        status="completed",
        issue_summary="High pressure test",
        what_we_know=["Unit 017 reported high pressure."],
        assessment="Assessment for ACX-420-017 indicates elevated discharge pressure.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Step 1: **Model Scope**: CoolCore ACX-420 Series",
                evidence_ids=["e17-sop"],
                rationale="Header line",
            ),
            RecommendedNextStep(
                step="Step 2: > **NOTICE**: Fictional demo dataset for testing",
                evidence_ids=["e17-sop"],
                rationale="Disclaimer block",
            ),
            RecommendedNextStep(
                step="Step 3: Document ID: SOP-ACX420-E17 Rev 3.0",
                evidence_ids=["e17-sop"],
                rationale="Doc ID line",
            ),
            RecommendedNextStep(
                step="Step 4: Prior to inspecting condenser fan deck, switch the unit disconnect switch to the OFF position.",
                evidence_ids=["e17-sop"],
                rationale="Procedural action",
            ),
        ],
        safety_considerations=["Mandatory Lockout/Tagout (LOTO) required before physical inspection."],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[
            ReasoningCitation(
                evidence_id="e17-sop",
                source="e17_troubleshooting_procedure.md",
                document_type="troubleshooting",
                relevant_excerpt="Standard operating procedure text.",
                score=0.95,
            )
        ],
        reasoning_metadata=ReasoningMetadata(
            provider="mock",
            latency_ms=1.2,
            retrieval_latency_ms=0.8,
        ),
    )

    spoken = SpokenResponseFormatter.format(result)

    # 1. Critical safety MUST be first
    assert spoken.startswith("Warning: Mandatory Lockout/Tagout (LOTO) required before physical inspection.")

    # 2. Must NOT contain metadata disqualifiers
    assert "Model Scope" not in spoken
    assert "model scope" not in spoken.lower()
    assert "NOTICE" not in spoken
    assert "Document ID" not in spoken
    assert "e17_troubleshooting_procedure.md" not in spoken
    assert "e17-sop" not in spoken
    assert "0.95" not in spoken

    # 3. Must select Step 4 (the first genuine actionable step)
    assert "Recommended next step: Prior to inspecting condenser fan deck, switch the unit disconnect switch to the OFF position." in spoken


def test_spoken_formatter_all_metadata_steps_graceful():
    """Verify that if all steps in the list are metadata, none are spoken and it degrades cleanly."""
    result = ReasoningResult(
        status="completed",
        issue_summary="Metadata test",
        what_we_know=[],
        assessment="Diagnostic check completed.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Step 1: **Model Scope**: CoolCore ACX-420 Series",
                evidence_ids=["doc1"],
                rationale="Header line",
            ),
            RecommendedNextStep(
                step="Step 2: Document ID: SOP-1234",
                evidence_ids=["doc1"],
                rationale="Doc ID line",
            ),
        ],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="supported",
        citations=[],
        reasoning_metadata=ReasoningMetadata(provider="mock", latency_ms=1.0, retrieval_latency_ms=0.5),
    )

    spoken = SpokenResponseFormatter.format(result)
    assert "Model Scope" not in spoken
    assert "Document ID" not in spoken
    assert spoken == "Diagnostic check completed."


def test_spoken_formatter_clarifying_questions_spoken_directly():
    """Verify that when status is needs_information, clarifying questions are voiced clearly."""
    result = ReasoningResult(
        status="needs_information",
        issue_summary="Vague query",
        what_we_know=[],
        assessment="Context is insufficient to formulate diagnosis.",
        evidence_claims=[],
        recommended_next_steps=[],
        safety_considerations=["Caution: High voltage circuit breaker present."],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[
            "Which equipment asset or unit identifier are you currently inspecting?",
            "What diagnostic trouble code is active?",
        ],
        certainty_level="insufficient_evidence",
        citations=[],
        reasoning_metadata=ReasoningMetadata(provider="mock", latency_ms=1.0, retrieval_latency_ms=0.5),
    )

    spoken = SpokenResponseFormatter.format(result)
    assert spoken.startswith("Caution: High voltage circuit breaker present.")
    assert "To assist you: Which equipment asset or unit identifier are you currently inspecting, and what diagnostic trouble code is active?" in spoken


def test_spoken_formatter_non_authoritative_contribution_notice():
    """Verify that if citation is a technician contribution, non-authoritative disclaimer is appended."""
    result = ReasoningResult(
        status="completed",
        issue_summary="Field observation test",
        what_we_know=[],
        assessment="Assessment points to potential biological blockage.",
        evidence_claims=[],
        recommended_next_steps=[
            RecommendedNextStep(
                step="Step 1: Inspect P-trap for biological algae growth and clear drain line.",
                evidence_ids=["contrib-01"],
                rationale="Field observation inspection",
            )
        ],
        safety_considerations=[],
        expected_observations=[],
        decision_branches=[],
        clarifying_questions=[],
        certainty_level="partially_supported",
        citations=[
            ReasoningCitation(
                evidence_id="contrib-01",
                source="Technician observation report",
                document_type="technician_contribution",
                relevant_excerpt="P-trap clogged with algae.",
                metadata={"provenance_type": "TECHNICIAN_CONTRIBUTION", "verification_status": "PENDING_REVIEW"},
            )
        ],
        reasoning_metadata=ReasoningMetadata(provider="mock", latency_ms=1.0, retrieval_latency_ms=0.5),
    )

    spoken = SpokenResponseFormatter.format(result)
    assert "Recommended next step: Inspect P-trap for biological algae growth and clear drain line." in spoken
    assert spoken.endswith("Note: this guidance references pending field observations.")
