# Named

**Intelligent Java Code Refactoring System for Naming Conventions**

Named analyzes Java codebases and suggests naming improvements based on banking industry code quality rules using AI (OpenAI GPT-4o).

## Features

- **9 Naming Rules**: Based on Clean Code principles adapted for banking industry
- **4 Guardrails**: Automatic protection against breaking changes (@JsonProperty, @Path, etc.)
- **AI-Powered**: Uses OpenAI GPT-4o to generate intelligent naming suggestions
- **Symbol References**: Shows where each symbol is used across the codebase
- **Report Generation**: JSON and Markdown reports with detailed analysis
- **Progress Logging**: Real-time progress with file/symbol information
- **Verbose Mode**: Debug logging for LLM prompts and responses

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/named.git
cd named

# Install with uv
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Quick Start

1. **Set your OpenAI API key:**
   ```bash
   export NAMED_OPENAI_API_KEY=your-key-here
   ```
   Or create a `.env` file:
   ```
   NAMED_OPENAI_API_KEY=your-key-here
   ```

2. **Analyze a project:**
   ```bash
   named analyze ./my-java-project --output ./report
   ```

3. **Review the generated reports** in `./report/`:
   - `report.json` - Machine-readable full report
   - `report.md` - Human-readable summary

## Usage

```bash
# Analyze a Java project
named analyze ./my-java-project --output ./report

# Analyze a single file
named analyze ./src/Main.java

# Dry run (parse only, no LLM calls)
named analyze ./my-project --dry-run

# Verbose mode (show LLM prompts/responses)
named analyze ./my-project -v

# Show all naming rules
named rules

# Show rules in Spanish
named rules --lang es
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--output, -o` | Output directory for reports (default: `./named-report`) |
| `--format, -f` | Output format: `json`, `md`, or `all` (default: `all`) |
| `--model, -m` | OpenAI model to use (default: `gpt-4o`) |
| `--dry-run` | Parse only, skip LLM analysis |
| `--verbose, -v` | Show detailed progress and LLM logs |
| `--exclude, -e` | Glob patterns to exclude |

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Naming Rules](docs/rules.md)
- [Guardrails](docs/guardrails.md)
- [Configuration](docs/configuration.md)

## Example Output

```markdown
### `bal` → `balance`
- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'balance' clearly indicates the account balance
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE
- **Used in 4 location(s)**:
  - Account.java:59 → `this.bal = amt;`
  - Account.java:88 → `return bal;`
```

## Naming Rules

| ID | Rule | Description |
|----|------|-------------|
| R1 | Reveal Intent | Names must explain why the element exists |
| R2 | No Disinformation | Don't use misleading names |
| R3 | Meaningful Distinctions | Avoid generic labels and noise words |
| R4 | Pronounceable | Use pronounceable names |
| R5 | No Type Encoding | Don't include types in names |
| R6 | No Mental Mapping | Avoid single-letter variables |
| R7 | One Word Per Concept | Be consistent with terminology |
| R8 | Context Naming | Use context-appropriate names |
| R9 | Correct Language | Use correct English |

## Guardrails

| ID | Guardrail | Blocked Annotations |
|----|-----------|---------------------|
| G1 | Immutable Contracts | @JsonProperty, @Column, @SerializedName |
| G2 | Reflection Usage | Symbols accessed via reflection |
| G3 | Public API | @Path, @GET, @POST, @QueryParam |
| G4 | Confidence Threshold | Suggestions below 80% confidence |

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=named

# Type check
uv run mypy src/named

# Format code
uv run ruff format src/named
```

## Project Structure

```
named/
├── src/named/
│   ├── cli.py                 # CLI commands (Typer)
│   ├── config.py              # Pydantic settings
│   ├── logging.py             # Logging configuration
│   ├── rules/                 # Naming rules & guardrails
│   │   ├── models.py          # Data models
│   │   ├── naming_rules.py    # 9 naming rules
│   │   ├── guardrails.py      # 4 guardrails
│   │   └── prompt_renderer.py # LLM prompt generation
│   ├── analysis/              # Java parsing
│   │   ├── parser.py          # javalang wrapper
│   │   ├── extractor.py       # Symbol extraction
│   │   └── reference_finder.py # Find symbol usages
│   ├── suggestions/           # LLM integration
│   │   ├── llm_client.py      # OpenAI wrapper
│   │   └── prompt_builder.py  # Prompt construction
│   ├── validation/            # Guardrail validation
│   │   └── validator.py       # Check guardrails
│   └── export/                # Report generation
│       ├── json_exporter.py   # JSON reports
│       └── markdown_exporter.py # Markdown reports
├── samples/                   # Sample Java projects
├── tests/                     # Test suite
└── docs/                      # Documentation
```

## License

MIT
