"""Configuration settings for Named."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="NAMED_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # OpenAI settings
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")
    openai_base_url: str = Field(
        default="",
        description="Custom base URL for OpenAI-compatible API (e.g., Azure AI Foundry)",
    )

    # Azure Workload Identity (env vars without NAMED_ prefix)
    azure_openai_endpoint: str = Field(default="", validation_alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str = Field(default="", validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_client_id: str = Field(default="", validation_alias="AZURE_CLIENT_ID")
    azure_openai_api_version: str = Field(
        default="2025-01-01-preview", validation_alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_batch_deployment_name: str = Field(
        default="",
        description="Deployment for batch jobs (e.g. gpt-4o-batch-v1). If set, batch mode uses this instead of AZURE_OPENAI_DEPLOYMENT_NAME.",
        validation_alias="AZURE_OPENAI_BATCH_DEPLOYMENT_NAME",
    )

    def effective_openai_model(self) -> str:
        """Model/deployment for streaming (and batch if no batch-specific one)."""
        if self.azure_openai_endpoint and self.azure_openai_deployment_name:
            return self.azure_openai_deployment_name
        return self.openai_model

    def effective_batch_model(self) -> str:
        """Model/deployment for batch API (use batch deployment if configured)."""
        if self.azure_openai_batch_deployment_name:
            return self.azure_openai_batch_deployment_name
        return self.effective_openai_model()

    # Analysis settings
    confidence_threshold: float = Field(
        default=0.80, description="Minimum confidence threshold for suggestions"
    )

    # Output settings
    output_format: str = Field(default="all", description="Output format: json, md, or all")

    # Batch processing settings
    batch_mode: bool = Field(default=False, description="Use batch API for analysis")
    batch_size: int = Field(default=50, description="Symbols per batch (1-100)")
    batch_poll_interval: int = Field(
        default=60, description="Seconds between status checks"
    )
    batch_timeout: int = Field(
        default=25 * 3600, description="Max wait time in seconds (25 hours)"
    )


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
