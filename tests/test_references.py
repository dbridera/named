"""Tests for reference finder enhancements."""

import tempfile
from pathlib import Path

from named.analysis.reference_finder import (
    SymbolReference,
    _find_import_references,
    _find_text_references,
    _get_exclusion_zones,
    _is_in_exclusion_zone,
)


class TestImportReferences:
    def test_import_reference_found(self):
        lines = [
            "package com.example;",
            "",
            "import com.bank.Account;",
            "import com.bank.Transaction;",
            "",
            "public class Service {}",
        ]
        refs = _find_import_references("Account", Path("Service.java"), lines)
        assert len(refs) == 1
        assert refs[0].line == 3
        assert refs[0].usage_type == "import"

    def test_import_column_points_to_class_name(self):
        lines = ["import com.bank.Account;"]
        refs = _find_import_references("Account", Path("Test.java"), lines)
        assert len(refs) == 1
        # Column should point to 'Account' not 'import'
        col_0based = refs[0].column - 1
        assert lines[0][col_0based : col_0based + 7] == "Account"

    def test_wildcard_import_not_matched(self):
        lines = ["import com.bank.*;"]
        refs = _find_import_references("Account", Path("Test.java"), lines)
        assert len(refs) == 0

    def test_different_class_not_matched(self):
        lines = ["import com.bank.Transaction;"]
        refs = _find_import_references("Account", Path("Test.java"), lines)
        assert len(refs) == 0

    def test_static_import_matched(self):
        lines = ["import static com.bank.Account;"]
        refs = _find_import_references("Account", Path("Test.java"), lines)
        assert len(refs) == 1

    def test_partial_name_not_matched(self):
        """AccountHelper should not match 'Account'."""
        lines = ["import com.bank.AccountHelper;"]
        refs = _find_import_references("Account", Path("Test.java"), lines)
        assert len(refs) == 0


class TestExclusionZones:
    def test_string_literal_zone(self):
        line = '    System.out.println("balance is zero");'
        zones = _get_exclusion_zones(line)
        assert len(zones) == 1
        # The string "balance is zero" should be a zone
        assert _is_in_exclusion_zone(line.index("balance"), zones)

    def test_line_comment_zone(self):
        line = "    int x = 5; // balance check"
        zones = _get_exclusion_zones(line)
        assert len(zones) == 1
        assert _is_in_exclusion_zone(line.index("balance"), zones)

    def test_code_not_in_zone(self):
        line = '    int balance = 0; // comment'
        zones = _get_exclusion_zones(line)
        code_pos = line.index("balance")
        assert not _is_in_exclusion_zone(code_pos, zones)

    def test_escaped_quote_handled(self):
        line = r'    String s = "say \"hello\"";'
        zones = _get_exclusion_zones(line)
        assert len(zones) == 1

    def test_char_literal_zone(self):
        line = "    char c = 'x';"
        zones = _get_exclusion_zones(line)
        assert len(zones) == 1

    def test_no_zones_in_plain_code(self):
        line = "    int balance = getBalance();"
        zones = _get_exclusion_zones(line)
        assert len(zones) == 0


class TestTextReferencesWithExclusion:
    def test_not_in_string_literal(self):
        lines = [
            '    System.out.println("balance is: " + balance);',
        ]
        refs = _find_text_references("balance", Path("Test.java"), lines, [])
        # Should find the code 'balance' but NOT the one in the string
        assert len(refs) == 1
        # The match should be the code reference, not the string one
        assert refs[0].column > 40  # After the string literal

    def test_not_in_comment(self):
        lines = [
            "    // Update the balance field",
            "    this.balance = newValue;",
        ]
        refs = _find_text_references("balance", Path("Test.java"), lines, [])
        # Should find only the code reference on line 2
        assert len(refs) == 1
        assert refs[0].line == 2

    def test_code_reference_still_found(self):
        lines = [
            "    double balance = this.balance;",
        ]
        refs = _find_text_references("balance", Path("Test.java"), lines, [])
        assert len(refs) == 2  # declaration + this.balance
