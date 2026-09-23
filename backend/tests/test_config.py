"""Test configuration loading and secret safeguarding."""

from app.config.settings import Settings


def test_default_settings():
    cfg = Settings(
        moss_project_id="",
        moss_project_key="",
        llm_provider="mock",
    )
    assert cfg.environment == "development"
    assert cfg.is_moss_configured is False
    assert cfg.llm_provider == "mock"

    safe_info = cfg.safe_dict()
    assert "moss_project_key" not in safe_info
    assert "gemini_api_key" not in safe_info
    assert safe_info["moss_configured"] is False


def test_moss_configured_flag():
    cfg_unconfigured = Settings(moss_project_id="your_moss_project_id_here", moss_project_key="")
    assert cfg_unconfigured.is_moss_configured is False

    cfg_configured = Settings(moss_project_id="proj_live_123", moss_project_key="sec_key_456")
    assert cfg_configured.is_moss_configured is True
    assert cfg_configured.safe_dict()["moss_configured"] is True
