"""Demo fixture data for local testing, endpoints, and mock retrieval."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.models.asset import Asset
from app.models.knowledge import KnowledgeDocument, KnowledgeMetadata
from app.models.service_record import ServiceRecord
from app.models.session import ConversationTurn, TechnicianSession

# Base path to knowledge directory
KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "knowledge"

DEMO_ASSETS: Dict[str, Asset] = {
    "ACX-420-017": Asset(
        asset_id="ACX-420-017",
        model="ACX-420",
        manufacturer="CoolCore",
        location="Facility 4, West Wing Rooftop (Pad 17)",
        status="maintenance_required",
        metadata={
            "serial_number": "CC-2024-ACX420-9841",
            "installation_date": "2024-03-15",
            "refrigerant": "Demo-R410A Equivalent",
            "nominal_tonnage": 35,
            "disclaimer": "Fictional demo asset for Relay system evaluation.",
        },
    )
}

DEMO_SERVICE_RECORDS: Dict[str, List[ServiceRecord]] = {
    "ACX-420-017": [
        ServiceRecord(
            record_id="SR-2026-0814-017",
            asset_id="ACX-420-017",
            date="2026-08-14",
            issue="Intermittent E17 high-pressure trip during peak afternoon heat",
            diagnosis="Discharge pressure transducer PT-1 showed fluctuating reference voltage (+0.8V bias).",
            action_taken="Replaced discharge pressure transducer PT-1. Recalibrated analog input channel.",
            parts_replaced=["PT-1-DISCH-TRANSDUCER-420", "O-RING-SCHRADER-04"],
            technician_notes=(
                "Unit 017 is installed adjacent to west wall exhaust vent. Condenser coils accumulate dust quickly here. "
                "Cleaned exterior coil face. Warned that repeat high pressure in 2-3 months likely indicates coil fouling."
            ),
        )
    ]
}

DEMO_SESSIONS: Dict[str, TechnicianSession] = {
    "sess-017": TechnicianSession(
        session_id="sess-017",
        technician_id="tech-dave-88",
        asset_id="ACX-420-017",
        started_at="2026-09-22T10:14:00Z",
        current_issue="Repeat E17 alarm; elevated pressure reading",
        current_error_code="E17",
        current_measurements={"pressure_psi": 195.0, "ambient_temp_f": 88.0},
        status="active",
    )
}

DEMO_TURNS: Dict[str, List[ConversationTurn]] = {
    "sess-017": [
        ConversationTurn(
            turn_id="turn-001",
            session_id="sess-017",
            speaker="technician",
            text="I'm getting E17 again on unit 017. Pressure is around 195 PSI.",
            timestamp="2026-09-22T10:14:05Z",
        ),
        ConversationTurn(
            turn_id="turn-002",
            session_id="sess-017",
            speaker="assistant",
            text="Understood. Unit 017 (CoolCore ACX-420) previously had sensor PT-1 replaced for E17 on August 14. Let's verify shutdown and check the condenser coil before running the compressor.",
            timestamp="2026-09-22T10:14:08Z",
        ),
    ]
}


def load_demo_knowledge_documents() -> List[KnowledgeDocument]:
    """Load fictional demo knowledge documents from the knowledge/ directory."""
    documents: List[KnowledgeDocument] = []

    # 1. ACX-420 Technical Manual
    manual_path = KNOWLEDGE_ROOT / "manuals" / "acx420_technical_manual.md"
    if manual_path.exists():
        documents.append(
            KnowledgeDocument(
                document_id="doc-manual-acx420",
                title="CoolCore ACX-420 Technical Manual (Fictional Demo)",
                document_type="manual",
                content=manual_path.read_text(encoding="utf-8"),
                metadata=KnowledgeMetadata(
                    asset_model="ACX-420",
                    document_type="manual",
                    safety_level="standard",
                    source="CoolCore Thermal Systems Documentation",
                    version="2.1",
                    date="2024-01-10",
                ),
            )
        )

    # 2. ACX-420 Troubleshooting Guide
    tb_guide_path = KNOWLEDGE_ROOT / "procedures" / "acx420_troubleshooting_guide.md"
    if tb_guide_path.exists():
        documents.append(
            KnowledgeDocument(
                document_id="doc-guide-acx420",
                title="CoolCore ACX-420 Troubleshooting Guide (Fictional Demo)",
                document_type="procedure",
                content=tb_guide_path.read_text(encoding="utf-8"),
                metadata=KnowledgeMetadata(
                    asset_model="ACX-420",
                    error_code="E17",
                    document_type="procedure",
                    safety_level="warning",
                    source="CoolCore Field Service Bulletin",
                    version="1.4",
                    date="2024-05-15",
                ),
            )
        )

    # 3. E17 Troubleshooting Procedure
    e17_path = KNOWLEDGE_ROOT / "procedures" / "e17_troubleshooting_procedure.md"
    if e17_path.exists():
        documents.append(
            KnowledgeDocument(
                document_id="doc-sop-e17",
                title="Fault E17 High-Pressure Troubleshooting Procedure (Fictional Demo)",
                document_type="procedure",
                content=e17_path.read_text(encoding="utf-8"),
                metadata=KnowledgeMetadata(
                    asset_model="ACX-420",
                    error_code="E17",
                    document_type="procedure",
                    safety_level="high_pressure",
                    source="CoolCore SOP Library",
                    version="3.0",
                    date="2025-02-01",
                ),
            )
        )

    # 4. Pressure Safety SOP
    safety_path = KNOWLEDGE_ROOT / "safety" / "pressure_safety_sop.md"
    if safety_path.exists():
        documents.append(
            KnowledgeDocument(
                document_id="doc-sop-safety-press",
                title="High-Pressure Refrigerant Safety SOP (Fictional Demo)",
                document_type="safety_sop",
                content=safety_path.read_text(encoding="utf-8"),
                metadata=KnowledgeMetadata(
                    document_type="safety_sop",
                    safety_level="critical",
                    source="Global Facility Safety Operations",
                    version="4.2",
                    date="2025-06-20",
                ),
            )
        )

    # 5. Unit 017 Service Record as searchable document
    record_path = KNOWLEDGE_ROOT / "service_history" / "unit_017_service_record.json"
    if record_path.exists():
        documents.append(
            KnowledgeDocument(
                document_id="doc-hist-unit017-sr",
                title="Service Record ACX-420-017 (2026-08-14)",
                document_type="service_history",
                content=record_path.read_text(encoding="utf-8"),
                metadata=KnowledgeMetadata(
                    asset_model="ACX-420",
                    asset_id="ACX-420-017",
                    error_code="E17",
                    document_type="service_history",
                    safety_level="standard",
                    source="Field Service CRM",
                    date="2026-08-14",
                ),
            )
        )

    # 6. Unit 017 Maintenance History log
    maint_path = KNOWLEDGE_ROOT / "service_history" / "unit_017_maintenance_history.md"
    if maint_path.exists():
        documents.append(
            KnowledgeDocument(
                document_id="doc-hist-unit017-maint",
                title="Unit ACX-420-017 Equipment Maintenance History",
                document_type="service_history",
                content=maint_path.read_text(encoding="utf-8"),
                metadata=KnowledgeMetadata(
                    asset_model="ACX-420",
                    asset_id="ACX-420-017",
                    document_type="service_history",
                    safety_level="standard",
                    source="Equipment Maintenance Ledger",
                    date="2026-08-14",
                ),
            )
        )

    return documents


def get_demo_asset(asset_id: str) -> Optional[Asset]:
    return DEMO_ASSETS.get(asset_id)


def get_demo_session(session_id: str) -> Optional[TechnicianSession]:
    return DEMO_SESSIONS.get(session_id)


def get_demo_service_records(asset_id: str) -> List[ServiceRecord]:
    return DEMO_SERVICE_RECORDS.get(asset_id, [])


def get_demo_turns(session_id: str) -> List[ConversationTurn]:
    return DEMO_TURNS.get(session_id, [])
