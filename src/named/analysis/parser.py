"""Java parser wrapper using javalang."""

from pathlib import Path
from typing import Any

import javalang
from javalang.tree import CompilationUnit


class JavaParseError(Exception):
    """Exception raised when Java parsing fails."""

    def __init__(self, file_path: Path, message: str):
        self.file_path = file_path
        self.message = message
        super().__init__(f"Failed to parse {file_path}: {message}")


def parse_java_file(file_path: Path) -> CompilationUnit:
    """Parse a Java file and return the AST.

    Args:
        file_path: Path to the Java file

    Returns:
        The parsed CompilationUnit (AST root)

    Raises:
        JavaParseError: If parsing fails
        FileNotFoundError: If the file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Java file not found: {file_path}")

    if not file_path.suffix == ".java":
        raise ValueError(f"Not a Java file: {file_path}")

    try:
        source_code = file_path.read_text(encoding="utf-8")
        tree = javalang.parse.parse(source_code)
        return tree
    except javalang.parser.JavaSyntaxError as e:
        raise JavaParseError(file_path, f"Syntax error: {e}") from e
    except Exception as e:
        raise JavaParseError(file_path, str(e)) from e


def parse_java_source(source_code: str) -> CompilationUnit:
    """Parse Java source code string and return the AST.

    Args:
        source_code: Java source code as a string

    Returns:
        The parsed CompilationUnit (AST root)

    Raises:
        JavaParseError: If parsing fails
    """
    try:
        tree = javalang.parse.parse(source_code)
        return tree
    except javalang.parser.JavaSyntaxError as e:
        raise JavaParseError(Path("<string>"), f"Syntax error: {e}") from e
    except Exception as e:
        raise JavaParseError(Path("<string>"), str(e)) from e


def get_node_position(node: Any) -> tuple[int, int] | None:
    """Get the position (line, column) of a node if available.

    Args:
        node: A javalang AST node

    Returns:
        Tuple of (line, column) or None if not available
    """
    if hasattr(node, "position") and node.position:
        return (node.position.line, node.position.column)
    return None


def get_package_name(tree: CompilationUnit) -> str | None:
    """Extract the package name from a compilation unit.

    Args:
        tree: The parsed AST

    Returns:
        The package name or None if not specified
    """
    if tree.package:
        return tree.package.name
    return None


def get_imports(tree: CompilationUnit) -> list[str]:
    """Extract all import statements from a compilation unit.

    Args:
        tree: The parsed AST

    Returns:
        List of imported class/package names
    """
    imports = []
    if tree.imports:
        for imp in tree.imports:
            imports.append(imp.path)
    return imports


def find_java_files(directory: Path, exclude_patterns: list[str] | None = None) -> list[Path]:
    """Find all Java files in a directory.

    Args:
        directory: The directory to search
        exclude_patterns: List of glob patterns to exclude (e.g., "**/test/**")

    Returns:
        List of paths to Java files
    """
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    exclude_patterns = exclude_patterns or []
    java_files = list(directory.rglob("*.java"))

    # Filter out excluded patterns
    if exclude_patterns:
        filtered = []
        for java_file in java_files:
            excluded = False
            for pattern in exclude_patterns:
                # Check if file matches any exclusion pattern
                try:
                    if java_file.match(pattern):
                        excluded = True
                        break
                except ValueError:
                    # Invalid pattern, skip
                    pass
            if not excluded:
                filtered.append(java_file)
        return filtered

    return java_files
