# Named: Intelligent Java Code Refactoring System

## Overview
Python-based CLI tool that analyzes Java codebases, uses OpenAI to suggest naming improvements based on bank policy rules.

---

# v0.2 - Enhanced Logging & Symbol References

## New Features for v0.2

### 1. Progress Logging During LLM Analysis
**Problem**: Users see a spinner but don't know which file/symbol is being analyzed.

**Solution**: Real-time logging showing:
- Current file being processed
- Current symbol name and kind
- Progress counter (e.g., "Analyzing 15/202: CustomerService.getData()")

**Files to modify**:
- [cli.py](src/named/cli.py) - Enhanced progress display with file/symbol details
- [llm_client.py](src/named/suggestions/llm_client.py) - Add callback for progress updates

### 2. Symbol References (Usage Tracking)
**Problem**: Suggestions don't show where symbols are used, making impact assessment difficult.

**Solution**: Track all usages of each symbol:
- Where classes are instantiated
- Where methods are called
- Where fields are accessed

**New file**:
- [reference_finder.py](src/named/analysis/reference_finder.py) - Find all symbol usages

**Files to modify**:
- [extractor.py](src/named/analysis/extractor.py) - Add `references: list[SourceLocation]` to Symbol
- [markdown_exporter.py](src/named/export/markdown_exporter.py) - Show references in report
- [json_exporter.py](src/named/export/json_exporter.py) - Include references in JSON

**Example report output** (line + code snippet):
```markdown
### `bal` → `balance`
- **Kind**: field
- **Location**: Account.java:25
- **Confidence**: 95%
- **Used in 5 locations**:
  - Account.java:45 → `this.bal = amount;`
  - Account.java:62 → `return this.bal;`
  - AccountService.java:30 → `account.getBal()`
  - AccountService.java:45 → `if (account.bal > 0)`
  - TransferService.java:18 → `source.bal - amount`
```

**Reference data structure**:
```python
@dataclass
class SymbolReference:
    file: Path
    line: int
    column: int
    code_snippet: str  # The actual line of code
    usage_type: str    # "read", "write", "call", "instantiate"
```

### 3. Verbose LLM Logging (Optional)
Add `--verbose` flag to log LLM prompts, responses, and token usage.

---

## Implementation Plan for v0.2

### Step 1: Progress Logging
1. Update CLI to show current file + symbol during analysis
2. Use Rich progress bar with dynamic description
3. Show per-file symbol counts

### Step 2: Reference Finder
1. Create `reference_finder.py` with `find_references(symbol, files)`
2. Scan Java files for identifier usages via javalang AST
3. Match usages to symbol definitions

### Step 3: Update Exporters
1. Add references to Symbol dataclass
2. Modify markdown exporter to show "Used in X locations"
3. Modify JSON exporter to include reference list

### Step 4: Verbose Mode
1. Add `--verbose` / `-v` CLI flag
2. Log prompts and responses when enabled

---

## Verification

```bash
# Test progress logging
uv run named analyze samples/banking-app --output ./report

# Verify references appear in report
cat report/report.md | grep "Used in"

# Test verbose mode
uv run named analyze samples/banking-app -v --output ./report
```

---
---

# MVP Scope (v0.1) - COMPLETED

| Aspect | MVP | Future |
|--------|-----|--------|
| **Scale** | <100 files | 500+ files |
| **Parser** | javalang only | + tree-sitter |
| **LLM** | Single-layer, streaming | 3-layer, Batch API |
| **Output** | JSON + Markdown report | + Excel, refactored code |
| **Mode** | Report only (no changes) | Auto-apply changes |
| **Rollback** | N/A | Git-based |

## Key Requirements (MVP)
- **LLM Provider**: OpenAI API (streaming, no batch)
- **Scale**: Small-medium projects (<100 files)
- **Interface**: CLI only
- **Output**: JSON + Markdown report of suggested changes (NO code modification)

---

## Project Structure (MVP - Simplified)

```
named/
├── pyproject.toml
├── src/named/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                  # Single CLI file (Typer)
│   ├── config.py               # Pydantic settings
│   │
│   ├── rules/                  # Rules & Guardrails Module
│   │   ├── __init__.py
│   │   ├── models.py           # NamingRule, Guardrail dataclasses
│   │   ├── naming_rules.py     # 9 naming rules
│   │   ├── guardrails.py       # Blocking conditions
│   │   └── prompt_renderer.py  # Render for LLM
│   │
│   ├── analysis/               # Java Parsing
│   │   ├── __init__.py
│   │   ├── parser.py           # javalang wrapper
│   │   └── extractor.py        # Symbol extraction
│   │
│   ├── suggestions/            # LLM Integration
│   │   ├── __init__.py
│   │   ├── llm_client.py       # OpenAI wrapper
│   │   └── prompt_builder.py   # Build prompts with rules
│   │
│   ├── validation/             # Rule Validation
│   │   ├── __init__.py
│   │   └── validator.py        # Check guardrails + rules
│   │
│   └── export/                 # Output (MVP: JSON + Markdown only)
│       ├── __init__.py
│       ├── json_exporter.py
│       └── markdown_exporter.py
│
└── tests/
    └── fixtures/               # Sample Java files
```

### MVP vs Future Structure

| MVP (v0.1) | Future (v1.0) |
|------------|---------------|
| `cli.py` (single file) | `cli/commands/*.py` |
| `analysis/parser.py` (javalang) | + `tree_sitter_parser.py` |
| No `refactoring/` module | Full refactoring engine |
| No `storage/` module | Caching + checkpoints |
| JSON + Markdown only | + Excel exporter |

---

## Core Dependencies (MVP)

| Library | Purpose | MVP | Future |
|---------|---------|-----|--------|
| `javalang` | Java parsing (pure Python) | Yes | Yes |
| `openai` | LLM API client | Yes | Yes |
| `typer` + `rich` | CLI framework | Yes | Yes |
| `pydantic` | Settings and data validation | Yes | Yes |
| `tree-sitter` | Incremental parsing | No | Yes |
| `networkx` | Dependency graph | No | Yes |
| `xlsxwriter` | Excel export | No | Yes |
| `diskcache` | LLM response caching | No | Yes |
| `gitpython` | Backup/rollback | No | Yes |
| `pyenchant` | Spelling validation | No | Yes |

**MVP dependencies: ~5 packages** vs Full: ~10 packages

---

## Implementation Phases (MVP)

### Phase 1: Static Analysis
- Parse `.java` files using **javalang** (pure Python)
- Extract symbols: classes, methods, fields, parameters, local variables
- Track annotations for guardrail checking

### Phase 2: AI Suggestions (Single Layer)
- Send each symbol with context to OpenAI
- Get naming suggestions with confidence scores
- **No batch API** - simple streaming requests

### Phase 3: Validation
- Check guardrails (blocked annotations, confidence threshold)
- Filter suggestions below 0.80 confidence
- Flag blocked symbols in report

### Phase 4: Report Generation (NO CODE CHANGES)
- **JSON**: Machine-readable full report
- **Markdown**: Human-readable summary

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Parse     │───▶│   Suggest   │───▶│  Validate   │───▶│   Report    │
│  (javalang) │    │  (OpenAI)   │    │ (guardrails)│    │ (JSON + MD) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Future Phases (v1.0+)
- Phase 5: Apply refactoring (tree-sitter for safe edits)
- Phase 6: Verification (compile check, test run)
- Phase 7: Git integration (backup, rollback)

---

## CLI Commands (MVP)

```bash
# Analyze a Java project and generate report
named analyze /path/to/project --output ./report

# Analyze a single file
named analyze /path/to/File.java

# Specify output format
named analyze /path/to/project --format json    # JSON only
named analyze /path/to/project --format md      # Markdown only
named analyze /path/to/project --format all     # Both (default)
```

### Future Commands (v1.0+)
```bash
named refactor /path/to/project    # Apply changes
named rollback /path/to/project    # Undo changes
```

---

## Rules & Guardrails Module

### Architecture Overview

The rules module provides a centralized, reusable definition of all naming rules and guardrails. It serves two purposes:
1. **Validation**: Check if symbols comply with rules
2. **Prompt Generation**: Render rules as LLM context for suggestions

```
┌─────────────────────────────────────────────────────────────┐
│                    rules/registry.py                         │
│         Central registry: get_all_rules(), get_rule(id)     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  naming_rules.py │    │  guardrails.py   │              │
│  │  (9 rules)       │    │  (blockers)      │              │
│  └────────┬─────────┘    └────────┬─────────┘              │
│           │                       │                         │
│           ▼                       ▼                         │
│  ┌─────────────────────────────────────────────┐           │
│  │              models.py                       │           │
│  │  NamingRule, Guardrail, RuleViolation       │           │
│  └─────────────────────────────────────────────┘           │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────┐           │
│  │           prompt_renderer.py                 │           │
│  │  render_for_llm(), render_for_validation()  │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## The 9 Naming Rules

| ID | Rule | Category | Severity |
|----|------|----------|----------|
| R1 | Reveal Intent | Semantic | ERROR |
| R2 | No Disinformation | Semantic | ERROR |
| R3 | Meaningful Distinctions | Semantic | ERROR |
| R4 | Pronounceable Names | Syntactic | WARNING |
| R5 | No Type Encoding | Syntactic | ERROR |
| R6 | No Mental Mapping | Semantic | ERROR |
| R7 | One Word Per Concept | Consistency | WARNING |
| R8 | Context-Aware Naming | Semantic | WARNING |
| R9 | Correct Language | Syntactic | ERROR |

---

## The 4 Guardrails

| ID | Guardrail | Type | Blocked |
|----|-----------|------|---------|
| G1 | Immutable Contracts | Annotation | @JsonProperty, @Column, @SerializedName |
| G2 | Reflection Usage | Pattern | Class.forName, getDeclaredField |
| G3 | Public API | Annotation | @Path, @GET, @POST, @QueryParam |
| G4 | Confidence Threshold | Confidence | < 0.80 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking changes | Git-based rollback, atomic commits per file |
| Reflection breakage | Pattern-based exclusion, `used_in_reflection` flag |
| API contract changes | Exclude all `@Path` annotated elements |
| LLM hallucinations | Confidence threshold (0.80), validation pipeline |
| Performance on large projects | Incremental processing, LLM response caching |
| Spelling false positives | Use pyenchant with en_US dictionary |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Compilation Success | 100% |
| Tests Passing | 100% |
| High-Confidence Suggestions | >= 80% confidence |
| Processing Time | < 1 hour for 500 files |
| False Positive Rate | < 5% |

---

## Future Roadmap (v1.0+)

- [ ] Tree-sitter parser for large projects
- [ ] 3-layer LLM suggestions (Individual → Module → Global)
- [ ] Batch API for 500+ files
- [ ] Code refactoring engine (apply changes)
- [ ] Git-based rollback
- [ ] Excel export
- [ ] CI/CD integration
- [ ] IDE plugins (VS Code, IntelliJ)
