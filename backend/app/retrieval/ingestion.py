"""Knowledge normalization and ingestion pipeline for Moss with explicit provenance."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from moss import DocumentInfo
except ImportError:
    # Graceful fallback for environments where moss is not yet installed
    DocumentInfo = Any  # type: ignore

KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "knowledge"


class NormalizedKnowledgeDocument(BaseModel):
    """Normalized document representation for ingestion into Moss."""

    id: str = Field(..., description="Deterministic, human-readable unique document ID")
    text: str = Field(..., description="Raw or formatted text content")
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="String key-value metadata attributes for Moss filtering",
    )

    def to_moss_document(self) -> Any:
        """Convert normalized document to a moss.DocumentInfo instance."""
        from moss import DocumentInfo
        return DocumentInfo(
            id=self.id,
            text=self.text,
            metadata=self.metadata,
        )


def load_normalized_documents(base_path: Optional[Path] = None) -> List[NormalizedKnowledgeDocument]:
    """
    Read all fictional HVAC documents from the knowledge repository and
    normalize them into deterministic documents with validated string metadata and provenance.
    """
    root = base_path or KNOWLEDGE_ROOT
    docs: List[NormalizedKnowledgeDocument] = []

    # 1. ACX-420 Technical Manual
    manual_file = root / "manuals" / "acx420_technical_manual.md"
    if manual_file.exists():
        docs.append(
            NormalizedKnowledgeDocument(
                id="acx420-technical-manual",
                text=manual_file.read_text(encoding="utf-8").strip(),
                metadata={
                    "source": "acx420_technical_manual.md",
                    "document_type": "technical_manual",
                    "asset_model": "ACX-420",
                    "asset_id": "all",
                    "error_code": "general",
                    "safety_level": "standard",
                    "version": "2.1",
                    "date": "2024-01-10",
                    "provenance_type": "MANUFACTURER_DOCUMENT",
                    "verification_status": "VERIFIED",
                },
            )
        )

    # 2. ACX-420 Troubleshooting Guide
    tb_file = root / "procedures" / "acx420_troubleshooting_guide.md"
    if tb_file.exists():
        docs.append(
            NormalizedKnowledgeDocument(
                id="acx420-troubleshooting-guide",
                text=tb_file.read_text(encoding="utf-8").strip(),
                metadata={
                    "source": "acx420_troubleshooting_guide.md",
                    "document_type": "troubleshooting_guide",
                    "asset_model": "ACX-420",
                    "asset_id": "all",
                    "error_code": "E17",
                    "safety_level": "warning",
                    "version": "1.4",
                    "date": "2024-05-15",
                    "provenance_type": "VERIFIED_COMPANY_DOCUMENT",
                    "verification_status": "VERIFIED",
                },
            )
        )

    # 3. E17 Troubleshooting Procedure
    e17_file = root / "procedures" / "e17_troubleshooting_procedure.md"
    if e17_file.exists():
        docs.append(
            NormalizedKnowledgeDocument(
                id="e17-troubleshooting",
                text=e17_file.read_text(encoding="utf-8").strip(),
                metadata={
                    "source": "e17_troubleshooting_procedure.md",
                    "document_type": "troubleshooting_procedure",
                    "asset_model": "ACX-420",
                    "asset_id": "ACX-420-017",
                    "error_code": "E17",
                    "safety_level": "high_pressure",
                    "version": "3.0",
                    "date": "2025-02-01",
                    "provenance_type": "VERIFIED_COMPANY_DOCUMENT",
                    "verification_status": "VERIFIED",
                },
            )
        )

    # 4. Pressure Safety SOP
    safety_file = root / "safety" / "pressure_safety_sop.md"
    if safety_file.exists():
        docs.append(
            NormalizedKnowledgeDocument(
                id="pressure-safety-sop",
                text=safety_file.read_text(encoding="utf-8").strip(),
                metadata={
                    "source": "pressure_safety_sop.md",
                    "document_type": "safety_sop",
                    "asset_model": "all",
                    "asset_id": "all",
                    "error_code": "general",
                    "safety_level": "critical",
                    "version": "4.2",
                    "date": "2025-06-20",
                    "provenance_type": "VERIFIED_COMPANY_DOCUMENT",
                    "verification_status": "VERIFIED",
                },
            )
        )

    # 5. Unit 017 Service Record
    sr_file = root / "service_history" / "unit_017_service_record.json"
    if sr_file.exists():
        raw_sr = sr_file.read_text(encoding="utf-8").strip()
        sr_json = json.loads(raw_sr)
        formatted_sr_text = (
            f"# Service Record: {sr_json.get('record_id')}\n"
            f"Asset ID: {sr_json.get('asset_id')}\n"
            f"Date: {sr_json.get('date')}\n"
            f"Issue: {sr_json.get('issue')}\n"
            f"Diagnosis: {sr_json.get('diagnosis')}\n"
            f"Action Taken: {sr_json.get('action_taken')}\n"
            f"Parts Replaced: {', '.join(sr_json.get('parts_replaced', []))}\n"
            f"Technician Notes: {sr_json.get('technician_notes')}\n"
        )
        docs.append(
            NormalizedKnowledgeDocument(
                id="unit-017-service-record",
                text=formatted_sr_text,
                metadata={
                    "source": "unit_017_service_record.json",
                    "document_type": "service_record",
                    "asset_model": "ACX-420",
                    "asset_id": "ACX-420-017",
                    "error_code": "E17",
                    "safety_level": "standard",
                    "version": "1.0",
                    "date": str(sr_json.get("date", "2026-08-14")),
                    "provenance_type": "HISTORICAL_SERVICE_RECORD",
                    "verification_status": "VERIFIED",
                },
            )
        )

    # 6. Unit 017 Maintenance History
    maint_file = root / "service_history" / "unit_017_maintenance_history.md"
    if maint_file.exists():
        docs.append(
            NormalizedKnowledgeDocument(
                id="unit-017-maintenance-history",
                text=maint_file.read_text(encoding="utf-8").strip(),
                metadata={
                    "source": "unit_017_maintenance_history.md",
                    "document_type": "maintenance_history",
                    "asset_model": "ACX-420",
                    "asset_id": "ACX-420-017",
                    "error_code": "E17",
                    "safety_level": "standard",
                    "version": "1.0",
                    "date": "2026-08-14",
                    "provenance_type": "HISTORICAL_SERVICE_RECORD",
                    "verification_status": "VERIFIED",
                },
            )
        )

    return docs


def load_moss_document_infos(base_path: Optional[Path] = None) -> List[Any]:
    """Load normalized documents as a list of moss.DocumentInfo objects."""
    normalized = load_normalized_documents(base_path)
    return [doc.to_moss_document() for doc in normalized]
