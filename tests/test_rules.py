"""Tests for the rules module."""

from named.rules.guardrails import (
    GUARDRAILS,
    check_annotation_guardrails,
    check_confidence_guardrail,
    get_guardrail,
    is_blocked,
)
from named.rules.models import RuleCategory, Severity
from named.rules.naming_rules import NAMING_RULES, get_rule


class TestNamingRules:
    """Tests for naming rules."""

    def test_has_9_rules(self):
        """Should have exactly 9 naming rules."""
        assert len(NAMING_RULES) == 9

    def test_all_rules_have_required_fields(self):
        """All rules should have required fields populated."""
        for rule in NAMING_RULES:
            assert rule.id.startswith("R")
            assert rule.name  # Spanish name
            assert rule.name_en  # English name
            assert rule.description
            assert rule.description_en
            assert rule.category in RuleCategory
            assert rule.severity in Severity
            assert len(rule.examples_good) > 0
            assert len(rule.examples_bad) > 0

    def test_get_rule_by_id(self):
        """Should retrieve rule by ID."""
        rule = get_rule("R1_REVEAL_INTENT")
        assert rule is not None
        assert rule.name_en == "Reveal Intent"

    def test_get_rule_not_found(self):
        """Should return None for unknown rule ID."""
        rule = get_rule("R99_UNKNOWN")
        assert rule is None

    def test_rule_categories(self):
        """Rules should be distributed across categories."""
        categories = {r.category for r in NAMING_RULES}
        assert RuleCategory.SEMANTIC in categories
        assert RuleCategory.SYNTACTIC in categories
        assert RuleCategory.CONSISTENCY in categories


class TestGuardrails:
    """Tests for guardrails."""

    def test_has_4_guardrails(self):
        """Should have exactly 4 guardrails."""
        assert len(GUARDRAILS) == 4

    def test_get_guardrail_by_id(self):
        """Should retrieve guardrail by ID."""
        guardrail = get_guardrail("G1_IMMUTABLE_CONTRACTS")
        assert guardrail is not None
        assert "JsonProperty" in guardrail.blocked_annotations

    def test_check_annotation_guardrails_blocks_json_property(self):
        """Should block symbols with @JsonProperty."""
        blocked = check_annotation_guardrails(["JsonProperty"])
        assert len(blocked) == 1
        assert blocked[0][0] == "G1_IMMUTABLE_CONTRACTS"

    def test_check_annotation_guardrails_blocks_path(self):
        """Should block symbols with @Path (REST API)."""
        blocked = check_annotation_guardrails(["Path"])
        assert len(blocked) == 1
        assert blocked[0][0] == "G3_PUBLIC_API"

    def test_check_annotation_guardrails_allows_override(self):
        """Should not block symbols with @Override."""
        blocked = check_annotation_guardrails(["Override"])
        assert len(blocked) == 0

    def test_check_confidence_guardrail_blocks_low_confidence(self):
        """Should block suggestions with confidence below 0.80."""
        result = check_confidence_guardrail(0.75)
        assert result is not None
        assert result[0] == "G4_CONFIDENCE_THRESHOLD"

    def test_check_confidence_guardrail_allows_high_confidence(self):
        """Should allow suggestions with confidence >= 0.80."""
        result = check_confidence_guardrail(0.85)
        assert result is None

    def test_is_blocked_with_blocking_annotation(self):
        """Should return True for blocking annotations."""
        assert is_blocked(["Column"]) is True
        assert is_blocked(["GET"]) is True

    def test_is_blocked_with_no_blocking_annotation(self):
        """Should return False for non-blocking annotations."""
        assert is_blocked(["Override"]) is False
        assert is_blocked([]) is False
