"""Factory for creating OpenAI-compatible API clients."""

from openai import OpenAI

from named.config import get_settings
from named.logging import get_logger

logger = get_logger("client_factory")


def create_openai_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    """Create an OpenAI client, optionally configured for Azure AI Foundry.

    Args:
        api_key: API key override. Falls back to settings.openai_api_key.
        base_url: Base URL override. Falls back to settings.openai_base_url.
            For Azure AI Foundry, use:
              https://RESOURCE.openai.azure.com/openai/v1/

    Returns:
        Configured OpenAI client instance.

    Raises:
        ValueError: If no API key is available.
    """
    settings = get_settings()

    resolved_key = api_key or settings.openai_api_key
    resolved_url = base_url or settings.openai_base_url or None

    if not resolved_key:
        raise ValueError(
            "API key not provided. Set NAMED_OPENAI_API_KEY environment variable "
            "or pass api_key parameter."
        )

    kwargs: dict = {"api_key": resolved_key}
    if resolved_url:
        kwargs["base_url"] = resolved_url
        logger.info(f"Using custom API endpoint: {resolved_url}")

    return OpenAI(**kwargs)
