"""Test demo endpoints and error handling."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_get_demo_asset_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/demo/asset/ACX-420-017")
        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == "ACX-420-017"
        assert data["model"] == "ACX-420"
        assert data["manufacturer"] == "CoolCore"


@pytest.mark.asyncio
async def test_get_demo_asset_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/demo/asset/UNKNOWN-999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "AssetNotFound"


@pytest.mark.asyncio
async def test_get_demo_session_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/demo/session/sess-017")
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["session_id"] == "sess-017"
        assert data["session"]["current_error_code"] == "E17"
        assert data["asset"]["model"] == "ACX-420"
        assert len(data["recent_turns"]) >= 1
        assert len(data["service_history"]) >= 1


@pytest.mark.asyncio
async def test_get_demo_session_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/demo/session/sess-nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "SessionNotFound"
