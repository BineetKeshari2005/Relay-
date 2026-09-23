"""Tests for Phase 3.1: Safety & Provenance Audit.

Verifies:
1. Unmentioned measurements are not fabricated when no session is passed.
2. Legitimate structured measurements from sessions are preserved with explicit provenance tags.
3. Safety thresholds are grounded in explicit knowledge documents (e.g. e17-troubleshooting).
4. Missing safety thresholds produce uncertainty (unverified_safety_threshold=True).
5. Safety warnings retain source document IDs and specific SOP references.
"""

import pytest
from app.context.assembler import ContextAssembler
from app.context.quality_validator import ContextQualityValidator
from app.retrieval.mock import MockRetrievalProvider


@pytest.mark.asyncio
async def test_unmentioned_measurements_not_fabricated_without_session():
    """Verify ambient_temp_f is NEVER present when only query facts exist and no session is provided."""
    provider = MockRetrievalProvider()
    assembler = ContextAssembler(retrieval_provider=provider)

    query = "I am getting E17 again on unit 017. Pressure is around 195 PSI."
    context = await assembler.assemble(query=query, session_id=None)

    # Technician only mentioned pressure
    assert "pressure_psi" in context.measurements
    assert context.measurements["pressure_psi"] == 195.0
    assert "ambient_temp_f" not in context.measurements

    # Provenance tracks technician_query origin
    assert context.measurement_provenance.get("pressure_psi") == "technician_query"
    assert "ambient_temp_f" not in context.measurement_provenance


@pytest.mark.asyncio
async def test_structured_measurements_preserved_with_session_provenance():
    """Verify ambient_temp_f from session telemetry is preserved with explicit session_telemetry provenance."""
    provider = MockRetrievalProvider()
    assembler = ContextAssembler(retrieval_provider=provider)

    query = "I am getting E17 again on unit 017. Pressure is around 195 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    # Both query and session measurements exist
    assert context.measurements.get("pressure_psi") == 195.0
    assert context.measurements.get("ambient_temp_f") == 88.0

    # Explicit provenance separation
    assert context.measurement_provenance["pressure_psi"] == "technician_query"
    assert context.measurement_provenance["ambient_temp_f"] == "session_telemetry:sess-017"


@pytest.mark.asyncio
async def test_safety_threshold_backed_by_explicit_knowledge():
    """Verify >190 PSI threshold is grounded in e17-troubleshooting knowledge document."""
    provider = MockRetrievalProvider()
    assembler = ContextAssembler(retrieval_provider=provider)

    query = "I am getting E17 again on unit 017. Pressure is around 195 PSI."
    context = await assembler.assemble(query=query, session_id="sess-017")

    # High pressure hazard flagged
    assert context.safety_context.high_pressure_hazard is True
    assert context.safety_context.mandatory_loto is True

    # Provenance of safety warning item
    e17_warnings = [
        w for w in context.safety_context.warning_items
        if w.source_document_id == "e17-troubleshooting"
    ]
    assert len(e17_warnings) >= 1
    w = e17_warnings[0]
    assert w.provenance_type == "VERIFIED_FROM_KNOWLEDGE"
    assert w.source_reference == "SOP-ACX420-E17 Rev 3.0 Step 3"
    assert "190.0 PSI" in (w.threshold_applied or "")

    # Threshold sources record
    assert "pressure_psi" in context.safety_context.threshold_sources
    assert "e17-troubleshooting" in context.safety_context.threshold_sources["pressure_psi"]


@pytest.mark.asyncio
async def test_missing_safety_threshold_produces_uncertainty():
    """Verify that ungrounded pressure reading produces uncertainty instead of fabricated certainty."""
    provider = MockRetrievalProvider()
    assembler = ContextAssembler(retrieval_provider=provider)

    # An unknown asset and unknown trouble code with a pressure reading
    query = "Unit 999 is humming loudly with pressure reading 195 PSI."
    context = await assembler.assemble(query=query, session_id=None)

    assert "pressure_psi" in context.measurements
    # Since neither e17-troubleshooting nor any verified pressure manual was retrieved for Unit 999:
    assert context.uncertainty.unverified_safety_threshold is True

    # Heuristic warning item emitted with DEMO_RULE provenance
    heuristic_warnings = [
        w for w in context.safety_context.warning_items
        if w.provenance_type == "DEMO_RULE"
    ]
    assert len(heuristic_warnings) >= 1


@pytest.mark.asyncio
async def test_validator_enforces_provenance_and_warning_integrity():
    """Verify ContextQualityValidator enforces provenance tags and warning item integrity."""
    provider = MockRetrievalProvider()
    assembler = ContextAssembler(retrieval_provider=provider)
    validator = ContextQualityValidator()

    context = await assembler.assemble(
        query="E17 trouble code on unit 017 with pressure 195 PSI.",
        session_id="sess-017",
    )

    report = validator.validate(context)
    assert report.valid is True
    assert len(report.errors) == 0
