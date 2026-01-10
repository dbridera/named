# Architecture Overview

Named is a Python-based CLI tool that analyzes Java codebases and suggests naming improvements using AI. This document explains the system architecture and data flow.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Named CLI                                       │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  Parse   │───▶│ Extract  │───▶│ Analyze  │───▶│ Validate │───▶│ Export ││
│  │(javalang)│    │ Symbols  │    │  (LLM)   │    │(guardrails)│   │(reports)││
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. CLI Layer (`cli.py`)

The entry point for the application using Typer framework.

**Commands:**
- `named analyze <path>` - Analyze Java files and generate reports
- `named rules` - Display all naming rules and guardrails

**Key Features:**
- Progress bar with real-time file/symbol information
- Verbose mode for debugging LLM interactions
- Multiple output formats (JSON, Markdown)

### 2. Analysis Module (`analysis/`)

Responsible for parsing Java files and extracting symbols.

#### Parser (`parser.py`)
- Wraps the `javalang` library for Java parsing
- Handles parse errors gracefully
- Finds Java files in directories

#### Extractor (`extractor.py`)
- Extracts symbols from the AST:
  - Classes, interfaces, enums
  - Methods, constructors
  - Fields, constants
  - Parameters
- Captures annotations, modifiers, and context

#### Reference Finder (`reference_finder.py`)
- Finds all usages of a symbol across the codebase
- Tracks usage type: read, write, call, instantiate
- Provides code snippets for each reference

### 3. Rules Module (`rules/`)

Defines the naming rules and guardrails.

#### Models (`models.py`)
Core data structures:
- `NamingRule` - Definition of a naming rule
- `Guardrail` - Definition of a blocking condition
- `NameSuggestion` - LLM-generated suggestion
- `RuleViolation` - Detected rule violation

#### Naming Rules (`naming_rules.py`)
9 naming rules based on Clean Code principles:
- Semantic rules (R1-R3): Intent, meaning
- Syntactic rules (R4-R5): Pronunciation, encoding
- Consistency rules (R6-R9): Project-wide patterns

#### Guardrails (`guardrails.py`)
4 blocking conditions:
- G1: Immutable contracts (serialization)
- G2: Reflection usage
- G3: Public API endpoints
- G4: Confidence threshold

#### Prompt Renderer (`prompt_renderer.py`)
- Renders rules as context for LLM prompts
- Supports bilingual output (English/Spanish)

### 4. Suggestions Module (`suggestions/`)

Handles LLM integration for generating suggestions.

#### LLM Client (`llm_client.py`)
- OpenAI API wrapper
- Handles response parsing
- Tracks token usage
- Supports verbose logging

#### Prompt Builder (`prompt_builder.py`)
- Constructs prompts with rules context
- Includes symbol information and code context

### 5. Validation Module (`validation/`)

#### Validator (`validator.py`)
- Checks suggestions against guardrails
- Pre-filters blocked symbols
- Validates suggested names don't violate rules

### 6. Export Module (`export/`)

Generates reports in different formats.

#### JSON Exporter (`json_exporter.py`)
- Machine-readable full report
- Includes all symbols and suggestions
- Summary statistics

#### Markdown Exporter (`markdown_exporter.py`)
- Human-readable summary
- High-confidence recommendations
- Reference locations

## Data Flow

### 1. Parsing Phase
```
Java Files → javalang Parser → AST → Symbol Extractor → List[Symbol]
```

### 2. Pre-filtering Phase
```
List[Symbol] → Guardrail Check → (Analyzable, Blocked)
```

### 3. Analysis Phase
```
Symbol → Prompt Builder → LLM → NameSuggestion
       ↓
Reference Finder → List[SymbolReference]
```

### 4. Validation Phase
```
NameSuggestion → Guardrail Validator → ValidationResult
```

### 5. Export Phase
```
List[ValidationResult] → JSON/Markdown Exporter → Reports
```

## Key Data Models

### Symbol
```python
@dataclass
class Symbol:
    name: str                    # Symbol name
    kind: SymbolKind            # class, method, field, etc.
    location: SourceLocation    # File, line, column
    annotations: list[str]      # @JsonProperty, etc.
    modifiers: list[str]        # public, static, final
    parent_class: str | None    # Containing class
    context: str                # Code snippet
    references: list            # Usage locations
```

### NameSuggestion
```python
@dataclass
class NameSuggestion:
    original_name: str          # Current name
    suggested_name: str         # Proposed name
    symbol_kind: str            # Symbol type
    confidence: float           # 0.0 - 1.0
    rationale: str              # Why this is better
    rules_addressed: list[str]  # Which rules it fixes
    references: list            # Usage locations
    location: dict              # Symbol location
```

### SymbolReference
```python
@dataclass
class SymbolReference:
    file: Path                  # File containing usage
    line: int                   # Line number
    column: int                 # Column number
    code_snippet: str           # Actual code line
    usage_type: UsageType       # read, write, call, etc.
```

## Configuration

Configuration is handled via environment variables and Pydantic settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `NAMED_OPENAI_API_KEY` | OpenAI API key | Required |
| `NAMED_OPENAI_MODEL` | Model to use | `gpt-4o` |
| `NAMED_CONFIDENCE_THRESHOLD` | Minimum confidence | `0.80` |

## Error Handling

- **Parse errors**: Logged and skipped, continues with other files
- **LLM errors**: Logged with warning, symbol skipped
- **Invalid responses**: JSON parsing with fallback handling

## Performance Considerations

- Symbols are processed sequentially (no batch API in MVP)
- Reference finding scans all files per symbol with suggestion
- Progress bar provides ETA estimates

## Future Enhancements

See the [roadmap](../README.md#future-v10) for planned features:
- Tree-sitter for incremental parsing
- Batch API for large codebases
- Code refactoring engine
- Git-based rollback
