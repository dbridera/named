"""Validation of suggestions against guardrails and rules."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from named.logging import get_logger
from named.rules.guardrails import check_all_guardrails, is_blocked
from named.rules.models import NameSuggestion, RuleViolation
from named.rules.naming_rules import NAMING_RULES

if TYPE_CHECKING:
    from named.analysis.extractor import Symbol

logger = get_logger("validation")


@dataclass
class ValidationResult:
    """Result of validating a suggestion."""

    is_valid: bool
    suggestion: NameSuggestion
    blocked_reasons: list[str]
    rule_violations: list[RuleViolation]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        suggestion_dict = {
            "original_name": self.suggestion.original_name,
            "suggested_name": self.suggestion.suggested_name,
            "symbol_kind": self.suggestion.symbol_kind,
            "confidence": self.suggestion.confidence,
            "rationale": self.suggestion.rationale,
            "rules_addressed": self.suggestion.rules_addressed,
            "blocked": self.suggestion.blocked,
            "blocked_reason": self.suggestion.blocked_reason,
        }

        # Include references if available
        if self.suggestion.references:
            refs_dicts = []
            for ref in self.suggestion.references:
                try:
                    refs_dicts.append(ref.to_dict())
                except Exception as e:
                    logger.warning(
                        f"Failed to serialize reference for {self.suggestion.original_name}: {e}"
                    )
                    # Include error info for debugging
                    refs_dicts.append(
                        {
                            "error": type(e).__name__,
                            "message": str(e),
                            "ref_type": type(ref).__name__,
                        }
                    )
            suggestion_dict["references"] = refs_dicts
            suggestion_dict["reference_count"] = len(self.suggestion.references)

        # Include location if available
        if self.suggestion.location:
            suggestion_dict["location"] = self.suggestion.location

        # Include impact analysis if available
        if self.suggestion.impact_analysis:
            suggestion_dict["impact_analysis"] = self.suggestion.impact_analysis.to_dict()

        return {
            "is_valid": self.is_valid,
            "suggestion": suggestion_dict,
            "blocked_reasons": self.blocked_reasons,
            "rule_violations": [
                {
                    "rule_id": v.rule_id,
                    "message": v.message,
                    "severity": v.severity.value,
                }
                for v in self.rule_violations
            ],
        }


def validate_suggestion(
    suggestion: NameSuggestion,
    annotations: list[str],
) -> ValidationResult:
    """Validate a naming suggestion against guardrails.

    Args:
        suggestion: The suggestion to validate
        annotations: Annotations on the original symbol

    Returns:
        ValidationResult indicating if the suggestion is valid
    """
    blocked_reasons = []
    rule_violations = []

    # Check guardrails
    guardrail_blocks = check_all_guardrails(
        annotations=annotations,
        confidence=suggestion.confidence,
    )

    if guardrail_blocks:
        for guardrail_id, reason in guardrail_blocks:
            blocked_reasons.append(f"{guardrail_id}: {reason}")

    # Update suggestion with blocked status
    if blocked_reasons:
        suggestion.blocked = True
        suggestion.blocked_reason = "; ".join(blocked_reasons)

    # Check if suggested name violates any rules
    if suggestion.suggested_name:
        rule_violations = check_name_against_rules(
            suggestion.suggested_name,
            suggestion.symbol_kind,
        )

    is_valid = len(blocked_reasons) == 0 and len(rule_violations) == 0

    return ValidationResult(
        is_valid=is_valid,
        suggestion=suggestion,
        blocked_reasons=blocked_reasons,
        rule_violations=rule_violations,
    )


def check_name_against_rules(name: str, symbol_kind: str) -> list[RuleViolation]:
    """Check a name against all naming rules.

    This is a pre-validation to ensure suggested names don't violate rules.

    Args:
        name: The name to check
        symbol_kind: The kind of symbol

    Returns:
        List of rule violations found
    """
    violations = []

    for rule in NAMING_RULES:
        violation = _check_single_rule(rule, name, symbol_kind)
        if violation:
            violations.append(violation)

    return violations


def _check_single_rule(rule, name: str, symbol_kind: str) -> RuleViolation | None:
    """Check a name against a single rule.

    Args:
        rule: The NamingRule to check
        name: The name to check
        symbol_kind: The kind of symbol

    Returns:
        RuleViolation if the rule is violated, None otherwise
    """
    # Check exceptions first
    if name in rule.exceptions:
        return None

    # Check detect patterns
    for pattern in rule.detect_patterns:
        try:
            if re.match(pattern, name):
                return RuleViolation(
                    rule_id=rule.id,
                    symbol_name=name,
                    severity=rule.severity,
                    message=f"Violates {rule.name_en}",
                )
        except re.error:
            # Invalid regex pattern, skip
            pass

    # Check tokens to avoid
    name_lower = name.lower()
    for token in rule.tokens_to_avoid:
        if token.lower() in name_lower:
            return RuleViolation(
                rule_id=rule.id,
                symbol_name=name,
                severity=rule.severity,
                message=f"Contains discouraged token '{token}'",
            )

    return None


def pre_filter_symbols(symbols: list["Symbol"]) -> tuple[list["Symbol"], list["Symbol"]]:
    """Pre-filter symbols to separate those that can be analyzed from blocked ones.

    Args:
        symbols: List of symbols to filter

    Returns:
        Tuple of (analyzable_symbols, blocked_symbols)
    """
    analyzable = []
    blocked = []

    for symbol in symbols:
        if is_blocked(symbol.annotations):
            blocked.append(symbol)
        else:
            analyzable.append(symbol)

    return analyzable, blocked


def validate_all_suggestions(
    suggestions: list[NameSuggestion],
    symbol_annotations: dict[str, list[str]],
) -> list[ValidationResult]:
    """Validate multiple suggestions.

    Args:
        suggestions: List of suggestions to validate
        symbol_annotations: Dict mapping symbol names to their annotations

    Returns:
        List of ValidationResult objects
    """
    results = []

    for suggestion in suggestions:
        annotations = symbol_annotations.get(suggestion.original_name, [])
        result = validate_suggestion(suggestion, annotations)
        results.append(result)

    return results
