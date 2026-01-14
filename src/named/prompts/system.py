"""System role prompts for LLM client."""

from named.prompts.base import PromptTemplate

# System prompt template as Python string
SYSTEM_ROLE_TEMPLATE = """You are an expert Java developer helping to improve code quality.
You analyze naming conventions and suggest improvements based on Java best practices.

Guidelines:
- Follow Java naming conventions strictly
- Provide clear, actionable suggestions
- Consider context and domain semantics
- Always respond with valid JSON only, no markdown formatting

Your goal is to help developers write cleaner, more maintainable Java code."""


class SystemRolePrompt(PromptTemplate):
    """System role prompt for Java naming analysis."""

    version = "1.0.0"

    def __init__(self, language: str = "en"):
        self.language = language

    def render(self, **kwargs) -> str:
        """Render system role prompt.

        Returns:
            Formatted system prompt string
        """
        self.validate_inputs(**kwargs)
        # Could add variable interpolation here if needed
        return SYSTEM_ROLE_TEMPLATE.strip()

    def validate_inputs(self, **kwargs) -> None:
        """No variables needed for system prompt."""
        pass


# Factory function
def get_system_prompt(language: str = "en") -> str:
    """Get the system role prompt.

    Args:
        language: Language code (currently only 'en' supported)

    Returns:
        System role prompt string
    """
    return SystemRolePrompt(language=language).render()
