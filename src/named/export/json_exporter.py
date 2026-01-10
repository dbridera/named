"""JSON report exporter."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from named.analysis.extractor import Symbol
from named.validation.validator import ValidationResult


def export_json(
    results: list[ValidationResult],
    symbols: list[Symbol],
    output_path: Path,
    project_path: Path,
    model: str = "gpt-4o",
) -> Path:
    """Export analysis results to JSON format.

    Args:
        results: List of validation results
        symbols: List of analyzed symbols
        output_path: Path to write the JSON file
        project_path: Path to the analyzed project
        model: LLM model used for analysis

    Returns:
        Path to the created JSON file
    """
    # Build summary statistics
    summary = _build_summary(results, symbols)

    # Build the report
    report = {
        "metadata": {
            "project_path": str(project_path.absolute()),
            "generated_at": datetime.now().isoformat(),
            "llm_model": model,
            "named_version": "0.1.0",
        },
        "summary": summary,
        "suggestions": [r.to_dict() for r in results if r.suggestion.suggested_name],
        "blocked_symbols": _get_blocked_symbols(results),
        "all_symbols": [s.to_dict() for s in symbols],
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    json_path = output_path if output_path.suffix == ".json" else output_path / "report.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return json_path


def _build_summary(results: list[ValidationResult], symbols: list[Symbol]) -> dict[str, Any]:
    """Build summary statistics from results."""
    total_symbols = len(symbols)
    suggestions_count = sum(1 for r in results if r.suggestion.suggested_name)
    valid_suggestions = sum(1 for r in results if r.is_valid and r.suggestion.suggested_name)
    blocked_count = sum(1 for r in results if r.suggestion.blocked)

    # Count violations by rule
    violations_by_rule: dict[str, int] = {}
    for result in results:
        for rule_id in result.suggestion.rules_addressed:
            violations_by_rule[rule_id] = violations_by_rule.get(rule_id, 0) + 1

    # Count by symbol kind
    symbols_by_kind: dict[str, int] = {}
    for symbol in symbols:
        symbols_by_kind[symbol.kind] = symbols_by_kind.get(symbol.kind, 0) + 1

    # Calculate average confidence
    confidences = [r.suggestion.confidence for r in results if r.suggestion.suggested_name]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "total_symbols_analyzed": total_symbols,
        "suggestions_generated": suggestions_count,
        "valid_suggestions": valid_suggestions,
        "blocked_suggestions": blocked_count,
        "average_confidence": round(avg_confidence, 2),
        "violations_by_rule": violations_by_rule,
        "symbols_by_kind": symbols_by_kind,
    }


def _get_blocked_symbols(results: list[ValidationResult]) -> list[dict[str, Any]]:
    """Get list of blocked symbols with reasons."""
    blocked = []
    for result in results:
        if result.suggestion.blocked:
            blocked.append({
                "symbol_name": result.suggestion.original_name,
                "symbol_kind": result.suggestion.symbol_kind,
                "reason": result.suggestion.blocked_reason,
            })
    return blocked


def export_json_string(
    results: list[ValidationResult],
    symbols: list[Symbol],
    project_path: Path,
    model: str = "gpt-4o",
) -> str:
    """Export analysis results to JSON string.

    Args:
        results: List of validation results
        symbols: List of analyzed symbols
        project_path: Path to the analyzed project
        model: LLM model used

    Returns:
        JSON string
    """
    summary = _build_summary(results, symbols)

    report = {
        "metadata": {
            "project_path": str(project_path.absolute()),
            "generated_at": datetime.now().isoformat(),
            "llm_model": model,
            "named_version": "0.1.0",
        },
        "summary": summary,
        "suggestions": [r.to_dict() for r in results if r.suggestion.suggested_name],
        "blocked_symbols": _get_blocked_symbols(results),
    }

    return json.dumps(report, indent=2, ensure_ascii=False)
