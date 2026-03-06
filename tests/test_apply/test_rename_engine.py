"""Tests for rename engine."""

import shutil
from pathlib import Path

import pytest

from named.apply.models import ApplyResult, ReplacementSite
from named.apply.rename_engine import (
    _replace_at_column,
    _replace_word_boundary,
    apply_renames,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "apply"


class TestReplaceAtColumn:
    def test_replace_simple(self):
        line = "    return s;"
        result = _replace_at_column(line, 12, "s", "status")
        assert result == "    return status;"

    def test_replace_mismatch_returns_none(self):
        line = "    return x;"
        result = _replace_at_column(line, 12, "s", "status")
        assert result is None

    def test_replace_at_start(self):
        line = "s = getValue();"
        result = _replace_at_column(line, 1, "s", "status")
        assert result == "status = getValue();"

    def test_replace_preserves_rest_of_line(self):
        line = "    repo.save(a);"
        result = _replace_at_column(line, 10, "save", "saveAccount")
        assert result == "    repo.saveAccount(a);"

    def test_replace_method_call(self):
        line = "        var accounts = repo.findAll();"
        result = _replace_at_column(line, 29, "findAll", "findAllAccounts")
        assert result == "        var accounts = repo.findAllAccounts();"

    def test_column_out_of_range(self):
        line = "short"
        result = _replace_at_column(line, 100, "s", "status")
        assert result is None

    def test_negative_column(self):
        line = "test"
        result = _replace_at_column(line, 0, "t", "x")
        assert result is None


class TestReplaceWordBoundary:
    def test_replace_single_char_identifier(self):
        line = "    void updateStatus(Account a, String s);"
        result, count = _replace_word_boundary(line, "s", "status")
        assert count == 1
        assert "String status)" in result
        # Should NOT match 's' in 'updateStatus' or 'String'
        assert "updateStatus" in result
        assert "String" in result

    def test_no_false_positives(self):
        line = "    String substring = getStatus();"
        result, count = _replace_word_boundary(line, "s", "status")
        assert count == 0

    def test_replace_method_name(self):
        line = "    List<Account> findAll();"
        result, count = _replace_word_boundary(line, "findAll", "findAllAccounts")
        assert count == 1
        assert "findAllAccounts" in result

    def test_multiple_matches_returns_count(self):
        line = "    int a = a + a;"
        result, count = _replace_word_boundary(line, "a", "value")
        # Multiple matches - should not replace
        assert count == 3
        assert "value" not in result  # Line should be unchanged

    def test_no_match(self):
        line = "    int counter = 0;"
        result, count = _replace_word_boundary(line, "xyz", "abc")
        assert count == 0
        assert result == line


class TestApplyRenames:
    def _copy_fixtures(self, tmp_path):
        """Copy fixture Java files to temp dir for modification."""
        for name in ["SampleTarget.java", "SampleReference.java"]:
            shutil.copy2(FIXTURES_DIR / name, tmp_path / name)

    def test_single_file_single_rename(self, tmp_path):
        self._copy_fixtures(tmp_path)
        target = tmp_path / "SampleTarget.java"

        sites = [
            ReplacementSite(
                file=target,
                line=6,
                column=None,
                original_name="findAll",
                new_name="findAllAccounts",
                site_type="declaration",
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.applied) == 1
        assert len(result.files_modified) == 1

        content = target.read_text()
        assert "findAllAccounts" in content
        assert "findAll()" not in content  # Original should be gone

    def test_declaration_and_reference(self, tmp_path):
        self._copy_fixtures(tmp_path)
        target = tmp_path / "SampleTarget.java"
        reference = tmp_path / "SampleReference.java"

        sites = [
            ReplacementSite(
                file=target,
                line=6,
                column=None,
                original_name="findAll",
                new_name="findAllAccounts",
                site_type="declaration",
            ),
            ReplacementSite(
                file=reference,
                line=9,
                column=29,
                original_name="findAll",
                new_name="findAllAccounts",
                site_type="reference",
                code_snippet="        var accounts = repo.findAll();",
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.applied) == 2
        assert len(result.files_modified) == 2

        target_content = target.read_text()
        ref_content = reference.read_text()
        assert "findAllAccounts" in target_content
        assert "findAllAccounts" in ref_content

    def test_same_line_multiple_renames(self, tmp_path):
        """Test renaming two identifiers on the same line."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("    void updateStatus(Account a, String s);\n")

        sites = [
            ReplacementSite(
                file=java_file,
                line=1,
                column=41,
                original_name="s",
                new_name="status",
                site_type="reference",
            ),
            ReplacementSite(
                file=java_file,
                line=1,
                column=31,
                original_name="a",
                new_name="account",
                site_type="reference",
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.applied) == 2

        content = java_file.read_text()
        assert "account" in content
        assert "status" in content

    def test_dry_run_does_not_modify(self, tmp_path):
        self._copy_fixtures(tmp_path)
        target = tmp_path / "SampleTarget.java"
        original_content = target.read_text()

        sites = [
            ReplacementSite(
                file=target,
                line=6,
                column=None,
                original_name="findAll",
                new_name="findAllAccounts",
                site_type="declaration",
            ),
        ]

        result = apply_renames(sites, dry_run=True, backup=False)
        assert len(result.files_modified) == 0  # No files modified

        # File content should be unchanged
        assert target.read_text() == original_content

    def test_backup_created(self, tmp_path):
        self._copy_fixtures(tmp_path)
        target = tmp_path / "SampleTarget.java"
        original_content = target.read_text()

        sites = [
            ReplacementSite(
                file=target,
                line=6,
                column=None,
                original_name="findAll",
                new_name="findAllAccounts",
                site_type="declaration",
            ),
        ]

        backup_base = tmp_path / "backups"
        result = apply_renames(sites, dry_run=False, backup=True, backup_base=backup_base)

        assert result.backup_dir is not None
        assert result.backup_dir.exists()
        # Should have a backup file
        backup_files = list(result.backup_dir.rglob("*.java"))
        assert len(backup_files) == 1

    def test_file_not_found_reports_error(self, tmp_path):
        sites = [
            ReplacementSite(
                file=tmp_path / "nonexistent.java",
                line=1,
                column=None,
                original_name="foo",
                new_name="bar",
                site_type="declaration",
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.errors) == 1
        assert "not found" in result.errors[0][1].lower()

    def test_line_out_of_range_skips(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("line1\nline2\n")

        sites = [
            ReplacementSite(
                file=java_file,
                line=999,
                column=None,
                original_name="foo",
                new_name="bar",
                site_type="declaration",
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.skipped) == 1
        assert "out of range" in result.skipped[0][1].lower()

    def test_deduplicates_same_site(self, tmp_path):
        self._copy_fixtures(tmp_path)
        target = tmp_path / "SampleTarget.java"

        # Same site duplicated
        site = ReplacementSite(
            file=target,
            line=6,
            column=None,
            original_name="findAll",
            new_name="findAllAccounts",
            site_type="declaration",
        )

        result = apply_renames([site, site], dry_run=False, backup=False)
        assert len(result.applied) == 1  # Should only apply once

    def test_short_identifier_rename(self, tmp_path):
        """Test renaming single-char identifier 'x' with word boundary."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("            double x = a.getBalance();\n")

        sites = [
            ReplacementSite(
                file=java_file,
                line=1,
                column=None,
                original_name="x",
                new_name="balance",
                site_type="declaration",
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.applied) == 1
        content = java_file.read_text()
        assert "double balance = a.getBalance();" in content
        # Should not affect 'getBalance'
        assert "getBalance" in content


class TestApplyConflictDetection:
    """Tests for apply-engine conflict safety net."""

    def test_conflicting_renames_blocked(self, tmp_path):
        """Two different originals -> same target in same file should block one."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("int data;\nint info;\n")

        sites = [
            ReplacementSite(
                file=java_file,
                line=1,
                column=None,
                original_name="data",
                new_name="details",
                site_type="declaration",
                suggestion_index=0,
            ),
            ReplacementSite(
                file=java_file,
                line=2,
                column=None,
                original_name="info",
                new_name="details",
                site_type="declaration",
                suggestion_index=1,
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.applied) == 1
        assert len(result.skipped) >= 1
        assert "Blocked" in result.skipped[0][1]

    def test_same_target_different_files_no_conflict(self, tmp_path):
        """Same target name in different files is fine."""
        file1 = tmp_path / "Foo.java"
        file2 = tmp_path / "Bar.java"
        file1.write_text("int data;\n")
        file2.write_text("int info;\n")

        sites = [
            ReplacementSite(
                file=file1,
                line=1,
                column=None,
                original_name="data",
                new_name="details",
                site_type="declaration",
                suggestion_index=0,
            ),
            ReplacementSite(
                file=file2,
                line=1,
                column=None,
                original_name="info",
                new_name="details",
                site_type="declaration",
                suggestion_index=1,
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        assert len(result.applied) == 2
        assert len(result.skipped) == 0

    def test_references_of_blocked_rename_also_blocked(self, tmp_path):
        """References tied to a blocked rename should also be blocked."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("int data;\nint info;\nreturn info;\n")

        sites = [
            ReplacementSite(
                file=java_file,
                line=1,
                column=None,
                original_name="data",
                new_name="details",
                site_type="declaration",
                suggestion_index=0,
            ),
            ReplacementSite(
                file=java_file,
                line=2,
                column=None,
                original_name="info",
                new_name="details",
                site_type="declaration",
                suggestion_index=1,
            ),
            ReplacementSite(
                file=java_file,
                line=3,
                column=8,
                original_name="info",
                new_name="details",
                site_type="reference",
                suggestion_index=1,
            ),
        ]

        result = apply_renames(sites, dry_run=False, backup=False)
        # 'data' -> 'details' should apply (declaration)
        # 'info' -> 'details' should be blocked (both declaration and reference)
        assert len(result.applied) == 1
        assert result.applied[0].original_name == "data"
