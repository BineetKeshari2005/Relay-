"""Deterministic quality validator for AssembledContext."""

from typing import List
from pydantic import BaseModel, Field

from app.context.assembled_context import AssembledContext


class ContextQualityReport(BaseModel):
    """Validation report summarizing context completeness and integrity."""

    valid: bool = Field(..., description="True if context meets all required architectural constraints")
    warnings: List[str] = Field(default_factory=list, description="Advisory context observations")
    errors: List[str] = Field(default_factory=list, description="Hard validation failures")


class ContextQualityValidator:
    """
    Validates assembled context integrity before passing to future reasoning layers.

    Invariants checked:
    1. Query exists and is non-empty.
    2. Asset identity is resolved OR explicitly marked as unresolved in uncertainty.
    3. Evidence items preserve deterministic chunk IDs and source metadata.
    4. Retrieval metadata and measured latency are preserved.
    5. Safety SOPs and high-pressure conditions are marked in SafetyContext.
    6. Context contains NO premature diagnostic conclusions or treatment recommendations.
    """

    # Prohibited reasoning keywords that belong strictly to Phase 4
    PROHIBITED_DIAGNOSIS_PHRASES = [
        "recommended action:",
        "diagnosis: the cause is",
        "you should replace",
        "the definitive cause",
        "solution:",
        "fix:",
    ]

    def validate(self, context: AssembledContext) -> ContextQualityReport:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Query non-empty check
        if not context.technician_query or not context.technician_query.strip():
            errors.append("Technician query is missing or empty.")

        # 2. Asset resolution check
        if not context.asset_id:
            if not context.uncertainty.missing_asset:
                errors.append("Asset ID is unresolved, but uncertainty.missing_asset is not set to True.")
            else:
                warnings.append("Asset ID is unresolved for this query.")
        else:
            if context.asset and context.asset.asset_id != context.asset_id:
                errors.append(f"Mismatch between asset.asset_id ({context.asset.asset_id}) and context.asset_id ({context.asset_id}).")

        # 3. Evidence integrity check
        if not context.evidence:
            if not context.uncertainty.insufficient_evidence:
                warnings.append("No evidence chunks retrieved, but uncertainty.insufficient_evidence is False.")
        else:
            for idx, item in enumerate(context.evidence):
                if not item.document_id:
                    errors.append(f"Evidence item #{idx} is missing a document_id.")
                if not item.text:
                    errors.append(f"Evidence item #{idx} ({item.document_id}) has empty text.")
                if not item.source:
                    warnings.append(f"Evidence item #{idx} ({item.document_id}) is missing source metadata.")

        # 4. Retrieval latency and metadata check
        if context.retrieval_metadata.latency_ms is None or context.retrieval_metadata.latency_ms < 0:
            errors.append("Retrieval metadata latency_ms is missing or negative.")
        if context.retrieval_metadata.result_count != len(context.evidence):
            warnings.append(
                f"Retrieval metadata count ({context.retrieval_metadata.result_count}) "
                f"differs from evidence list length ({len(context.evidence)})."
            )

        # 5. Safety context integrity check
        has_safety_doc = any(item.classification == "safety_procedure" for item in context.evidence)
        if has_safety_doc and not context.safety_context.safety_documents:
            warnings.append("Safety procedure evidence is present, but safety_context.safety_documents is empty.")

        # Validate structured safety warning items
        for idx, w_item in enumerate(context.safety_context.warning_items):
            if w_item.provenance_type not in ["VERIFIED_FROM_KNOWLEDGE", "DEMO_RULE"]:
                errors.append(f"Safety warning item #{idx} has invalid provenance_type: '{w_item.provenance_type}'")
            if w_item.provenance_type == "VERIFIED_FROM_KNOWLEDGE" and not w_item.source_document_id:
                errors.append(f"Safety warning item #{idx} marked VERIFIED_FROM_KNOWLEDGE is missing source_document_id.")

        # 6. Measurement provenance integrity check
        for m_key in context.measurements.keys():
            if m_key not in context.measurement_provenance:
                warnings.append(f"Measurement '{m_key}' is present without an explicit measurement_provenance tag.")

        # 7. Strict Phase 3 Boundary: Verify NO diagnosis or solution was placed in observations
        for obs in context.observations:
            obs_lower = obs.lower()
            for phrase in self.PROHIBITED_DIAGNOSIS_PHRASES:
                if phrase in obs_lower:
                    errors.append(f"Premature diagnosis/solution found in observations: '{phrase}'")

        is_valid = len(errors) == 0
        return ContextQualityReport(
            valid=is_valid,
            warnings=warnings,
            errors=errors,
        )
