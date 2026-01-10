"""Tests for validation logic."""

import pytest
from pathlib import Path

from named.rules.models import NameSuggestion
from named.validation.validator import (
    validate_suggestion,
    pre_filter_symbols,
    check_name_against_rules,
)
from named.analysis.extractor import extract_symbols


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_FILE = FIXTURES_DIR / "SampleService.java"


class TestValidateSuggestion:
    """Tests for suggestion validation."""

    def test_valid_suggestion(self):
        """High-confidence suggestion without blocking annotations should be valid."""
        suggestion = NameSuggestion(
            original_name="data",
            suggested_name="customerRecord",
            symbol_kind="variable",
            confidence=0.90,
            rationale="Reveals intent better",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert result.is_valid is True
        assert len(result.blocked_reasons) == 0

    def test_blocked_by_annotation(self):
        """Suggestion should be blocked if symbol has blocking annotation."""
        suggestion = NameSuggestion(
            original_name="userName",
            suggested_name="customerName",
            symbol_kind="field",
            confidence=0.90,
            rationale="More specific",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=["JsonProperty"])
        assert result.is_valid is False
        assert "G1_IMMUTABLE_CONTRACTS" in result.blocked_reasons[0]

    def test_blocked_by_low_confidence(self):
        """Suggestion should be blocked if confidence is too low."""
        suggestion = NameSuggestion(
            original_name="tmp",
            suggested_name="temporaryValue",
            symbol_kind="variable",
            confidence=0.70,  # Below threshold
            rationale="Better name",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert result.is_valid is False
        assert "G4_CONFIDENCE_THRESHOLD" in result.blocked_reasons[0]


class TestPreFilterSymbols:
    """Tests for pre-filtering symbols by guardrails."""

    def test_pre_filter_separates_blocked_symbols(self):
        """Should separate symbols blocked by annotation guardrails."""
        symbols = extract_symbols(SAMPLE_FILE)
        analyzable, blocked = pre_filter_symbols(symbols)

        # Should have some in each category
        assert len(analyzable) > 0
        assert len(blocked) > 0

        # Total should match
        assert len(analyzable) + len(blocked) == len(symbols)

    def test_blocked_symbols_have_blocking_annotations(self):
        """Blocked symbols should have annotations that trigger guardrails."""
        symbols = extract_symbols(SAMPLE_FILE)
        _, blocked = pre_filter_symbols(symbols)

        blocking_annotations = {
            "JsonProperty", "Column", "Path", "GET", "POST",
            "QueryParam", "PathParam", "RequestMapping",
        }

        for symbol in blocked:
            has_blocking = any(
                ann in blocking_annotations
                for ann in symbol.annotations
            )
            assert has_blocking, f"{symbol.name} has no blocking annotation"


class TestCheckNameAgainstRules:
    """Tests for checking names against rules."""

    def test_single_letter_variable_violates_r6(self):
        """Single-letter variables should violate R6_NO_MENTAL_MAPPING."""
        violations = check_name_against_rules("x", "variable")
        rule_ids = [v.rule_id for v in violations]
        assert "R6_NO_MENTAL_MAPPING" in rule_ids

    def test_loop_counters_are_exceptions(self):
        """Loop counters i, j, k should not violate R6."""
        for name in ["i", "j", "k"]:
            violations = check_name_against_rules(name, "variable")
            rule_ids = [v.rule_id for v in violations]
            assert "R6_NO_MENTAL_MAPPING" not in rule_ids

    def test_generic_names_violate_r1(self):
        """Generic names like 'data' should violate R1_REVEAL_INTENT."""
        violations = check_name_against_rules("data", "variable")
        rule_ids = [v.rule_id for v in violations]
        assert "R1_REVEAL_INTENT" in rule_ids

    def test_good_names_have_no_violations(self):
        """Well-named identifiers should have no violations."""
        violations = check_name_against_rules("customerEmailAddress", "field")
        assert len(violations) == 0
