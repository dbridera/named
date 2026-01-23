"""Tests for batch analysis client."""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from named.suggestions.batch_client import BatchAnalysisClient, BatchJob


def test_batch_job_to_dict():
    """Test BatchJob serialization to dict."""
    job = BatchJob(
        batch_id="batch_123",
        input_file_id="file_456",
        status="completed",
        symbols=[{"name": "foo", "kind": "method"}],
        created_at=1234567890,
        completed_at=1234567900,
        output_file_id="file_789",
        error=None,
    )

    result = job.to_dict()

    assert result["batch_id"] == "batch_123"
    assert result["input_file_id"] == "file_456"
    assert result["status"] == "completed"
    assert len(result["symbols"]) == 1
    assert result["created_at"] == 1234567890
    assert result["completed_at"] == 1234567900
    assert result["output_file_id"] == "file_789"
    assert result["error"] is None


def test_create_batch_requests():
    """Test batch request generation."""
    client = BatchAnalysisClient(api_key="test-key", model="gpt-4o")

    symbols = [
        {"name": "foo", "kind": "method", "context": "void foo() {}"},
        {"name": "bar", "kind": "field", "context": "int bar;"},
    ]

    system_prompt = "You are a naming expert."
    rules_context = "Follow Java naming conventions."

    requests = client.create_batch_requests(symbols, system_prompt, rules_context)

    assert len(requests) == 2

    # Check first request
    assert requests[0]["custom_id"] == "symbol-0"
    assert requests[0]["method"] == "POST"
    assert requests[0]["url"] == "/v1/chat/completions"
    assert requests[0]["body"]["model"] == "gpt-4o"
    assert len(requests[0]["body"]["messages"]) == 2
    assert requests[0]["body"]["messages"][0]["role"] == "system"
    assert requests[0]["body"]["messages"][1]["role"] == "user"

    # Check second request
    assert requests[1]["custom_id"] == "symbol-1"


def test_build_symbol_prompt():
    """Test symbol prompt building."""
    client = BatchAnalysisClient(api_key="test-key")

    symbol = {
        "name": "foo",
        "kind": "method",
        "context": "void foo() { }",
        "annotations": ["Override", "Deprecated"],
    }
    rules_context = "Follow naming rules."

    prompt = client._build_symbol_prompt(symbol, rules_context)

    assert "foo" in prompt
    assert "method" in prompt
    assert "void foo() { }" in prompt
    assert "Override" in prompt
    assert "Deprecated" in prompt
    assert "Follow naming rules" in prompt


@patch("named.suggestions.batch_client.OpenAI")
def test_submit_batch(mock_openai):
    """Test batch submission."""
    # Setup mock
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # Mock file upload
    mock_file_response = Mock()
    mock_file_response.id = "file-123"
    mock_client.files.create.return_value = mock_file_response

    # Mock batch creation
    mock_batch_response = Mock()
    mock_batch_response.id = "batch-456"
    mock_batch_response.status = "validating"
    mock_batch_response.created_at = 1234567890
    mock_client.batches.create.return_value = mock_batch_response

    # Test
    client = BatchAnalysisClient(api_key="test-key")
    client.client = mock_client

    requests = [
        {
            "custom_id": "symbol-0",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {},
        }
    ]
    symbols = [{"name": "foo"}]

    job = client.submit_batch(requests, symbols, description="Test batch")

    # Verify
    assert job.batch_id == "batch-456"
    assert job.input_file_id == "file-123"
    assert job.status == "validating"
    assert len(job.symbols) == 1

    # Verify file upload was called
    mock_client.files.create.assert_called_once()
    call_args = mock_client.files.create.call_args
    assert call_args[1]["purpose"] == "batch"

    # Verify batch creation was called
    mock_client.batches.create.assert_called_once()
    batch_call_args = mock_client.batches.create.call_args
    assert batch_call_args[1]["input_file_id"] == "file-123"
    assert batch_call_args[1]["endpoint"] == "/v1/chat/completions"
    assert batch_call_args[1]["completion_window"] == "24h"


@patch("named.suggestions.batch_client.OpenAI")
def test_get_batch_status(mock_openai):
    """Test getting batch status."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    mock_batch = Mock()
    mock_batch.status = "in_progress"
    mock_client.batches.retrieve.return_value = mock_batch

    client = BatchAnalysisClient(api_key="test-key")
    client.client = mock_client

    status = client.get_batch_status("batch-123")

    assert status == "in_progress"
    mock_client.batches.retrieve.assert_called_once_with("batch-123")


@patch("named.suggestions.batch_client.OpenAI")
@patch("named.suggestions.batch_client.time.sleep")
def test_poll_batch_success(mock_sleep, mock_openai):
    """Test polling batch until completion."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # Simulate progression: validating -> in_progress -> completed
    mock_responses = [
        Mock(status="validating"),
        Mock(status="in_progress"),
        Mock(status="completed", completed_at=1234567900, output_file_id="file-out"),
    ]
    mock_client.batches.retrieve.side_effect = mock_responses

    client = BatchAnalysisClient(api_key="test-key")
    client.client = mock_client

    job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-in",
        status="validating",
        symbols=[],
        created_at=1234567890,
    )

    result = client.poll_batch(job, poll_interval=1, timeout=100)

    assert result.status == "completed"
    assert result.completed_at == 1234567900
    assert result.output_file_id == "file-out"
    assert mock_client.batches.retrieve.call_count == 3


@patch("named.suggestions.batch_client.OpenAI")
@patch("named.suggestions.batch_client.time.sleep")
def test_poll_batch_timeout(mock_sleep, mock_openai):
    """Test polling batch timeout."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # Always return in_progress to trigger timeout
    mock_client.batches.retrieve.return_value = Mock(status="in_progress")

    client = BatchAnalysisClient(api_key="test-key")
    client.client = mock_client

    job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-in",
        status="validating",
        symbols=[],
        created_at=1234567890,
    )

    with pytest.raises(TimeoutError):
        client.poll_batch(job, poll_interval=1, timeout=2)


@patch("named.suggestions.batch_client.OpenAI")
@patch("named.suggestions.batch_client.time.sleep")
def test_poll_batch_failed(mock_sleep, mock_openai):
    """Test polling batch that fails."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    mock_client.batches.retrieve.return_value = Mock(status="failed")

    client = BatchAnalysisClient(api_key="test-key")
    client.client = mock_client

    job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-in",
        status="validating",
        symbols=[],
        created_at=1234567890,
    )

    with pytest.raises(RuntimeError, match="Batch failed"):
        client.poll_batch(job, poll_interval=1, timeout=100)


@patch("named.suggestions.batch_client.OpenAI")
def test_download_results(mock_openai):
    """Test downloading batch results."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # Mock file content
    result1 = {"custom_id": "symbol-0", "response": {"body": {"choices": []}}}
    result2 = {"custom_id": "symbol-1", "response": {"body": {"choices": []}}}
    jsonl_content = f"{json.dumps(result1)}\n{json.dumps(result2)}"

    mock_file_response = Mock()
    mock_file_response.read.return_value = jsonl_content.encode("utf-8")
    mock_client.files.content.return_value = mock_file_response

    client = BatchAnalysisClient(api_key="test-key")
    client.client = mock_client

    job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-in",
        status="completed",
        symbols=[],
        created_at=1234567890,
        output_file_id="file-out",
    )

    results = client.download_results(job)

    assert len(results) == 2
    assert results[0]["custom_id"] == "symbol-0"
    assert results[1]["custom_id"] == "symbol-1"
    mock_client.files.content.assert_called_once_with("file-out")


def test_download_results_no_output_file():
    """Test download results fails without output file."""
    client = BatchAnalysisClient(api_key="test-key")

    job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-in",
        status="completed",
        symbols=[],
        created_at=1234567890,
        output_file_id=None,
    )

    with pytest.raises(ValueError, match="no output file"):
        client.download_results(job)


def test_parse_batch_results():
    """Test parsing batch results and mapping to symbols."""
    client = BatchAnalysisClient(api_key="test-key")

    # Mock batch results
    results = [
        {
            "custom_id": "symbol-0",
            "response": {
                "body": {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "needs_rename": True,
                                        "suggestion": {
                                            "suggested_name": "betterName",
                                            "confidence": 0.9,
                                        },
                                    }
                                )
                            }
                        }
                    ]
                }
            },
        },
        {
            "custom_id": "symbol-1",
            "response": {
                "body": {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "needs_rename": False,
                                    }
                                )
                            }
                        }
                    ]
                }
            },
        },
    ]

    batch_job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-123",
        status="completed",
        symbols=[{"name": "foo"}, {"name": "bar"}],
        created_at=123456,
    )

    parsed = client.parse_batch_results(results, batch_job)

    assert len(parsed) == 2
    assert 0 in parsed
    assert 1 in parsed
    assert parsed[0]["needs_rename"] is True
    assert parsed[0]["suggestion"]["suggested_name"] == "betterName"
    assert parsed[1]["needs_rename"] is False


def test_parse_batch_results_invalid_custom_id():
    """Test parsing handles invalid custom_id gracefully."""
    client = BatchAnalysisClient(api_key="test-key")

    results = [
        {
            "custom_id": "invalid-id",  # Wrong format
            "response": {"body": {"choices": [{"message": {"content": "{}"}}]}},
        }
    ]

    batch_job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-123",
        status="completed",
        symbols=[{"name": "foo"}],
        created_at=123456,
    )

    parsed = client.parse_batch_results(results, batch_job)

    assert len(parsed) == 0  # Should skip invalid custom_id


def test_parse_batch_results_invalid_json():
    """Test parsing handles invalid JSON gracefully."""
    client = BatchAnalysisClient(api_key="test-key")

    results = [
        {
            "custom_id": "symbol-0",
            "response": {
                "body": {"choices": [{"message": {"content": "not valid json"}}]}
            },
        }
    ]

    batch_job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-123",
        status="completed",
        symbols=[{"name": "foo"}],
        created_at=123456,
    )

    parsed = client.parse_batch_results(results, batch_job)

    assert len(parsed) == 0  # Should skip invalid JSON


def test_parse_batch_results_missing_choices():
    """Test parsing handles missing choices gracefully."""
    client = BatchAnalysisClient(api_key="test-key")

    results = [
        {
            "custom_id": "symbol-0",
            "response": {"body": {"choices": []}},  # Empty choices
        }
    ]

    batch_job = BatchJob(
        batch_id="batch-123",
        input_file_id="file-123",
        status="completed",
        symbols=[{"name": "foo"}],
        created_at=123456,
    )

    parsed = client.parse_batch_results(results, batch_job)

    assert len(parsed) == 0  # Should skip missing choices
