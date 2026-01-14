"""Render rules and guardrails for LLM prompts."""

from named.prompts import get_rules_context as get_rules_context_new
from named.rules.guardrails import GUARDRAILS
from named.rules.models import RuleCategory
from named.rules.naming_rules import NAMING_RULES


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
        # Use the new prompts module for rules context
        return get_rules_context_new(
            rules=NAMING_RULES, guardrails=GUARDRAILS, include_schema=False
        )

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
