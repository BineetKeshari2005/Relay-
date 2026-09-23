"""Configuration settings for Relay backend."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    environment: Literal["development", "staging", "production", "test"] = "development"
    service_name: str = "relay-backend"
    version: str = "0.1.0"
    log_level: str = "INFO"

    # Server Bindings
    host: str = "0.0.0.0"
    port: int = 8000

    # Moss Low-Latency Retrieval Engine
    # When unconfigured, MossRetrievalProvider cleanly communicates missing credentials
    # without faking latency or masquerading mock results as Moss results.
    moss_project_id: str = Field(default="", description="Moss project ID")
    moss_project_key: str = Field(default="", description="Moss API secret key")
    moss_base_url: str = Field(
        default="https://api.moss.sh/v1",
        description="Base URL for Moss retrieval API",
    )
    moss_index_name: str = Field(
        default="relay-hvac",
        description="Target Moss index name for equipment knowledge",
    )
    moss_hybrid_alpha: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Hybrid retrieval alpha (1.0 = embedding-only, 0.0 = keyword-only, 0.8 = balanced hybrid)",
    )

    # LLM Provider Configuration
    llm_provider: Literal["mock", "gemini", "openai"] = "mock"
    gemini_api_key: str = Field(default="", description="Gemini API Key")
    openai_api_key: str = Field(default="", description="OpenAI API Key")

    @property
    def is_moss_configured(self) -> bool:
        """Check whether valid Moss credentials are provided."""
        return bool(
            self.moss_project_id
            and self.moss_project_key
            and not self.moss_project_id.startswith("your_")
        )

    def safe_dict(self) -> dict:
        """Return non-sensitive settings dictionary safe for health endpoints and logs."""
        return {
            "environment": self.environment,
            "service_name": self.service_name,
            "version": self.version,
            "log_level": self.log_level,
            "moss_configured": self.is_moss_configured,
            "moss_index_name": self.moss_index_name,
            "moss_hybrid_alpha": self.moss_hybrid_alpha,
            "llm_provider": self.llm_provider,
        }


settings = Settings()
