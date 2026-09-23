"""Test retrieval abstraction and provider implementations."""

import pytest
from app.config.settings import Settings
from app.data.demo_fixtures import load_demo_knowledge_documents
from app.retrieval.base import RetrievalProvider
from app.retrieval.mock import MockRetrievalProvider
from app.retrieval.moss import MossConfigurationError, MossRetrievalProvider


@pytest.mark.asyncio
async def test_mock_retrieval_search():
    docs = load_demo_knowledge_documents()
    assert len(docs) > 0

    provider = MockRetrievalProvider(seed_documents=docs)
    assert isinstance(provider, RetrievalProvider)
    assert provider.name == "mock-retrieval"

    # Search for E17 procedure
    response = await provider.search(query="E17 high-pressure airflow", limit=3)
    assert response.provider == "mock-retrieval"
    assert response.total_count > 0
    assert len(response.results) <= 3
    assert response.latency_ms is not None
    assert response.latency_ms >= 0.0

    # Top result should match E17 or high pressure
    top_result = response.results[0]
    assert "e17" in top_result.title.lower() or "pressure" in top_result.title.lower() or "acx-420" in top_result.title.lower()


@pytest.mark.asyncio
async def test_mock_retrieval_filtering():
    docs = load_demo_knowledge_documents()
    provider = MockRetrievalProvider(seed_documents=docs)

    # Filter strictly by document_type = "safety_sop"
    response = await provider.search(query="", filters={"document_type": "safety_sop"}, limit=5)
    assert response.total_count >= 1
    for item in response.results:
        assert item.metadata.get("document_type") == "safety_sop"


@pytest.mark.asyncio
async def test_moss_retrieval_unconfigured_error():
    # Test that Moss provider refuses to fake credentials or mock results
    unconfigured_settings = Settings(
        moss_project_id="",
        moss_project_key="",
    )
    moss_provider = MossRetrievalProvider(config=unconfigured_settings)
    assert moss_provider.name == "moss"
    assert not moss_provider.is_configured()

    with pytest.raises(MossConfigurationError) as exc_info:
        await moss_provider.search("high pressure E17")
    assert "Moss is not configured" in str(exc_info.value)
