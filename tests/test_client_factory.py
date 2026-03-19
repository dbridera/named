"""Tests for the OpenAI client factory."""

from unittest.mock import Mock, patch

import pytest

from named.suggestions.client_factory import create_openai_client


def _mock_settings(**overrides):
    """Create a mock settings object with sensible defaults for all fields."""
    defaults = {
        "openai_api_key": "",
        "openai_base_url": "",
        "azure_openai_endpoint": "",
        "azure_openai_deployment_name": "",
        "azure_client_id": "",
        "azure_openai_api_version": "2025-01-01-preview",
    }
    defaults.update(overrides)
    m = Mock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


@patch("named.suggestions.client_factory.OpenAI")
def test_creates_default_client(mock_openai):
    """Test creating a client with just an API key (OpenAI direct)."""
    mock_openai.return_value = Mock()
    create_openai_client(api_key="sk-test")
    mock_openai.assert_called_once_with(api_key="sk-test")


@patch("named.suggestions.client_factory.OpenAI")
def test_creates_client_with_base_url(mock_openai):
    """Test creating a client with a custom base URL (Azure AI Foundry)."""
    mock_openai.return_value = Mock()
    create_openai_client(
        api_key="azure-key",
        base_url="https://myresource.openai.azure.com/openai/v1/",
    )
    mock_openai.assert_called_once_with(
        api_key="azure-key",
        base_url="https://myresource.openai.azure.com/openai/v1/",
    )


def test_raises_without_api_key():
    """Test that ValueError is raised when no API key is available."""
    with patch("named.suggestions.client_factory.get_settings") as mock_get:
        mock_get.return_value = _mock_settings()
        with pytest.raises(ValueError, match="API key not provided"):
            create_openai_client()


@patch("named.suggestions.client_factory.OpenAI")
def test_falls_back_to_settings(mock_openai):
    """Test that settings are used when no explicit params are given."""
    mock_openai.return_value = Mock()
    with patch("named.suggestions.client_factory.get_settings") as mock_get:
        mock_get.return_value = _mock_settings(
            openai_api_key="from-settings",
            openai_base_url="https://azure.example.com/v1/",
        )
        create_openai_client()
    mock_openai.assert_called_once_with(
        api_key="from-settings",
        base_url="https://azure.example.com/v1/",
    )


@patch("named.suggestions.client_factory.OpenAI")
def test_empty_base_url_not_passed(mock_openai):
    """Test that empty base_url from settings is not passed to OpenAI."""
    mock_openai.return_value = Mock()
    with patch("named.suggestions.client_factory.get_settings") as mock_get:
        mock_get.return_value = _mock_settings(openai_api_key="sk-test")
        create_openai_client()
    mock_openai.assert_called_once_with(api_key="sk-test")


@patch("named.suggestions.client_factory.OpenAI")
def test_explicit_params_override_settings(mock_openai):
    """Test that explicit params take priority over settings."""
    mock_openai.return_value = Mock()
    with patch("named.suggestions.client_factory.get_settings") as mock_get:
        mock_get.return_value = _mock_settings(
            openai_api_key="from-settings",
            openai_base_url="https://settings-url.com/v1/",
        )
        create_openai_client(api_key="explicit-key", base_url="https://explicit-url.com/v1/")
    mock_openai.assert_called_once_with(
        api_key="explicit-key",
        base_url="https://explicit-url.com/v1/",
    )


@patch("named.suggestions.client_factory.AzureOpenAI")
def test_creates_azure_client_with_workload_identity(mock_azure):
    """Test that AzureOpenAI is used when AZURE_OPENAI_ENDPOINT is set."""
    mock_azure.return_value = Mock()
    mock_credential = Mock()
    mock_token_provider = Mock()

    # Mock azure.identity since it may not be installed in dev
    mock_azure_identity = Mock()
    mock_azure_identity.DefaultAzureCredential.return_value = mock_credential
    mock_azure_identity.get_bearer_token_provider.return_value = mock_token_provider

    with patch("named.suggestions.client_factory.get_settings") as mock_get:
        mock_get.return_value = _mock_settings(
            azure_openai_endpoint="https://myresource.cognitiveservices.azure.com/",
            azure_openai_deployment_name="gpt-4o",
            azure_client_id="test-client-id",
        )
        with patch.dict("sys.modules", {"azure": Mock(), "azure.identity": mock_azure_identity}):
            create_openai_client()
    mock_azure.assert_called_once_with(
        azure_endpoint="https://myresource.cognitiveservices.azure.com",
        azure_ad_token_provider=mock_token_provider,
        api_version="2025-01-01-preview",
    )


def test_azure_skipped_when_endpoint_empty():
    """Test that Azure path is skipped when endpoint is empty, falling back to API key."""
    with patch("named.suggestions.client_factory.get_settings") as mock_get:
        mock_get.return_value = _mock_settings(openai_api_key="sk-test")
        with patch("named.suggestions.client_factory.OpenAI") as mock_openai:
            mock_openai.return_value = Mock()
            create_openai_client()
        mock_openai.assert_called_once_with(api_key="sk-test")
