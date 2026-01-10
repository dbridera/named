"""LLM suggestions module for Named."""

from named.suggestions.llm_client import LLMClient
from named.suggestions.prompt_builder import build_suggestion_prompt

__all__ = [
    "LLMClient",
    "build_suggestion_prompt",
]
