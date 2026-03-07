"""Tests for validation logic."""

from pathlib import Path

from named.analysis.extractor import extract_symbols
from named.rules.models import NameSuggestion
from named.validation.validator import (
    ValidationResult,
    check_name_against_rules,
    detect_scope_conflicts,
    pre_filter_symbols,
    validate_suggestion,
)

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
            "JsonProperty",
            "Column",
            "Path",
            "GET",
            "POST",
            "QueryParam",
            "PathParam",
            "RequestMapping",
        }

        for symbol in blocked:
            has_blocking = any(ann in blocking_annotations for ann in symbol.annotations)
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


class TestConstantNamingConvention:
    """Tests for constant naming convention check."""

    def test_constant_with_lowercase_is_invalid(self):
        """Constants with camelCase names should be blocked."""
        suggestion = NameSuggestion(
            original_name="RATE",
            suggested_name="interestRate",
            symbol_kind="constant",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert result.is_valid is False
        assert any("R_CONSTANT_CASE" == v.rule_id for v in result.rule_violations)

    def test_constant_with_upper_snake_case_is_valid(self):
        """Constants with UPPER_SNAKE_CASE should pass."""
        suggestion = NameSuggestion(
            original_name="RATE",
            suggested_name="INTEREST_RATE",
            symbol_kind="constant",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not any("R_CONSTANT_CASE" == v.rule_id for v in result.rule_violations)

    def test_non_constant_allows_camelcase(self):
        """Non-constant fields should allow camelCase."""
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="interestRate",
            symbol_kind="field",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not any("R_CONSTANT_CASE" == v.rule_id for v in result.rule_violations)


class TestJavaKeywordValidation:
    """Tests for Java keyword blocking."""

    def test_keyword_blocked(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="class",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not result.is_valid
        assert any(v.rule_id == "R_JAVA_KEYWORD" for v in result.rule_violations)

    def test_non_keyword_allowed(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="className",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not any(v.rule_id == "R_JAVA_KEYWORD" for v in result.rule_violations)

    def test_all_common_keywords_blocked(self):
        for kw in ("int", "return", "void", "this", "null", "true", "false"):
            suggestion = NameSuggestion(
                original_name="x",
                suggested_name=kw,
                symbol_kind="variable",
                confidence=0.95,
                rationale="test",
                rules_addressed=["R1_REVEAL_INTENT"],
            )
            result = validate_suggestion(suggestion, annotations=[])
            assert any(v.rule_id == "R_JAVA_KEYWORD" for v in result.rule_violations), f"{kw} not blocked"


class TestJavaIdentifierValidation:
    """Tests for valid Java identifier checking."""

    def test_starts_with_digit_blocked(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="1stValue",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not result.is_valid
        assert any(v.rule_id == "R_INVALID_IDENTIFIER" for v in result.rule_violations)

    def test_contains_hyphen_blocked(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="my-value",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not result.is_valid
        assert any(v.rule_id == "R_INVALID_IDENTIFIER" for v in result.rule_violations)

    def test_contains_space_blocked(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="my value",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not result.is_valid

    def test_valid_camelcase_allowed(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="myValue",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not any(v.rule_id == "R_INVALID_IDENTIFIER" for v in result.rule_violations)

    def test_underscore_and_dollar_allowed(self):
        suggestion = NameSuggestion(
            original_name="x",
            suggested_name="_my$Value",
            symbol_kind="variable",
            confidence=0.95,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
        )
        result = validate_suggestion(suggestion, annotations=[])
        assert not any(v.rule_id == "R_INVALID_IDENTIFIER" for v in result.rule_violations)


class TestDetectScopeConflicts:
    """Tests for cross-suggestion conflict detection."""

    def _make_result(self, original, suggested, file="Account.java", confidence=0.90):
        s = NameSuggestion(
            original_name=original,
            suggested_name=suggested,
            symbol_kind="field",
            confidence=confidence,
            rationale="test",
            rules_addressed=[],
            location={"file": file, "line": 1},
        )
        from named.validation.validator import ValidationResult

        return ValidationResult(
            is_valid=True,
            suggestion=s,
            blocked_reasons=[],
            rule_violations=[],
        )

    def test_duplicate_target_blocks_lower_confidence(self):
        """When two suggestions map to same target, lower-confidence one is blocked."""
        r1 = self._make_result("data", "accountDetails", confidence=0.95)
        r2 = self._make_result("info", "accountDetails", confidence=0.90)

        detect_scope_conflicts([r1, r2])

        assert r1.is_valid is True
        assert r2.is_valid is False
        assert "G5_DUPLICATE_TARGET" in r2.blocked_reasons[0]

    def test_three_duplicates_keeps_highest(self):
        """With three duplicates, only the highest confidence survives."""
        r1 = self._make_result("data", "details", confidence=0.85)
        r2 = self._make_result("info", "details", confidence=0.95)
        r3 = self._make_result("obj", "details", confidence=0.80)

        detect_scope_conflicts([r1, r2, r3])

        assert r2.is_valid is True  # Highest confidence
        assert r1.is_valid is False
        assert r3.is_valid is False

    def test_different_files_no_conflict(self):
        """Same target name in different files is not a conflict."""
        r1 = self._make_result("data", "details", file="Foo.java")
        r2 = self._make_result("info", "details", file="Bar.java")

        detect_scope_conflicts([r1, r2])

        assert r1.is_valid is True
        assert r2.is_valid is True

    def test_different_targets_no_conflict(self):
        """Different target names in same file should not conflict."""
        r1 = self._make_result("data", "accountData")
        r2 = self._make_result("info", "accountInfo")

        detect_scope_conflicts([r1, r2])

        assert r1.is_valid is True
        assert r2.is_valid is True

    def test_already_invalid_not_considered(self):
        """Already-invalid results should not participate in conflict detection."""
        r1 = self._make_result("data", "details", confidence=0.95)
        r2 = self._make_result("info", "details", confidence=0.90)
        r2.is_valid = False  # Pre-blocked by another check

        detect_scope_conflicts([r1, r2])

        assert r1.is_valid is True  # No conflict since r2 was already invalid


class TestDetectOverrideConflicts:
    """Tests for override/implementation conflict detection."""

    def test_method_rename_blocked_when_override_exists(self):
        """Renaming a method that has overrides should be blocked."""
        from named.analysis.extractor import extract_symbols
        from named.validation.validator import detect_override_conflicts

        fixtures = Path(__file__).parent / "fixtures" / "hierarchy"
        all_symbols = []
        for f in sorted(fixtures.glob("*.java")):
            all_symbols.extend(extract_symbols(f))

        # Find Animal.java file path
        animal_file = str(fixtures / "Animal.java")

        suggestion = NameSuggestion(
            original_name="process",
            suggested_name="execute",
            symbol_kind="method",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
            location={"file": animal_file, "line": 6},
        )
        result = ValidationResult(
            is_valid=True,
            suggestion=suggestion,
            blocked_reasons=[],
            rule_violations=[],
        )

        detect_override_conflicts([result], all_symbols)
        assert result.is_valid is False
        assert any("G6_OVERRIDE_NOT_PROPAGATED" in r for r in result.blocked_reasons)

    def test_method_rename_allowed_when_no_overrides(self):
        """Renaming a method with no overrides should be allowed."""
        from named.analysis.extractor import extract_symbols
        from named.validation.validator import detect_override_conflicts

        fixtures = Path(__file__).parent / "fixtures" / "hierarchy"
        all_symbols = []
        for f in sorted(fixtures.glob("*.java")):
            all_symbols.extend(extract_symbols(f))

        animal_file = str(fixtures / "Animal.java")

        suggestion = NameSuggestion(
            original_name="uniqueMethod",
            suggested_name="specialMethod",
            symbol_kind="method",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
            location={"file": animal_file, "line": 14},
        )
        result = ValidationResult(
            is_valid=True,
            suggestion=suggestion,
            blocked_reasons=[],
            rule_violations=[],
        )

        detect_override_conflicts([result], all_symbols)
        assert result.is_valid is True


class TestDetectGetterSetterMismatches:
    """Tests for getter/setter mismatch warnings."""

    def test_warning_when_field_renamed_but_accessor_not(self):
        from named.analysis.extractor import extract_symbols
        from named.validation.validator import detect_getter_setter_mismatches

        fixtures = Path(__file__).parent / "fixtures" / "hierarchy"
        all_symbols = []
        for f in sorted(fixtures.glob("*.java")):
            all_symbols.extend(extract_symbols(f))

        gs_file = str(fixtures / "GetterSetterExample.java")

        suggestion = NameSuggestion(
            original_name="name",
            suggested_name="fullName",
            symbol_kind="field",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
            location={"file": gs_file, "line": 4},
        )
        result = ValidationResult(
            is_valid=True,
            suggestion=suggestion,
            blocked_reasons=[],
            rule_violations=[],
        )

        detect_getter_setter_mismatches([result], all_symbols)
        # Should still be valid (warning only, not blocking)
        assert result.is_valid is True
        # But should have a W_GETTER_SETTER warning
        assert any(v.rule_id == "W_GETTER_SETTER" for v in result.rule_violations)

    def test_no_warning_when_no_accessors(self):
        from named.analysis.extractor import extract_symbols
        from named.validation.validator import detect_getter_setter_mismatches

        fixtures = Path(__file__).parent / "fixtures" / "shadow"
        all_symbols = []
        for f in sorted(fixtures.glob("*.java")):
            all_symbols.extend(extract_symbols(f))

        shadow_file = str(fixtures / "ShadowExample.java")

        # 'data' field has a processData() method, but no getData()/setData()
        suggestion = NameSuggestion(
            original_name="data",
            suggested_name="content",
            symbol_kind="field",
            confidence=0.90,
            rationale="More descriptive",
            rules_addressed=["R1_REVEAL_INTENT"],
            location={"file": shadow_file, "line": 5},
        )
        result = ValidationResult(
            is_valid=True,
            suggestion=suggestion,
            blocked_reasons=[],
            rule_violations=[],
        )

        detect_getter_setter_mismatches([result], all_symbols)
        assert not any(v.rule_id == "W_GETTER_SETTER" for v in result.rule_violations)
