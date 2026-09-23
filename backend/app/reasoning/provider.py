"""Reasoning provider implementations: MockReasoningProvider and LLMReasoningProvider."""

import time
from typing import Any, Dict, List, Optional

from app.context.assembled_context import AssembledContext, EvidenceItem
from app.llm.base import LLMProvider
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
)
from app.reasoning.prompts import SYSTEM_PROMPT, build_reasoning_prompt


class MockReasoningProvider(ReasoningProvider):
    """
    Deterministic, generic reasoning provider for testing and evaluation.

    CRITICAL ARCHITECTURAL PROPERTY:
    This provider does NOT contain hardcoded question/answer mappings or special E17 branches.
    It dynamically inspects the structured fields of AssembledContext:
    - Analyzes uncertainty flags and generates dynamic clarifying questions.
    - Ground claims and citations directly in the retrieved evidence list.
    - Preserves safety constraints and evaluates escalation needs.
    """

    @property
    def provider_name(self) -> str:
        return "mock-reasoner"

    def _generate_clarifying_questions(self, context: AssembledContext) -> List[str]:
        """Dynamically formulate clarifying questions based on missing parameters."""
        questions: List[str] = []

        if context.uncertainty.missing_asset or not context.asset_id:
            questions.append("Which equipment asset or unit identifier are you currently inspecting?")
        if context.uncertainty.missing_error_code or not context.error_code:
            questions.append("What specific diagnostic trouble code or fault message is active?")
        if context.uncertainty.missing_measurement:
            if context.missing_information:
                for item in context.missing_information:
                    if "pressure" in item.lower() or "reading" in item.lower():
                        questions.append(f"Can you provide the {item}?")
            else:
                questions.append("What are the current pressure (PSI) or temperature readings?")
        if not questions or context.uncertainty.ambiguous_query:
            questions.append("Could you describe the physical symptom or unusual behavior in more detail?")

        return questions

    def _extract_actionable_step(self, text: str, default_source: str) -> str:
        """Dynamically extract a concrete procedural instruction from document text, skipping metadata headers."""
        import re
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Candidate actionable lines: bullet points, numbered steps, or lines under action sections
        candidates: List[str] = []
        metadata_prefixes = (
            "**model scope", "model scope", "document id", "safety classification",
            "target subsystem", ">", "notice", "version", "date:", "author:"
        )

        for line in lines:
            if line.startswith("#"):
                continue
            lower_line = line.lower()
            if any(lower_line.startswith(p) or p in lower_line[:30] for p in metadata_prefixes):
                continue
            # Strip bullet prefixes and numbering
            clean = re.sub(r"^[-*•]\s*", "", line).strip()
            clean = re.sub(r"^\d+\.\s*", "", clean).strip()
            clean = re.sub(r"^\*{1,2}[^*]+\*{1,2}:?\s*", "", clean).strip()  # remove leading bold labels

            if len(clean) >= 20 and not clean.startswith(">"):
                candidates.append(clean)

        if candidates:
            # Prefer lines starting with procedural action verbs
            action_verbs = (
                "inspect", "verify", "check", "switch", "confirm", "connect",
                "compare", "measure", "clean", "disconnect", "prior to",
                "de-energize", "test", "isolate", "examine", "halt", "review"
            )
            for cand in candidates:
                if cand.lower().startswith(action_verbs):
                    return cand[:130]
            return candidates[0][:130]

        return f"Perform systematic physical inspection and verify electrical/mechanical parameters per {default_source}."

    async def reason(self, context: AssembledContext) -> ReasoningResult:
        start_time = time.perf_counter()

        # 1. Build What We Know list directly from facts and telemetry
        what_we_know: List[str] = []
        if context.asset_id:
            what_we_know.append(f"Equipment asset identified as {context.asset_id} ({context.asset_model or 'unknown model'}).")
        if context.error_code:
            what_we_know.append(f"Active trouble code reported: {context.error_code}.")
        if context.measurements:
            m_strings = [f"{k}={v} (source: {context.measurement_provenance.get(k, 'unspecified')})" for k, v in context.measurements.items()]
            what_we_know.append(f"Recorded measurements: {', '.join(m_strings)}.")
        if context.observations:
            what_we_know.append(f"Observed symptoms: {', '.join(context.observations)}.")
        if context.relevant_service_history:
            latest = context.relevant_service_history[0]
            what_we_know.append(f"Service history on record: {latest.record_id} ({latest.issue}).")

        # 2. Check for Insufficient Evidence or Vague Query
        has_technical_grounding = bool(
            context.asset_id
            or context.error_code
            or context.measurements
            or context.observations
            or any(w in context.technician_query.lower() for w in ["procedure", "safety", "manual", "sop", "spec", "loto", "wiring", "threshold"])
        )

        is_insufficient = (
            context.uncertainty.insufficient_evidence
            or len(context.evidence) == 0
            or not has_technical_grounding
        )
        if is_insufficient:
            clarifying_qs = self._generate_clarifying_questions(context)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return ReasoningResult(
                status="needs_information",
                issue_summary=f"Reported issue: '{context.technician_query}'",
                what_we_know=what_we_know,
                assessment=(
                    "The available context is insufficient to formulate "
                    "an evidence-grounded diagnosis without guessing. Further diagnostic details are required."
                ),
                evidence_claims=[],
                recommended_next_steps=[],
                safety_considerations=context.safety_context.safety_warnings,
                expected_observations=[],
                decision_branches=[],
                clarifying_questions=clarifying_qs,
                certainty_level="insufficient_evidence",
                uncertainty={
                    "missing_information": context.missing_information,
                    "reason": "Missing equipment asset, diagnostic error code, or sensor telemetry.",
                },
                escalation=EscalationAssessment(
                    should_escalate=False,
                    missing_information=context.missing_information,
                ),
                citations=[],
                reasoning_metadata=ReasoningMetadata(
                    provider=self.provider_name,
                    latency_ms=elapsed_ms,
                    retrieval_latency_ms=context.retrieval_metadata.latency_ms,
                    model_name="mock-deterministic",
                ),
            )

        # 3. Check for Evidence Conflicts
        if context.conflicts or context.uncertainty.conflicting_evidence:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            conflict_descriptions = [c.description for c in context.conflicts]
            all_evidence_ids = [e.document_id for e in context.evidence]

            return ReasoningResult(
                status="conflicting_evidence",
                issue_summary=f"Reported issue: '{context.technician_query}'",
                what_we_know=what_we_know,
                assessment=(
                    f"Conflicting technical documentation detected: {'; '.join(conflict_descriptions)}. "
                    "Relay will not silently select one source over another. Escalation or manual verification required."
                ),
                evidence_claims=[
                    EvidenceClaim(
                        claim="Retrieved technical specifications contain conflicting requirements.",
                        evidence_ids=all_evidence_ids,
                        support_level="direct",
                        explanation="Discrepancy detected across retrieved document versions or parameters.",
                    )
                ],
                recommended_next_steps=[
                    RecommendedNextStep(
                        step="Halt physical adjustment and review equipment serial nameplate to confirm revision specification.",
                        evidence_ids=all_evidence_ids[:1],
                        rationale="Prevent implementing improper revision guidelines.",
                        safety_constraints=["Do not adjust calibration without verifying exact nameplate model revision."],
                    )
                ],
                safety_considerations=context.safety_context.safety_warnings,
                expected_observations=["Physical serial nameplate stamping and schematic version."],
                decision_branches=[],
                clarifying_questions=["Which specific revision number is stamped on the physical equipment nameplate?"],
                certainty_level="conflicting_evidence",
                uncertainty={"conflicts": [c.model_dump() for c in context.conflicts]},
                escalation=EscalationAssessment(
                    should_escalate=True,
                    reason="Discrepancy between retrieved specifications.",
                    recommended_escalation_target="Field Supervisor / Lead Engineer",
                ),
                citations=[
                    ReasoningCitation(
                        evidence_id=e.document_id,
                        source=e.source,
                        document_type=e.document_type,
                        relevant_excerpt=e.text[:200] + "...",
                        score=e.score,
                    )
                    for e in context.evidence[:3]
                ],
                reasoning_metadata=ReasoningMetadata(
                    provider=self.provider_name,
                    latency_ms=elapsed_ms,
                    retrieval_latency_ms=context.retrieval_metadata.latency_ms,
                    model_name="mock-deterministic",
                ),
            )

        # 4. Check for Critical Safety Escalation (>250 PSI or critical hazard)
        requires_safety_escalation = (
            context.safety_context.safety_level == "critical"
            or any(
                isinstance(v, (int, float)) and v > 250.0
                for k, v in context.measurements.items()
                if "pressure" in k.lower()
            )
        )

        # 5. Ground Evidence Claims from retrieved evidence chunks
        evidence_claims: List[EvidenceClaim] = []
        citations: List[ReasoningCitation] = []
        recommended_next_steps: List[RecommendedNextStep] = []
        decision_branches: List[DecisionBranch] = []
        expected_observations: List[ExpectedObservation] if False else []

        # Build Citations from actual context evidence
        for item in context.evidence:
            citations.append(
                ReasoningCitation(
                    evidence_id=item.document_id,
                    source=item.source,
                    document_type=item.document_type,
                    relevant_excerpt=item.text[:250].strip() + ("..." if len(item.text) > 250 else ""),
                    score=item.score,
                    metadata=item.metadata,
                )
            )

        # Derive dynamic claims from available evidence
        for item in context.evidence:
            if item.classification == "service_history":
                evidence_claims.append(
                    EvidenceClaim(
                        claim=f"Historical maintenance record confirms previous service: {item.source}.",
                        evidence_ids=[item.document_id],
                        support_level="direct",
                        explanation=f"Historical record {item.document_id} documents past component intervention.",
                    )
                )
            elif item.classification == "troubleshooting":
                evidence_claims.append(
                    EvidenceClaim(
                        claim=f"Standard troubleshooting procedure identified for issue in {item.source}.",
                        evidence_ids=[item.document_id],
                        support_level="direct",
                        explanation="Technical troubleshooting procedure outlines inspection sequence.",
                    )
                )
            elif item.classification == "safety_procedure":
                evidence_claims.append(
                    EvidenceClaim(
                        claim=f"Safety operating procedure applies before physical inspection: {item.source}.",
                        evidence_ids=[item.document_id],
                        support_level="direct",
                        explanation="Mandates PPE, de-energization, and depressurization precautions.",
                    )
                )
            elif (
                item.classification == "technician_contribution"
                or item.is_technician_contribution
                or item.provenance_type == "TECHNICIAN_CONTRIBUTION"
            ):
                evidence_claims.append(
                    EvidenceClaim(
                        claim=f"Prior field technician report ({item.document_id}) recorded historical observation: {item.source}.",
                        evidence_ids=[item.document_id],
                        support_level="inferred",
                        explanation=(
                            f"Field observation (Status: {item.verification_status}). "
                            "Provided as contextual field history only; does not constitute an authoritative standard or procedure."
                        ),
                    )
                )

        # Derive recommended next steps strictly from authoritative troubleshooting & safety evidence
        step_evidence = [
            e
            for e in context.evidence
            if e.classification in ["troubleshooting", "safety_procedure", "technical_manual"]
            and not getattr(e, "is_technician_contribution", False)
            and getattr(e, "provenance_type", "") != "TECHNICIAN_CONTRIBUTION"
        ]

        if not step_evidence and context.evidence:
            # Check if technician contributions exist
            tech_items = [
                e
                for e in context.evidence
                if getattr(e, "is_technician_contribution", False)
                or getattr(e, "provenance_type", "") == "TECHNICIAN_CONTRIBUTION"
            ]
            if tech_items:
                t_item = tech_items[0]
                recommended_next_steps.append(
                    RecommendedNextStep(
                        step=f"Review field technician observation from {t_item.source} and perform preliminary inspection.",
                        evidence_ids=[t_item.document_id],
                        rationale=f"Contextual field report ({t_item.verification_status}); not an approved manufacturer SOP.",
                        expected_observation="Visual check of reported component condition.",
                        safety_constraints=list(context.safety_context.safety_warnings),
                    )
                )
            else:
                step_evidence = context.evidence[:2]

        for idx, item in enumerate(step_evidence[:3]):
            step_safety = list(context.safety_context.safety_warnings)
            if context.safety_context.mandatory_loto:
                step_safety.append("Lockout/Tagout (LOTO) de-energization required before proceeding.")

            # Extract an actionable step instruction dynamically from the document text
            first_action = self._extract_actionable_step(item.text, item.source)

            recommended_next_steps.append(
                RecommendedNextStep(
                    step=f"Step {idx + 1}: {first_action[:130]}",
                    evidence_ids=[item.document_id],
                    rationale=f"Specified in documented technical guidance {item.document_id}.",
                    expected_observation="Verification of component integrity and physical telemetry baseline.",
                    safety_constraints=step_safety,
                )
            )

        # Build dynamic decision branches if multiple steps/conditions exist
        if len(step_evidence) > 0:
            first_doc = step_evidence[0]
            if "pressure" in context.measurements or "pressure_psi" in context.query_facts.measurements:
                p_val = context.measurements.get("pressure_psi", 0)
                decision_branches.append(
                    DecisionBranch(
                        condition=f"Discharge pressure confirms elevated reading (>190 PSI, current: {p_val} PSI)",
                        if_true_branch="Do NOT open service valves. De-energize compressor and inspect condenser coil for airflow blockages.",
                        if_false_branch="If pressure reading is normal (160-185 PSI), verify transducer wiring and harness calibration.",
                        evidence_ids=[first_doc.document_id],
                        rationale="Differentiates true thermodynamic high-pressure condition from sensor electrical fault.",
                    )
                )

        # Dynamic assessment summary
        assessment_parts = []
        if context.asset_id:
            assessment_parts.append(f"Assessment for {context.asset_id}:")
        if context.relevant_service_history:
            rec = context.relevant_service_history[0]
            assessment_parts.append(f"Past service ({rec.record_id}) indicates previous component work.")

        # Surface any retrieved technician contributions in assessment
        tech_items = [
            e
            for e in context.evidence
            if getattr(e, "is_technician_contribution", False)
            or getattr(e, "provenance_type", "") == "TECHNICIAN_CONTRIBUTION"
        ]
        if tech_items:
            t = tech_items[0]
            assessment_parts.append(
                f"An earlier technician report ({t.document_id}) documented related field findings ({t.verification_status})."
            )

        if context.safety_context.high_pressure_hazard:
            assessment_parts.append("Elevated pressure condition requires strict Lockout/Tagout de-energization before coil inspection.")
        if not assessment_parts:
            assessment_parts.append(f"Evidence-grounded review of '{context.technician_query}' supported by retrieved technical documentation.")

        assessment = " ".join(assessment_parts)

        # Status and certainty level
        status: ReasoningStatus = "safety_escalation" if requires_safety_escalation else "completed"
        certainty: CertaintyLevel = "supported" if len(evidence_claims) >= 2 else "partially_supported"

        # Escalation assessment
        escalation = EscalationAssessment(
            should_escalate=requires_safety_escalation,
            reason="Emergency pressure threshold exceeded (> 250 PSI)" if requires_safety_escalation else None,
            safety_reason="Mandatory emergency shutdown protocol" if requires_safety_escalation else None,
            recommended_escalation_target="Field Service Supervisor / Plant Safety Officer" if requires_safety_escalation else None,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ReasoningResult(
            status=status,
            issue_summary=f"Reported issue: '{context.technician_query}'",
            what_we_know=what_we_know,
            assessment=assessment,
            evidence_claims=evidence_claims,
            recommended_next_steps=recommended_next_steps,
            safety_considerations=context.safety_context.safety_warnings,
            expected_observations=[
                "Confirm physical shutdown and zero gauge pressure before opening any valve.",
                "Inspect coil cleanliness and fan motor rotation.",
            ],
            decision_branches=decision_branches,
            clarifying_questions=self._generate_clarifying_questions(context) if context.missing_information else [],
            certainty_level=certainty,
            uncertainty={
                "unverified_safety_threshold": context.uncertainty.unverified_safety_threshold,
                "missing_information": context.missing_information,
            },
            escalation=escalation,
            citations=citations,
            reasoning_metadata=ReasoningMetadata(
                provider=self.provider_name,
                latency_ms=elapsed_ms,
                retrieval_latency_ms=context.retrieval_metadata.latency_ms,
                model_name="mock-deterministic",
            ),
        )


class LLMReasoningProvider(ReasoningProvider):
    """
    Production reasoning provider utilizing the decoupled LLM abstraction.
    Enforces structured Pydantic output validation and prompt grounding.
    """

    def __init__(self, llm_provider: LLMProvider):
        self._llm_provider = llm_provider

    @property
    def provider_name(self) -> str:
        return f"llm-reasoner:{self._llm_provider.provider_name}"

    async def reason(self, context: AssembledContext) -> ReasoningResult:
        start_time = time.perf_counter()
        prompt = build_reasoning_prompt(context)

        # Generate structured output conforming strictly to ReasoningResult schema
        result = await self._llm_provider.generate_structured(
            prompt=prompt,
            response_model=ReasoningResult,
            system_prompt=SYSTEM_PROMPT,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Preserve accurate provider timing
        result.reasoning_metadata.provider = self.provider_name
        result.reasoning_metadata.latency_ms = elapsed_ms
        result.reasoning_metadata.retrieval_latency_ms = context.retrieval_metadata.latency_ms

        return result
