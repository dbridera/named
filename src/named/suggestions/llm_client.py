"""OpenAI LLM client for generating naming suggestions."""

import json
from typing import Any

from named.config import get_settings
from named.logging import get_logger
from named.rules.models import NameSuggestion
from named.suggestions.client_factory import create_openai_client
from named.suggestions.common import (
    CHUNK_SIZE,
    CHUNK_THRESHOLD,
    METHOD_PREFIXES,
    TOKENS_BASE,
    TOKENS_MAX,
    TOKENS_MIN,
    TOKENS_PER_SYMBOL,
    is_hallucinated,
    strip_markdown_fences,
)

logger = get_logger("llm")

# Re-export for backward compatibility (used by batch_retrieve in cli.py)
_METHOD_PREFIXES = METHOD_PREFIXES
_CHUNK_THRESHOLD = CHUNK_THRESHOLD
_CHUNK_SIZE = CHUNK_SIZE
_TOKENS_PER_SYMBOL = TOKENS_PER_SYMBOL
_TOKENS_BASE = TOKENS_BASE
_TOKENS_MAX = TOKENS_MAX
_TOKENS_MIN = TOKENS_MIN


def parse_llm_response(data: dict[str, Any], symbol_name: str) -> "NameSuggestion | None":
    """Parse a batch API LLM response into a NameSuggestion.

    Handles the per-symbol response format returned by the Batch API,
    where the LLM returns a ``suggestions`` array with camelCase keys.

    Args:
        data: Parsed JSON dict from the LLM response.
        symbol_name: Original symbol name for fallback matching.

    Returns:
        NameSuggestion if a rename is suggested, None otherwise.
    """
    # Format 1: {"needs_rename": bool, "suggestion": {...}}
    if "needs_rename" in data:
        if not data.get("needs_rename"):
            return None
        s = data.get("suggestion", {})
        suggested = s.get("suggested_name") or s.get("suggestedName", "")
        if not suggested:
            return None
        return NameSuggestion(
            original_name=s.get("original_name") or s.get("originalName", symbol_name),
            suggested_name=suggested,
            symbol_kind=s.get("symbol_kind") or s.get("symbolKind", ""),
            confidence=s.get("confidence", 0.0),
            rationale=s.get("rationale", ""),
            rules_addressed=s.get("rules_addressed") or s.get("rulesAddressed", []),
        )

    # Format 2: {"suggestions": [{"originalName": ..., "suggestedName": ..., ...}]}
    suggestions_list = data.get("suggestions", [])
    if not suggestions_list:
        return None

    # Find the entry matching our symbol (or take the first one)
    entry = None
    for item in suggestions_list:
        orig = item.get("originalName") or item.get("original_name", "")
        if orig == symbol_name:
            entry = item
            break
    if entry is None:
        entry = suggestions_list[0]

    suggested = entry.get("suggestedName") or entry.get("suggested_name", "")
    if not suggested:
        return None

    return NameSuggestion(
        original_name=entry.get("originalName") or entry.get("original_name", symbol_name),
        suggested_name=suggested,
        symbol_kind=entry.get("symbolKind") or entry.get("symbol_kind", ""),
        confidence=entry.get("confidence", 0.0),
        rationale=entry.get("rationale", ""),
        rules_addressed=entry.get("rulesAddressed") or entry.get("rules_addressed", []),
    )


class LLMError(Exception):
    """Exception raised when LLM operations fail."""

    pass


class LLMClient:
    """Client for interacting with OpenAI's API for naming suggestions."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        verbose: bool = False,
    ):
        """Initialize the LLM client.

        Args:
            api_key: API key. If not provided, uses environment variable.
            model: Model to use. If not provided, uses settings default.
            base_url: Custom base URL for OpenAI-compatible API (e.g., Azure AI Foundry).
            verbose: If True, log prompts and responses at DEBUG level.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.effective_openai_model()
        self.verbose = verbose
        self._total_tokens = 0
        self._request_count = 0

        try:
            self.client = create_openai_client(api_key=self.api_key, base_url=base_url)
        except ValueError as e:
            raise LLMError(str(e)) from e

        logger.debug(f"LLM client initialized with model: {self.model}")

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all requests."""
        return self._total_tokens

    @property
    def request_count(self) -> int:
        """Total number of API requests made."""
        return self._request_count

    def _call_llm(self, prompt: str, max_tokens: int) -> tuple[str, str]:
        """Make a raw LLM API call.

        Args:
            prompt: The prompt to send.
            max_tokens: Maximum output tokens.

        Returns:
            Tuple of (response_content, finish_reason).
            finish_reason is "stop" on normal completion, "length" if truncated.

        Raises:
            LLMError: On API failure or empty response.
        """
        try:
            if self.verbose:
                logger.debug("=" * 60)
                logger.debug("[LLM PROMPT]")
                logger.debug("=" * 60)
                if len(prompt) > 500:
                    logger.debug(prompt[:500] + f"\n... ({len(prompt)} chars total)")
                else:
                    logger.debug(prompt)
                logger.debug("=" * 60)

            self._request_count += 1

            from named.prompts import get_system_prompt

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason or "stop"

            if not content:
                raise LLMError("Empty response from LLM")

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

            return content, finish_reason

        except Exception as e:
            if "LLMError" in str(type(e)):
                raise
            raise LLMError(f"LLM API call failed: {e}") from e

    def get_suggestion(self, prompt: str, max_tokens: int = 4000) -> dict[str, Any]:
        """Send a prompt to the LLM and get a parsed JSON response.

        Args:
            prompt: The prompt to send.
            max_tokens: Maximum tokens in the response.

        Returns:
            Parsed JSON response from the LLM.

        Raises:
            LLMError: If the API call fails or response is invalid.
        """
        try:
            content, _ = self._call_llm(prompt, max_tokens)
            return self._parse_json_response(content)
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse LLM response as JSON: {e}") from e
        except Exception as e:
            if "LLMError" in str(type(e)):
                raise
            raise LLMError(f"LLM API call failed: {e}") from e

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        return json.loads(strip_markdown_fences(content))

    def _is_hallucinated(self, suggested_name: str, symbol_kind: str) -> bool:
        """Return True if the suggestion looks like a method name for a non-method symbol."""
        return is_hallucinated(suggested_name, symbol_kind)

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

    def _analyze_file_chunk(
        self,
        file_path: "Path",
        symbols: list,
        rules_context: str,
        source: str,
    ) -> list["NameSuggestion | None"]:
        """Analyze a chunk of symbols from a file with one LLM call.

        Uses dynamic max_tokens based on symbol count. Checks finish_reason
        and warns if output was truncated. Applies hallucination filter to results.

        Returns a list parallel to `symbols`.
        """
        from pathlib import Path

        from named.prompts.analysis import FileAnalysisPrompt
        from named.rules.models import NameSuggestion

        symbol_dicts = [
            {
                "name": s.name,
                "kind": s.kind,
                "line": s.location.line if s.location else None,
                "annotations": ", ".join(f"@{a}" for a in s.annotations) if s.annotations else "None",
            }
            for s in symbols
        ]

        # Dynamic max_tokens: scale with symbol count, cap at API limit
        max_tokens = min(
            max(_TOKENS_MIN, len(symbols) * _TOKENS_PER_SYMBOL + _TOKENS_BASE),
            _TOKENS_MAX,
        )

        prompt = FileAnalysisPrompt().render(
            file_name=Path(file_path).name,
            file_source=source,
            symbols=symbol_dicts,
            rules_context=rules_context,
        )

        try:
            content, finish_reason = self._call_llm(prompt, max_tokens)
        except Exception as e:
            logger.warning(f"LLM call failed for {Path(file_path).name}: {e}")
            return [None] * len(symbols)

        if finish_reason == "length":
            logger.warning(
                f"Output truncated for {Path(file_path).name} "
                f"({len(symbols)} symbols, max_tokens={max_tokens}). "
                "Some symbols near the end of the list may be missing from results."
            )

        try:
            response = self._parse_json_response(content)
        except json.JSONDecodeError as e:
            logger.warning(
                f"JSON parse failed for {Path(file_path).name}: {e}. "
                "This is likely caused by output truncation."
            )
            return [None] * len(symbols)

        results_raw = response.get("results", [])
        suggestions: list[NameSuggestion | None] = [None] * len(symbols)

        for item in results_raw:
            idx = item.get("symbol_index")
            if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(symbols):
                continue
            if not item.get("needs_rename", False):
                continue

            suggestion_data = item.get("suggestion")
            if not suggestion_data:
                continue

            sym = symbols[idx]
            suggested_name = suggestion_data.get("suggested_name", "")

            # Hallucination filter: fields/parameters must not get method-style names
            if self._is_hallucinated(suggested_name, sym.kind):
                logger.warning(
                    f"Filtered hallucination: {sym.name} ({sym.kind}) → "
                    f"'{suggested_name}' (looks like a method name)"
                )
                continue

            suggestions[idx] = NameSuggestion(
                original_name=sym.name,
                suggested_name=suggested_name,
                symbol_kind=sym.kind,
                confidence=suggestion_data.get("confidence", 0.0),
                rationale=suggestion_data.get("rationale", ""),
                rules_addressed=suggestion_data.get("rules_addressed", []),
            )

        return suggestions

    def analyze_file(
        self,
        file_path: "Path",
        symbols: list,
        rules_context: str,
    ) -> list["NameSuggestion | None"]:
        """Analyze all symbols in a single Java file with one (or more) API call(s).

        Sends the full file source + symbol list to the LLM, gets back
        a JSON array of suggestions indexed to the original symbol list.

        Files with more than _CHUNK_SIZE symbols are automatically split into
        chunks to prevent output truncation and attention dilution.

        Args:
            file_path: Path to the Java file.
            symbols: List of Symbol objects from the file.
            rules_context: Pre-rendered rules context string.

        Returns:
            List of NameSuggestion | None, parallel to input symbols list.
            None means the symbol does not need renaming.
        """
        from pathlib import Path

        try:
            source = Path(file_path).read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return [None] * len(symbols)

        if len(symbols) <= _CHUNK_THRESHOLD:
            return self._analyze_file_chunk(file_path, symbols, rules_context, source)

        # Large file: split into chunks of _CHUNK_SIZE to prevent output truncation
        file_name = Path(file_path).name
        num_chunks = (len(symbols) + _CHUNK_SIZE - 1) // _CHUNK_SIZE
        logger.info(
            f"Large file {file_name}: {len(symbols)} symbols → {num_chunks} chunks of {_CHUNK_SIZE}"
        )

        all_suggestions: list = [None] * len(symbols)
        for chunk_start in range(0, len(symbols), _CHUNK_SIZE):
            chunk = symbols[chunk_start: chunk_start + _CHUNK_SIZE]
            chunk_suggestions = self._analyze_file_chunk(
                file_path, chunk, rules_context, source
            )
            for local_idx, suggestion in enumerate(chunk_suggestions):
                all_suggestions[chunk_start + local_idx] = suggestion

        return all_suggestions

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
