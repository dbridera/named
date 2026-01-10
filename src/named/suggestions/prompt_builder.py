"""Build prompts for LLM analysis."""

from named.analysis.extractor import Symbol
from named.rules.prompt_renderer import PromptRenderer, get_llm_rules_context


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
    rules_context = get_llm_rules_context(lang)

    symbols_text = "\n\n".join(
        f"### Symbol {i+1}\n"
        f"- **Name**: `{s.name}`\n"
        f"- **Kind**: {s.kind}\n"
        f"- **Annotations**: {', '.join(f'@{a}' for a in s.annotations) or 'None'}\n"
        f"- **Context**: {s.context[:200]}..."
        for i, s in enumerate(symbols)
    )

    return f"""{rules_context}

---

## Symbols to Analyze

{symbols_text}

## Your Task

Analyze each symbol above and determine if it violates any naming rules.
For each symbol that needs renaming, provide a suggestion.

Respond with JSON in this exact format:
```json
{{
  "results": [
    {{
      "symbol_index": 0,
      "needs_rename": true,
      "analysis": "Brief explanation",
      "suggestion": {{
        "suggested_name": "betterName",
        "confidence": 0.85,
        "rationale": "Why this name is better",
        "rules_addressed": ["R1_REVEAL_INTENT"]
      }}
    }},
    {{
      "symbol_index": 1,
      "needs_rename": false,
      "analysis": "Name is appropriate",
      "suggestion": null
    }}
  ]
}}
```
"""


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
