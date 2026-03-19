"""Shared constants and utilities for streaming and batch analysis."""

from pathlib import Path
from typing import Any

from named.logging import get_logger
from named.rules.models import NameSuggestion

logger = get_logger("suggestions")

# Method-style name prefixes that are invalid for fields/parameters.
# Catching LLM hallucinations like "getBalance" suggested for a parameter.
METHOD_PREFIXES = (
    "get", "set", "is", "has", "find", "fetch", "load",
    "save", "update", "delete", "create", "build",
)

# Files with more symbols than CHUNK_THRESHOLD are split into chunks of CHUNK_SIZE.
CHUNK_THRESHOLD = 50
CHUNK_SIZE = 25

# Tokens per symbol output entry (rough estimate for JSON output sizing).
TOKENS_PER_SYMBOL = 120
TOKENS_BASE = 500
TOKENS_MAX = 8000
TOKENS_MIN = 1000


def strip_markdown_fences(content: str) -> str:
    """Strip markdown code fences from LLM response content.

    Handles ``\\`\\`\\`json ... \\`\\`\\`` and ``\\`\\`\\` ... \\`\\`\\`` wrappers.
    """
    stripped = content.strip()
    if stripped.startswith("```json"):
        stripped = stripped[7:]
    elif stripped.startswith("```"):
        stripped = stripped[3:]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    return stripped.strip()


def is_hallucinated(suggested_name: str, symbol_kind: str) -> bool:
    """Return True if the suggestion looks like a method name for a non-method symbol.

    Detects the common hallucination where the LLM suggests a getter/setter-style
    name for a field or parameter (e.g., 'getBalance' suggested for a parameter).
    """
    if symbol_kind not in ("field", "parameter", "constant"):
        return False
    for prefix in METHOD_PREFIXES:
        if (
            suggested_name.startswith(prefix)
            and len(suggested_name) > len(prefix)
            and suggested_name[len(prefix)].isupper()
        ):
            return True
    return False


def enrich_suggestion(
    suggestion: NameSuggestion,
    symbol_name: str,
    symbol_kind: str,
    symbol_file: str,
    symbol_line: int,
    parent_class: str | None,
    annotations: list[str],
    java_files: list[Path],
) -> "ValidationResult | None":
    """Enrich a NameSuggestion with references, impact, location, and validate it.

    This is the shared post-LLM processing pipeline used by both streaming and batch modes.

    Returns:
        ValidationResult if the suggestion is valid, None if filtered out.
    """
    from named.analysis.impact_analyzer import compute_rename_impact
    from named.analysis.reference_finder import find_references
    from named.validation.validator import ValidationResult, validate_suggestion

    # Fill in symbol_kind if missing
    if not suggestion.symbol_kind:
        suggestion.symbol_kind = symbol_kind

    # Hallucination filter
    if is_hallucinated(suggestion.suggested_name, suggestion.symbol_kind):
        logger.info(
            f"Filtered hallucination: {symbol_name} ({symbol_kind}) → "
            f"'{suggestion.suggested_name}' (looks like a method name)"
        )
        return None

    # Find references
    refs = find_references(
        symbol_name=symbol_name,
        symbol_kind=symbol_kind,
        java_files=java_files,
        parent_class=parent_class,
    )
    suggestion.references = refs
    suggestion.location = {
        "file": symbol_file,
        "line": symbol_line,
    }

    # Compute impact
    suggestion.impact_analysis = compute_rename_impact(refs)

    # Validate against guardrails
    return validate_suggestion(suggestion, annotations)


def post_validate_results(
    results: list,
    all_symbols: list,
) -> tuple[list, int]:
    """Run all cross-suggestion validation checks.

    This is the shared post-validation pipeline used by both streaming and batch modes.

    Args:
        results: List of ValidationResult objects.
        all_symbols: List of Symbol objects for hierarchy/scope analysis.

    Returns:
        Tuple of (updated_results, conflicts_found_count).
    """
    from named.validation.validator import (
        detect_getter_setter_mismatches,
        detect_override_conflicts,
        detect_scope_conflicts,
        detect_shadow_collisions,
    )

    pre_valid = sum(1 for r in results if r.is_valid)
    results = detect_scope_conflicts(results, all_symbols)
    results = detect_override_conflicts(results, all_symbols)
    results = detect_shadow_collisions(results, all_symbols)
    results = detect_getter_setter_mismatches(results, all_symbols)
    post_valid = sum(1 for r in results if r.is_valid)

    return results, pre_valid - post_valid


def export_reports(
    results: list,
    all_symbols: list,
    output: Path,
    project_path: Path,
    model: str,
    format: str = "all",
) -> dict[str, Path]:
    """Generate JSON and/or Markdown reports.

    Args:
        results: List of ValidationResult objects.
        all_symbols: List of Symbol objects.
        output: Output directory.
        project_path: Path to the analyzed project.
        model: LLM model used.
        format: Output format: "json", "md", or "all".

    Returns:
        Dict of format -> path for generated reports.
    """
    output.mkdir(parents=True, exist_ok=True)
    paths = {}

    if format in ("json", "all"):
        from named.export.json_exporter import export_json

        paths["json"] = export_json(results, all_symbols, output, project_path, model)

    if format in ("md", "all"):
        from named.export.markdown_exporter import export_markdown

        paths["md"] = export_markdown(results, all_symbols, output, project_path, model)

    return paths


def reconstruct_symbol(sd: dict[str, Any]) -> "Symbol":
    """Reconstruct a Symbol object from a serialized dict.

    Used by batch_retrieve to rebuild Symbol objects from batch_jobs.json data.
    """
    from named.analysis.extractor import SourceLocation, Symbol

    method_locals = {}
    if sd.get("method_locals"):
        method_locals = {k: set(v) for k, v in sd["method_locals"].items()}

    return Symbol(
        name=sd["name"],
        kind=sd["kind"],
        location=SourceLocation(
            file=Path(sd["file"]),
            line=sd.get("line", 0),
            column=0,
        ),
        annotations=sd.get("annotations", []),
        modifiers=sd.get("modifiers", []),
        parent_class=sd.get("parent_class"),
        context=sd.get("context", ""),
        extends_type=sd.get("extends_type"),
        implements_types=sd.get("implements_types", []),
        parameter_types=sd.get("parameter_types", []),
        method_locals=method_locals,
    )
