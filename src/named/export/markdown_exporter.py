"""Markdown report exporter."""

from datetime import datetime
from pathlib import Path

from named.analysis.extractor import Symbol
from named.validation.validator import ValidationResult

# Display configuration constants for impact analysis report
MAX_HIGH_IMPACT_ITEMS = 5  # Maximum high-impact items to show in detail
MAX_MEDIUM_IMPACT_ITEMS = 10  # Maximum medium-impact items to show in detail
MAX_LOW_IMPACT_ITEMS = 20  # Maximum low-impact items to show in collapsed section
MAX_FILES_PER_ITEM = 6  # Maximum files to show per impact item
MAX_REFS_PER_FILE = 3  # Maximum references to show per file
MAX_SNIPPET_LENGTH = 60  # Maximum code snippet length before truncation


def export_markdown(
    results: list[ValidationResult],
    symbols: list[Symbol],
    output_path: Path,
    project_path: Path,
    model: str = "gpt-4o",
) -> Path:
    """Export analysis results to Markdown format.

    Args:
        results: List of validation results
        symbols: List of analyzed symbols
        output_path: Path to write the Markdown file
        project_path: Path to the analyzed project
        model: LLM model used for analysis

    Returns:
        Path to the created Markdown file
    """
    content = _build_markdown_content(results, symbols, project_path, model)

    # Determine final output path
    md_path = output_path if output_path.suffix == ".md" else output_path / "report.md"

    # Ensure output directory exists
    md_path.parent.mkdir(parents=True, exist_ok=True)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    return md_path


def _build_markdown_content(
    results: list[ValidationResult],
    symbols: list[Symbol],
    project_path: Path,
    model: str,
) -> str:
    """Build the Markdown report content."""
    # Calculate statistics
    total_symbols = len(symbols)
    suggestions_count = sum(1 for r in results if r.suggestion.suggested_name)
    valid_suggestions = sum(1 for r in results if r.is_valid and r.suggestion.suggested_name)
    blocked_count = sum(1 for r in results if r.suggestion.blocked)

    # High confidence suggestions (>= 0.85)
    high_confidence = [
        r for r in results if r.suggestion.suggested_name and r.suggestion.confidence >= 0.85
    ]

    # Count violations by rule
    violations_by_rule: dict[str, int] = {}
    for result in results:
        for rule_id in result.suggestion.rules_addressed:
            violations_by_rule[rule_id] = violations_by_rule.get(rule_id, 0) + 1

    content = f"""# Named Analysis Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Project**: `{project_path.absolute()}`
**Model**: {model}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Symbols Analyzed | {total_symbols} |
| Suggestions Generated | {suggestions_count} |
| Valid Suggestions | {valid_suggestions} |
| Blocked by Guardrails | {blocked_count} |

"""

    # Violations by rule
    if violations_by_rule:
        content += """## Violations by Rule

| Rule | Count |
|------|-------|
"""
        for rule_id, count in sorted(violations_by_rule.items()):
            content += f"| {rule_id} | {count} |\n"
        content += "\n"

    # Impact analysis section
    content += _build_impact_analysis_section(results)

    # High confidence suggestions
    if high_confidence:
        content += """## Recommended Changes (High Confidence)

These suggestions have confidence >= 0.85 and should be safe to apply.

"""
        for result in sorted(high_confidence, key=lambda r: -r.suggestion.confidence):
            s = result.suggestion
            content += f"""### `{s.original_name}` → `{s.suggested_name}`

- **Kind**: {s.symbol_kind}
- **Confidence**: {s.confidence:.0%}
- **Rationale**: {s.rationale}
- **Rules Addressed**: {", ".join(s.rules_addressed) or "N/A"}
"""
            # Add references if available
            if hasattr(s, "references") and s.references:
                content += f"- **Used in {len(s.references)} location(s)**:\n"
                for ref in s.references[:10]:  # Limit to 10 references
                    content += f"  - {ref.file.name}:{ref.line} → `{ref.code_snippet.strip()}`\n"
                if len(s.references) > 10:
                    content += f"  - ... and {len(s.references) - 10} more\n"

            content += "\n"

    # All suggestions
    all_valid = [r for r in results if r.is_valid and r.suggestion.suggested_name]
    if all_valid:
        content += """## All Valid Suggestions

| Original | Suggested | Kind | Confidence | Rules |
|----------|-----------|------|------------|-------|
"""
        for result in sorted(all_valid, key=lambda r: -r.suggestion.confidence):
            s = result.suggestion
            rules = ", ".join(s.rules_addressed) if s.rules_addressed else "-"
            content += f"| `{s.original_name}` | `{s.suggested_name}` | {s.symbol_kind} | {s.confidence:.0%} | {rules} |\n"
        content += "\n"

    # Blocked symbols
    blocked = [r for r in results if r.suggestion.blocked]
    if blocked:
        content += """## Blocked Symbols

These symbols were not renamed due to guardrail restrictions.

| Symbol | Kind | Reason |
|--------|------|--------|
"""
        for result in blocked:
            s = result.suggestion
            reason = s.blocked_reason or "Unknown"
            content += f"| `{s.original_name}` | {s.symbol_kind} | {reason} |\n"
        content += "\n"

    # Footer
    content += """---

*Report generated by [Named](https://github.com/your-org/named) - Intelligent Java Code Refactoring System*
"""

    return content


def _build_impact_analysis_section(results: list[ValidationResult]) -> str:
    """Build the impact analysis section of the report.

    Args:
        results: List of validation results

    Returns:
        Markdown string for impact analysis section
    """
    # Collect suggestions with impact analysis
    results_with_impact = [
        r for r in results if r.suggestion.impact_analysis and r.suggestion.suggested_name
    ]

    if not results_with_impact:
        return ""

    # Categorize by risk level
    high_impact = [
        r for r in results_with_impact if r.suggestion.impact_analysis.risk_level == "high"
    ]
    medium_impact = [
        r for r in results_with_impact if r.suggestion.impact_analysis.risk_level == "medium"
    ]
    low_impact = [
        r for r in results_with_impact if r.suggestion.impact_analysis.risk_level == "low"
    ]

    # Calculate total unique files affected
    all_files = set()
    for r in results_with_impact:
        all_files.update(r.suggestion.impact_analysis.affected_files)

    total = len(results_with_impact)

    content = """## Rename Impact Analysis

This section shows which files will be affected by each suggested rename.

### Impact Distribution

| Risk Level | Count | Percentage |
|------------|-------|------------|
"""

    # Calculate percentages
    high_pct = (len(high_impact) / total * 100) if total > 0 else 0
    medium_pct = (len(medium_impact) / total * 100) if total > 0 else 0
    low_pct = (len(low_impact) / total * 100) if total > 0 else 0

    content += f"| High (11+) | {len(high_impact)} | {high_pct:.0f}% |\n"
    content += f"| Medium (4-10) | {len(medium_impact)} | {medium_pct:.0f}% |\n"
    content += f"| Low (1-3) | {len(low_impact)} | {low_pct:.0f}% |\n"
    content += (
        f"\n**Total unique files affected**: {len(all_files)} files across all suggestions\n\n"
    )
    content += "---\n\n"

    # High impact changes
    if high_impact:
        content += "### High Impact Changes (11+ files)\n\n"
        for result in sorted(
            high_impact, key=lambda r: -r.suggestion.impact_analysis.affected_file_count
        )[:MAX_HIGH_IMPACT_ITEMS]:
            content += _format_impact_item(result, show_details=False)
        if len(high_impact) > MAX_HIGH_IMPACT_ITEMS:
            content += (
                f"*... and {len(high_impact) - MAX_HIGH_IMPACT_ITEMS} more high-impact changes*\n\n"
            )
        content += "---\n\n"

    # Medium impact changes
    if medium_impact:
        content += "### Medium Impact Changes (4-10 files)\n\n"
        for result in sorted(
            medium_impact, key=lambda r: -r.suggestion.impact_analysis.affected_file_count
        )[:MAX_MEDIUM_IMPACT_ITEMS]:
            content += _format_impact_item(result, show_details=True)
        if len(medium_impact) > MAX_MEDIUM_IMPACT_ITEMS:
            content += f"*... and {len(medium_impact) - MAX_MEDIUM_IMPACT_ITEMS} more medium-impact changes*\n\n"
        content += "---\n\n"

    # Low impact changes (just show count)
    if low_impact:
        content += "### Low Impact Changes (1-3 files)\n\n"
        content += f"**{len(low_impact)} low-impact changes** affecting 1-3 files each.\n\n"
        content += "<details>\n<summary>Click to expand low-impact changes</summary>\n\n"
        for result in sorted(low_impact, key=lambda r: -r.suggestion.confidence)[
            :MAX_LOW_IMPACT_ITEMS
        ]:
            s = result.suggestion
            ia = s.impact_analysis
            content += f"- `{s.original_name}` → `{s.suggested_name}` ({s.symbol_kind}, {ia.affected_file_count} files, {s.confidence:.0%})\n"
        if len(low_impact) > MAX_LOW_IMPACT_ITEMS:
            content += f"\n*... and {len(low_impact) - MAX_LOW_IMPACT_ITEMS} more*\n"
        content += "\n</details>\n\n"

    return content


def _format_impact_item(result: ValidationResult, show_details: bool = True) -> str:
    """Format a single impact analysis item.

    Args:
        result: ValidationResult with impact analysis
        show_details: Whether to show detailed file-level references

    Returns:
        Formatted markdown string
    """
    s = result.suggestion
    ia = s.impact_analysis

    # Get file name from location if available
    location_file = "Unknown"
    if s.location:
        location_file = (
            Path(s.location["file"]).name if isinstance(s.location.get("file"), str) else "Unknown"
        )
        location_line = s.location.get("line", "?")
        location_str = f"{location_file}:{location_line}"
    else:
        location_str = "Unknown location"

    content = f"#### `{s.original_name}` → `{s.suggested_name}`\n\n"
    content += f"- **Kind**: {s.symbol_kind} | **Confidence**: {s.confidence:.0%} | **Location**: {location_str}\n"
    content += f"- **Impact**: {ia.affected_file_count} files, {ia.total_references} references\n"

    if show_details and ia.references_by_file:
        content += "- **Affected Files**:\n"

        # Sort files by number of references (descending)
        sorted_files = sorted(ia.references_by_file.items(), key=lambda x: len(x[1]), reverse=True)

        for file_path, refs in sorted_files[:MAX_FILES_PER_ITEM]:
            file_name = Path(file_path).name
            ref_count = len(refs)
            content += (
                f"  - **{file_name}** ({ref_count} reference{'s' if ref_count > 1 else ''}):\n"
            )

            # Show up to MAX_REFS_PER_FILE references per file
            for ref in refs[:MAX_REFS_PER_FILE]:
                line = ref.get("line", "?")
                snippet = ref.get("code_snippet", "").strip()
                if len(snippet) > MAX_SNIPPET_LENGTH:
                    snippet = snippet[: MAX_SNIPPET_LENGTH - 3] + "..."
                content += f"    - Line {line}: `{snippet}`\n"

            if len(refs) > 3:
                content += f"    - *... and {len(refs) - 3} more*\n"

        if len(sorted_files) > 6:
            content += f"  - *... and {len(sorted_files) - 6} more files*\n"
    else:
        # Just list affected file names
        content += "- **Affected Files**: "
        file_names = [Path(f).name for f in ia.affected_files[:5]]
        content += ", ".join(file_names)
        if len(ia.affected_files) > 5:
            content += f", ... and {len(ia.affected_files) - 5} more"
        content += "\n"

    content += "\n"
    return content


def export_markdown_string(
    results: list[ValidationResult],
    symbols: list[Symbol],
    project_path: Path,
    model: str = "gpt-4o",
) -> str:
    """Export analysis results to Markdown string.

    Args:
        results: List of validation results
        symbols: List of analyzed symbols
        project_path: Path to the analyzed project
        model: LLM model used

    Returns:
        Markdown string
    """
    return _build_markdown_content(results, symbols, project_path, model)
