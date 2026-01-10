"""Logging configuration for Named."""

import logging
import sys
from typing import Literal

# Create the project logger
logger = logging.getLogger("named")


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    verbose: bool = False,
) -> None:
    """Configure logging for the Named project.

    Args:
        level: The logging level to use.
        verbose: If True, set level to DEBUG and use detailed format.
    """
    if verbose:
        level = "DEBUG"

    # Set the logger level
    logger.setLevel(getattr(logging, level))

    # Remove any existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level))

    # Create formatter based on verbosity
    if verbose:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger for the given name.

    Args:
        name: Optional sub-logger name. If provided, returns named.{name}.

    Returns:
        A logger instance.
    """
    if name:
        return logging.getLogger(f"named.{name}")
    return logger
