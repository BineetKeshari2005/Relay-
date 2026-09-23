"""API Contract and Schema Validation Tests for Relay FastAPI Endpoints.

Verifies:
1. Valid request / response schemas.
2. 422 Unprocessable Entity on missing required fields or constraint violations.
3. 404 Not Found on missing resources.
4. Absence of leaked secret keys or internal stack traces.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_api_retrieval_search_contracts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid request
        resp = await client.post("/api/retrieval/search", json={"query": "discharge pressure sensor", "top_k": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "results" in data
        assert "latency_ms" in data
        assert isinstance(data["results"], list)

        # 2. Missing query field (422)
        resp_missing = await client.post("/api/retrieval/search", json={"top_k": 3})
        assert resp_missing.status_code == 422

        # 3. Empty query string (min_length=1 violation -> 422)
        resp_empty = await client.post("/api/retrieval/search", json={"query": ""})
        assert resp_empty.status_code == 422

        # 4. Out of bounds top_k (>20 -> 422)
        resp_oob = await client.post("/api/retrieval/search", json={"query": "test", "top_k": 99})
        assert resp_oob.status_code == 422


@pytest.mark.asyncio
async def test_api_retrieval_health_contract_no_secrets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/retrieval/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "status" in data
        assert "index" in data
        assert "configured" in data
        # Secrets MUST NOT be exposed
        assert "key" not in data
        assert "project_key" not in data
        assert "api_key" not in data


@pytest.mark.asyncio
async def test_api_context_assemble_contracts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid request
        resp = await client.post("/api/context/assemble", json={"query": "E17 error code on unit 017"})
        assert resp.status_code == 200
        data = resp.json()
        assert "context" in data
        assert "quality_report" in data
        assert "technician_query" in data["context"]
        assert "query_facts" in data["context"]
        assert "evidence" in data["context"]
        assert "safety_context" in data["context"]

        # 2. Missing required query (422)
        resp_missing = await client.post("/api/context/assemble", json={"top_k": 3})
        assert resp_missing.status_code == 422

        # 3. Empty string query (422)
        resp_empty = await client.post("/api/context/assemble", json={"query": ""})
        assert resp_empty.status_code == 422


@pytest.mark.asyncio
async def test_api_reasoning_analyze_contracts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid request
        resp = await client.post(
            "/api/reasoning/analyze",
            json={"query": "Check system pressures on unit 017"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "context" in data
        assert "reasoning" in data
        assert "validation_report" in data
        assert "spoken_response" in data["reasoning"]

        # 2. Missing required query (422)
        resp_missing = await client.post("/api/reasoning/analyze", json={})
        assert resp_missing.status_code == 422

        # 3. Empty string query (422)
        resp_empty = await client.post("/api/reasoning/analyze", json={"query": ""})
        assert resp_empty.status_code == 422


@pytest.mark.asyncio
async def test_api_knowledge_contributions_contracts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid creation (201)
        resp = await client.post(
            "/api/knowledge/contributions",
            json={
                "title": "Contract test finding for loose belt",
                "action_taken": "Tightened fan belt tension to 1/2 inch deflection",
                "asset_id": "ACX-420-017",
            },
        )
        assert resp.status_code == 201
        created = resp.json()
        assert "id" in created
        assert created["provenance_type"] == "TECHNICIAN_CONTRIBUTION"
        assert created["verification_status"] == "PENDING_REVIEW"
        created_id = created["id"]

        # 2. Get by ID (200)
        get_resp = await client.get(f"/api/knowledge/contributions/{created_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == created_id

        # 3. Get non-existent ID (404)
        get_404 = await client.get("/api/knowledge/contributions/contrib-nonexistent-999")
        assert get_404.status_code == 404

        # 4. List contributions (200)
        list_resp = await client.get("/api/knowledge/contributions")
        assert list_resp.status_code == 200
        assert isinstance(list_resp.json(), list)

        # 5. Missing required action_taken (422)
        resp_missing = await client.post(
            "/api/knowledge/contributions",
            json={"title": "Missing action taken"},
        )
        assert resp_missing.status_code == 422

        # 6. Title too short (<3 chars -> 422)
        resp_short = await client.post(
            "/api/knowledge/contributions",
            json={"title": "hi", "action_taken": "did something"},
        )
        assert resp_short.status_code == 422


@pytest.mark.asyncio
async def test_api_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.get("/health")
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "ok"

        resp2 = await client.get("/api/health")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"
