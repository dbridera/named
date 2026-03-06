"""Data models for the apply module."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class ReplacementSite:
    """A single location where a rename must be applied."""

    file: Path
    line: int  # 1-based
    column: int | None  # 1-based, None for declarations
    original_name: str
    new_name: str
    site_type: Literal["declaration", "reference"]
    usage_type: str | None = None  # read, write, call, instantiate, type_reference
    code_snippet: str = ""  # Expected line content for verification
    suggestion_index: int = 0  # Index into suggestions list for tracing


@dataclass
class FileChange:
    """Aggregated changes for a single file."""

    file: Path
    replacements: list[ReplacementSite] = field(default_factory=list)
    original_content: str = ""
    modified_content: str | None = None


@dataclass
class ApplyResult:
    """Result of applying renames."""

    applied: list[ReplacementSite] = field(default_factory=list)
    skipped: list[tuple[ReplacementSite, str]] = field(default_factory=list)
    errors: list[tuple[ReplacementSite, str]] = field(default_factory=list)
    files_modified: list[Path] = field(default_factory=list)
    backup_dir: Path | None = None
