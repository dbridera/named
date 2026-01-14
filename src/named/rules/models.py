"""Data models for naming rules and guardrails."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from named.analysis.impact_analyzer import RenameImpact


class Severity(Enum):
    """Severity level for rule violations."""

    ERROR = "error"  # Blocks refactoring
    WARNING = "warning"  # Suggests improvement


class RuleCategory(Enum):
    """Category of naming rules."""

    SEMANTIC = "semantic"  # Intent, meaning
    SYNTACTIC = "syntactic"  # Casing, format
    CONSISTENCY = "consistency"  # Project-wide patterns


@dataclass
class NamingRule:
    """Represents one of the 9 naming rules.

    Each rule has bilingual support (Spanish/English) for descriptions
    and includes detection patterns and examples for validation.
    """

    id: str  # e.g., "R1_REVEAL_INTENT"
    name: str  # Spanish name
    name_en: str  # English name
    description: str  # Full description in Spanish
    description_en: str  # Full description in English
    category: RuleCategory
    severity: Severity
    examples_good: list[str]  # Good naming examples
    examples_bad: list[str]  # Bad naming examples
    detect_patterns: list[str] = field(default_factory=list)  # Regex patterns
    tokens_to_avoid: list[str] = field(default_factory=list)  # Discouraged tokens
    exceptions: list[str] = field(default_factory=list)  # Allowed exceptions

    def to_prompt_section(self, lang: str = "en") -> str:
        """Render rule as a section for LLM prompt.

        Args:
            lang: Language code ("en" for English, "es" for Spanish)

        Returns:
            Formatted string for LLM prompt
        """
        name = self.name_en if lang == "en" else self.name
        desc = self.description_en if lang == "en" else self.description
        good = ", ".join(f"`{e}`" for e in self.examples_good[:3])
        bad = ", ".join(f"`{e}`" for e in self.examples_bad[:3])

        return f"""### {self.id}: {name}
{desc}
- **Good examples**: {good}
- **Bad examples**: {bad}"""


@dataclass
class Guardrail:
    """Represents a blocking condition that prevents renaming.

    Guardrails are hard constraints that override any suggestion.
    """

    id: str  # e.g., "G1_IMMUTABLE_CONTRACTS"
    name: str  # Spanish name
    name_en: str  # English name
    description: str  # Spanish description
    description_en: str  # English description
    check_type: Literal["annotation", "pattern", "confidence"]
    blocked_annotations: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)
    threshold: float | None = None  # For confidence guardrail

    def to_prompt_section(self, lang: str = "en") -> str:
        """Render guardrail as a section for LLM prompt."""
        name = self.name_en if lang == "en" else self.name
        desc = self.description_en if lang == "en" else self.description

        result = f"- **{name}**: {desc}"
        if self.blocked_annotations:
            annotations = ", ".join(f"@{a}" for a in self.blocked_annotations)
            result += f"\n  - Blocked annotations: {annotations}"

        return result


@dataclass
class RuleViolation:
    """Records a violation of a naming rule."""

    rule_id: str  # Which rule was violated
    symbol_name: str  # The name that violated the rule
    severity: Severity  # Error or warning
    message: str  # Human-readable explanation
    suggestion: str | None = None  # Suggested fix if available
    confidence: float = 1.0  # How confident we are in this violation


@dataclass
class NameSuggestion:
    """A suggested name improvement from the LLM."""

    original_name: str
    suggested_name: str
    symbol_kind: str  # class, method, field, variable, etc.
    confidence: float  # 0.0 - 1.0
    rationale: str  # Why this name is better
    rules_addressed: list[str] = field(default_factory=list)  # Which rules this fixes
    blocked: bool = False  # Whether a guardrail blocked this
    blocked_reason: str | None = None  # Why it was blocked
    references: list = field(default_factory=list)  # Symbol references (usages)
    location: dict | None = None  # Symbol location info
    impact_analysis: Optional["RenameImpact"] = None  # Impact analysis for the rename
