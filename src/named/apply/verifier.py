"""Pre-apply and post-apply verification for rename operations."""

import subprocess
from pathlib import Path

from named.apply.models import ReplacementSite
from named.logging import get_logger

logger = get_logger("verifier")


def verify_site(site: ReplacementSite, actual_lines: list[str]) -> tuple[bool, str]:
    """Verify a replacement site against actual file content.

    Checks that the identifier exists at the expected location.

    Args:
        site: The replacement site to verify.
        actual_lines: Lines of the actual file content.

    Returns:
        (is_valid, reason_if_invalid)
    """
    line_idx = site.line - 1

    if line_idx < 0 or line_idx >= len(actual_lines):
        return False, f"Line {site.line} out of range (file has {len(actual_lines)} lines)"

    actual_line = actual_lines[line_idx]

    # For column-based sites, verify identifier at exact position
    if site.column is not None:
        idx = site.column - 1
        if idx < 0 or idx + len(site.original_name) > len(actual_line):
            return False, f"Column {site.column} out of range on line {site.line}"
        actual_text = actual_line[idx : idx + len(site.original_name)]
        if actual_text != site.original_name:
            return False, (
                f"Expected '{site.original_name}' at column {site.column}, "
                f"found '{actual_text}'"
            )

    # For snippet-based verification (if snippet is available)
    if site.code_snippet:
        snippet_stripped = site.code_snippet.strip()
        actual_stripped = actual_line.strip()
        if snippet_stripped and snippet_stripped != actual_stripped:
            # Allow fuzzy match - the core identifier should still be present
            if site.original_name not in actual_line:
                return False, (
                    f"Line content has changed. Expected snippet: '{snippet_stripped}', "
                    f"actual: '{actual_stripped}'"
                )

    return True, ""


def detect_build_system(project_root: Path) -> str | None:
    """Detect the Java build system in a project.

    Args:
        project_root: Root directory of the Java project.

    Returns:
        Build system name ('maven', 'gradle', or None).
    """
    if (project_root / "pom.xml").exists():
        return "maven"
    if (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
        return "gradle"
    return None


def verify_compilation(project_root: Path) -> tuple[bool, str]:
    """Run compilation check to verify the project still builds.

    Auto-detects the build system and runs the appropriate compile command.

    Args:
        project_root: Root directory of the Java project.

    Returns:
        (success, output_message)
    """
    build_system = detect_build_system(project_root)

    if build_system == "maven":
        cmd = ["mvn", "compile", "-q"]
    elif build_system == "gradle":
        cmd = ["gradle", "compileJava", "-q"]
    else:
        return True, "No build system detected. Skipping compilation check."

    logger.info(f"Running compilation check with {build_system}: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, f"Compilation successful ({build_system})"
        else:
            error_output = result.stderr or result.stdout
            return False, f"Compilation failed ({build_system}):\n{error_output}"

    except FileNotFoundError:
        return True, f"Build tool '{cmd[0]}' not found. Skipping compilation check."
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out after 120 seconds."
