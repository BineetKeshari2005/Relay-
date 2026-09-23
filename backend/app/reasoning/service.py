"""Reasoning Service orchestrating provider execution, quality validation, and safe fallback handling."""

from typing import Optional, Tuple

from app.context.assembled_context import AssembledContext
from app.reasoning.base import ReasoningProvider
from app.reasoning.models import (
    EscalationAssessment,
    ReasoningMetadata,
    ReasoningResult,
)
from app.reasoning.validator import ReasoningQualityValidator, ReasoningValidationReport
from app.voice.formatter import SpokenResponseFormatter


class ReasoningService:
    """
    Coordinates reasoning execution and enforces strict evidence/safety gating.

    Pipeline:
    AssembledContext -> ReasoningProvider -> ReasoningQualityValidator -> Final Result (or safe fallback)
    """

    def __init__(
        self,
        provider: ReasoningProvider,
        validator: Optional[ReasoningQualityValidator] = None,
    ):
        self.provider = provider
        self.validator = validator or ReasoningQualityValidator()

    async def analyze(
        self,
        context: AssembledContext,
    ) -> Tuple[ReasoningResult, ReasoningValidationReport]:
        """
        Execute end-to-end reasoning over context, validate output, and return validated result.
        Rejects invalid or ungrounded responses and produces a safe structured failure.
        """
        raw_result = await self.provider.reason(context)
        report = self.validator.validate(raw_result, context)

        if not report.is_valid:
            # Build safe structured failure response
            fallback_result = ReasoningResult(
                status="insufficient_evidence",
                issue_summary=f"Reported issue: '{context.technician_query}'",
                what_we_know=[f"Technician query: '{context.technician_query}'"],
                assessment=(
                    "The generated diagnostic recommendation failed evidence grounding or safety validation "
                    "and was rejected to protect technician safety. "
                    "Please provide verified equipment details or escalate to a senior technician."
                ),
                evidence_claims=[],
                recommended_next_steps=[],
                safety_considerations=context.safety_context.safety_warnings,
                expected_observations=[],
                decision_branches=[],
                clarifying_questions=(
                    context.missing_information
                    if context.missing_information
                    else [
                        "Could you specify the exact equipment asset identifier?",
                        "What diagnostic trouble code or fault message is active?",
                        "What physical measurements (pressure, temperature) have been taken?",
                    ]
                ),
                certainty_level="insufficient_evidence",
                uncertainty={"validation_errors": report.errors},
                escalation=EscalationAssessment(
                    should_escalate=True,
                    reason="Generated reasoning failed safety or evidence validation check.",
                    recommended_escalation_target="Field Service Supervisor / Lead Technician",
                ),
                citations=[],
                reasoning_metadata=ReasoningMetadata(
                    provider=self.provider.provider_name,
                    latency_ms=raw_result.reasoning_metadata.latency_ms,
                    retrieval_latency_ms=context.retrieval_metadata.latency_ms,
                    model_name="validation-fallback",
                ),
            )
            fallback_result.spoken_response = SpokenResponseFormatter.format(fallback_result)
            return fallback_result, report

        raw_result.spoken_response = SpokenResponseFormatter.format(raw_result)
        return raw_result, report
