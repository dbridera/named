"""Tests for report loader."""

import json
from pathlib import Path

import pytest

from named.apply.report_loader import extract_replacement_sites, load_report

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "apply"


class TestLoadReport:
    def test_load_valid_report(self):
        report = load_report(FIXTURES_DIR / "sample_report.json")
        assert "suggestions" in report
        assert "metadata" in report
        assert len(report["suggestions"]) == 4

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_report(Path("/nonexistent/report.json"))

    def test_load_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            load_report(bad_file)

    def test_load_missing_suggestions(self, tmp_path):
        bad_file = tmp_path / "no_suggestions.json"
        bad_file.write_text('{"metadata": {}}')
        with pytest.raises(ValueError, match="suggestions"):
            load_report(bad_file)

    def test_load_missing_metadata(self, tmp_path):
        bad_file = tmp_path / "no_metadata.json"
        bad_file.write_text('{"suggestions": []}')
        with pytest.raises(ValueError, match="metadata"):
            load_report(bad_file)


class TestExtractReplacementSites:
    def test_extracts_valid_suggestions_only(self):
        report = load_report(FIXTURES_DIR / "sample_report.json")
        sites = extract_replacement_sites(report, project_root=FIXTURES_DIR)
        # Should have 3 valid suggestions (the 4th is is_valid=false)
        # findAll: 1 declaration + 1 reference = 2
        # save: 1 declaration + 1 reference = 2
        # x: 1 declaration + 0 references = 1
        assert len(sites) == 5

    def test_filters_by_confidence(self):
        report = load_report(FIXTURES_DIR / "sample_report.json")
        sites = extract_replacement_sites(
            report, project_root=FIXTURES_DIR, min_confidence=0.95
        )
        # Only findAll has confidence >= 0.95
        declaration_sites = [s for s in sites if s.site_type == "declaration"]
        assert len(declaration_sites) == 1
        assert declaration_sites[0].original_name == "findAll"

    def test_declaration_has_no_column(self):
        report = load_report(FIXTURES_DIR / "sample_report.json")
        sites = extract_replacement_sites(report, project_root=FIXTURES_DIR)
        declarations = [s for s in sites if s.site_type == "declaration"]
        for decl in declarations:
            assert decl.column is None

    def test_references_have_columns(self):
        report = load_report(FIXTURES_DIR / "sample_report.json")
        sites = extract_replacement_sites(report, project_root=FIXTURES_DIR)
        references = [s for s in sites if s.site_type == "reference"]
        for ref in references:
            assert ref.column is not None
            assert ref.column > 0

    def test_resolves_file_paths(self):
        report = load_report(FIXTURES_DIR / "sample_report.json")
        sites = extract_replacement_sites(report, project_root=FIXTURES_DIR)
        for site in sites:
            assert site.file.exists(), f"File should exist: {site.file}"

    def test_excludes_blocked_suggestions(self):
        report = {
            "metadata": {"project_path": "."},
            "suggestions": [
                {
                    "is_valid": True,
                    "suggestion": {
                        "original_name": "foo",
                        "suggested_name": "bar",
                        "symbol_kind": "method",
                        "confidence": 0.95,
                        "rationale": "test",
                        "rules_addressed": [],
                        "blocked": True,
                        "blocked_reason": "G1",
                        "references": [],
                        "location": {"file": "test.java", "line": 1},
                    },
                    "blocked_reasons": ["G1"],
                    "rule_violations": [],
                }
            ],
        }
        sites = extract_replacement_sites(report, project_root=FIXTURES_DIR)
        assert len(sites) == 0

    def test_excludes_same_name_suggestions(self):
        report = {
            "metadata": {"project_path": "."},
            "suggestions": [
                {
                    "is_valid": True,
                    "suggestion": {
                        "original_name": "foo",
                        "suggested_name": "foo",
                        "symbol_kind": "method",
                        "confidence": 0.95,
                        "rationale": "test",
                        "rules_addressed": [],
                        "blocked": False,
                        "blocked_reason": None,
                        "references": [],
                        "location": {"file": "test.java", "line": 1},
                    },
                    "blocked_reasons": [],
                    "rule_violations": [],
                }
            ],
        }
        sites = extract_replacement_sites(report, project_root=FIXTURES_DIR)
        assert len(sites) == 0
