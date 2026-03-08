"""Type hierarchy analysis for Java class/interface inheritance."""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from named.logging import get_logger

logger = get_logger("hierarchy")


@dataclass
class TypeInfo:
    """Information about a type (class/interface/enum) in the hierarchy."""

    name: str
    kind: str  # "class", "interface", "enum"
    file: Path
    extends: str | None = None
    implements: list[str] = field(default_factory=list)
    methods: list = field(default_factory=list)  # list of Symbol objects


def build_type_hierarchy(all_symbols: list) -> dict[str, TypeInfo]:
    """Build a type hierarchy map from all extracted symbols.

    Args:
        all_symbols: List of Symbol objects from extraction.

    Returns:
        Dict mapping type name to TypeInfo with methods attached.
    """
    type_map: dict[str, TypeInfo] = {}

    # First pass: collect all types
    for symbol in all_symbols:
        if symbol.kind in ("class", "interface", "enum"):
            type_map[symbol.name] = TypeInfo(
                name=symbol.name,
                kind=symbol.kind,
                file=symbol.location.file,
                extends=symbol.extends_type,
                implements=symbol.implements_types[:],
            )

    # Second pass: attach methods to their parent types
    for symbol in all_symbols:
        if symbol.kind == "method" and symbol.parent_class:
            type_info = type_map.get(symbol.parent_class)
            if type_info:
                type_info.methods.append(symbol)

    return type_map


def find_subtypes(type_name: str, type_map: dict[str, TypeInfo]) -> list[str]:
    """Find all direct and transitive subtypes of a given type.

    Args:
        type_name: Name of the parent type.
        type_map: Type hierarchy map from build_type_hierarchy().

    Returns:
        List of subtype names (does not include type_name itself).
    """
    subtypes = []
    visited = set()
    queue = [type_name]

    while queue:
        current = queue.pop(0)
        for name, info in type_map.items():
            if name in visited:
                continue
            is_subtype = (
                info.extends == current
                or current in info.implements
            )
            if is_subtype:
                visited.add(name)
                subtypes.append(name)
                queue.append(name)

    return subtypes


def find_override_methods(
    method_name: str,
    param_types: list[str],
    parent_class: str,
    type_map: dict[str, TypeInfo],
) -> list:
    """Find methods that override/implement a given method in subtypes.

    Walks down the hierarchy from parent_class and finds methods with
    matching name and parameter types in any subtype.

    Args:
        method_name: Name of the method being renamed.
        param_types: Parameter types of the method for signature matching.
        parent_class: Class/interface where the method is declared.
        type_map: Type hierarchy map.

    Returns:
        List of Symbol objects for override methods found.
    """
    overrides = []
    subtypes = find_subtypes(parent_class, type_map)

    for subtype_name in subtypes:
        type_info = type_map.get(subtype_name)
        if not type_info:
            continue

        for method in type_info.methods:
            if method.name != method_name:
                continue
            # Match by parameter count and types
            if len(method.parameter_types) != len(param_types):
                continue
            if method.parameter_types == param_types or not param_types:
                overrides.append(method)
                logger.debug(
                    f"Found override: {subtype_name}.{method_name}() "
                    f"in {type_info.file.name}"
                )

    return overrides
