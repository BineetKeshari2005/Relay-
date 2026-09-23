"""Tests for Moss retrieval pipeline, normalization, filter translation, and API."""

import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.config.settings import Settings
from app.main import app
from app.retrieval.base import SearchResponse, SearchResult
from app.retrieval.ingestion import load_normalized_documents
from app.retrieval.moss import (
    MossConfigurationError,
    MossRetrievalProvider,
    translate_filters_to_moss,
)


def test_knowledge_normalization_and_stable_ids():
    """Verify all 6 documents are parsed with stable, deterministic IDs and string metadata."""
    docs = load_normalized_documents()
    assert len(docs) == 6

    expected_ids = {
        "acx420-technical-manual",
        "acx420-troubleshooting-guide",
        "e17-troubleshooting",
        "pressure-safety-sop",
        "unit-017-service-record",
        "unit-017-maintenance-history",
    }
    actual_ids = {doc.id for doc in docs}
    assert actual_ids == expected_ids

    for doc in docs:
        assert doc.id != ""
        assert len(doc.text) > 50
        assert "source" in doc.metadata
        assert "document_type" in doc.metadata
        # Check all metadata values are strings (required by Moss DocumentInfo)
        for k, v in doc.metadata.items():
            assert isinstance(v, str), f"Metadata field '{k}' in {doc.id} must be string, got {type(v)}"


def test_filter_translation_to_moss():
    """Test translating internal Relay metadata filters to Moss DSL."""
    # Empty or None
    assert translate_filters_to_moss(None) is None
    assert translate_filters_to_moss({}) is None

    # Single filter
    single = translate_filters_to_moss({"asset_model": "ACX-420"})
    assert single == {"$and": [{"field": "asset_model", "condition": {"$eq": "ACX-420"}}]}

    # Multiple filters
    multiple = translate_filters_to_moss({"asset_model": "ACX-420", "error_code": "E17"})
    assert multiple == {
        "$and": [
            {"field": "asset_model", "condition": {"$eq": "ACX-420"}},
            {"field": "error_code", "condition": {"$eq": "E17"}},
        ]
    }

    # List filter with $in
    in_filter = translate_filters_to_moss({"document_type": ["manual", "procedure"]})
    assert in_filter == {
        "$and": [
            {"field": "document_type", "condition": {"$in": ["manual", "procedure"]}},
        ]
    }


def test_moss_provider_unconfigured():
    """Test Moss provider behavior when credentials are intentionally blank."""
    cfg = Settings(moss_project_id="", moss_project_key="")
    provider = MossRetrievalProvider(config=cfg)
    assert provider.status == "unconfigured"
    assert provider.is_configured() is False

    status_dict = provider.get_status_dict()
    assert status_dict["status"] == "unconfigured"
    assert status_dict["configured"] is False
    assert "moss_project_key" not in status_dict


@pytest.mark.asyncio
async def test_api_retrieval_health():
    """Test GET /api/retrieval/health returns provider readiness without credentials."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/retrieval/health")
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "status" in data
        assert "index" in data
        assert "configured" in data
        assert "default_alpha" in data
        # Ensure no secrets in payload
        assert "project_key" not in data
        assert "api_key" not in data


@pytest.mark.asyncio
async def test_api_retrieval_search_validation():
    """Test input validation on POST /api/retrieval/search."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty query should fail validation (min_length=1)
        resp = await client.post("/api/retrieval/search", json={"query": ""})
        assert resp.status_code == 422

        # Invalid top_k (< 1)
        resp2 = await client.post("/api/retrieval/search", json={"query": "E17", "top_k": 0})
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_api_retrieval_search_execution():
    """Test POST /api/retrieval/search executes query and returns structured response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "query": "I'm getting E17 again on unit 017. Pressure is around 195 PSI.",
            "top_k": 3,
        }
        resp = await client.post("/api/retrieval/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == payload["query"]
        assert len(data["results"]) <= 3
        assert data["result_count"] == len(data["results"])
        assert data["latency_ms"] >= 0.0
        assert data["provider"] in ["moss", "mock-retrieval"]

        for item in data["results"]:
            assert "id" in item
            assert "text" in item
            assert "metadata" in item


# Optional integration test marked with 'integration'
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_moss_integration_query():
    """Integration test connecting to the live Moss index."""
    pid = os.environ.get("MOSS_PROJECT_ID")
    pkey = os.environ.get("MOSS_PROJECT_KEY")

    if not pid or not pkey or pid.startswith("your_"):
        pytest.skip("Moss credentials not available in environment.")

    provider = MossRetrievalProvider()
    await provider.load()
    if not provider._is_index_loaded:
        pytest.skip("Moss index could not be loaded from remote cloud (credits exhausted).")
    assert provider.status == "ready"

    resp = await provider.search("E17 high pressure trip", limit=3)
    assert resp.provider == "moss"
    assert resp.latency_ms is not None
    assert len(resp.results) > 0
    top_ids = [r.chunk_id for r in resp.results]
    assert any(exp in top_ids for exp in ["e17-troubleshooting", "acx420-troubleshooting-guide", "unit-017-service-record"])
