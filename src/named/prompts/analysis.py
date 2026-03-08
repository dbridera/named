"""Analysis task prompts."""

from typing import Any

from named.prompts.base import PromptTemplate
from named.rules.guardrails import Guardrail
from named.rules.models import NamingRule

# Batch analysis template using Python string
BATCH_ANALYSIS_TEMPLATE = """Analyze the following Java symbols and determine if they violate any naming rules.
For each symbol that needs renaming, provide a suggestion.

Symbols to analyze:
{symbols_text}

Apply these naming rules and conventions:
{rules_context}

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


class RulesContextPrompt(PromptTemplate):
    """Prompt for rendering rules context."""

    version = "1.0.0"

    def render(
        self,
        rules: list[NamingRule],
        guardrails: list[Guardrail],
        include_schema: bool = True,
        **kwargs,
    ) -> str:
        """Render rules context with optional JSON schema.

        Args:
            rules: List of naming rules to include
            guardrails: List of guardrails to include
            include_schema: Whether to include the JSON response schema

        Returns:
            Formatted rules context string
        """
        self.validate_inputs(rules=rules, guardrails=guardrails)

        sections = []

        # Header
        sections.append("# Banking Code Quality - Naming Rules\n")
        sections.append(
            "You are an expert Java developer helping to improve code quality by suggesting better names for identifiers."
        )
        sections.append(
            "You must analyze Java code and suggest name improvements following these rules:\n"
        )

        # Rules section
        sections.append("## Naming Convention Rules\n")
        for rule in rules:
            sections.append(f"\n### {rule.name_en}")
            sections.append(f"**ID**: `{rule.id}`")
            sections.append(f"**Description**: {rule.description_en}")
            sections.append(f"**Severity**: {rule.severity.value}")
            if rule.detect_patterns:
                sections.append(
                    f"**Patterns**: {', '.join(f'`{p}`' for p in rule.detect_patterns)}"
                )
            if rule.tokens_to_avoid:
                sections.append(f"**Avoid**: {', '.join(rule.tokens_to_avoid)}")

        # Guardrails section
        sections.append("\n\n## Guardrails\n")
        for guardrail in guardrails:
            sections.append(f"\n### {guardrail.name}")
            sections.append(f"**ID**: `{guardrail.id}`")
            sections.append(f"**Description**: {guardrail.description}")

        # Output requirements
        sections.append("\n\n## Output Requirements\n")
        sections.append("1. Only suggest changes when you have **confidence >= 0.80**")
        sections.append(
            '2. Provide rationale referencing specific rule IDs (e.g., "Violates R1_REVEAL_INTENT")'
        )
        sections.append("3. Return suggestions in valid JSON format")
        sections.append(
            "4. If a symbol has a blocking annotation (see guardrails above), do NOT suggest renaming it"
        )
        sections.append(
            "5. Consider the context: method purpose, class responsibility, parameter meaning"
        )

        # Confidence guidelines
        sections.append("\n\n## Confidence Guidelines\n")
        sections.append(
            "- 0.95-1.00: Obvious violation with clear fix (e.g., `data` → `customerRecord`)"
        )
        sections.append("- 0.85-0.94: Clear violation with good suggested fix")
        sections.append("- 0.80-0.84: Probable violation, reasonable fix")
        sections.append("- Below 0.80: Don't suggest (uncertain or context-dependent)")

        return "\n".join(sections)

    def validate_inputs(self, **kwargs) -> None:
        """Validate required inputs."""
        if "rules" not in kwargs:
            raise ValueError("rules parameter is required")
        if "guardrails" not in kwargs:
            raise ValueError("guardrails parameter is required")


class BatchAnalysisPrompt(PromptTemplate):
    """Prompt for batch symbol analysis."""

    version = "1.0.0"

    def render(self, symbols: list[dict[str, Any]], rules_context: str, **kwargs) -> str:
        """Render batch analysis prompt.

        Args:
            symbols: List of symbol dictionaries with name, kind, annotations, context
            rules_context: Pre-rendered rules and guardrails context

        Returns:
            Formatted batch analysis prompt
        """
        self.validate_inputs(symbols=symbols, rules_context=rules_context)

        # Format symbol list
        symbols_text = "\n\n".join(
            f"### Symbol {i + 1}\n"
            f"- **Name**: `{s['name']}`\n"
            f"- **Kind**: {s['kind']}\n"
            f"- **Annotations**: {s.get('annotations', 'None')}\n"
            f"- **Context**: {s.get('context', 'N/A')[:200]}..."
            for i, s in enumerate(symbols)
        )

        # Use format() for string interpolation
        return BATCH_ANALYSIS_TEMPLATE.format(
            symbols_text=symbols_text,
            rules_context=rules_context,
        ).strip()

    def validate_inputs(self, **kwargs) -> None:
        """Validate required inputs."""
        if "symbols" not in kwargs or not kwargs["symbols"]:
            raise ValueError("symbols parameter is required and must be non-empty")
        if "rules_context" not in kwargs:
            raise ValueError("rules_context parameter is required")


FILE_ANALYSIS_TEMPLATE = """## Java File: {file_name}

```java
{file_source}
```

## Symbols to Analyze

The following symbols from this file need naming evaluation:

{symbols_list}

{rules_context}

## Your Task

Analyze each symbol listed above using the **full file source above as context**.

Pay special attention to:
- The symbol's **declared type** (visible in the source)
- **Sibling fields/methods** in the same class (for consistency checks)
- **Method bodies** (for understanding parameter and variable intent)
- **Annotations** that may act as guardrails (do NOT rename annotated symbols)

Respond with JSON in this exact format:
```json
{{
  "results": [
    {{
      "symbol_index": 0,
      "needs_rename": true,
      "analysis": "Brief explanation referencing rule IDs",
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

Include an entry for every symbol index. If confidence is below 0.80, set needs_rename to false.
"""


class FileAnalysisPrompt(PromptTemplate):
    """Prompt for per-file symbol analysis using full source context."""

    version = "1.0.0"

    def render(
        self,
        file_name: str,
        file_source: str,
        symbols: list[dict[str, Any]],
        rules_context: str,
        **kwargs,
    ) -> str:
        """Render a per-file analysis prompt.

        Args:
            file_name: Name of the Java file (e.g., 'Account.java')
            file_source: Full source code of the file
            symbols: List of symbol dicts with name, kind, annotations, line
            rules_context: Pre-rendered rules and guardrails context

        Returns:
            Formatted prompt string
        """
        self.validate_inputs(
            file_name=file_name,
            file_source=file_source,
            symbols=symbols,
            rules_context=rules_context,
        )

        symbols_list = "\n".join(
            f"{i}. `{s['name']}` — {s['kind']}"
            + (f", line {s['line']}" if s.get("line") else "")
            + (f", annotations: {s['annotations']}" if s.get("annotations") and s["annotations"] != "None" else "")
            for i, s in enumerate(symbols)
        )

        return FILE_ANALYSIS_TEMPLATE.format(
            file_name=file_name,
            file_source=file_source,
            symbols_list=symbols_list,
            rules_context=rules_context,
        ).strip()

    def validate_inputs(self, **kwargs) -> None:
        for key in ("file_name", "file_source", "symbols", "rules_context"):
            if not kwargs.get(key):
                raise ValueError(f"{key} parameter is required and must be non-empty")


# Factory functions
def get_rules_context(
    rules: list[NamingRule],
    guardrails: list[Guardrail],
    include_schema: bool = True,
) -> str:
    """Get rules context prompt.

    Args:
        rules: List of naming rules
        guardrails: List of guardrails
        include_schema: Whether to include JSON schema

    Returns:
        Formatted rules context string
    """
    return RulesContextPrompt().render(
        rules=rules,
        guardrails=guardrails,
        include_schema=include_schema,
    )


def get_batch_analysis_prompt(
    symbols: list[dict[str, Any]],
    rules_context: str,
) -> str:
    """Get batch analysis prompt.

    Args:
        symbols: List of symbols to analyze (dicts with name, kind, annotations, context)
        rules_context: Pre-rendered rules context

    Returns:
        Formatted batch analysis prompt
    """
    return BatchAnalysisPrompt().render(
        symbols=symbols,
        rules_context=rules_context,
    )
