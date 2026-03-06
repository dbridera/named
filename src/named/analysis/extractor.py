"""Symbol extraction from Java AST."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from javalang.tree import (
    ClassDeclaration,
    CompilationUnit,
    ConstructorDeclaration,
    EnumDeclaration,
    FieldDeclaration,
    InterfaceDeclaration,
    MethodDeclaration,
)

from named.analysis.parser import get_package_name, parse_java_file

SymbolKind = Literal[
    "class",
    "interface",
    "enum",
    "method",
    "constructor",
    "field",
    "parameter",
    "variable",
    "constant",
]


@dataclass
class SourceLocation:
    """Location of a symbol in source code."""

    file: Path
    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class Symbol:
    """Represents an extracted Java symbol (class, method, field, etc.)."""

    name: str
    kind: SymbolKind
    location: SourceLocation
    annotations: list[str] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    parent_class: str | None = None
    package: str | None = None
    context: str = ""  # Code snippet for context
    return_type: str | None = None  # For methods
    parameter_types: list[str] = field(default_factory=list)  # For methods
    references: list = field(default_factory=list)  # List of SymbolReference

    def is_constant(self) -> bool:
        """Check if this symbol is a constant (static final field)."""
        return self.kind == "field" and "static" in self.modifiers and "final" in self.modifiers

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "kind": self.kind,
            "location": {
                "file": str(self.location.file),
                "line": self.location.line,
                "column": self.location.column,
            },
            "annotations": self.annotations,
            "modifiers": self.modifiers,
            "parent_class": self.parent_class,
            "package": self.package,
            "context": self.context,
        }
        if self.references:
            result["references"] = [ref.to_dict() for ref in self.references]
            result["reference_count"] = len(self.references)
        return result


def _get_annotations(node) -> list[str]:
    """Extract annotation names from a node."""
    annotations = []
    if hasattr(node, "annotations") and node.annotations:
        for ann in node.annotations:
            if hasattr(ann, "name"):
                annotations.append(ann.name)
    return annotations


def _get_modifiers(node) -> list[str]:
    """Extract modifiers from a node."""
    modifiers = []
    if hasattr(node, "modifiers") and node.modifiers:
        modifiers = list(node.modifiers)
    return modifiers


def _get_position(node, file_path: Path) -> SourceLocation:
    """Get source location from a node."""
    line = 1
    column = 1
    if hasattr(node, "position") and node.position:
        line = node.position.line or 1
        column = node.position.column or 1
    return SourceLocation(file=file_path, line=line, column=column)


def _extract_from_type_declaration(
    node,
    kind: SymbolKind,
    file_path: Path,
    package: str | None,
    source_lines: list[str],
) -> list[Symbol]:
    """Extract symbols from a class, interface, or enum declaration."""
    symbols = []

    # Extract the type itself
    type_name = node.name
    type_location = _get_position(node, file_path)

    # Get context (a few lines around the declaration)
    context_lines = source_lines[max(0, type_location.line - 2) : type_location.line + 5]
    context = "\n".join(context_lines)

    symbols.append(
        Symbol(
            name=type_name,
            kind=kind,
            location=type_location,
            annotations=_get_annotations(node),
            modifiers=_get_modifiers(node),
            package=package,
            context=context,
        )
    )

    # Extract members
    if hasattr(node, "body") and node.body:
        for member in node.body:
            # Methods
            if isinstance(member, MethodDeclaration):
                method_location = _get_position(member, file_path)
                method_context = source_lines[
                    max(0, method_location.line - 2) : method_location.line + 10
                ]

                # Get parameter types
                param_types = []
                if member.parameters:
                    for param in member.parameters:
                        if hasattr(param, "type") and param.type:
                            param_types.append(str(param.type.name))

                symbols.append(
                    Symbol(
                        name=member.name,
                        kind="method",
                        location=method_location,
                        annotations=_get_annotations(member),
                        modifiers=_get_modifiers(member),
                        parent_class=type_name,
                        package=package,
                        context="\n".join(method_context),
                        return_type=str(member.return_type.name) if member.return_type else "void",
                        parameter_types=param_types,
                    )
                )

                # Extract parameters
                if member.parameters:
                    for param in member.parameters:
                        param_location = _get_position(param, file_path)
                        symbols.append(
                            Symbol(
                                name=param.name,
                                kind="parameter",
                                location=param_location,
                                annotations=_get_annotations(param),
                                modifiers=_get_modifiers(param),
                                parent_class=type_name,
                                package=package,
                                context=f"Parameter '{param.name}' of type {param.type.name if param.type else 'unknown'} in method {member.name}",
                            )
                        )

            # Constructors
            elif isinstance(member, ConstructorDeclaration):
                constructor_location = _get_position(member, file_path)
                symbols.append(
                    Symbol(
                        name=member.name,
                        kind="constructor",
                        location=constructor_location,
                        annotations=_get_annotations(member),
                        modifiers=_get_modifiers(member),
                        parent_class=type_name,
                        package=package,
                        context=f"Constructor of {type_name}",
                    )
                )

            # Fields
            elif isinstance(member, FieldDeclaration):
                field_modifiers = _get_modifiers(member)
                field_annotations = _get_annotations(member)

                if member.declarators:
                    for declarator in member.declarators:
                        field_location = _get_position(member, file_path)

                        # Determine if it's a constant
                        is_constant = "static" in field_modifiers and "final" in field_modifiers
                        kind: SymbolKind = "constant" if is_constant else "field"

                        symbols.append(
                            Symbol(
                                name=declarator.name,
                                kind=kind,
                                location=field_location,
                                annotations=field_annotations,
                                modifiers=field_modifiers,
                                parent_class=type_name,
                                package=package,
                                context=f"Field in {type_name}",
                            )
                        )

    return symbols


def extract_symbols_from_tree(
    tree: CompilationUnit,
    file_path: Path,
    source_code: str,
) -> list[Symbol]:
    """Extract all symbols from a parsed Java AST.

    Args:
        tree: The parsed compilation unit
        file_path: Path to the source file
        source_code: The original source code

    Returns:
        List of extracted symbols
    """
    symbols = []
    package = get_package_name(tree)
    source_lines = source_code.split("\n")

    # Iterate through all types in the compilation unit
    for path, node in tree.filter(ClassDeclaration):
        symbols.extend(
            _extract_from_type_declaration(node, "class", file_path, package, source_lines)
        )

    for path, node in tree.filter(InterfaceDeclaration):
        symbols.extend(
            _extract_from_type_declaration(node, "interface", file_path, package, source_lines)
        )

    for path, node in tree.filter(EnumDeclaration):
        symbols.extend(
            _extract_from_type_declaration(node, "enum", file_path, package, source_lines)
        )

    return symbols


def extract_symbols(file_path: Path) -> list[Symbol]:
    """Extract all symbols from a Java file.

    Args:
        file_path: Path to the Java file

    Returns:
        List of extracted symbols
    """
    source_code = file_path.read_text(encoding="utf-8")
    tree = parse_java_file(file_path)
    return extract_symbols_from_tree(tree, file_path, source_code)


def extract_symbols_from_directory(
    directory: Path,
    exclude_patterns: list[str] | None = None,
) -> dict[Path, list[Symbol]]:
    """Extract symbols from all Java files in a directory.

    Args:
        directory: The directory to scan
        exclude_patterns: Glob patterns to exclude

    Returns:
        Dictionary mapping file paths to their symbols
    """
    from named.analysis.parser import find_java_files

    result = {}
    java_files = find_java_files(directory, exclude_patterns)

    for java_file in java_files:
        try:
            symbols = extract_symbols(java_file)
            result[java_file] = symbols
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Failed to extract symbols from {java_file}: {e}")
            result[java_file] = []

    return result
