"""Render rules and guardrails for LLM prompts."""

from named.rules.models import NamingRule, RuleCategory
from named.rules.naming_rules import NAMING_RULES
from named.rules.guardrails import GUARDRAILS


class PromptRenderer:
    """Renders rules and guardrails for LLM prompts.

    This class provides methods to convert the rule definitions into
    formatted text suitable for inclusion in LLM prompts.
    """

    def __init__(self, lang: str = "en"):
        """Initialize the renderer.

        Args:
            lang: Language code ("en" for English, "es" for Spanish)
        """
        self.lang = lang

    def render_all_rules(self) -> str:
        """Render all 9 naming rules for LLM context.

        Returns:
            Formatted string with all rules grouped by category
        """
        sections = []

        # Group rules by category
        for category in RuleCategory:
            rules = [r for r in NAMING_RULES if r.category == category]
            if rules:
                category_name = {
                    RuleCategory.SEMANTIC: "Semantic Rules (Intent & Meaning)",
                    RuleCategory.SYNTACTIC: "Syntactic Rules (Format & Style)",
                    RuleCategory.CONSISTENCY: "Consistency Rules (Project-wide)",
                }[category]

                sections.append(f"\n## {category_name}\n")
                for rule in rules:
                    sections.append(rule.to_prompt_section(self.lang))

        return "\n\n".join(sections)

    def render_guardrails(self) -> str:
        """Render guardrails as constraints for LLM.

        Returns:
            Formatted string with all guardrails
        """
        lines = [
            "## Blocking Conditions (DO NOT suggest renaming if any apply)\n",
            "The following conditions must prevent any renaming suggestion:\n",
        ]

        for guardrail in GUARDRAILS:
            lines.append(guardrail.to_prompt_section(self.lang))

        return "\n".join(lines)

    def render_full_context(self) -> str:
        """Render complete rules context for LLM prompt.

        Returns:
            Complete formatted context including all rules and guardrails
        """
        return f"""# Banking Code Quality - Naming Rules

You are an expert Java developer helping to improve code quality by suggesting better names for identifiers.
You must analyze Java code and suggest name improvements following these rules:

{self.render_all_rules()}

{self.render_guardrails()}

## Output Requirements

1. Only suggest changes when you have **confidence >= 0.80**
2. Provide rationale referencing specific rule IDs (e.g., "Violates R1_REVEAL_INTENT")
3. Return suggestions in valid JSON format
4. If a symbol has a blocking annotation (see guardrails above), do NOT suggest renaming it
5. Consider the context: method purpose, class responsibility, parameter meaning

## Confidence Guidelines

- 0.95-1.00: Obvious violation with clear fix (e.g., `data` → `customerRecord`)
- 0.85-0.94: Clear violation with good suggested fix
- 0.80-0.84: Probable violation, reasonable fix
- Below 0.80: Don't suggest (uncertain or context-dependent)
"""

    def render_for_symbol_analysis(
        self,
        symbol_name: str,
        symbol_kind: str,
        annotations: list[str],
        context: str,
    ) -> str:
        """Render a prompt for analyzing a specific symbol.

        Args:
            symbol_name: The name of the symbol to analyze
            symbol_kind: The kind of symbol (class, method, field, variable)
            annotations: List of annotations on the symbol
            context: Code context (surrounding code snippet)

        Returns:
            Complete prompt for symbol analysis
        """
        ann_str = ", ".join(f"@{a}" for a in annotations) if annotations else "None"

        return f"""{self.render_full_context()}

---

## Symbol to Analyze

- **Name**: `{symbol_name}`
- **Kind**: {symbol_kind}
- **Annotations**: {ann_str}

### Code Context
```java
{context}
```

## Your Task

Analyze the symbol name above and determine if it violates any naming rules.
If it does, suggest a better name.

Respond with JSON in this exact format:
```json
{{
  "needs_rename": true/false,
  "analysis": "Brief explanation of issues found (reference rule IDs)",
  "suggestion": {{
    "suggested_name": "betterName",
    "confidence": 0.85,
    "rationale": "Why this name is better",
    "rules_addressed": ["R1_REVEAL_INTENT"]
  }}
}}
```

If the symbol doesn't need renaming or has a blocking annotation, respond:
```json
{{
  "needs_rename": false,
  "analysis": "Explanation of why no rename is needed",
  "suggestion": null
}}
```
"""


def get_llm_rules_context(lang: str = "en") -> str:
    """Get the full rules context ready for LLM prompts.

    This is a convenience function for quick access.

    Args:
        lang: Language code ("en" for English, "es" for Spanish)

    Returns:
        Complete formatted context string
    """
    return PromptRenderer(lang).render_full_context()


def get_symbol_analysis_prompt(
    symbol_name: str,
    symbol_kind: str,
    annotations: list[str],
    context: str,
    lang: str = "en",
) -> str:
    """Get a prompt for analyzing a specific symbol.

    Args:
        symbol_name: The name of the symbol to analyze
        symbol_kind: The kind of symbol
        annotations: List of annotations
        context: Code context
        lang: Language code

    Returns:
        Complete prompt string
    """
    return PromptRenderer(lang).render_for_symbol_analysis(
        symbol_name, symbol_kind, annotations, context
    )
