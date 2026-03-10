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
