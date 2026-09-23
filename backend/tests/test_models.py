"""Test core data model validation and constraints."""

import pytest
from pydantic import ValidationError

from app.models.asset import Asset
from app.models.service_record import ServiceRecord
from app.models.knowledge import KnowledgeDocument, KnowledgeMetadata
from app.models.session import TechnicianSession, ConversationTurn


def test_asset_model_valid():
    asset = Asset(
        asset_id="ACX-420-017",
        model="ACX-420",
        manufacturer="CoolCore",
        location="Pad 17",
        status="operational",
        metadata={"tonnage": 35},
    )
    assert asset.asset_id == "ACX-420-017"
    assert asset.model == "ACX-420"
    assert asset.metadata["tonnage"] == 35


def test_asset_model_missing_required():
    with pytest.raises(ValidationError):
        Asset(model="ACX-420")  # Missing asset_id, manufacturer, location


def test_service_record_model():
    rec = ServiceRecord(
        record_id="SR-001",
        asset_id="ACX-420-017",
        date="2026-08-14",
        issue="E17 trip",
        diagnosis="Faulty transducer",
        action_taken="Replaced transducer",
        parts_replaced=["PT-1"],
        technician_notes="Exhaust vent nearby",
    )
    assert rec.record_id == "SR-001"
    assert "PT-1" in rec.parts_replaced


def test_knowledge_document_model():
    doc = KnowledgeDocument(
        document_id="doc-01",
        title="E17 Procedure",
        document_type="procedure",
        content="Step 1: Check airflow",
        metadata=KnowledgeMetadata(
            asset_model="ACX-420",
            error_code="E17",
            document_type="procedure",
            safety_level="warning",
            source="Manual",
        ),
    )
    assert doc.metadata.error_code == "E17"
    assert doc.metadata.safety_level == "warning"


def test_technician_session_and_turns():
    session = TechnicianSession(
        session_id="sess-001",
        technician_id="tech-12",
        asset_id="ACX-420-017",
        current_issue="E17 alarm",
        current_error_code="E17",
        current_measurements={"pressure_psi": 195.0},
        status="active",
    )
    assert session.status == "active"
    assert session.current_measurements["pressure_psi"] == 195.0

    turn = ConversationTurn(
        turn_id="turn-1",
        session_id="sess-001",
        speaker="technician",
        text="Getting E17 on unit 017",
    )
    assert turn.speaker == "technician"
