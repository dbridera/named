"""Tests for type hierarchy analysis."""

from pathlib import Path

from named.analysis.extractor import extract_symbols
from named.analysis.hierarchy import (
    build_type_hierarchy,
    find_override_methods,
    find_subtypes,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "hierarchy"


def _all_symbols():
    """Extract symbols from all hierarchy fixture files."""
    symbols = []
    for java_file in sorted(FIXTURES_DIR.glob("*.java")):
        symbols.extend(extract_symbols(java_file))
    return symbols


class TestBuildTypeHierarchy:
    def test_captures_extends(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        assert "Dog" in type_map
        assert type_map["Dog"].extends == "Animal"

    def test_captures_implements(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        assert "CreditCard" in type_map
        assert "Payable" in type_map["CreditCard"].implements

    def test_captures_transitive_extends(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        assert "Puppy" in type_map
        assert type_map["Puppy"].extends == "Dog"

    def test_methods_attached_to_types(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        animal_methods = [m.name for m in type_map["Animal"].methods]
        assert "process" in animal_methods
        assert "getName" in animal_methods

    def test_interface_has_methods(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        payable_methods = [m.name for m in type_map["Payable"].methods]
        assert "pay" in payable_methods
        assert "getReceipt" in payable_methods


class TestFindSubtypes:
    def test_direct_subtypes(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        subtypes = find_subtypes("Animal", type_map)
        assert "Dog" in subtypes
        assert "Cat" in subtypes

    def test_transitive_subtypes(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        subtypes = find_subtypes("Animal", type_map)
        assert "Puppy" in subtypes  # Dog -> Puppy

    def test_interface_implementors(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        subtypes = find_subtypes("Payable", type_map)
        assert "CreditCard" in subtypes

    def test_no_subtypes(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        subtypes = find_subtypes("Cat", type_map)
        assert len(subtypes) == 0


class TestFindOverrideMethods:
    def test_finds_overrides_in_subclass(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        overrides = find_override_methods("process", ["String"], "Animal", type_map)
        override_classes = [m.parent_class for m in overrides]
        assert "Dog" in override_classes
        assert "Cat" in override_classes

    def test_finds_transitive_overrides(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        overrides = find_override_methods("process", ["String"], "Animal", type_map)
        override_classes = [m.parent_class for m in overrides]
        assert "Puppy" in override_classes

    def test_finds_interface_implementations(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        overrides = find_override_methods("pay", ["double"], "Payable", type_map)
        override_classes = [m.parent_class for m in overrides]
        assert "CreditCard" in override_classes

    def test_no_overrides_for_unique_method(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        overrides = find_override_methods("uniqueMethod", [], "Animal", type_map)
        assert len(overrides) == 0

    def test_different_param_types_not_matched(self):
        symbols = _all_symbols()
        type_map = build_type_hierarchy(symbols)

        # process() takes String, not int
        overrides = find_override_methods("process", ["int"], "Animal", type_map)
        assert len(overrides) == 0
