"""Core rename engine - applies identifier replacements to Java source files."""

import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from named.apply.models import ApplyResult, FileChange, ReplacementSite
from named.logging import get_logger

logger = get_logger("rename_engine")


def apply_renames(
    sites: list[ReplacementSite],
    dry_run: bool = False,
    backup: bool = True,
    backup_base: Path | None = None,
) -> ApplyResult:
    """Apply all renames to source files.

    Groups sites by file, processes each file with replacements
    ordered bottom-right to top-left to preserve coordinates.

    Args:
        sites: List of replacement sites to apply.
        dry_run: If True, compute changes but don't write files.
        backup: If True, create backups before modifying.
        backup_base: Base directory for backups. Defaults to .named-backup/.

    Returns:
        ApplyResult with details of what was applied/skipped/errored.
    """
    result = ApplyResult()

    # Pre-apply conflict detection (safety net)
    sites, conflicts = _detect_apply_conflicts(sites)
    for site, reason in conflicts:
        result.skipped.append((site, reason))
    if conflicts:
        logger.warning(f"Blocked {len(conflicts)} conflicting replacement sites")

    # Group by file
    sites_by_file: dict[Path, list[ReplacementSite]] = defaultdict(list)
    for site in sites:
        sites_by_file[site.file].append(site)

    # Create backup directory if needed
    if backup and not dry_run:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup_dir = (backup_base or Path(".named-backup")) / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        result.backup_dir = backup_dir

    # Process each file
    for file_path, file_sites in sites_by_file.items():
        change = _process_file(file_path, file_sites, result)

        if change and change.modified_content is not None:
            if not dry_run:
                # Create backup
                if backup and result.backup_dir:
                    _backup_file(file_path, result.backup_dir)

                # Write modified content
                file_path.write_text(change.modified_content, encoding="utf-8")
                result.files_modified.append(file_path)
                logger.info(f"Modified: {file_path}")

    return result


def _process_file(
    file_path: Path,
    sites: list[ReplacementSite],
    result: ApplyResult,
) -> FileChange | None:
    """Process all replacement sites for a single file.

    Args:
        file_path: Path to the file to modify.
        sites: List of sites in this file.
        result: ApplyResult to accumulate results into.

    Returns:
        FileChange with original and modified content, or None on error.
    """
    if not file_path.exists():
        for site in sites:
            result.errors.append((site, f"File not found: {file_path}"))
        return None

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        for site in sites:
            result.errors.append((site, f"Failed to read file: {e}"))
        return None

    lines = content.split("\n")
    change = FileChange(file=file_path, original_content=content)

    # Deduplicate sites: same file+line+column+original_name should only appear once
    seen = set()
    unique_sites = []
    for site in sites:
        key = (site.line, site.column, site.original_name, site.new_name)
        if key not in seen:
            seen.add(key)
            unique_sites.append(site)

    # Sort: by line DESC, then column DESC (process bottom-right first)
    sorted_sites = sorted(
        unique_sites,
        key=lambda s: (s.line, s.column or 0),
        reverse=True,
    )

    modified = False
    for site in sorted_sites:
        line_idx = site.line - 1  # Convert to 0-based

        if line_idx < 0 or line_idx >= len(lines):
            result.skipped.append((site, f"Line {site.line} out of range (file has {len(lines)} lines)"))
            continue

        current_line = lines[line_idx]

        if site.column is not None:
            # Column-precise replacement for references
            new_line = _replace_at_column(current_line, site.column, site.original_name, site.new_name)
            if new_line is None:
                result.skipped.append(
                    (site, f"Name '{site.original_name}' not found at column {site.column} on line {site.line}")
                )
                continue
        else:
            # Word-boundary replacement for declarations
            new_line, count = _replace_word_boundary(current_line, site.original_name, site.new_name)
            if count == 0:
                result.skipped.append(
                    (site, f"Name '{site.original_name}' not found on line {site.line}")
                )
                continue
            if count > 1:
                result.skipped.append(
                    (site, f"Ambiguous: '{site.original_name}' found {count} times on line {site.line}")
                )
                continue

        lines[line_idx] = new_line
        result.applied.append(site)
        modified = True

    if modified:
        change.modified_content = "\n".join(lines)

    return change


def _replace_at_column(line: str, column: int, old: str, new: str) -> str | None:
    """Replace old with new at exact column position (1-based).

    Returns the modified line, or None if the text at that column
    does not match old.
    """
    idx = column - 1  # Convert to 0-based
    if idx < 0 or idx + len(old) > len(line):
        return None
    if line[idx : idx + len(old)] != old:
        return None
    return line[:idx] + new + line[idx + len(old) :]


def _replace_word_boundary(line: str, old: str, new: str) -> tuple[str, int]:
    """Replace old with new using word boundary matching.

    Returns (modified_line, replacement_count).
    Only replaces if exactly one match is found.
    """
    pattern = r"\b" + re.escape(old) + r"\b"
    matches = list(re.finditer(pattern, line))
    count = len(matches)

    if count == 1:
        result = re.sub(pattern, new, line, count=1)
        return result, 1

    return line, count


def _detect_apply_conflicts(
    sites: list[ReplacementSite],
) -> tuple[list[ReplacementSite], list[tuple[ReplacementSite, str]]]:
    """Detect conflicting renames: different originals -> same new_name in same file.

    Args:
        sites: All replacement sites to apply.

    Returns:
        (safe_sites, conflicts) - sites safe to apply and blocked conflicts.
    """
    # Group declaration sites by (file, new_name)
    declarations_by_target: dict[tuple[Path, str], list[ReplacementSite]] = defaultdict(list)

    for site in sites:
        if site.site_type == "declaration":
            declarations_by_target[(site.file, site.new_name)].append(site)

    # Find conflicting original_names for the same target
    blocked_keys: set[tuple[Path, str]] = set()  # (file, original_name) to block
    for (file_path, new_name), decl_sites in declarations_by_target.items():
        unique_originals = {s.original_name for s in decl_sites}
        if len(unique_originals) > 1:
            sorted_sites = sorted(decl_sites, key=lambda s: s.suggestion_index)
            for s in sorted_sites[1:]:
                blocked_keys.add((s.file, s.original_name))
                logger.warning(
                    f"Conflict: '{s.original_name}' -> '{new_name}' in "
                    f"{file_path.name} conflicts with "
                    f"'{sorted_sites[0].original_name}' -> '{new_name}'"
                )

    safe = []
    conflicts = []
    for site in sites:
        if (site.file, site.original_name) in blocked_keys:
            conflicts.append((
                site,
                f"Blocked: '{site.original_name}' -> '{site.new_name}' conflicts "
                f"with another rename to '{site.new_name}' in {site.file.name}",
            ))
        else:
            safe.append(site)

    return safe, conflicts


def _backup_file(file_path: Path, backup_dir: Path) -> None:
    """Create a backup of a file, preserving directory structure."""
    try:
        # Use relative path from CWD for backup structure
        try:
            rel_path = file_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = file_path.name

        backup_path = backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backup created: {backup_path}")
    except Exception as e:
        logger.warning(f"Failed to create backup for {file_path}: {e}")


def get_file_diff(change: FileChange) -> str:
    """Generate a unified diff-like string for a file change.

    Args:
        change: FileChange with original and modified content.

    Returns:
        Formatted diff string.
    """
    if not change.modified_content:
        return ""

    original_lines = change.original_content.split("\n")
    modified_lines = change.modified_content.split("\n")
    diff_parts = []

    for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
        if orig != mod:
            line_num = i + 1
            diff_parts.append(f"@@ line {line_num} @@")
            diff_parts.append(f"- {orig}")
            diff_parts.append(f"+ {mod}")

    return "\n".join(diff_parts)
