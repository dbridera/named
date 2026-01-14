"""Build prompts for LLM analysis."""

from named.analysis.extractor import Symbol
from named.prompts import get_batch_analysis_prompt, get_rules_context
from named.rules.guardrails import GUARDRAILS
from named.rules.naming_rules import NAMING_RULES
from named.rules.prompt_renderer import PromptRenderer


def build_suggestion_prompt(symbol: Symbol, lang: str = "en") -> str:
    """Build a complete prompt for analyzing a symbol.

    Args:
        symbol: The Symbol to analyze
        lang: Language for rule descriptions ("en" or "es")

    Returns:
        Complete prompt string ready to send to LLM
    """
    renderer = PromptRenderer(lang)

    return renderer.render_for_symbol_analysis(
        symbol_name=symbol.name,
        symbol_kind=symbol.kind,
        annotations=symbol.annotations,
        context=symbol.context,
    )


def build_batch_prompt(symbols: list[Symbol], lang: str = "en") -> str:
    """Build a prompt for analyzing multiple symbols at once.

    This can be more efficient for small batches.

    Args:
        symbols: List of Symbols to analyze
        lang: Language for rule descriptions

    Returns:
        Complete prompt string
    """
    # Get rules context from new prompts module
    rules_context = get_rules_context(
        rules=NAMING_RULES, guardrails=GUARDRAILS, include_schema=False
    )

    # Convert symbols to dict format for batch analysis
    symbols_dicts = [
        {
            "name": s.name,
            "kind": s.kind,
            "annotations": ", ".join(f"@{a}" for a in s.annotations) or "None",
            "context": s.context[:200] if s.context else "N/A",
        }
        for s in symbols
    ]

    # Use new batch analysis prompt
    return get_batch_analysis_prompt(symbols=symbols_dicts, rules_context=rules_context)


def build_context_for_symbol(symbol: Symbol, max_lines: int = 15) -> str:
    """Build a code context string for a symbol.

    Args:
        symbol: The symbol to get context for
        max_lines: Maximum lines of context to include

    Returns:
        Formatted context string
    """
    context_parts = []

    if symbol.parent_class:
        context_parts.append(f"// In class: {symbol.parent_class}")

    if symbol.package:
        context_parts.append(f"// Package: {symbol.package}")

    if symbol.modifiers:
        context_parts.append(f"// Modifiers: {', '.join(symbol.modifiers)}")

    if symbol.annotations:
        for ann in symbol.annotations:
            context_parts.append(f"@{ann}")

    if symbol.kind == "method":
        params = ", ".join(symbol.parameter_types) if symbol.parameter_types else ""
        return_type = symbol.return_type or "void"
        context_parts.append(f"{return_type} {symbol.name}({params})")
    elif symbol.kind == "field" or symbol.kind == "constant":
        context_parts.append(f"{symbol.name}")
    elif symbol.kind in ("class", "interface", "enum"):
        context_parts.append(f"{symbol.kind} {symbol.name}")
    else:
        context_parts.append(symbol.name)

    # Add the actual context if available
    if symbol.context:
        # Limit context to max_lines
        lines = symbol.context.split("\n")[:max_lines]
        context_parts.append("\n// Code context:")
        context_parts.extend(lines)

    return "\n".join(context_parts)
