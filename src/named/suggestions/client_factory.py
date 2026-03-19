"""Factory for creating OpenAI-compatible API clients."""

from typing import Union

from openai import AzureOpenAI, OpenAI

from named.config import get_settings
from named.logging import get_logger

logger = get_logger("client_factory")


def create_openai_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> Union[OpenAI, AzureOpenAI]:
    """Create an OpenAI client for OpenAI, Azure AI Foundry (API key), or Azure Workload Identity.

    When AZURE_OPENAI_ENDPOINT is set (e.g. in AKS with workload identity), uses
    AzureOpenAI + DefaultAzureCredential + azure_ad_token_provider.
    Otherwise uses NAMED_OPENAI_API_KEY and optional NAMED_OPENAI_BASE_URL.

    Args:
        api_key: API key override. Ignored when Azure Workload Identity env vars are set.
        base_url: Base URL override. Ignored when AZURE_OPENAI_ENDPOINT is set.

    Returns:
        Configured OpenAI or AzureOpenAI client instance.

    Raises:
        ValueError: If neither Azure endpoint nor API key is available.
    """
    settings = get_settings()

    # Azure Workload Identity
    if settings.azure_openai_endpoint:
        try:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        except ImportError as e:
            raise ValueError(
                "Azure Workload Identity requires azure-identity. Install with: pip install azure-identity"
            ) from e
        deployment = settings.azure_openai_deployment_name or "gpt-4o"
        credential = DefaultAzureCredential(
            managed_identity_client_id=settings.azure_client_id or None
        )
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        api_version = settings.azure_openai_api_version or "2025-01-01-preview"
        endpoint = settings.azure_openai_endpoint.rstrip("/")
        logger.info(
            f"Using Azure Workload Identity (AzureOpenAI): endpoint={endpoint}, "
            f"deployment={deployment}, api_version={api_version}"
        )
        return AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )

    # API key (OpenAI or Azure AI Foundry with key)
    resolved_key = api_key or settings.openai_api_key
    resolved_url = base_url or settings.openai_base_url or None

    if not resolved_key:
        raise ValueError(
            "API key not provided. Set NAMED_OPENAI_API_KEY, or for Azure Workload Identity "
            "set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT_NAME (and optionally AZURE_CLIENT_ID)."
        )

    kwargs: dict = {"api_key": resolved_key}
    if resolved_url:
        kwargs["base_url"] = resolved_url
        logger.info(f"Using custom API endpoint: {resolved_url}")

    return OpenAI(**kwargs)
