"""Find references (usages) of symbols across Java files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import javalang
from javalang.tree import (
    ClassCreator,
    MemberReference,
    MethodInvocation,
    ReferenceType,
)

from named.logging import get_logger

logger = get_logger("reference_finder")

UsageType = Literal["read", "write", "call", "instantiate", "type_reference"]


@dataclass
class SymbolReference:
    """Represents a reference (usage) of a symbol."""

    file: Path
    line: int
    column: int
    code_snippet: str
    usage_type: UsageType

    def __str__(self) -> str:
        return f"{self.file.name}:{self.line} → `{self.code_snippet.strip()}`"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": str(self.file),
            "line": self.line,
            "column": self.column,
            "code_snippet": self.code_snippet.strip(),
            "usage_type": self.usage_type,
        }


def find_references(
    symbol_name: str,
    symbol_kind: str,
    java_files: list[Path],
    parent_class: str | None = None,
) -> list[SymbolReference]:
    """Find all references to a symbol across Java files.

    Args:
        symbol_name: Name of the symbol to find references for
        symbol_kind: Kind of symbol (class, method, field, etc.)
        java_files: List of Java files to search
        parent_class: Optional parent class for methods/fields

    Returns:
        List of SymbolReference objects
    """
    references = []

    for java_file in java_files:
        try:
            file_refs = _find_references_in_file(symbol_name, symbol_kind, java_file, parent_class)
            references.extend(file_refs)
        except Exception as e:
            logger.debug(f"Error searching {java_file}: {e}")

    return references


def _find_references_in_file(
    symbol_name: str,
    symbol_kind: str,
    java_file: Path,
    parent_class: str | None,
) -> list[SymbolReference]:
    """Find references to a symbol in a single file."""
    references = []

    try:
        source_code = java_file.read_text(encoding="utf-8")
        source_lines = source_code.split("\n")
        tree = javalang.parse.parse(source_code)
    except Exception as e:
        logger.debug(f"Failed to parse {java_file}: {e}")
        return references

    # Find references based on symbol kind
    if symbol_kind == "class" or symbol_kind == "interface":
        references.extend(_find_class_references(symbol_name, tree, java_file, source_lines))
    elif symbol_kind == "method":
        references.extend(_find_method_references(symbol_name, tree, java_file, source_lines))
    elif symbol_kind == "field" or symbol_kind == "constant":
        references.extend(_find_field_references(symbol_name, tree, java_file, source_lines))
    elif symbol_kind == "parameter" or symbol_kind == "variable":
        references.extend(_find_variable_references(symbol_name, tree, java_file, source_lines))

    return references


def _find_class_references(
    class_name: str,
    tree: javalang.tree.CompilationUnit,
    java_file: Path,
    source_lines: list[str],
) -> list[SymbolReference]:
    """Find references to a class (instantiations, type references)."""
    references = []

    # Find instantiations: new ClassName()
    for path, node in tree.filter(ClassCreator):
        if hasattr(node, "type") and node.type:
            type_name = node.type.name
            if type_name == class_name:
                ref = _create_reference(node, java_file, source_lines, "instantiate")
                if ref:
                    references.append(ref)

    # Find type references: ClassName variable, List<ClassName>
    for path, node in tree.filter(ReferenceType):
        if hasattr(node, "name") and node.name == class_name:
            ref = _create_reference(node, java_file, source_lines, "type_reference")
            if ref:
                references.append(ref)

    return references


def _find_method_references(
    method_name: str,
    tree: javalang.tree.CompilationUnit,
    java_file: Path,
    source_lines: list[str],
) -> list[SymbolReference]:
    """Find method invocations."""
    references = []

    for path, node in tree.filter(MethodInvocation):
        if hasattr(node, "member") and node.member == method_name:
            ref = _create_reference(node, java_file, source_lines, "call")
            if ref:
                references.append(ref)

    return references


def _find_field_references(
    field_name: str,
    tree: javalang.tree.CompilationUnit,
    java_file: Path,
    source_lines: list[str],
) -> list[SymbolReference]:
    """Find field access references."""
    references = []

    for path, node in tree.filter(MemberReference):
        if hasattr(node, "member") and node.member == field_name:
            # Determine if it's a read or write based on context
            usage_type = _determine_field_usage_type(path)
            ref = _create_reference(node, java_file, source_lines, usage_type)
            if ref:
                references.append(ref)

    return references


def _find_variable_references(
    var_name: str,
    tree: javalang.tree.CompilationUnit,
    java_file: Path,
    source_lines: list[str],
) -> list[SymbolReference]:
    """Find variable references (identifiers)."""
    references = []

    # MemberReference can also be used for local variables
    for path, node in tree.filter(MemberReference):
        if hasattr(node, "member") and node.member == var_name:
            usage_type = _determine_field_usage_type(path)
            ref = _create_reference(node, java_file, source_lines, usage_type)
            if ref:
                references.append(ref)

    return references


def _determine_field_usage_type(path: list) -> UsageType:
    """Determine if a field reference is a read or write.

    This is a simplified heuristic - a proper implementation would
    analyze the full AST context.
    """
    # Check if parent is an assignment
    for node in reversed(path):
        if hasattr(node, "__class__"):
            class_name = node.__class__.__name__
            if "Assignment" in class_name:
                return "write"
    return "read"


def _create_reference(
    node,
    java_file: Path,
    source_lines: list[str],
    usage_type: UsageType,
) -> SymbolReference | None:
    """Create a SymbolReference from an AST node."""
    if not hasattr(node, "position") or not node.position:
        return None

    line = node.position.line
    column = node.position.column or 1

    # Get the code snippet (the line where the reference occurs)
    if 0 < line <= len(source_lines):
        code_snippet = source_lines[line - 1]
    else:
        code_snippet = ""

    return SymbolReference(
        file=java_file,
        line=line,
        column=column,
        code_snippet=code_snippet,
        usage_type=usage_type,
    )


def find_all_references(
    symbols: list,
    java_files: list[Path],
) -> dict[str, list[SymbolReference]]:
    """Find references for multiple symbols.

    Args:
        symbols: List of Symbol objects
        java_files: List of Java files to search

    Returns:
        Dictionary mapping symbol names to their references
    """
    all_references = {}

    for symbol in symbols:
        key = f"{symbol.parent_class}.{symbol.name}" if symbol.parent_class else symbol.name
        refs = find_references(
            symbol_name=symbol.name,
            symbol_kind=symbol.kind,
            java_files=java_files,
            parent_class=symbol.parent_class,
        )
        all_references[key] = refs
        logger.debug(f"Found {len(refs)} references for {key}")

    return all_references
