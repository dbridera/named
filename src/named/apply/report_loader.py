"""Load and parse Named report JSON into replacement sites."""

import json
from pathlib import Path

from named.apply.models import ReplacementSite
from named.logging import get_logger

logger = get_logger("report_loader")


def load_report(report_path: Path) -> dict:
    """Load and validate a Named report JSON.

    Args:
        report_path: Path to the report JSON file.

    Returns:
        Parsed report dictionary.

    Raises:
        FileNotFoundError: If report file does not exist.
        json.JSONDecodeError: If report is not valid JSON.
        ValueError: If report is missing required fields.
    """
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    if "suggestions" not in report:
        raise ValueError("Report JSON missing 'suggestions' field")
    if "metadata" not in report:
        raise ValueError("Report JSON missing 'metadata' field")

    return report


def extract_replacement_sites(
    report: dict,
    project_root: Path | None = None,
    min_confidence: float = 0.80,
) -> list[ReplacementSite]:
    """Extract all replacement sites from a report.

    For each valid suggestion, creates one ReplacementSite for the
    declaration and one for each reference location.

    Args:
        report: Parsed report dictionary.
        project_root: Root directory for resolving relative file paths.
            If None, uses metadata.project_path parent or current dir.
        min_confidence: Minimum confidence threshold to include.

    Returns:
        List of ReplacementSite objects.
    """
    if project_root is None:
        project_path = report.get("metadata", {}).get("project_path", ".")
        project_root = Path(project_path)
        # If project_path is absolute and points to a subdirectory,
        # we need the workspace root (parent of relative paths in report)
        # The report paths are relative to the workspace root, not project_path
        # Check if any suggestion file path starts with a common prefix
        if not project_root.exists():
            project_root = Path(".")

    sites: list[ReplacementSite] = []

    for idx, entry in enumerate(report.get("suggestions", [])):
        suggestion = entry.get("suggestion", {})

        # Filter: only valid, non-blocked suggestions above confidence threshold
        if not entry.get("is_valid", False):
            continue
        if suggestion.get("blocked", False):
            continue
        if suggestion.get("confidence", 0) < min_confidence:
            continue

        original_name = suggestion.get("original_name", "")
        suggested_name = suggestion.get("suggested_name", "")

        if not original_name or not suggested_name:
            continue
        if original_name == suggested_name:
            continue

        location = suggestion.get("location", {})
        if not location:
            continue

        # Create declaration site
        decl_file = _resolve_path(location.get("file", ""), project_root)
        decl_line = location.get("line", 0)

        if decl_file and decl_line > 0:
            sites.append(
                ReplacementSite(
                    file=decl_file,
                    line=decl_line,
                    column=None,  # Declarations don't have column in the report
                    original_name=original_name,
                    new_name=suggested_name,
                    site_type="declaration",
                    suggestion_index=idx,
                )
            )

        # Create reference sites
        for ref in suggestion.get("references", []):
            ref_file = _resolve_path(ref.get("file", ""), project_root)
            ref_line = ref.get("line", 0)
            ref_column = ref.get("column")

            if ref_file and ref_line > 0:
                sites.append(
                    ReplacementSite(
                        file=ref_file,
                        line=ref_line,
                        column=ref_column,
                        original_name=original_name,
                        new_name=suggested_name,
                        site_type="reference",
                        usage_type=ref.get("usage_type"),
                        code_snippet=ref.get("code_snippet", ""),
                        suggestion_index=idx,
                    )
                )

    return sites


def _resolve_path(file_path_str: str, project_root: Path) -> Path | None:
    """Resolve a file path from the report to an absolute path.

    Tries multiple strategies:
    1. If already absolute and exists, use as-is
    2. Resolve relative to project_root
    3. Resolve relative to current working directory
    """
    if not file_path_str:
        return None

    path = Path(file_path_str)

    # If absolute and exists, use it
    if path.is_absolute() and path.exists():
        return path

    # Try relative to project_root
    resolved = project_root / path
    if resolved.exists():
        return resolved

    # Try relative to CWD
    cwd_resolved = Path.cwd() / path
    if cwd_resolved.exists():
        return cwd_resolved

    logger.warning(f"Could not resolve file path: {file_path_str}")
    return None
