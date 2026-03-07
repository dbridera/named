"""Tests for LLMClient safety guards (no live API calls)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from named.suggestions.llm_client import (
    LLMClient,
    LLMError,
    _CHUNK_SIZE,
    _CHUNK_THRESHOLD,
    _TOKENS_BASE,
    _TOKENS_MAX,
    _TOKENS_MIN,
    _TOKENS_PER_SYMBOL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client() -> LLMClient:
    """Return an LLMClient with a dummy key (no network calls made)."""
    return LLMClient(api_key="sk-test", model="gpt-4o")


def _make_symbol(name: str, kind: str, line: int = 1) -> MagicMock:
    """Build a minimal Symbol mock."""
    sym = MagicMock()
    sym.name = name
    sym.kind = kind
    sym.annotations = []
    sym.location = MagicMock()
    sym.location.line = line
    return sym


def _results_json(items: list[dict]) -> str:
    """Wrap items in the expected LLM response envelope."""
    return json.dumps({"results": items})


# ---------------------------------------------------------------------------
# _is_hallucinated
# ---------------------------------------------------------------------------

class TestIsHallucinated:
    def setup_method(self):
        self.client = _make_client()

    def test_method_style_name_for_field_is_blocked(self):
        assert self.client._is_hallucinated("getBalance", "field") is True

    def test_setter_for_field_is_blocked(self):
        assert self.client._is_hallucinated("setAmount", "field") is True

    def test_is_prefix_for_field_is_blocked(self):
        assert self.client._is_hallucinated("isActive", "field") is True

    def test_has_prefix_for_field_is_blocked(self):
        assert self.client._is_hallucinated("hasOverdue", "field") is True

    def test_find_prefix_for_field_is_blocked(self):
        assert self.client._is_hallucinated("findAccount", "field") is True

    def test_method_style_for_parameter_is_blocked(self):
        assert self.client._is_hallucinated("getBalance", "parameter") is True

    def test_method_style_for_constant_is_blocked(self):
        assert self.client._is_hallucinated("getMax", "constant") is True

    def test_camel_case_field_name_allowed(self):
        assert self.client._is_hallucinated("accountNumber", "field") is False

    def test_plain_field_name_allowed(self):
        assert self.client._is_hallucinated("balance", "field") is False

    def test_method_kind_never_filtered(self):
        # Even method-style names are fine for actual methods
        assert self.client._is_hallucinated("getBalance", "method") is False

    def test_class_kind_never_filtered(self):
        assert self.client._is_hallucinated("getBalance", "class") is False

    def test_lowercase_prefix_without_uppercase_not_blocked(self):
        # "getter" starts with "get" but "getter"[3] is 't' (lowercase) → OK
        assert self.client._is_hallucinated("getter", "field") is False

    def test_save_prefix_blocked(self):
        assert self.client._is_hallucinated("saveAccount", "field") is True

    def test_create_prefix_blocked(self):
        assert self.client._is_hallucinated("createRecord", "parameter") is True


# ---------------------------------------------------------------------------
# Dynamic max_tokens
# ---------------------------------------------------------------------------

class TestDynamicMaxTokens:
    """Test that _analyze_file_chunk computes max_tokens correctly."""

    def setup_method(self):
        self.client = _make_client()

    def _expected_max_tokens(self, n_symbols: int) -> int:
        return min(max(_TOKENS_MIN, n_symbols * _TOKENS_PER_SYMBOL + _TOKENS_BASE), _TOKENS_MAX)

    def test_small_file_uses_minimum(self):
        # 1 symbol → 120+500=620, but min is 1000
        assert self._expected_max_tokens(1) == _TOKENS_MIN

    def test_medium_file_scales(self):
        # 20 symbols → 20*120+500=2900
        assert self._expected_max_tokens(20) == 2900

    def test_large_chunk_caps_at_max(self):
        # 70 symbols → 70*120+500=8900 → capped at 8000
        assert self._expected_max_tokens(70) == _TOKENS_MAX

    def test_chunk_boundary_below_max(self):
        # 25 symbols → 25*120+500=3500 (well under 8000)
        assert self._expected_max_tokens(25) == 3500

    def test_max_tokens_passed_to_call_llm(self, tmp_path):
        """Verify _analyze_file_chunk passes computed max_tokens to _call_llm."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol("foo", "field")]
        expected = self._expected_max_tokens(1)

        with patch.object(self.client, "_call_llm") as mock_call:
            mock_call.return_value = (_results_json([]), "stop")
            self.client._analyze_file_chunk(java_file, symbols, "rules", "class Test {}")
            mock_call.assert_called_once()
            _, called_max = mock_call.call_args[0]
            assert called_max == expected


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

class TestChunking:
    def setup_method(self):
        self.client = _make_client()

    def test_small_file_uses_single_chunk(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")
        # Use a count at or below the threshold (no chunking expected)
        symbols = [_make_symbol(f"field{i}", "field") for i in range(_CHUNK_THRESHOLD)]

        call_count = 0

        def fake_call(prompt, max_tokens):
            nonlocal call_count
            call_count += 1
            return (_results_json([]), "stop")

        with patch.object(self.client, "_call_llm", side_effect=fake_call):
            result = self.client.analyze_file(java_file, symbols, "rules")

        assert call_count == 1
        assert len(result) == _CHUNK_THRESHOLD

    def test_large_file_splits_into_chunks(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")
        n = _CHUNK_THRESHOLD + 1  # One above threshold → 2 chunks (25 + remainder)
        symbols = [_make_symbol(f"field{i}", "field") for i in range(n)]

        call_count = 0

        def fake_call(prompt, max_tokens):
            nonlocal call_count
            call_count += 1
            return (_results_json([]), "stop")

        with patch.object(self.client, "_call_llm", side_effect=fake_call):
            result = self.client.analyze_file(java_file, symbols, "rules")

        expected_chunks = (n + _CHUNK_SIZE - 1) // _CHUNK_SIZE
        assert call_count == expected_chunks
        assert len(result) == n

    def test_chunk_results_merged_correctly(self, tmp_path):
        """Suggestion from chunk 2 lands at the correct index in the full list."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        # Use threshold+5 so two chunks: _CHUNK_SIZE + remainder
        n = _CHUNK_THRESHOLD + 5
        symbols = [_make_symbol(f"field{i}", "field") for i in range(n)]

        # Second chunk starts at _CHUNK_SIZE (25). Local index 2 → global index 27.
        chunk_calls = []

        def fake_call(prompt, max_tokens):
            call_idx = len(chunk_calls)
            chunk_calls.append(call_idx)
            if call_idx == 1:
                items = [{"symbol_index": 2, "needs_rename": True,
                          "suggestion": {"suggested_name": "renamedField",
                                         "confidence": 0.9, "rationale": "test",
                                         "rules_addressed": ["R1"]}}]
                return (_results_json(items), "stop")
            return (_results_json([]), "stop")

        global_idx = _CHUNK_SIZE + 2  # second chunk, local index 2

        with patch.object(self.client, "_call_llm", side_effect=fake_call):
            result = self.client.analyze_file(java_file, symbols, "rules")

        assert len(result) == n
        assert result[global_idx] is not None
        assert result[global_idx].suggested_name == "renamedField"
        for i, s in enumerate(result):
            if i != global_idx:
                assert s is None, f"Expected None at index {i}"


# ---------------------------------------------------------------------------
# finish_reason=length handling
# ---------------------------------------------------------------------------

class TestFinishReasonLength:
    def setup_method(self):
        self.client = _make_client()

    def test_truncated_output_logs_warning_and_returns_partial(self, tmp_path, caplog):
        import logging
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol(f"f{i}", "field") for i in range(3)]
        # Only first symbol in response — rest silently dropped
        items = [{"symbol_index": 0, "needs_rename": True,
                  "suggestion": {"suggested_name": "firstName", "confidence": 0.9,
                                 "rationale": "r", "rules_addressed": []}}]

        with patch.object(self.client, "_call_llm",
                          return_value=(_results_json(items), "length")):
            with caplog.at_level(logging.WARNING, logger="named.llm"):
                result = self.client._analyze_file_chunk(
                    java_file, symbols, "rules", "class Test {}"
                )

        assert "truncated" in caplog.text.lower()
        assert result[0] is not None  # First symbol was in the truncated response
        assert result[1] is None
        assert result[2] is None

    def test_json_parse_failure_returns_all_none(self, tmp_path, caplog):
        import logging
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol("foo", "field")]

        with patch.object(self.client, "_call_llm",
                          return_value=('{"results": [BROKEN JSON', "length")):
            with caplog.at_level(logging.WARNING, logger="named.llm"):
                result = self.client._analyze_file_chunk(
                    java_file, symbols, "rules", "class Test {}"
                )

        assert result == [None]
        assert "json" in caplog.text.lower()

    def test_llm_call_failure_returns_all_none(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol("foo", "field")]

        with patch.object(self.client, "_call_llm", side_effect=LLMError("api error")):
            result = self.client._analyze_file_chunk(
                java_file, symbols, "rules", "class Test {}"
            )

        assert result == [None]


# ---------------------------------------------------------------------------
# Hallucination filter applied in _analyze_file_chunk
# ---------------------------------------------------------------------------

class TestHallucinationFilterInChunk:
    def setup_method(self):
        self.client = _make_client()

    def test_getter_style_name_for_field_filtered(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol("bal", "field")]
        items = [{"symbol_index": 0, "needs_rename": True,
                  "suggestion": {"suggested_name": "getBalance",  # hallucination
                                 "confidence": 0.9, "rationale": "r",
                                 "rules_addressed": []}}]

        with patch.object(self.client, "_call_llm",
                          return_value=(_results_json(items), "stop")):
            result = self.client._analyze_file_chunk(
                java_file, symbols, "rules", "class Test {}"
            )

        assert result[0] is None  # Filtered out

    def test_good_field_name_passes_filter(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol("bal", "field")]
        items = [{"symbol_index": 0, "needs_rename": True,
                  "suggestion": {"suggested_name": "currentBalance",  # OK
                                 "confidence": 0.9, "rationale": "r",
                                 "rules_addressed": []}}]

        with patch.object(self.client, "_call_llm",
                          return_value=(_results_json(items), "stop")):
            result = self.client._analyze_file_chunk(
                java_file, symbols, "rules", "class Test {}"
            )

        assert result[0] is not None
        assert result[0].suggested_name == "currentBalance"

    def test_getter_for_method_not_filtered(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        symbols = [_make_symbol("getBal", "method")]
        items = [{"symbol_index": 0, "needs_rename": True,
                  "suggestion": {"suggested_name": "getBalance",
                                 "confidence": 0.9, "rationale": "r",
                                 "rules_addressed": []}}]

        with patch.object(self.client, "_call_llm",
                          return_value=(_results_json(items), "stop")):
            result = self.client._analyze_file_chunk(
                java_file, symbols, "rules", "class Test {}"
            )

        assert result[0] is not None
        assert result[0].suggested_name == "getBalance"
