"""Tests for verifier module."""

from pathlib import Path

from named.apply.models import ReplacementSite
from named.apply.verifier import detect_build_system, verify_site


class TestVerifySite:
    def test_valid_column_site(self):
        lines = ["    return s;"]
        site = ReplacementSite(
            file=Path("test.java"),
            line=1,
            column=12,
            original_name="s",
            new_name="status",
            site_type="reference",
            code_snippet="    return s;",
        )
        is_valid, reason = verify_site(site, lines)
        assert is_valid is True

    def test_invalid_column_mismatch(self):
        lines = ["    return x;"]
        site = ReplacementSite(
            file=Path("test.java"),
            line=1,
            column=12,
            original_name="s",
            new_name="status",
            site_type="reference",
        )
        is_valid, reason = verify_site(site, lines)
        assert is_valid is False
        assert "Expected 's'" in reason

    def test_line_out_of_range(self):
        lines = ["line1"]
        site = ReplacementSite(
            file=Path("test.java"),
            line=5,
            column=1,
            original_name="foo",
            new_name="bar",
            site_type="reference",
        )
        is_valid, reason = verify_site(site, lines)
        assert is_valid is False
        assert "out of range" in reason.lower()

    def test_stale_snippet_with_name_present(self):
        """If snippet doesn't match but name is present, still valid."""
        lines = ["    return  s;"]  # Extra space vs snippet
        site = ReplacementSite(
            file=Path("test.java"),
            line=1,
            column=None,
            original_name="s",
            new_name="status",
            site_type="declaration",
            code_snippet="return s;",
        )
        is_valid, reason = verify_site(site, lines)
        assert is_valid is True

    def test_stale_snippet_name_absent(self):
        """If snippet doesn't match and name isn't present, invalid."""
        lines = ["    return value;"]
        site = ReplacementSite(
            file=Path("test.java"),
            line=1,
            column=None,
            original_name="s",
            new_name="status",
            site_type="declaration",
            code_snippet="return s;",
        )
        is_valid, reason = verify_site(site, lines)
        assert is_valid is False
        assert "changed" in reason.lower()

    def test_column_out_of_line_range(self):
        lines = ["short"]
        site = ReplacementSite(
            file=Path("test.java"),
            line=1,
            column=100,
            original_name="foo",
            new_name="bar",
            site_type="reference",
        )
        is_valid, reason = verify_site(site, lines)
        assert is_valid is False
        assert "out of range" in reason.lower()


class TestDetectBuildSystem:
    def test_detect_maven(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project></project>")
        assert detect_build_system(tmp_path) == "maven"

    def test_detect_gradle(self, tmp_path):
        (tmp_path / "build.gradle").write_text("apply plugin: 'java'")
        assert detect_build_system(tmp_path) == "gradle"

    def test_detect_gradle_kts(self, tmp_path):
        (tmp_path / "build.gradle.kts").write_text("plugins { java }")
        assert detect_build_system(tmp_path) == "gradle"

    def test_detect_none(self, tmp_path):
        assert detect_build_system(tmp_path) is None
