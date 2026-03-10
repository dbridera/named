"""Tests for the OpenAI client factory."""

from unittest.mock import Mock, patch

import pytest

from named.suggestions.client_factory import create_openai_client


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
    with patch("named.suggestions.client_factory.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = ""
        mock_settings.return_value.openai_base_url = ""
        with pytest.raises(ValueError, match="API key not provided"):
            create_openai_client()


@patch("named.suggestions.client_factory.OpenAI")
def test_falls_back_to_settings(mock_openai):
    """Test that settings are used when no explicit params are given."""
    mock_openai.return_value = Mock()
    with patch("named.suggestions.client_factory.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = "from-settings"
        mock_settings.return_value.openai_base_url = "https://azure.example.com/v1/"
        create_openai_client()
    mock_openai.assert_called_once_with(
        api_key="from-settings",
        base_url="https://azure.example.com/v1/",
    )


@patch("named.suggestions.client_factory.OpenAI")
def test_empty_base_url_not_passed(mock_openai):
    """Test that empty base_url from settings is not passed to OpenAI."""
    mock_openai.return_value = Mock()
    with patch("named.suggestions.client_factory.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = "sk-test"
        mock_settings.return_value.openai_base_url = ""
        create_openai_client()
    mock_openai.assert_called_once_with(api_key="sk-test")


@patch("named.suggestions.client_factory.OpenAI")
def test_explicit_params_override_settings(mock_openai):
    """Test that explicit params take priority over settings."""
    mock_openai.return_value = Mock()
    with patch("named.suggestions.client_factory.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = "from-settings"
        mock_settings.return_value.openai_base_url = "https://settings-url.com/v1/"
        create_openai_client(api_key="explicit-key", base_url="https://explicit-url.com/v1/")
    mock_openai.assert_called_once_with(
        api_key="explicit-key",
        base_url="https://explicit-url.com/v1/",
    )
