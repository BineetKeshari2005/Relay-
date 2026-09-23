"""Reasoning Quality Validator enforcing evidence grounding, safety integrity, and zero hallucination."""

from typing import List, Set
from pydantic import BaseModel, Field

from app.context.assembled_context import AssembledContext
from app.reasoning.models import ReasoningResult


class ReasoningValidationReport(BaseModel):
    """Validation outcome report for an assembled reasoning result."""

    is_valid: bool = Field(..., description="True if reasoning satisfies all grounding and safety constraints")
    errors: List[str] = Field(default_factory=list, description="Hard validation failures rejecting the reasoning")
    warnings: List[str] = Field(default_factory=list, description="Advisory observations or minor gaps")


class ReasoningQualityValidator:
    """
    Strict evidence and safety validator for generated reasoning output.

    Core Principle:
    Reject invalid reasoning output. Do not silently repair hallucinated citations.
    """

    PROHIBITED_SAFETY_ACTIONS = [
        "bypass lockout",
        "bypass loto",
        "ignore interlock",
        "open service valve under pressure",
        "without depressurizing",
        "without lockout",
        "do not need loto",
    ]

    def validate(
        self,
        result: ReasoningResult,
        context: AssembledContext,
    ) -> ReasoningValidationReport:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Build set of valid evidence IDs from context
        valid_evidence_ids: Set[str] = {item.document_id for item in context.evidence}
        for rec in context.relevant_service_history:
            valid_evidence_ids.add(rec.record_id)

        # 2. Validate Citations
        for idx, citation in enumerate(result.citations):
            if citation.evidence_id not in valid_evidence_ids:
                errors.append(
                    f"Citation #{idx} references non-existent or fabricated evidence ID: '{citation.evidence_id}'."
                )

        # 3. Validate Evidence Claims
        for idx, claim in enumerate(result.evidence_claims):
            if not claim.evidence_ids:
                if claim.support_level == "direct":
                    errors.append(
                        f"Evidence claim #{idx} is marked 'direct' but provides no supporting evidence IDs: '{claim.claim}'."
                    )
            else:
                for eid in claim.evidence_ids:
                    if eid not in valid_evidence_ids:
                        errors.append(
                            f"Evidence claim #{idx} cites fabricated or unretrieved evidence ID: '{eid}'."
                        )

        # 4. Validate Recommended Next Steps
        for idx, step in enumerate(result.recommended_next_steps):
            if not step.evidence_ids and result.status == "completed":
                warnings.append(
                    f"Recommended step #{idx} has no supporting evidence IDs: '{step.step}'."
                )
            for eid in step.evidence_ids:
                if eid not in valid_evidence_ids:
                    errors.append(
                        f"Recommended step #{idx} references unretrieved evidence ID: '{eid}'."
                    )

        # 5. Safety Constraint Adherence
        combined_text = (
            f"{result.assessment} "
            + " ".join(result.safety_considerations)
            + " "
            + " ".join(s.step for s in result.recommended_next_steps)
        ).lower()

        for prohibited in self.PROHIBITED_SAFETY_ACTIONS:
            if prohibited in combined_text:
                errors.append(f"Safety violation: Reasoning output contains prohibited action: '{prohibited}'.")

        # If high pressure hazard or mandatory LOTO is active, verify that reasoning acknowledges it
        if context.safety_context.mandatory_loto and result.status == "completed":
            has_loto_mention = (
                "lockout" in combined_text
                or "loto" in combined_text
                or "de-energiz" in combined_text
                or "shutdown" in combined_text
            )
            if not has_loto_mention:
                errors.append(
                    "Safety integrity failure: Context mandates Lockout/Tagout (LOTO), but reasoning result does not mention LOTO, shutdown, or de-energization."
                )

        # 6. Uncertainty Representation
        if context.uncertainty.insufficient_evidence:
            if result.status == "completed" and result.certainty_level == "supported":
                errors.append(
                    "Uncertainty violation: Context has insufficient_evidence=True, but reasoning claims status='completed' and certainty_level='supported'."
                )
            if not result.clarifying_questions and not result.uncertainty.get("missing_information"):
                warnings.append(
                    "Context has insufficient evidence, but no clarifying questions or missing information were identified."
                )

        # 7. Check for Evidence Conflicts
        if context.conflicts:
            if result.status not in ["conflicting_evidence", "needs_information", "safety_escalation"]:
                errors.append(
                    f"Conflict violation: Context contains {len(context.conflicts)} detected conflict(s), but reasoning status is '{result.status}'."
                )

        # 8. Technician Contribution Non-Authoritative Invariant
        evidence_by_id = {item.document_id: item for item in context.evidence}
        for idx, step in enumerate(result.recommended_next_steps):
            for eid in step.evidence_ids:
                ev_item = evidence_by_id.get(eid)
                if ev_item and (getattr(ev_item, "is_technician_contribution", False) or ev_item.provenance_type == "TECHNICIAN_CONTRIBUTION"):
                    if ev_item.verification_status == "PENDING_REVIEW":
                        step_lower = f"{step.step} {step.rationale}".lower()
                        if any(phrase in step_lower for phrase in ["approved procedure", "official sop", "manufacturer standard", "mandatory procedure"]):
                            errors.append(
                                f"Provenance violation: Step #{idx} asserts that pending technician contribution '{eid}' is an approved or official standard."
                            )

        is_valid = len(errors) == 0
        return ReasoningValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )
