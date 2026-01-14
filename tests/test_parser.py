"""Tests for the Java parser and symbol extractor."""

from pathlib import Path

import pytest

from named.analysis.extractor import extract_symbols
from named.analysis.parser import find_java_files, parse_java_file

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_FILE = FIXTURES_DIR / "SampleService.java"


class TestJavaParser:
    """Tests for Java file parsing."""

    def test_parse_valid_java_file(self):
        """Should parse a valid Java file."""
        tree = parse_java_file(SAMPLE_FILE)
        assert tree is not None

    def test_parse_nonexistent_file(self):
        """Should raise error for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            parse_java_file(Path("/nonexistent/File.java"))

    def test_find_java_files(self):
        """Should find Java files in directory."""
        files = find_java_files(FIXTURES_DIR)
        assert len(files) >= 1
        assert any(f.name == "SampleService.java" for f in files)


class TestSymbolExtractor:
    """Tests for symbol extraction."""

    def test_extract_symbols_from_sample(self):
        """Should extract symbols from sample file."""
        symbols = extract_symbols(SAMPLE_FILE)
        assert len(symbols) > 0

    def test_extract_classes(self):
        """Should extract class symbols."""
        symbols = extract_symbols(SAMPLE_FILE)
        classes = [s for s in symbols if s.kind == "class"]
        assert len(classes) >= 1

        class_names = [c.name for c in classes]
        assert "SampleService" in class_names

    def test_extract_methods(self):
        """Should extract method symbols."""
        symbols = extract_symbols(SAMPLE_FILE)
        methods = [s for s in symbols if s.kind == "method"]
        assert len(methods) >= 1

    def test_extract_fields(self):
        """Should extract field symbols."""
        symbols = extract_symbols(SAMPLE_FILE)
        fields = [s for s in symbols if s.kind == "field"]
        assert len(fields) >= 1

    def test_extract_annotations(self):
        """Should extract annotations on symbols."""
        symbols = extract_symbols(SAMPLE_FILE)

        # Find the SampleService class which has @Path
        service = next((s for s in symbols if s.name == "SampleService"), None)
        assert service is not None
        assert "Path" in service.annotations

    def test_symbol_has_location(self):
        """Symbols should have location information."""
        symbols = extract_symbols(SAMPLE_FILE)
        for symbol in symbols:
            assert symbol.location is not None
            assert symbol.location.line > 0

    def test_symbol_has_context(self):
        """Symbols should have code context."""
        symbols = extract_symbols(SAMPLE_FILE)
        for symbol in symbols:
            assert symbol.context is not None
