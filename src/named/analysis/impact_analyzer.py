"""Impact analysis module for rename operations.

This module provides functionality to analyze the impact of renaming symbols,
including which files are affected and the risk level of the change.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from named.analysis.reference_finder import SymbolReference

# Risk level type for type safety
RiskLevel = Literal["low", "medium", "high"]

# Risk threshold configuration
# These thresholds determine how file count maps to risk levels
MEDIUM_RISK_MIN_FILES = 4  # 4-10 files = medium risk (module-level change)
HIGH_RISK_MIN_FILES = 11  # 11+ files = high risk (cross-cutting concern)


@dataclass
class RenameImpact:
    """Aggregated impact analysis for a rename operation.

    This class encapsulates the results of analyzing how a symbol rename
    will impact a codebase. It includes reference counts, file locations,
    and a risk assessment.

    Attributes:
        total_references: Total number of references to the symbol across all files
        affected_files: List of file paths that contain references to the symbol
        affected_file_count: Number of unique files affected (len of affected_files)
        references_by_file: Dictionary mapping file paths to lists of reference details.
            Each reference dict contains: line, column, code_snippet, usage_type
        risk_level: Assessment of rename risk based on affected file count:
            - "low": 1-3 files (localized change)
            - "medium": 4-10 files (module-level change)
            - "high": 11+ files (cross-cutting concern)

    Example:
        >>> impact = RenameImpact(
        ...     total_references=5,
        ...     affected_files=["Foo.java", "Bar.java"],
        ...     affected_file_count=2,
        ...     references_by_file={"Foo.java": [...], "Bar.java": [...]},
        ...     risk_level="low"
        ... )
        >>> impact.to_dict()  # Serialize for JSON export
    """

    total_references: int
    affected_files: list[str]
    affected_file_count: int
    references_by_file: dict[str, list[dict]]
    risk_level: RiskLevel

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all impact data, suitable for JSON export.
            Keys match the attribute names for consistency.
        """
        return {
            "total_references": self.total_references,
            "affected_file_count": self.affected_file_count,
            "affected_files": self.affected_files,
            "risk_level": self.risk_level,
            "references_by_file": self.references_by_file,
        }


def calculate_risk_level(file_count: int) -> RiskLevel:
    """Calculate risk level based on affected file count.

    Risk levels are determined by module-level constants:
    - low: 1-3 files affected (localized change)
    - medium: 4-10 files affected (module-level change)
    - high: 11+ files affected (cross-cutting concern)

    The thresholds can be adjusted via MEDIUM_RISK_MIN_FILES and HIGH_RISK_MIN_FILES
    constants at the top of this module.

    Args:
        file_count: Number of files affected by the rename

    Returns:
        Risk level: "low", "medium", or "high"
    """
    if file_count >= HIGH_RISK_MIN_FILES:
        return "high"
    elif file_count >= MEDIUM_RISK_MIN_FILES:
        return "medium"
    else:
        return "low"


def aggregate_references_by_file(
    references: list["SymbolReference"],
) -> dict[str, list[dict]]:
    """Group references by file path.

    Uses defaultdict for more efficient grouping without manual key checks.

    Args:
        references: List of SymbolReference objects

    Returns:
        Dictionary mapping file paths to lists of reference dictionaries
    """
    by_file: dict[str, list[dict]] = defaultdict(list)

    for ref in references:
        file_path = str(ref.file)

        # Convert reference to dict for serialization
        ref_dict = {
            "line": ref.line,
            "column": ref.column,
            "code_snippet": ref.code_snippet,
            "usage_type": ref.usage_type,  # Already a string from Literal
        }
        by_file[file_path].append(ref_dict)

    return dict(by_file)  # Convert back to regular dict for serialization


def compute_rename_impact(references: list["SymbolReference"]) -> RenameImpact:
    """Compute the impact of renaming a symbol.

    Analyzes all references to a symbol and produces an impact analysis
    showing which files are affected, how many references per file,
    and the overall risk level of the rename operation.

    Args:
        references: List of SymbolReference objects showing where the symbol is used

    Returns:
        RenameImpact object with aggregated impact data
    """
    if not references:
        return RenameImpact(
            total_references=0,
            affected_files=[],
            affected_file_count=0,
            references_by_file={},
            risk_level="low",
        )

    # Aggregate references by file
    references_by_file = aggregate_references_by_file(references)

    # Extract unique file paths
    affected_files = list(references_by_file.keys())

    # Calculate risk level based on file count
    file_count = len(affected_files)
    risk_level = calculate_risk_level(file_count)

    return RenameImpact(
        total_references=len(references),
        affected_files=affected_files,
        affected_file_count=file_count,
        references_by_file=references_by_file,
        risk_level=risk_level,
    )
