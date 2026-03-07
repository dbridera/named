"""Prompt management for Named.

This module provides all prompts used in the Named system,
separated from business logic for easy modification and testing.

Usage:
    from named.prompts import get_system_prompt, get_rules_context

    system_prompt = get_system_prompt()
    rules_context = get_rules_context(rules, guardrails)
"""

from named.prompts.analysis import FileAnalysisPrompt, get_batch_analysis_prompt, get_rules_context
from named.prompts.schemas import get_name_suggestion_schema, load_schema
from named.prompts.system import get_system_prompt

__all__ = [
    "get_system_prompt",
    "get_rules_context",
    "get_batch_analysis_prompt",
    "FileAnalysisPrompt",
    "get_name_suggestion_schema",
    "load_schema",
]
