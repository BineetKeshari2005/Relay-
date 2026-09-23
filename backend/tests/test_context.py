"""Test Context object schema, builder, and serialization."""

from app.context.context import Context, ContextBuilder
from app.models.asset import Asset
from app.models.knowledge import KnowledgeDocument, KnowledgeMetadata
from app.models.service_record import ServiceRecord
from app.models.session import ConversationTurn


def test_context_defaults():
    ctx = Context()
    assert ctx.user_query is None
    assert ctx.asset is None
    assert ctx.measurements == {}
    assert ctx.conversation == []
    assert ctx.service_history == []
    assert ctx.retrieved_evidence == []
    assert ctx.safety_context == []
    assert ctx.uncertainty.confidence_score == 1.0


def test_context_builder():
    asset = Asset(
        asset_id="ACX-420-017",
        model="ACX-420",
        manufacturer="CoolCore",
        location="Pad 17",
    )
    turn = ConversationTurn(
        turn_id="turn-01",
        session_id="sess-01",
        speaker="technician",
        text="Getting E17",
    )
    record = ServiceRecord(
        record_id="SR-01",
        asset_id="ACX-420-017",
        date="2026-08-14",
        issue="E17 trip",
        diagnosis="Bad sensor",
        action_taken="Replaced PT-1",
    )
    doc = KnowledgeDocument(
        document_id="doc-01",
        title="E17 SOP",
        document_type="procedure",
        content="Inspect condenser coil",
        metadata=KnowledgeMetadata(
            document_type="procedure",
            source="SOP",
        ),
    )

    ctx = (
        ContextBuilder()
        .with_query("I'm getting E17 again on unit 017. Pressure is around 195 PSI.")
        .with_asset(asset)
        .with_issue("E17 high-pressure trip", error_code="E17")
        .with_measurement("pressure_psi", 195.0)
        .add_turn(turn)
        .add_service_record(record)
        .add_evidence(doc)
        .add_safety_warning("Shut down compressor before inspection.")
        .set_uncertainty(missing=["ambient_temperature"], confidence=0.85)
        .build()
    )

    assert ctx.user_query == "I'm getting E17 again on unit 017. Pressure is around 195 PSI."
    assert ctx.asset.asset_id == "ACX-420-017"
    assert ctx.error_code == "E17"
    assert ctx.measurements["pressure_psi"] == 195.0
    assert len(ctx.conversation) == 1
    assert len(ctx.service_history) == 1
    assert len(ctx.retrieved_evidence) == 1
    assert len(ctx.safety_context) == 1
    assert ctx.uncertainty.missing_information == ["ambient_temperature"]
    assert ctx.uncertainty.confidence_score == 0.85
