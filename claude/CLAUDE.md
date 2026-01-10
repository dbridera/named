# Claude Code Context

This project was built with Claude Code (Anthropic's CLI for Claude).

## Project Overview

**Named** is an intelligent Java code refactoring system that analyzes Java codebases and suggests naming improvements using AI (OpenAI GPT-4o) based on Clean Code principles adapted for banking industry standards.

## How This Project Was Built

This project was developed through iterative conversations with Claude Code:

1. **MVP Planning (v0.1)**: Designed the architecture, rules module, and core components
2. **Implementation**: Built all modules following the plan
3. **v0.2 Enhancements**: Added progress logging, symbol references, and verbose mode
4. **Documentation**: Created comprehensive docs

## Key Design Decisions

- **javalang parser**: Pure Python Java parsing (no native dependencies)
- **9 naming rules**: Based on Clean Code principles
- **4 guardrails**: Protect API contracts (@JsonProperty, @Path, etc.)
- **Confidence threshold**: 80% minimum for suggestions
- **Report-only mode**: No automatic code changes (safety first)

## Architecture

```
Parse (javalang) → Extract Symbols → Analyze (LLM) → Validate → Export Reports
```

## Running the Project

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Set API key
export NAMED_OPENAI_API_KEY=your-key

# Analyze
named analyze ./samples/banking-app --output ./report

# Verbose mode
named analyze ./samples/banking-app -v --output ./report
```

## Future Improvements

See [PLAN.md](./PLAN.md) for the full roadmap including:
- Tree-sitter for large projects
- 3-layer LLM suggestions
- Batch API support
- Code refactoring engine
- Git-based rollback
