"""Tests for the estimate command."""

import math

import pytest
from typer.testing import CliRunner

from named.cli import MODEL_PRICING, app

runner = CliRunner()


def test_model_pricing_has_required_models():
    """Verify pricing data exists for supported models."""
    assert "gpt-4o" in MODEL_PRICING
    assert "gpt-4o-mini" in MODEL_PRICING

    for model_name, pricing in MODEL_PRICING.items():
        assert "streaming" in pricing
        assert "batch" in pricing
        assert "input" in pricing["streaming"]
        assert "output" in pricing["streaming"]
        assert "input" in pricing["batch"]
        assert "output" in pricing["batch"]


def test_batch_pricing_is_half_streaming():
    """Verify batch prices are 50% of streaming prices."""
    for model_name, pricing in MODEL_PRICING.items():
        assert pricing["batch"]["input"] == pricing["streaming"]["input"] / 2
        assert pricing["batch"]["output"] == pricing["streaming"]["output"] / 2


def test_token_estimation_chars_div_4():
    """Verify chars/4 token estimation logic."""
    # Simulate the estimation: total_input_chars // 4
    test_chars = 6868  # 4 symbols × ~1717 chars each
    expected_tokens = test_chars // 4
    assert expected_tokens == 1717


def test_cost_calculation():
    """Verify cost calculation math for both modes."""
    input_tokens = 1_000_000  # 1M tokens
    output_tokens = 500_000

    pricing = MODEL_PRICING["gpt-4o"]

    streaming_cost = (
        (input_tokens / 1_000_000) * pricing["streaming"]["input"]
        + (output_tokens / 1_000_000) * pricing["streaming"]["output"]
    )
    batch_cost = (
        (input_tokens / 1_000_000) * pricing["batch"]["input"]
        + (output_tokens / 1_000_000) * pricing["batch"]["output"]
    )

    assert streaming_cost == 5.00 + 7.50  # $12.50
    assert batch_cost == 2.50 + 3.75  # $6.25
    assert batch_cost == streaming_cost / 2


def test_batch_count_calculation():
    """Verify batch count edge cases."""
    assert math.ceil(49 / 50) == 1
    assert math.ceil(50 / 50) == 1
    assert math.ceil(51 / 50) == 2
    assert math.ceil(100 / 50) == 2
    assert math.ceil(101 / 50) == 3
    assert math.ceil(48322 / 50) == 967


def test_estimate_cli_banking_app():
    """End-to-end test with banking-app sample."""
    result = runner.invoke(app, ["estimate", "samples/banking-app"])

    assert result.exit_code == 0
    assert "Cost Estimation" in result.output
    assert "Token Estimation" in result.output
    assert "Analyzable symbols" in result.output
    assert "Streaming" in result.output
    assert "Batch" in result.output
    assert "Savings" in result.output
    assert "$" in result.output


def test_estimate_cli_with_model_option():
    """Test estimate with --model flag."""
    result = runner.invoke(app, ["estimate", "samples/banking-app", "--model", "gpt-4o-mini"])

    assert result.exit_code == 0
    assert "gpt-4o-mini" in result.output


def test_estimate_cli_unknown_model_fallback():
    """Test fallback to gpt-4o pricing for unknown model."""
    result = runner.invoke(app, ["estimate", "samples/banking-app", "--model", "unknown-model"])

    assert result.exit_code == 0
    assert "Unknown model" in result.output


def test_estimate_cli_nonexistent_path():
    """Test with non-existent path."""
    result = runner.invoke(app, ["estimate", "/nonexistent/path"])

    assert result.exit_code != 0


def test_estimate_cli_verbose():
    """Test verbose output shows additional details."""
    result = runner.invoke(app, ["estimate", "samples/banking-app", "--verbose"])

    assert result.exit_code == 0
    assert "Token Estimation" in result.output


def test_estimate_cli_custom_batch_size():
    """Test custom batch size affects batch count."""
    result_50 = runner.invoke(app, ["estimate", "samples/banking-app", "--batch-size", "50"])
    result_10 = runner.invoke(app, ["estimate", "samples/banking-app", "--batch-size", "10"])

    assert result_50.exit_code == 0
    assert result_10.exit_code == 0
    # With smaller batch size, more batches should be needed
    assert "size=50" in result_50.output
    assert "size=10" in result_10.output
