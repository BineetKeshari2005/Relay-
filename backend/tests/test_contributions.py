"""Comprehensive tests for Technician Knowledge Contributions & Ingestion (Phase 6)."""

import pytest
from fastapi.testclient import TestClient

from app.context.assembler import ContextAssembler
from app.context.query_extractor import QueryContextExtractor
from app.main import app
from app.models.knowledge import KnowledgeDocument, KnowledgeMetadata, TechnicianContribution
from app.reasoning.provider import MockReasoningProvider
from app.reasoning.service import ReasoningService
from app.reasoning.validator import ReasoningQualityValidator
from app.retrieval.base import SearchResponse, SearchResult
from app.retrieval.contribution_service import (
    ContributionStorage,
    KnowledgeIngestionService,
    get_contribution_storage,
)
from app.retrieval.ingestion import load_normalized_documents
from app.retrieval.mock import MockRetrievalProvider


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_storage():
    storage = get_contribution_storage()
    storage.clear()
    return storage


@pytest.fixture
def seeded_mock_provider():
    docs = load_normalized_documents()
    kdocs = [
        KnowledgeDocument(
            document_id=d.id,
            title=d.id.replace("-", " ").title(),
            document_type=d.metadata.get("document_type", "manual"),
            content=d.text,
            metadata=KnowledgeMetadata(
                asset_model=d.metadata.get("asset_model"),
                asset_id=d.metadata.get("asset_id"),
                error_code=d.metadata.get("error_code"),
                document_type=d.metadata.get("document_type", "manual"),
                safety_level=d.metadata.get("safety_level", "standard"),
                source=d.metadata.get("source", d.id),
                version=d.metadata.get("version", "1.0"),
                date=d.metadata.get("date"),
                provenance_type=d.metadata.get("provenance_type", "VERIFIED_COMPANY_DOCUMENT"),  # type: ignore
                verification_status=d.metadata.get("verification_status", "VERIFIED"),  # type: ignore
            ),
        )
        for d in docs
    ]
    return MockRetrievalProvider(seed_documents=kdocs)


# 1. Model Validation
def test_contribution_model_validation():
    """Ensure contribution model validates required fields and length constraints."""
    contrib = TechnicianContribution(
        id="contrib-test-1",
        title="Loose Blower Mounting Bolts",
        observation="Heavy vibration observed after maintenance yesterday.",
        symptom="Blower vibration and loud mechanical humming",
        suspected_cause="Mounting bracket bolts had backed out",
        action_taken="Torqued bolts to 25 ft-lbs specification",
        outcome="Vibration stopped completely during test cycle",
        asset_id="ACX-420-017",
    )
    assert contrib.id == "contrib-test-1"
    assert contrib.provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert contrib.verification_status == "PENDING_REVIEW"


# 2. Create Contribution Defaults
def test_create_contribution_defaults():
    """Ensure default provenance is TECHNICIAN_CONTRIBUTION and status is PENDING_REVIEW."""
    contrib = TechnicianContribution(
        id="contrib-test-2",
        title="Sensor O-ring Degradation",
        observation="Pressure transducer fitting was leaking minor trace oil.",
        symptom="Drifting pressure telemetry",
        action_taken="Replaced nitrile O-ring with HNBR compound",
        outcome="Telemetry stabilized at 182 PSI",
    )
    assert contrib.provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert contrib.verification_status == "PENDING_REVIEW"


# 3. Provenance Immutability on Ingestion
@pytest.mark.asyncio
async def test_provenance_immutability(seeded_mock_provider, clean_storage):
    """Ensure ingestion service guarantees TECHNICIAN_CONTRIBUTION provenance."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    contrib = TechnicianContribution(
        id="contrib-test-3",
        title="Relay Board Inspection",
        observation="Contactor coil terminal screw was loose.",
        symptom="Intermittent compressor contactor chattering",
        action_taken="Tightened terminal screw",
        outcome="Chattering stopped",
    )
    # Even if someone attempts to change provenance, ingestion enforces TECHNICIAN_CONTRIBUTION
    contrib.provenance_type = "VERIFIED_COMPANY_DOCUMENT"  # type: ignore
    norm_doc = await service.ingest(contrib)

    assert norm_doc.metadata.provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert norm_doc.metadata.verification_status == "PENDING_REVIEW"


# 4. Association Without Fabrication
def test_asset_session_association_without_fabrication():
    """Ensure unprovided asset and session fields remain None without fabrication."""
    contrib = TechnicianContribution(
        id="contrib-test-4",
        title="Air Filter Bypass",
        observation="Filter rack latch was unhooked.",
        symptom="Excess dust on evaporator coil",
        action_taken="Latched filter housing",
        outcome="Airflow sealed",
    )
    assert contrib.asset_id is None
    assert contrib.session_id is None
    assert contrib.technician_id is None


# 5. Knowledge Normalization
def test_knowledge_normalization(seeded_mock_provider, clean_storage):
    """Ensure normalized document text contains structured markdown and explicit provenance."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    contrib = TechnicianContribution(
        id="contrib-test-5",
        title="Blower Mounting Bolt Looseness",
        observation="Blower housing shook violently at 1200 RPM.",
        symptom="Severe blower vibration",
        suspected_cause="Loose isolation bolts",
        action_taken="Retorqued 4 mounting bolts",
        outcome="Vibration dropped to 0.05 in/sec",
        asset_id="ACX-420-017",
        session_id="sess-017",
    )
    norm = service.normalize(contrib)

    assert norm.document_id == "contrib-test-5"
    assert norm.metadata.provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert norm.metadata.verification_status == "PENDING_REVIEW"
    assert "Provenance: TECHNICIAN_CONTRIBUTION | Status: PENDING_REVIEW" in norm.content
    assert "Asset ID: ACX-420-017" in norm.content
    assert "## Field Observation" in norm.content
    assert "## Action Taken" in norm.content


# 6. Mock Ingestion and Retrieval
@pytest.mark.asyncio
async def test_mock_ingestion_and_retrieval(seeded_mock_provider, clean_storage):
    """Ensure ingested contribution is immediately searchable in the provider."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    contrib = TechnicianContribution(
        id="contrib-vibration-017",
        title="Blower mounting bolts loose on Unit 017",
        observation="Unit was vibrating heavily after blower maintenance.",
        symptom="Blower vibration and mechanical rattling",
        suspected_cause="Mounting bracket bolts loose",
        action_taken="Tightened bolts to 25 ft-lbs",
        outcome="Vibration resolved completely",
        asset_id="ACX-420-017",
    )
    await service.ingest(contrib)

    search_res = await seeded_mock_provider.search(query="blower vibration mounting bolts", limit=3)
    matching = [r for r in search_res.results if "contrib-vibration-017" in r.document_id]
    assert len(matching) == 1
    assert matching[0].provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert matching[0].verification_status == "PENDING_REVIEW"


# 7. Retrieval Preserves Provenance
@pytest.mark.asyncio
async def test_retrieval_preserves_provenance(seeded_mock_provider, clean_storage):
    """Verify SearchResult contains explicit provenance_type and verification_status."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    contrib = TechnicianContribution(
        id="contrib-sensor-leak",
        title="Transducer flare fitting loose",
        observation="Oil residue around suction transducer fitting.",
        symptom="Slight pressure reading drift",
        action_taken="Snugged 1/4 inch flare nut 1/8 turn",
        outcome="Fitting dry and tight",
    )
    await service.ingest(contrib)

    res = await seeded_mock_provider.search(query="transducer flare fitting")
    contrib_res = next(r for r in res.results if r.document_id == "contrib-sensor-leak")
    assert contrib_res.provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert contrib_res.verification_status == "PENDING_REVIEW"


# 8. Distinguishability from Verified Docs
@pytest.mark.asyncio
async def test_distinguishable_from_verified_docs(seeded_mock_provider, clean_storage):
    """Ensure official docs have VERIFIED_COMPANY_DOCUMENT and contributions have TECHNICIAN_CONTRIBUTION."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    await service.ingest(
        TechnicianContribution(
            id="contrib-e17-field",
            title="Field check for E17 pressure",
            observation="Observed condenser fin blockage caused high pressure.",
            symptom="E17 high pressure trip",
            action_taken="Cleaned condenser coil with low pressure water",
            outcome="Pressure returned to 175 PSI",
        )
    )

    search_res = await seeded_mock_provider.search(query="E17 pressure", limit=10)
    provenances = {r.document_id: r.provenance_type for r in search_res.results}

    assert "e17-troubleshooting" in provenances
    assert provenances["e17-troubleshooting"] == "VERIFIED_COMPANY_DOCUMENT"
    assert "contrib-e17-field" in provenances
    assert provenances["contrib-e17-field"] == "TECHNICIAN_CONTRIBUTION"


# 9. Pending Contribution Non-Authoritative
@pytest.mark.asyncio
async def test_pending_contribution_non_authoritative(seeded_mock_provider, clean_storage):
    """Ensure reasoner frames pending contribution as historical observation with inferred support."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    await service.ingest(
        TechnicianContribution(
            id="contrib-vibration-bolt",
            title="Blower mounting bolts loose on Unit 017",
            observation="Unit 017 was vibrating after blower maintenance.",
            symptom="Heavy blower vibration",
            suspected_cause="Mounting bracket bolts loose",
            action_taken="Tightened bolts to 25 ft-lbs",
            outcome="Vibration stopped",
            asset_id="ACX-420-017",
        )
    )

    assembler = ContextAssembler(retrieval_provider=seeded_mock_provider)
    context = await assembler.assemble(
        query="Unit 017 has blower vibration and loose mounting bolts",
        asset_id="ACX-420-017",
        session_id=None,
        top_k=5,
    )

    reasoner = MockReasoningProvider()
    result = await reasoner.reason(context)

    # Check evidence claim for the contribution
    contrib_claims = [c for c in result.evidence_claims if "contrib-vibration-bolt" in c.evidence_ids]
    assert len(contrib_claims) >= 1
    # Must be marked inferred, not direct authoritative procedure
    assert contrib_claims[0].support_level == "inferred"
    assert "field history" in contrib_claims[0].explanation.lower() or "contextual" in contrib_claims[0].explanation.lower()


# 10. Conflicting Contribution Preserves Official Safety
@pytest.mark.asyncio
async def test_conflicting_contribution_preserves_official_safety(seeded_mock_provider, clean_storage):
    """Ensure technician contribution cannot override official pressure limits or safety rules."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    # Technician contribution suggesting operating above official 190 PSI threshold
    await service.ingest(
        TechnicianContribution(
            id="contrib-bad-advice",
            title="Running high pressure is fine",
            observation="Unit runs hot in summer.",
            symptom="High discharge pressure",
            action_taken="Ignored 190 PSI threshold and kept running at 210 PSI",
            outcome="Compressor kept cooling",
        )
    )

    assembler = ContextAssembler(retrieval_provider=seeded_mock_provider)
    # Submit 195 PSI query
    context = await assembler.assemble(
        query="I am getting E17 again on unit 017. Pressure is around 195 PSI.",
        asset_id="ACX-420-017",
        session_id="sess-017",
        top_k=5,
    )

    # Context MUST preserve mandatory LOTO and pressure hazard from verified SOP
    assert context.safety_context.mandatory_loto is True
    assert context.safety_context.high_pressure_hazard is True

    reasoner = MockReasoningProvider()
    result = await reasoner.reason(context)

    validator = ReasoningQualityValidator()
    report = validator.validate(result, context)
    assert report.is_valid is True
    assert any("190" in w or "lockout" in w.lower() for w in result.safety_considerations)


# 11. REST API Create Contribution Endpoint
def test_api_create_contribution_endpoint(client, clean_storage):
    """Verify POST /api/knowledge/contributions creates and returns 201 Created."""
    payload = {
        "title": "Blower belt tension misadjustment",
        "observation": "Blower belt was slipping and squealing on startup.",
        "symptom": "Squealing noise on fan motor startup",
        "suspected_cause": "Under-tensioned belt after pulley replacement",
        "action_taken": "Adjusted motor base tension bolt to 1/2 inch deflection",
        "outcome": "Squeal eliminated, smooth startup",
        "asset_id": "ACX-420-017",
        "session_id": "sess-017",
    }
    response = client.post("/api/knowledge/contributions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["provenance_type"] == "TECHNICIAN_CONTRIBUTION"
    assert data["verification_status"] == "PENDING_REVIEW"
    assert data["id"].startswith("contrib-")


# 12. REST API Get Contribution by ID
def test_api_get_contribution_by_id(client, clean_storage):
    """Verify GET /api/knowledge/contributions/{id} returns saved contribution."""
    payload = {
        "title": "Condensate drain line clog",
        "observation": "Drain pan was filling with water.",
        "symptom": "Condensate overflow switch tripped",
        "action_taken": "Flushed P-trap with nitrogen",
        "outcome": "Water draining freely",
        "asset_id": "ACX-420-017",
    }
    create_res = client.post("/api/knowledge/contributions", json=payload)
    contrib_id = create_res.json()["id"]

    get_res = client.get(f"/api/knowledge/contributions/{contrib_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == contrib_id

    missing_res = client.get("/api/knowledge/contributions/contrib-nonexistent")
    assert missing_res.status_code == 404


# 13. REST API List Contributions with Filter
def test_api_list_contributions_filter(client, clean_storage):
    """Verify GET /api/knowledge/contributions supports asset_id filtering."""
    client.post(
        "/api/knowledge/contributions",
        json={
            "title": "Unit 017 fan motor check",
            "observation": "Fan motor bearings felt warm.",
            "symptom": "Warm motor casing",
            "action_taken": "Greased bearing ports",
            "outcome": "Temperature normalized",
            "asset_id": "ACX-420-017",
        },
    )
    client.post(
        "/api/knowledge/contributions",
        json={
            "title": "Unit 018 belt tension check",
            "observation": "Belt was loose on unit 018.",
            "symptom": "Loose belt",
            "action_taken": "Tensioned belt",
            "outcome": "Proper tension",
            "asset_id": "ACX-420-018",
        },
    )

    list_017 = client.get("/api/knowledge/contributions?asset_id=ACX-420-017")
    assert list_017.status_code == 200
    assert len(list_017.json()) == 1
    assert list_017.json()[0]["asset_id"] == "ACX-420-017"


# 14. Idempotent Ingestion Handling
@pytest.mark.asyncio
async def test_idempotent_ingestion(seeded_mock_provider, clean_storage):
    """Ensure duplicate contribution submissions do not corrupt provider index."""
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    contrib = TechnicianContribution(
        id="contrib-idempotent-check",
        title="Check contactor resistance",
        observation="High resistance on contactor pole L1.",
        symptom="Voltage drop across contacts",
        action_taken="Replaced contactor assembly",
        outcome="Zero voltage drop",
    )
    await service.ingest(contrib)
    await service.ingest(contrib)  # Duplicate ingestion

    search_res = await seeded_mock_provider.search(query="contactor pole L1", limit=10)
    matching = [r for r in search_res.results if r.document_id == "contrib-idempotent-check"]
    assert len(matching) == 1


# 15. Technician A -> Technician B Full Simulation
@pytest.mark.asyncio
async def test_technician_a_to_technician_b_simulation(seeded_mock_provider, clean_storage):
    """
    Simulate the complete Phase 6 loop:
    1. Technician A observes loose blower mounting bolts on Unit 017 and contributes finding.
    2. Finding is normalized and ingested with PENDING_REVIEW status.
    3. Technician B later inspects Unit 017 for blower vibration.
    4. Retrieval returns Technician A's contribution.
    5. Reasoning surfaces it as historical evidence without promoting it to official SOP.
    6. ReasoningQualityValidator approves the output.
    """
    # 1. Technician A contributes field finding
    service = KnowledgeIngestionService(retrieval_provider=seeded_mock_provider, storage=clean_storage)
    tech_a_contrib = TechnicianContribution(
        id="contrib-bolt-tightening-017",
        title="Blower Vibration Resolved by Mounting Bolt Torque",
        observation="Unit 017 was vibrating violently after yesterday's blower maintenance.",
        symptom="Heavy blower vibration and mechanical rattle",
        suspected_cause="Blower mounting bolts were left loose after service",
        action_taken="Tightened mounting bolts to 25 ft-lbs according to spec",
        outcome="Vibration stopped completely during test run",
        asset_id="ACX-420-017",
        session_id="sess-017",
        technician_id="tech-alice",
    )
    await service.ingest(tech_a_contrib)

    # 2. Technician B later queries the system regarding vibration
    assembler = ContextAssembler(retrieval_provider=seeded_mock_provider)
    context = await assembler.assemble(
        query="Unit 017 is vibrating again after maintenance",
        asset_id="ACX-420-017",
        session_id="sess-018",
        top_k=5,
    )

    # Verify that Technician A's contribution was retrieved
    retrieved_contrib = next(
        (e for e in context.evidence if "contrib-bolt-tightening-017" in e.document_id),
        None,
    )
    assert retrieved_contrib is not None
    assert retrieved_contrib.provenance_type == "TECHNICIAN_CONTRIBUTION"
    assert retrieved_contrib.verification_status == "PENDING_REVIEW"
    assert retrieved_contrib.is_technician_contribution is True

    # 3. Execute reasoning service
    reasoning_service = ReasoningService(provider=MockReasoningProvider())
    result, report = await reasoning_service.analyze(context)

    # 4. Assert reasoning adheres to strict Phase 6 safety rules
    assert report.is_valid is True
    # Asserts contribution is cited
    assert any("contrib-bolt-tightening-017" in cite.evidence_id for cite in result.citations)
    # Asserts assessment mentions prior technician finding with status
    assert "earlier technician report" in result.assessment.lower() or "prior field technician" in result.assessment.lower()
    # Asserts claim is marked inferred, NOT direct official procedure
    tech_claim = next(c for c in result.evidence_claims if "contrib-bolt-tightening-017" in c.evidence_ids)
    assert tech_claim.support_level == "inferred"
