"""Configuration settings for Named."""

from pathlib import Path
from typing import Optional

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

    # Analysis settings
    confidence_threshold: float = Field(
        default=0.80, description="Minimum confidence threshold for suggestions"
    )

    # Output settings
    output_format: str = Field(
        default="all", description="Output format: json, md, or all"
    )


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
