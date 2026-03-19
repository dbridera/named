"""Tests for CLI commands: config, batch-cancel, files-cleanup."""

import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from named.cli import app

runner = CliRunner()


def _mock_settings(**overrides):
    """Create a mock settings object with defaults for all fields."""
    defaults = {
        "openai_api_key": "sk-test",
        "openai_model": "gpt-4o",
        "openai_base_url": "",
        "azure_openai_endpoint": "",
        "azure_openai_deployment_name": "",
        "azure_client_id": "",
        "azure_openai_api_version": "2025-01-01-preview",
        "azure_openai_batch_deployment_name": "",
        "batch_size": 50,
        "batch_poll_interval": 60,
    }
    defaults.update(overrides)
    m = Mock()
    for k, v in defaults.items():
        setattr(m, k, v)
    m.effective_openai_model.return_value = defaults.get("openai_model", "gpt-4o")
    m.effective_batch_model.return_value = defaults.get("openai_model", "gpt-4o")
    return m


# --- config command ---


@patch("named.config.get_settings")
def test_config_shows_openai_key_set(mock_get):
    """Test config command displays API key as set."""
    mock_get.return_value = _mock_settings()
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "(set)" in result.output
    assert "gpt-4o" in result.output


@patch("named.config.get_settings")
def test_config_shows_openai_key_not_set(mock_get):
    """Test config command displays API key as not set."""
    mock_get.return_value = _mock_settings(openai_api_key="")
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "(not set)" in result.output


@patch("named.config.get_settings")
def test_config_shows_azure_when_configured(mock_get):
    """Test config command shows Azure endpoint when configured."""
    mock_get.return_value = _mock_settings(
        azure_openai_endpoint="https://myresource.cognitiveservices.azure.com/",
        azure_openai_deployment_name="gpt-4o-deploy",
    )
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "endpoint + deployment set" in result.output
    assert "myresource" in result.output


@patch("named.config.get_settings")
def test_config_shows_batch_settings(mock_get):
    """Test config command shows batch settings."""
    mock_get.return_value = _mock_settings(batch_size=100, batch_poll_interval=30)
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "100" in result.output
    assert "30s" in result.output


# --- batch-cancel command ---


def test_batch_cancel_requires_input():
    """Test batch-cancel errors when no input is provided."""
    result = runner.invoke(app, ["batch-cancel"])
    assert result.exit_code == 1
    assert "Provide either" in result.output


@patch("named.config.get_settings")
def test_batch_cancel_no_auth(mock_get, tmp_path):
    """Test batch-cancel errors when no auth is configured."""
    mock_get.return_value = _mock_settings(openai_api_key="", azure_openai_endpoint="")
    jobs_file = tmp_path / "batch_jobs.json"
    jobs_file.write_text(json.dumps({"run_id": "test", "jobs": [{"batch_id": "b-1"}]}))
    result = runner.invoke(app, ["batch-cancel", "--batch-jobs", str(jobs_file)])
    assert result.exit_code == 1
    assert "NAMED_OPENAI_API_KEY" in result.output


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_batch_cancel_from_batch_jobs(mock_get, mock_client_cls, tmp_path):
    """Test batch-cancel cancels jobs from batch_jobs.json."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client

    jobs_file = tmp_path / "batch_jobs.json"
    jobs_file.write_text(json.dumps({
        "run_id": "test-run",
        "jobs": [
            {"batch_id": "batch-1", "input_file_id": "file-1"},
            {"batch_id": "batch-2", "input_file_id": "file-2"},
        ],
    }))

    result = runner.invoke(app, ["batch-cancel", "--batch-jobs", str(jobs_file)])
    assert result.exit_code == 0
    assert mock_client.cancel_batch.call_count == 2
    assert mock_client.delete_file.call_count == 2
    assert "2 cancelled" in result.output


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_batch_cancel_no_delete_files(mock_get, mock_client_cls, tmp_path):
    """Test batch-cancel with --no-delete-files skips file deletion."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client

    jobs_file = tmp_path / "batch_jobs.json"
    jobs_file.write_text(json.dumps({
        "run_id": "test-run",
        "jobs": [{"batch_id": "batch-1", "input_file_id": "file-1"}],
    }))

    result = runner.invoke(app, ["batch-cancel", "--batch-jobs", str(jobs_file), "--no-delete-files"])
    assert result.exit_code == 0
    mock_client.cancel_batch.assert_called_once_with("batch-1")
    mock_client.delete_file.assert_not_called()


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_batch_cancel_from_ids_file(mock_get, mock_client_cls, tmp_path):
    """Test batch-cancel reads batch IDs from a text file."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client
    # get_batch returns an object with input_file_id
    mock_batch = Mock(input_file_id="file-99")
    mock_client.get_batch.return_value = mock_batch

    ids_file = tmp_path / "ids.txt"
    ids_file.write_text("batch-10\n# comment\nbatch-20\n")

    result = runner.invoke(app, ["batch-cancel", "--ids-file", str(ids_file)])
    assert result.exit_code == 0
    assert mock_client.cancel_batch.call_count == 2
    assert mock_client.get_batch.call_count == 2  # looked up input_file_id


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_batch_cancel_handles_errors(mock_get, mock_client_cls, tmp_path):
    """Test batch-cancel reports errors without crashing."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client
    mock_client.cancel_batch.side_effect = Exception("API error")

    jobs_file = tmp_path / "batch_jobs.json"
    jobs_file.write_text(json.dumps({
        "run_id": "test-run",
        "jobs": [{"batch_id": "batch-1", "input_file_id": "file-1"}],
    }))

    result = runner.invoke(app, ["batch-cancel", "--batch-jobs", str(jobs_file)])
    assert result.exit_code == 0
    assert "1 error" in result.output


# --- files-cleanup command ---


@patch("named.config.get_settings")
def test_files_cleanup_no_auth(mock_get):
    """Test files-cleanup errors when no auth is configured."""
    mock_get.return_value = _mock_settings(openai_api_key="", azure_openai_endpoint="")
    result = runner.invoke(app, ["files-cleanup"])
    assert result.exit_code == 1
    assert "NAMED_OPENAI_API_KEY" in result.output


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_files_cleanup_dry_run(mock_get, mock_client_cls):
    """Test files-cleanup --dry-run lists but does not delete."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client

    mock_file = Mock(id="file-1", filename="batch.jsonl")
    mock_client.list_files.return_value = [mock_file]

    result = runner.invoke(app, ["files-cleanup", "--dry-run"])
    assert result.exit_code == 0
    assert "file-1" in result.output
    assert "no files deleted" in result.output.lower()
    mock_client.delete_file.assert_not_called()


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_files_cleanup_deletes(mock_get, mock_client_cls):
    """Test files-cleanup deletes files when not dry-run."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client

    mock_files = [Mock(id=f"file-{i}") for i in range(3)]
    mock_client.list_files.return_value = mock_files

    result = runner.invoke(app, ["files-cleanup"])
    assert result.exit_code == 0
    assert mock_client.delete_file.call_count == 3
    assert "3 deleted" in result.output


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_files_cleanup_no_files(mock_get, mock_client_cls):
    """Test files-cleanup with no files to clean."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client
    mock_client.list_files.return_value = []

    result = runner.invoke(app, ["files-cleanup"])
    assert result.exit_code == 0
    assert "Found 0 file(s)" in result.output


@patch("named.suggestions.batch_client.BatchAnalysisClient")
@patch("named.config.get_settings")
def test_files_cleanup_purpose_all(mock_get, mock_client_cls):
    """Test files-cleanup --purpose all passes None to list_files."""
    mock_get.return_value = _mock_settings()
    mock_client = Mock()
    mock_client_cls.return_value = mock_client
    mock_client.list_files.return_value = []

    runner.invoke(app, ["files-cleanup", "--purpose", "all"])
    mock_client.list_files.assert_called_once_with(purpose=None, limit=1000)
