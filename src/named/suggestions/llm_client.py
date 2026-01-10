"""OpenAI LLM client for generating naming suggestions."""

import json
from typing import Any

from openai import OpenAI

from named.config import get_settings
from named.logging import get_logger
from named.rules.models import NameSuggestion

logger = get_logger("llm")


class LLMError(Exception):
    """Exception raised when LLM operations fail."""

    pass


class LLMClient:
    """Client for interacting with OpenAI's API for naming suggestions."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        verbose: bool = False,
    ):
        """Initialize the LLM client.

        Args:
            api_key: OpenAI API key. If not provided, uses environment variable.
            model: Model to use. If not provided, uses settings default.
            verbose: If True, log prompts and responses at DEBUG level.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.verbose = verbose
        self._total_tokens = 0
        self._request_count = 0

        if not self.api_key:
            raise LLMError(
                "OpenAI API key not provided. Set NAMED_OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        logger.debug(f"LLM client initialized with model: {self.model}")

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all requests."""
        return self._total_tokens

    @property
    def request_count(self) -> int:
        """Total number of API requests made."""
        return self._request_count

    def get_suggestion(self, prompt: str) -> dict[str, Any]:
        """Send a prompt to the LLM and get a response.

        Args:
            prompt: The prompt to send

        Returns:
            Parsed JSON response from the LLM

        Raises:
            LLMError: If the API call fails or response is invalid
        """
        try:
            if self.verbose:
                logger.debug("=" * 60)
                logger.debug("[LLM PROMPT]")
                logger.debug("=" * 60)
                # Show truncated prompt in verbose mode
                if len(prompt) > 500:
                    logger.debug(prompt[:500] + f"\n... ({len(prompt)} chars total)")
                else:
                    logger.debug(prompt)
                logger.debug("=" * 60)

            self._request_count += 1

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Java developer helping to improve code quality. "
                            "You analyze naming conventions and suggest improvements. "
                            "Always respond with valid JSON only, no markdown formatting."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent suggestions
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            if not content:
                raise LLMError("Empty response from LLM")

            # Track token usage
            if response.usage:
                self._total_tokens += response.usage.total_tokens
                if self.verbose:
                    logger.debug(
                        f"[TOKENS] Prompt: {response.usage.prompt_tokens}, "
                        f"Completion: {response.usage.completion_tokens}, "
                        f"Total: {response.usage.total_tokens}"
                    )

            if self.verbose:
                logger.debug("=" * 60)
                logger.debug("[LLM RESPONSE]")
                logger.debug("=" * 60)
                logger.debug(content[:500] if len(content) > 500 else content)
                logger.debug("=" * 60)

            # Parse JSON from response
            return self._parse_json_response(content)

        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse LLM response as JSON: {e}") from e
        except Exception as e:
            if "LLMError" in str(type(e)):
                raise
            raise LLMError(f"LLM API call failed: {e}") from e

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks.

        Args:
            content: The raw response content

        Returns:
            Parsed JSON dictionary
        """
        # Remove markdown code blocks if present
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        return json.loads(content)

    def analyze_symbol(
        self,
        symbol_name: str,
        symbol_kind: str,
        annotations: list[str],
        context: str,
    ) -> NameSuggestion | None:
        """Analyze a symbol and get a naming suggestion if needed.

        Args:
            symbol_name: The name of the symbol
            symbol_kind: The kind of symbol (class, method, etc.)
            annotations: List of annotations on the symbol
            context: Code context

        Returns:
            NameSuggestion if a rename is suggested, None otherwise
        """
        from named.rules.prompt_renderer import get_symbol_analysis_prompt

        prompt = get_symbol_analysis_prompt(
            symbol_name=symbol_name,
            symbol_kind=symbol_kind,
            annotations=annotations,
            context=context,
        )

        response = self.get_suggestion(prompt)

        if not response.get("needs_rename", False):
            return None

        suggestion_data = response.get("suggestion")
        if not suggestion_data:
            return None

        return NameSuggestion(
            original_name=symbol_name,
            suggested_name=suggestion_data.get("suggested_name", ""),
            symbol_kind=symbol_kind,
            confidence=suggestion_data.get("confidence", 0.0),
            rationale=suggestion_data.get("rationale", ""),
            rules_addressed=suggestion_data.get("rules_addressed", []),
        )

    def analyze_symbols_batch(
        self,
        symbols: list[dict[str, Any]],
    ) -> list[NameSuggestion]:
        """Analyze multiple symbols and get suggestions.

        This method processes symbols one at a time (no batch API in MVP).

        Args:
            symbols: List of symbol dictionaries with name, kind, annotations, context

        Returns:
            List of NameSuggestion objects for symbols needing rename
        """
        suggestions = []

        for symbol in symbols:
            try:
                suggestion = self.analyze_symbol(
                    symbol_name=symbol["name"],
                    symbol_kind=symbol["kind"],
                    annotations=symbol.get("annotations", []),
                    context=symbol.get("context", ""),
                )
                if suggestion:
                    suggestions.append(suggestion)
            except LLMError as e:
                logger.warning(f"Failed to analyze {symbol['name']}: {e}")

        return suggestions
