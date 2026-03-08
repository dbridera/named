"""Tests for shadow collision detection."""

from pathlib import Path

from named.analysis.extractor import extract_symbols
from named.rules.models import NameSuggestion
from named.validation.validator import ValidationResult, detect_shadow_collisions

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "shadow"
SHADOW_FILE = FIXTURES_DIR / "ShadowExample.java"


def _make_field_result(original, suggested, file, parent_class, confidence=0.90):
    s = NameSuggestion(
        original_name=original,
        suggested_name=suggested,
        symbol_kind="field",
        confidence=confidence,
        rationale="test",
        rules_addressed=["R1_REVEAL_INTENT"],
        location={"file": str(file), "line": 1},
    )
    return ValidationResult(
        is_valid=True,
        suggestion=s,
        blocked_reasons=[],
        rule_violations=[],
    )


class TestExtractMethodLocals:
    def test_method_locals_extracted(self):
        symbols = extract_symbols(SHADOW_FILE)
        type_sym = next(s for s in symbols if s.kind == "class" and s.name == "ShadowExample")

        assert "getBalance" in type_sym.method_locals
        assert "amount" in type_sym.method_locals["getBalance"]

    def test_parameters_included_in_locals(self):
        symbols = extract_symbols(SHADOW_FILE)
        type_sym = next(s for s in symbols if s.kind == "class" and s.name == "ShadowExample")

        assert "setBalance" in type_sym.method_locals
        assert "newBal" in type_sym.method_locals["setBalance"]

    def test_multiple_methods_captured(self):
        symbols = extract_symbols(SHADOW_FILE)
        type_sym = next(s for s in symbols if s.kind == "class" and s.name == "ShadowExample")

        assert "processData" in type_sym.method_locals
        assert "result" in type_sym.method_locals["processData"]


class TestDetectShadowCollisions:
    def test_shadow_collision_detected(self):
        symbols = extract_symbols(SHADOW_FILE)
        # Rename field 'bal' to 'amount' — shadows local 'amount' in getBalance()
        r = _make_field_result("bal", "amount", SHADOW_FILE, "ShadowExample")

        results = detect_shadow_collisions([r], symbols)

        assert r.is_valid is False
        assert any("G7_SHADOW_COLLISION" in reason for reason in r.blocked_reasons)

    def test_no_shadow_when_name_not_in_locals(self):
        symbols = extract_symbols(SHADOW_FILE)
        # Rename field 'bal' to 'balance' — no local named 'balance'
        r = _make_field_result("bal", "balance", SHADOW_FILE, "ShadowExample")

        results = detect_shadow_collisions([r], symbols)

        assert r.is_valid is True

    def test_no_shadow_for_method_kind(self):
        """Shadow check only applies to field/constant renames."""
        symbols = extract_symbols(SHADOW_FILE)
        s = NameSuggestion(
            original_name="getBalance",
            suggested_name="amount",
            symbol_kind="method",
            confidence=0.90,
            rationale="test",
            rules_addressed=["R1_REVEAL_INTENT"],
            location={"file": str(SHADOW_FILE), "line": 1},
        )
        r = ValidationResult(
            is_valid=True,
            suggestion=s,
            blocked_reasons=[],
            rule_violations=[],
        )

        results = detect_shadow_collisions([r], symbols)
        assert r.is_valid is True  # Method renames don't trigger shadow check

    def test_already_invalid_not_checked(self):
        symbols = extract_symbols(SHADOW_FILE)
        r = _make_field_result("bal", "amount", SHADOW_FILE, "ShadowExample")
        r.is_valid = False  # Pre-blocked

        results = detect_shadow_collisions([r], symbols)
        # Should not add more blocked reasons
        assert len(r.blocked_reasons) == 0
