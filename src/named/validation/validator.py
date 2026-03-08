"""Validation of suggestions against guardrails and rules."""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from named.logging import get_logger
from named.rules.guardrails import check_all_guardrails, is_blocked
from named.rules.models import NameSuggestion, RuleViolation, Severity
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

        # Check constant naming convention
        constant_violation = _check_constant_naming_convention(
            suggestion.suggested_name,
            suggestion.symbol_kind,
        )
        if constant_violation:
            rule_violations.append(constant_violation)

        # Check Java keyword collision
        keyword_violation = _check_java_keyword(suggestion.suggested_name)
        if keyword_violation:
            rule_violations.append(keyword_violation)

        # Check valid Java identifier
        identifier_violation = _check_valid_java_identifier(suggestion.suggested_name)
        if identifier_violation:
            rule_violations.append(identifier_violation)

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


def _check_constant_naming_convention(
    suggested_name: str,
    symbol_kind: str,
) -> RuleViolation | None:
    """Check that constants use UPPER_SNAKE_CASE.

    Args:
        suggested_name: The proposed new name.
        symbol_kind: The kind of symbol (constant, field, etc.).

    Returns:
        RuleViolation if a constant is suggested with non-uppercase name.
    """
    if symbol_kind != "constant":
        return None

    if not re.match(r"^[A-Z][A-Z0-9_]*$", suggested_name):
        upper = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", suggested_name).upper()
        return RuleViolation(
            rule_id="R_CONSTANT_CASE",
            symbol_name=suggested_name,
            severity=Severity.ERROR,
            message=f"Constant must use UPPER_SNAKE_CASE. Suggestion: '{upper}'",
            suggestion=upper,
        )
    return None


JAVA_KEYWORDS = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "false", "final", "finally", "float", "for", "goto", "if",
    "implements", "import", "instanceof", "int", "interface", "long", "native",
    "new", "null", "package", "private", "protected", "public", "return",
    "short", "static", "strictfp", "super", "switch", "synchronized", "this",
    "throw", "throws", "transient", "true", "try", "void", "volatile", "while",
    # Java literals that can't be identifiers
    "var", "yield", "record", "sealed", "permits",
})


def _check_java_keyword(suggested_name: str) -> RuleViolation | None:
    """Block renaming to a Java reserved keyword."""
    if suggested_name in JAVA_KEYWORDS:
        return RuleViolation(
            rule_id="R_JAVA_KEYWORD",
            symbol_name=suggested_name,
            severity=Severity.ERROR,
            message=f"'{suggested_name}' is a Java reserved keyword",
        )
    return None


def _check_valid_java_identifier(suggested_name: str) -> RuleViolation | None:
    """Block names that aren't valid Java identifiers."""
    if not suggested_name:
        return RuleViolation(
            rule_id="R_INVALID_IDENTIFIER",
            symbol_name=suggested_name,
            severity=Severity.ERROR,
            message="Empty identifier name",
        )
    if suggested_name[0].isdigit():
        return RuleViolation(
            rule_id="R_INVALID_IDENTIFIER",
            symbol_name=suggested_name,
            severity=Severity.ERROR,
            message=f"'{suggested_name}' starts with a digit",
        )
    if not all(c.isalnum() or c in ("_", "$") for c in suggested_name):
        return RuleViolation(
            rule_id="R_INVALID_IDENTIFIER",
            symbol_name=suggested_name,
            severity=Severity.ERROR,
            message=f"'{suggested_name}' contains invalid characters for a Java identifier",
        )
    return None


def detect_scope_conflicts(
    results: list[ValidationResult],
    all_symbols: list["Symbol"] | None = None,
) -> list[ValidationResult]:
    """Detect cross-suggestion naming conflicts within the same scope.

    Checks two conflict types:
    - G5a: Two suggestions produce the same target name in the same scope.
    - G5b: A suggested name collides with an existing (non-renamed) symbol.

    Args:
        results: List of ValidationResults from individual validation.
        all_symbols: All symbols in the project for collision checks.

    Returns:
        The same list with conflicts marked as invalid/blocked.
    """
    # Build scope -> {suggested_name -> [results]} mapping
    # Scope key = (file_path, parent_class)
    scope_map: dict[tuple[str, str], dict[str, list[ValidationResult]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for r in results:
        if not r.is_valid or not r.suggestion.suggested_name:
            continue

        file_path = ""
        if r.suggestion.location:
            file_path = r.suggestion.location.get("file", "")

        parent_class = getattr(r.suggestion, "parent_class", "") or ""
        scope_key = (file_path, parent_class)

        scope_map[scope_key][r.suggestion.suggested_name].append(r)

    # G5a: Detect duplicate suggested names within same scope
    for scope_key, name_groups in scope_map.items():
        for suggested_name, conflicting in name_groups.items():
            if len(conflicting) <= 1:
                continue

            # Keep highest confidence, block the rest
            sorted_by_conf = sorted(
                conflicting,
                key=lambda r: r.suggestion.confidence,
                reverse=True,
            )
            for r in sorted_by_conf[1:]:
                reason = (
                    f"G5_DUPLICATE_TARGET: Suggested name '{suggested_name}' "
                    f"conflicts with another suggestion in the same scope"
                )
                r.is_valid = False
                r.blocked_reasons.append(reason)
                r.suggestion.blocked = True
                r.suggestion.blocked_reason = (
                    (r.suggestion.blocked_reason + "; " if r.suggestion.blocked_reason else "")
                    + reason
                )
                logger.info(
                    f"Blocked duplicate: {r.suggestion.original_name} -> "
                    f"{suggested_name} (lower confidence)"
                )

    # G5b: Detect collision with existing symbol names
    if all_symbols:
        existing_by_file: dict[str, set[str]] = defaultdict(set)
        for sym in all_symbols:
            file_key = str(sym.location.file)
            existing_by_file[file_key].add(sym.name)

        # Build set of names being renamed away (per file)
        renamed_away_by_file: dict[str, set[str]] = defaultdict(set)
        for r in results:
            if not r.is_valid or not r.suggestion.location:
                continue
            fp = r.suggestion.location.get("file", "")
            renamed_away_by_file[fp].add(r.suggestion.original_name)

        for r in results:
            if not r.is_valid or not r.suggestion.suggested_name:
                continue

            file_path = ""
            if r.suggestion.location:
                file_path = r.suggestion.location.get("file", "")

            existing = existing_by_file.get(file_path, set())
            renamed_away = renamed_away_by_file.get(file_path, set())
            still_existing = existing - renamed_away

            if r.suggestion.suggested_name in still_existing:
                reason = (
                    f"G5_EXISTING_COLLISION: Suggested name '{r.suggestion.suggested_name}' "
                    f"already exists in {Path(file_path).name}"
                )
                r.is_valid = False
                r.blocked_reasons.append(reason)
                r.suggestion.blocked = True
                r.suggestion.blocked_reason = (
                    (r.suggestion.blocked_reason + "; " if r.suggestion.blocked_reason else "")
                    + reason
                )
                logger.info(
                    f"Blocked collision: {r.suggestion.original_name} -> "
                    f"{r.suggestion.suggested_name} (name exists)"
                )

    return results


def detect_override_conflicts(
    results: list[ValidationResult],
    all_symbols: list["Symbol"],
) -> list[ValidationResult]:
    """Block method renames that have unhandled overrides/implementations.

    When a method in a parent class or interface is renamed, all overriding
    methods in subclasses/implementations must also be renamed. Since we
    don't propagate renames automatically, we block such renames with a
    warning listing the affected subtypes.

    Args:
        results: Validation results to check.
        all_symbols: All extracted symbols for hierarchy analysis.

    Returns:
        Updated results with override conflicts blocked.
    """
    if not all_symbols:
        return results

    from named.analysis.hierarchy import build_type_hierarchy, find_override_methods

    type_map = build_type_hierarchy(all_symbols)

    for r in results:
        if not r.is_valid:
            continue
        if r.suggestion.symbol_kind != "method":
            continue
        if not r.suggestion.original_name or not r.suggestion.suggested_name:
            continue

        # Find the Symbol to get parent_class and param_types
        parent_class = None
        param_types: list[str] = []
        if r.suggestion.location:
            for sym in all_symbols:
                if (
                    sym.kind == "method"
                    and sym.name == r.suggestion.original_name
                    and sym.parent_class
                    and str(sym.location.file) == r.suggestion.location.get("file", "")
                ):
                    parent_class = sym.parent_class
                    param_types = sym.parameter_types
                    break

        if not parent_class:
            continue

        overrides = find_override_methods(
            method_name=r.suggestion.original_name,
            param_types=param_types,
            parent_class=parent_class,
            type_map=type_map,
        )

        if overrides:
            override_classes = [m.parent_class for m in overrides]
            reason = (
                f"G6_OVERRIDE_NOT_PROPAGATED: Method '{r.suggestion.original_name}()' "
                f"is overridden in {', '.join(override_classes)}. "
                f"Rename would break compilation."
            )
            r.is_valid = False
            r.blocked_reasons.append(reason)
            r.suggestion.blocked = True
            r.suggestion.blocked_reason = (
                (r.suggestion.blocked_reason + "; " if r.suggestion.blocked_reason else "")
                + reason
            )
            logger.info(
                f"Blocked override conflict: {parent_class}.{r.suggestion.original_name}() "
                f"overridden in {override_classes}"
            )

    return results


def detect_shadow_collisions(
    results: list[ValidationResult],
    all_symbols: list["Symbol"],
) -> list[ValidationResult]:
    """Block field/constant renames that shadow local variables in the same class.

    Args:
        results: Validation results to check.
        all_symbols: All extracted symbols (type symbols have method_locals).

    Returns:
        Updated results with shadow collisions blocked.
    """
    if not all_symbols:
        return results

    # Build class → method_locals map
    class_locals: dict[str, dict[str, set[str]]] = {}
    for sym in all_symbols:
        if sym.kind in ("class", "interface", "enum") and sym.method_locals:
            class_locals[sym.name] = sym.method_locals

    for r in results:
        if not r.is_valid:
            continue
        if r.suggestion.symbol_kind not in ("field", "constant"):
            continue
        if not r.suggestion.suggested_name:
            continue

        # Find parent class for this field
        parent_class = None
        for sym in all_symbols:
            if (
                sym.kind in ("field", "constant")
                and sym.name == r.suggestion.original_name
                and sym.parent_class
                and r.suggestion.location
                and str(sym.location.file) == r.suggestion.location.get("file", "")
            ):
                parent_class = sym.parent_class
                break

        if not parent_class or parent_class not in class_locals:
            continue

        # Check if suggested name shadows any local variable
        for method_name, local_names in class_locals[parent_class].items():
            if r.suggestion.suggested_name in local_names:
                reason = (
                    f"G7_SHADOW_COLLISION: Renaming '{r.suggestion.original_name}' "
                    f"to '{r.suggestion.suggested_name}' would shadow local variable "
                    f"'{r.suggestion.suggested_name}' in method '{method_name}()'"
                )
                r.is_valid = False
                r.blocked_reasons.append(reason)
                r.suggestion.blocked = True
                r.suggestion.blocked_reason = (
                    (r.suggestion.blocked_reason + "; " if r.suggestion.blocked_reason else "")
                    + reason
                )
                logger.info(
                    f"Blocked shadow: {r.suggestion.original_name} -> "
                    f"{r.suggestion.suggested_name} shadows local in {method_name}()"
                )
                break  # One shadow is enough to block

    return results


def detect_getter_setter_mismatches(
    results: list[ValidationResult],
    all_symbols: list["Symbol"],
) -> list[ValidationResult]:
    """Add warnings when field renames leave getters/setters with stale names.

    Does NOT block the rename — only attaches a warning for the report.

    Args:
        results: Validation results to check.
        all_symbols: All extracted symbols.

    Returns:
        Updated results with warnings attached.
    """
    if not all_symbols:
        return results

    # Build class → method names map
    class_methods: dict[str, set[str]] = defaultdict(set)
    for sym in all_symbols:
        if sym.kind == "method" and sym.parent_class:
            class_methods[sym.parent_class].add(sym.name)

    # Build set of method names being renamed (to avoid false positives)
    renamed_methods: set[str] = set()
    for r in results:
        if r.is_valid and r.suggestion.symbol_kind == "method":
            renamed_methods.add(r.suggestion.original_name)

    for r in results:
        if not r.is_valid:
            continue
        if r.suggestion.symbol_kind not in ("field", "constant"):
            continue
        if not r.suggestion.suggested_name or not r.suggestion.original_name:
            continue

        # Find parent class
        parent_class = None
        for sym in all_symbols:
            if (
                sym.kind in ("field", "constant")
                and sym.name == r.suggestion.original_name
                and sym.parent_class
                and r.suggestion.location
                and str(sym.location.file) == r.suggestion.location.get("file", "")
            ):
                parent_class = sym.parent_class
                break

        if not parent_class:
            continue

        methods = class_methods.get(parent_class, set())
        old_name = r.suggestion.original_name
        new_name = r.suggestion.suggested_name
        old_capitalized = old_name[0].upper() + old_name[1:] if old_name else ""

        stale_methods = []
        for prefix in ("get", "set", "is"):
            accessor = prefix + old_capitalized
            if accessor in methods and accessor not in renamed_methods:
                stale_methods.append(accessor)

        if stale_methods:
            new_capitalized = new_name[0].upper() + new_name[1:] if new_name else ""
            stale_str = ", ".join(f"{m}()" for m in stale_methods)
            warning = (
                f"Field renamed to '{new_name}' but {stale_str} "
                f"not renamed. Consider renaming to match "
                f"(e.g., get{new_capitalized}()/set{new_capitalized}())."
            )
            # Add as a non-blocking warning (don't set is_valid=False)
            r.rule_violations.append(
                RuleViolation(
                    rule_id="W_GETTER_SETTER",
                    symbol_name=r.suggestion.original_name,
                    severity=Severity.WARNING,
                    message=warning,
                )
            )
            logger.info(
                f"Getter/setter warning: {old_name} -> {new_name}, "
                f"stale accessors: {stale_methods}"
            )

    return results
