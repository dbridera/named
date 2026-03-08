"""Find references (usages) of symbols across Java files."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import javalang
from javalang.tree import (
    ClassCreator,
    MemberReference,
    MethodInvocation,
    ReferenceType,
)

from named.logging import get_logger

logger = get_logger("reference_finder")

UsageType = Literal["read", "write", "call", "instantiate", "type_reference", "import"]


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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with file (str), line (int), column (int),
            code_snippet (str), and usage_type (str).
        """
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
        references.extend(_find_import_references(symbol_name, java_file, source_lines))
    elif symbol_kind == "method":
        references.extend(_find_method_references(symbol_name, tree, java_file, source_lines))
    elif symbol_kind == "field" or symbol_kind == "constant":
        references.extend(_find_field_references(symbol_name, tree, java_file, source_lines))
    elif symbol_kind == "parameter" or symbol_kind == "variable":
        references.extend(_find_variable_references(symbol_name, tree, java_file, source_lines))

    # Text-based fallback for field/parameter/variable references
    # Catches this.field patterns and other usages the AST may miss
    if symbol_kind in ("field", "constant", "parameter", "variable"):
        text_refs = _find_text_references(symbol_name, java_file, source_lines, references)
        references.extend(text_refs)

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


def _find_import_references(
    class_name: str,
    java_file: Path,
    source_lines: list[str],
) -> list[SymbolReference]:
    """Find import statements that reference a class name.

    Matches patterns like 'import com.example.ClassName;' where the
    last segment of the import path matches the class name.
    Does NOT match wildcard imports (import com.example.*).

    Args:
        class_name: Name of the class/interface to find.
        java_file: Path to the Java file.
        source_lines: Lines of the file.

    Returns:
        List of SymbolReference objects with usage_type='import'.
    """
    references = []
    pattern = re.compile(
        r"import\s+(?:static\s+)?[\w.]*\." + re.escape(class_name) + r"\s*;"
    )

    for line_num, line_text in enumerate(source_lines, start=1):
        match = pattern.search(line_text)
        if match:
            # Find the column of the class name within the import
            name_start = line_text.rfind(class_name, match.start(), match.end())
            col = name_start + 1 if name_start >= 0 else match.start() + 1
            references.append(
                SymbolReference(
                    file=java_file,
                    line=line_num,
                    column=col,
                    code_snippet=line_text,
                    usage_type="import",
                )
            )

    return references


def _get_exclusion_zones(line: str) -> list[tuple[int, int]]:
    """Return (start, end) ranges of string literals and comments in a line.

    Handles double-quoted strings, single-quoted chars, and // line comments.
    Does NOT handle multi-line /* */ comments (would need cross-line state).

    Args:
        line: A single line of source code.

    Returns:
        List of (start, end) tuples marking zones to exclude from text matching.
    """
    zones = []
    i = 0
    length = len(line)

    while i < length:
        ch = line[i]

        # Line comment
        if ch == "/" and i + 1 < length and line[i + 1] == "/":
            zones.append((i, length))
            break

        # String literal
        if ch == '"':
            start = i
            i += 1
            while i < length:
                if line[i] == "\\" and i + 1 < length:
                    i += 2  # Skip escaped character
                    continue
                if line[i] == '"':
                    i += 1
                    break
                i += 1
            zones.append((start, i))
            continue

        # Char literal
        if ch == "'":
            start = i
            i += 1
            while i < length:
                if line[i] == "\\" and i + 1 < length:
                    i += 2
                    continue
                if line[i] == "'":
                    i += 1
                    break
                i += 1
            zones.append((start, i))
            continue

        i += 1

    return zones


def _is_in_exclusion_zone(pos: int, zones: list[tuple[int, int]]) -> bool:
    """Check if a position falls inside any exclusion zone."""
    return any(start <= pos < end for start, end in zones)


def _find_text_references(
    symbol_name: str,
    java_file: Path,
    source_lines: list[str],
    known_refs: list[SymbolReference],
) -> list[SymbolReference]:
    """Fallback text-based reference search using word boundaries.

    Finds references that the AST-based search may have missed (e.g., this.field).
    Deduplicates against already-found references.
    Excludes matches inside string literals and comments.

    Args:
        symbol_name: Name of the symbol.
        java_file: Path to the file.
        source_lines: Lines of the file.
        known_refs: References already found by AST search.

    Returns:
        Additional references not already in known_refs.
    """
    known_positions = {(r.line, r.column) for r in known_refs}

    additional = []
    pattern = re.compile(r"\b" + re.escape(symbol_name) + r"\b")

    for line_num, line_text in enumerate(source_lines, start=1):
        exclusion_zones = _get_exclusion_zones(line_text)

        for match in pattern.finditer(line_text):
            col = match.start() + 1  # 1-based
            if (line_num, col) not in known_positions:
                # Skip matches inside strings or comments
                if _is_in_exclusion_zone(match.start(), exclusion_zones):
                    continue
                additional.append(
                    SymbolReference(
                        file=java_file,
                        line=line_num,
                        column=col,
                        code_snippet=line_text,
                        usage_type="read",
                    )
                )

    return additional


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
