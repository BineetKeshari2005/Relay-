"""Prompts and context serialization for evidence-grounded reasoning."""

import json
from typing import Any, Dict
from app.context.assembled_context import AssembledContext

SYSTEM_PROMPT = """You are a field technician decision-support assistant.

Use only the provided context and evidence.
Do not invent equipment specifications, safety limits, service history, measurements, or procedures.

Distinguish:
1. directly supported facts
2. reasonable inference
3. unknown information

If evidence is insufficient, say so.
If evidence conflicts, surface the conflict instead of choosing a source without justification.
Do not claim that a diagnosis is certain unless the evidence supports it.
Every substantive claim must cite one or more evidence IDs.
Never fabricate citations.
Never invent document IDs or test readings that are not in the context.
If required information is missing, provide clarifying questions instead of guessing.
Safety considerations and procedures provided in the context are mandatory and authoritative.
"""


def build_reasoning_prompt(context: AssembledContext) -> str:
    """
    Format an AssembledContext into a structured text prompt for the reasoning engine.
    Ensures complete transparency of facts, evidence chunks, safety rules, and uncertainty.
    """
    sections = []

    # 1. Technician Query
    sections.append(f"### TECHNICIAN UTTERANCE\n{context.technician_query.strip()}\n")

    # 2. Extracted Facts & Measurements
    facts_dict: Dict[str, Any] = {
        "asset_reference": context.query_facts.asset_reference,
        "asset_model": context.asset_model,
        "error_code": context.error_code,
        "is_repeat_issue": context.query_facts.is_repeat_issue,
        "observations": context.observations,
        "measurements": context.measurements,
        "measurement_provenance": context.measurement_provenance,
    }
    sections.append(f"### STRUCTURED QUERY FACTS & TELEMETRY\n{json.dumps(facts_dict, indent=2)}\n")

    # 3. Asset Details if resolved
    if context.asset:
        asset_info = {
            "asset_id": context.asset.asset_id,
            "model": context.asset.model,
            "type": getattr(context.asset, "asset_type", context.asset.metadata.get("type", "HVAC Unit")),
            "manufacturer": context.asset.manufacturer,
            "location": context.asset.location,
            "serial_number": getattr(context.asset, "serial_number", context.asset.metadata.get("serial_number", "N/A")),
        }
        sections.append(f"### EQUIPMENT ASSET SPECIFICATION\n{json.dumps(asset_info, indent=2)}\n")

    # 4. Structured Service History
    if context.relevant_service_history:
        history_list = [
            {
                "record_id": r.record_id,
                "asset_id": r.asset_id,
                "date": r.date,
                "issue": r.issue,
                "diagnosis": r.diagnosis,
                "action_taken": r.action_taken,
                "parts_replaced": r.parts_replaced,
                "technician_notes": r.technician_notes,
            }
            for r in context.relevant_service_history
        ]
        sections.append(f"### STRUCTURED HISTORICAL WORK ORDERS\n{json.dumps(history_list, indent=2)}\n")

    # 5. Conversation History
    if context.conversation_context:
        turns = [
            f"[{t.speaker.upper()}]: {t.text}"
            for t in context.conversation_context
        ]
        sections.append(f"### CONVERSATION CONTEXT\n" + "\n".join(turns) + "\n")

    # 6. Retrieved Knowledge Evidence (from Moss)
    if context.evidence:
        evidence_chunks = []
        for e in context.evidence:
            evidence_chunks.append(
                f"--- EVIDENCE CHUNK: {e.document_id} ---\n"
                f"Source: {e.source} | Classification: {e.classification} | Safety Level: {e.safety_level}\n"
                f"Content:\n{e.text}\n"
            )
        sections.append("### RETRIEVED TECHNICAL EVIDENCE (MOSS)\n" + "\n".join(evidence_chunks))
    else:
        sections.append("### RETRIEVED TECHNICAL EVIDENCE (MOSS)\nNo evidence chunks found for this query.\n")

    # 7. Grounded Safety Constraints
    safety_info = {
        "safety_level": context.safety_context.safety_level,
        "high_pressure_hazard": context.safety_context.high_pressure_hazard,
        "mandatory_loto": context.safety_context.mandatory_loto,
        "safety_warnings": context.safety_context.safety_warnings,
        "threshold_sources": context.safety_context.threshold_sources,
        "warning_items": [w.model_dump() for w in context.safety_context.warning_items],
    }
    sections.append(f"### MANDATORY SAFETY CONSTRAINTS & HAZARDS\n{json.dumps(safety_info, indent=2)}\n")

    # 8. Uncertainty Model & Missing Info
    uncertainty_dict = {
        "missing_asset": context.uncertainty.missing_asset,
        "missing_error_code": context.uncertainty.missing_error_code,
        "missing_measurement": context.uncertainty.missing_measurement,
        "insufficient_evidence": context.uncertainty.insufficient_evidence,
        "conflicting_evidence": context.uncertainty.conflicting_evidence,
        "ambiguous_query": context.uncertainty.ambiguous_query,
        "unverified_safety_threshold": context.uncertainty.unverified_safety_threshold,
        "missing_information_required": context.missing_information,
    }
    sections.append(f"### DIAGNOSTIC UNCERTAINTY & MISSING PARAMETERS\n{json.dumps(uncertainty_dict, indent=2)}\n")

    # 9. Detected Evidence Conflicts
    if context.conflicts:
        conflicts_list = [c.model_dump() for c in context.conflicts]
        sections.append(f"### DETECTED EVIDENCE CONFLICTS\n{json.dumps(conflicts_list, indent=2)}\n")

    # Instructions
    sections.append(
        "Generate a structured ReasoningResult based SOLELY on the above data. "
        "Include issue_summary, what_we_know, assessment, evidence_claims, recommended_next_steps, "
        "safety_considerations, expected_observations, decision_branches, clarifying_questions, "
        "certainty_level, uncertainty, escalation, and citations."
    )

    return "\n\n".join(sections)
