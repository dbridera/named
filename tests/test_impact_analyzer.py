"""Tests for impact analysis functionality."""

from pathlib import Path

from named.analysis.impact_analyzer import (
    RenameImpact,
    aggregate_references_by_file,
    calculate_risk_level,
    compute_rename_impact,
)
from named.analysis.reference_finder import SymbolReference


def test_calculate_risk_level_low():
    """Test risk level calculation for low risk (1-3 files)."""
    assert calculate_risk_level(1) == "low"
    assert calculate_risk_level(2) == "low"
    assert calculate_risk_level(3) == "low"


def test_calculate_risk_level_medium():
    """Test risk level calculation for medium risk (4-10 files)."""
    assert calculate_risk_level(4) == "medium"
    assert calculate_risk_level(7) == "medium"
    assert calculate_risk_level(10) == "medium"


def test_calculate_risk_level_high():
    """Test risk level calculation for high risk (11+ files)."""
    assert calculate_risk_level(11) == "high"
    assert calculate_risk_level(15) == "high"
    assert calculate_risk_level(100) == "high"


def test_aggregate_references_by_file_empty():
    """Test aggregating empty references list."""
    result = aggregate_references_by_file([])
    assert result == {}


def test_aggregate_references_by_file_single_file():
    """Test aggregating references from a single file."""
    refs = [
        SymbolReference(
            file=Path("Service.java"),
            line=10,
            column=5,
            code_snippet="doSomething()",
            usage_type="call",
        ),
        SymbolReference(
            file=Path("Service.java"),
            line=25,
            column=10,
            code_snippet="this.doSomething()",
            usage_type="call",
        ),
    ]

    result = aggregate_references_by_file(refs)

    assert len(result) == 1
    assert "Service.java" in result
    assert len(result["Service.java"]) == 2
    assert result["Service.java"][0]["line"] == 10
    assert result["Service.java"][1]["line"] == 25


def test_aggregate_references_by_file_multiple_files():
    """Test aggregating references from multiple files."""
    refs = [
        SymbolReference(
            file=Path("ServiceA.java"),
            line=10,
            column=5,
            code_snippet="method()",
            usage_type="call",
        ),
        SymbolReference(
            file=Path("ServiceB.java"),
            line=20,
            column=8,
            code_snippet="method()",
            usage_type="call",
        ),
        SymbolReference(
            file=Path("ServiceA.java"),
            line=30,
            column=5,
            code_snippet="method()",
            usage_type="call",
        ),
    ]

    result = aggregate_references_by_file(refs)

    assert len(result) == 2
    assert len(result["ServiceA.java"]) == 2
    assert len(result["ServiceB.java"]) == 1


def test_compute_rename_impact_empty_references():
    """Test computing impact with no references."""
    result = compute_rename_impact([])

    assert result.total_references == 0
    assert result.affected_file_count == 0
    assert result.affected_files == []
    assert result.references_by_file == {}
    assert result.risk_level == "low"


def test_compute_rename_impact_single_file():
    """Test computing impact with references in a single file."""
    refs = [
        SymbolReference(
            file=Path("Service.java"),
            line=10,
            column=5,
            code_snippet="findById(id)",
            usage_type="call",
        ),
        SymbolReference(
            file=Path("Service.java"),
            line=25,
            column=10,
            code_snippet="findById(customerId)",
            usage_type="call",
        ),
    ]

    result = compute_rename_impact(refs)

    assert result.total_references == 2
    assert result.affected_file_count == 1
    assert len(result.affected_files) == 1
    assert "Service.java" in result.affected_files
    assert result.risk_level == "low"
    assert len(result.references_by_file) == 1
    assert len(result.references_by_file["Service.java"]) == 2


def test_compute_rename_impact_multiple_files_low_risk():
    """Test computing impact with low risk (3 files)."""
    refs = [
        SymbolReference(Path("ServiceA.java"), 10, 5, "method()", "call"),
        SymbolReference(Path("ServiceB.java"), 20, 8, "method()", "call"),
        SymbolReference(Path("ServiceC.java"), 30, 12, "method()", "call"),
    ]

    result = compute_rename_impact(refs)

    assert result.total_references == 3
    assert result.affected_file_count == 3
    assert result.risk_level == "low"
    assert set(result.affected_files) == {"ServiceA.java", "ServiceB.java", "ServiceC.java"}


def test_compute_rename_impact_multiple_files_medium_risk():
    """Test computing impact with medium risk (5 files)."""
    refs = [
        SymbolReference(Path(f"Service{i}.java"), i * 10, 5, "method()", "call") for i in range(5)
    ]

    result = compute_rename_impact(refs)

    assert result.total_references == 5
    assert result.affected_file_count == 5
    assert result.risk_level == "medium"


def test_compute_rename_impact_multiple_files_high_risk():
    """Test computing impact with high risk (12 files)."""
    refs = [
        SymbolReference(Path(f"Service{i}.java"), i * 10, 5, "method()", "call") for i in range(12)
    ]

    result = compute_rename_impact(refs)

    assert result.total_references == 12
    assert result.affected_file_count == 12
    assert result.risk_level == "high"


def test_rename_impact_to_dict():
    """Test RenameImpact to_dict() serialization."""
    impact = RenameImpact(
        total_references=5,
        affected_files=["FileA.java", "FileB.java"],
        affected_file_count=2,
        references_by_file={
            "FileA.java": [
                {"line": 10, "column": 5, "code_snippet": "test()", "usage_type": "call"}
            ],
            "FileB.java": [
                {"line": 20, "column": 8, "code_snippet": "test()", "usage_type": "call"}
            ],
        },
        risk_level="low",
    )

    result = impact.to_dict()

    assert result["total_references"] == 5
    assert result["affected_file_count"] == 2
    assert result["risk_level"] == "low"
    assert "FileA.java" in result["references_by_file"]
    assert "FileB.java" in result["references_by_file"]


def test_compute_rename_impact_same_file_multiple_references():
    """Test impact when same file has many references."""
    refs = [
        SymbolReference(Path("Service.java"), 10 + i * 5, 5, "method()", "call") for i in range(10)
    ]

    result = compute_rename_impact(refs)

    assert result.total_references == 10
    assert result.affected_file_count == 1
    assert result.risk_level == "low"
    assert len(result.references_by_file["Service.java"]) == 10
