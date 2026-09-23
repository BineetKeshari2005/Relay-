"""Groq reasoning provider implementing evidence-grounded inference behind ReasoningProvider interface."""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from groq import APIConnectionError, APIError, APITimeoutError, AsyncGroq
from pydantic import ValidationError

from app.config.settings import settings
from app.context.assembled_context import AssembledContext
from app.reasoning.base import ReasoningProvider
from app.reasoning.models import (
    CertaintyLevel,
    DecisionBranch,
    EscalationAssessment,
    EvidenceClaim,
    ReasoningCitation,
    ReasoningMetadata,
    ReasoningResult,
    ReasoningStatus,
    RecommendedNextStep,
    SupportLevel,
)
from app.reasoning.prompts import build_reasoning_prompt

logger = logging.getLogger(__name__)

GROQ_SYSTEM_PROMPT = """You are the reasoning layer of Relay, a decision-support copilot for field HVAC technicians.

CRITICAL INVARIANTS:
1. Grounding & Evidence:
   - You must reason ONLY over the supplied AssembledContext and retrieved evidence from Moss.
   - Do NOT search the internet or invent operational knowledge.
   - Do NOT invent measurements, asset history, documents, citations, safety thresholds, technical specifications, or procedures.
   - Every substantive claim in evidence_claims must cite actual evidence IDs present in the supplied context.
   - Every citation in citations must reference an actual evidence_id from the RETRIEVED TECHNICAL EVIDENCE (e.g. 'doc-e17-001', 'doc-loto-001') or a record_id from HISTORICAL WORK ORDERS. Never invent or guess an evidence ID.

2. Uncertainty & Insufficient Evidence:
   - If the query is vague, missing required information, or the retrieved evidence is insufficient:
     * Set status to "needs_information" or "insufficient_evidence".
     * Set certainty_level to "insufficient_evidence".
     * In clarifying_questions, provide targeted questions asking the technician for missing parameters (e.g. unit ID, exact error code, gauge pressure).
     * In uncertainty, explicitly track what is missing.
     * Do NOT fabricate a diagnosis or procedure when evidence is missing.

3. Mandatory Safety & Prohibited Actions:
   - Safety constraints provided in the context are mandatory and authoritative.
   - Preserve all safety warnings in safety_considerations.
   - If mandatory LOTO or high-pressure hazard is present, you MUST explicitly mandate Lockout/Tagout (LOTO), shutdown, or de-energization in recommended_next_steps before any physical service.
   - NEVER recommend prohibited actions such as "bypass lockout", "bypass LOTO", "ignore interlock", "without depressurizing", or "without lockout".

4. Evidence Conflicts:
   - If evidence conflicts, represent the conflict explicitly rather than silently choosing unsupported information.
   - Set status to "conflicting_evidence" or "needs_information".

5. Technician Contributions:
   - Technician-contributed knowledge is NOT equivalent to verified company knowledge.
   - If evidence is classified as technician_contribution or PENDING_REVIEW, treat it as unverified field observation, NEVER as an approved SOP or official manufacturer standard.

6. Procedural Actions:
   - Document metadata headers, such as '**Model Scope:**', 'Document ID:', 'Classification:', or section titles, are NOT procedural actions.
   - Do NOT put metadata headers into recommended_next_steps.
   - Every step in recommended_next_steps MUST be a concrete physical inspection, measurement, or diagnostic action.

OUTPUT FORMAT:
You MUST return a valid JSON object strictly adhering to this schema:
{
  "status": "completed" | "insufficient_evidence" | "needs_information" | "conflicting_evidence" | "safety_escalation",
  "issue_summary": string,
  "what_we_know": [string],
  "assessment": string,
  "evidence_claims": [
    {
      "claim": string,
      "evidence_ids": [string],
      "support_level": "direct" | "inferred" | "insufficient",
      "explanation": string | null
    }
  ],
  "recommended_next_steps": [
    {
      "step": string,
      "evidence_ids": [string],
      "rationale": string,
      "expected_observation": string | null,
      "safety_constraints": [string]
    }
  ],
  "safety_considerations": [string],
  "expected_observations": [string],
  "decision_branches": [
    {
      "condition": string,
      "if_true_branch": string,
      "if_false_branch": string | null,
      "evidence_ids": [string],
      "rationale": string | null
    }
  ],
  "clarifying_questions": [string],
  "certainty_level": "supported" | "partially_supported" | "insufficient_evidence" | "conflicting_evidence",
  "uncertainty": object,
  "escalation": {
    "should_escalate": boolean,
    "reason": string | null,
    "missing_information": [string],
    "safety_reason": string | null,
    "recommended_escalation_target": string | null
  },
  "citations": [
    {
      "evidence_id": string,
      "source": string,
      "document_type": string,
      "relevant_excerpt": string,
      "score": number | null,
      "metadata": object
    }
  ]
}
"""


class GroqReasoningProvider(ReasoningProvider):
    """
    Production reasoning provider utilizing Groq's high-speed inference engine.
    Strictly grounded in AssembledContext and retrieved Moss evidence.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[AsyncGroq] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.groq_api_key
        self.model = model if model is not None else settings.groq_model
        if client is not None:
            self._client = client
        elif self.is_configured:
            self._client = AsyncGroq(
                api_key=self.api_key,
                base_url=settings.groq_base_url,
                timeout=settings.groq_timeout_seconds,
            )
        else:
            self._client = None

    @property
    def provider_name(self) -> str:
        return f"groq-reasoner:{self.model}"

    @property
    def is_configured(self) -> bool:
        """Check whether valid Groq credentials are available."""
        return bool(
            self.api_key
            and self.api_key.strip()
            and not self.api_key.startswith("your_")
        )

    def _build_safe_fallback(
        self,
        context: AssembledContext,
        elapsed_ms: float,
        error_reason: str,
        escalation_target: str = "Field Service Lead / Dispatcher",
    ) -> ReasoningResult:
        """Create a safe structured fallback response when Groq is unconfigured or encounters an error."""
        clarifying_questions = (
            context.missing_information
            if context.missing_information
            else [
                "Could you specify the exact equipment asset identifier?",
                "What diagnostic trouble code or fault message is active?",
                "What physical measurements (pressure, temperature) have been taken?",
            ]
        )

        return ReasoningResult(
            status="insufficient_evidence",
            issue_summary=f"Reported issue: '{context.technician_query}'",
            what_we_know=[f"Technician query: '{context.technician_query}'"],
            assessment=(
                "Automated reasoning could not be completed safely. "
                "Please review verified standard operating procedures or consult a senior technician."
            ),
            evidence_claims=[],
            recommended_next_steps=[],
            safety_considerations=context.safety_context.safety_warnings,
            expected_observations=[],
            decision_branches=[],
            clarifying_questions=clarifying_questions,
            certainty_level="insufficient_evidence",
            uncertainty={
                "error": error_reason,
                "missing_information": context.missing_information,
            },
            escalation=EscalationAssessment(
                should_escalate=True,
                reason=f"Reasoning provider fallback triggered: {error_reason}",
                recommended_escalation_target=escalation_target,
            ),
            citations=[],
            reasoning_metadata=ReasoningMetadata(
                provider=self.provider_name,
                latency_ms=elapsed_ms,
                retrieval_latency_ms=context.retrieval_metadata.latency_ms,
                model_name=self.model,
            ),
        )

    def _sanitize_steps(self, raw_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out model scope or document metadata headers that might leak into procedural steps."""
        sanitized = []
        metadata_prefixes = (
            "**model scope", "model scope", "document id", "safety classification",
            "target subsystem", "version", "date:", "author:", "sop-"
        )
        for s in raw_steps:
            step_text = str(s.get("step", "")).strip()
            lower_text = step_text.lower()
            if any(lower_text.startswith(p) for p in metadata_prefixes):
                continue
            if len(step_text) < 10:
                continue
            sanitized.append(s)
        return sanitized

    async def reason(self, context: AssembledContext) -> ReasoningResult:
        """
        Execute evidence-grounded reasoning over AssembledContext using Groq LLM.

        Flow:
        1. Verify Groq credentials (fail safely if missing).
        2. Format AssembledContext into structured reasoning prompt.
        3. Request JSON object completion from Groq model.
        4. Validate JSON payload against Pydantic ReasoningResult schema.
        5. Record inference latency and preserve Moss retrieval latency.
        """
        start_time = time.perf_counter()

        # 1. Check credentials
        if not self.is_configured or self._client is None:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning("Groq reasoning invoked without valid GROQ_API_KEY. Returning safe fallback.")
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason="Missing or unconfigured GROQ_API_KEY",
            )

        # 2. Build structured prompt
        user_prompt = build_reasoning_prompt(context)

        # 3. Call Groq API
        try:
            chat_completion = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": GROQ_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=4096,
            )
        except APITimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Groq API timeout after %.2f ms", elapsed_ms)
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason="Groq API timeout",
            )
        except (APIConnectionError, APIError) as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Groq API error encountered: %s", type(e).__name__)
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason=f"Groq API connection or response error: {type(e).__name__}",
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Unexpected error during Groq invocation: %s", type(e).__name__)
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason=f"Unexpected error: {type(e).__name__}",
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # 4. Parse and Validate JSON
        choice = chat_completion.choices[0] if chat_completion.choices else None
        content = choice.message.content if choice and choice.message else None

        if not content:
            logger.error("Groq returned empty completion content")
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason="Groq returned empty content",
            )

        try:
            data = json.loads(content)
        except json.JSONDecodeError as err:
            logger.error("Failed to decode Groq JSON response: %s", err)
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason=f"Invalid JSON from Groq: {err}",
            )

        # Sanitize recommended steps from leaking metadata
        if "recommended_next_steps" in data and isinstance(data["recommended_next_steps"], list):
            data["recommended_next_steps"] = self._sanitize_steps(data["recommended_next_steps"])

        # Populate reasoning_metadata
        token_usage = {}
        if hasattr(chat_completion, "usage") and chat_completion.usage:
            token_usage = {
                "prompt_tokens": getattr(chat_completion.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(chat_completion.usage, "completion_tokens", 0),
                "total_tokens": getattr(chat_completion.usage, "total_tokens", 0),
            }

        data["reasoning_metadata"] = {
            "provider": self.provider_name,
            "latency_ms": elapsed_ms,
            "retrieval_latency_ms": context.retrieval_metadata.latency_ms,
            "model_name": self.model,
            "token_usage": token_usage,
        }

        # 5. Pydantic validation
        try:
            result = ReasoningResult.model_validate(data)
        except ValidationError as val_err:
            logger.error("Groq response failed ReasoningResult schema validation: %s", val_err)
            return self._build_safe_fallback(
                context=context,
                elapsed_ms=elapsed_ms,
                error_reason="Groq output schema validation failed",
            )

        # Ensure metadata contains exact wall-clock timing and provider
        result.reasoning_metadata.provider = self.provider_name
        result.reasoning_metadata.latency_ms = elapsed_ms
        result.reasoning_metadata.retrieval_latency_ms = context.retrieval_metadata.latency_ms
        result.reasoning_metadata.model_name = self.model
        result.reasoning_metadata.token_usage = token_usage

        return result
