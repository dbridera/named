# Named

**Intelligent Java Code Refactoring System for Naming Conventions**

Named analyzes Java codebases and suggests naming improvements based on banking industry code quality rules using AI (OpenAI GPT-4o).

## Features

- **9 Naming Rules**: Based on Clean Code principles adapted for banking industry
- **4 Guardrails**: Automatic protection against breaking changes (@JsonProperty, @Path, etc.)
- **AI-Powered**: Uses OpenAI GPT-4o to generate intelligent naming suggestions
- **Dual Processing Modes**: Real-time streaming or async batch processing (50% cost savings)
- **Symbol References**: Shows where each symbol is used across the codebase
- **Impact Analysis**: Risk assessment for each rename (low/medium/high)
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

### Streaming Mode (Default)

Real-time analysis with immediate results:

```bash
# Analyze a Java project (streaming mode)
named analyze ./my-java-project --output ./report

# Analyze a single file
named analyze ./src/Main.java

# Dry run (parse only, no LLM calls)
named analyze ./my-project --dry-run

# Verbose mode (show LLM prompts/responses)
named analyze ./my-project -v
```

### Batch Mode (50% Cost Savings)

Asynchronous processing for large codebases (~24 hour latency):

```bash
# Submit batch analysis job
named analyze ./my-java-project --mode batch --output ./report

# Check batch job status
named batch-status --batch-jobs ./report/batch_jobs.json

# Retrieve results when completed
named batch-retrieve --batch-jobs ./report/batch_jobs.json --output ./report
```

**When to use batch mode:**
- Large codebases (500+ files, 1000+ symbols)
- Scheduled/overnight analysis
- Cost-sensitive projects (50% discount)
- Non-time-critical analysis

**Cost comparison (1000 symbols):**
- Streaming: ~$10-15 (full price)
- Batch: ~$5-7.50 (50% discount)

### Other Commands

```bash
# Show all naming rules
named rules

# Show rules in Spanish
named rules --lang es
```

### CLI Options

#### `named analyze` Options

| Option | Description |
|--------|-------------|
| `--output, -o` | Output directory for reports (default: `./named-report`) |
| `--format, -f` | Output format: `json`, `md`, or `all` (default: `all`) |
| `--model, -m` | OpenAI model to use (default: `gpt-4o`) |
| `--mode` | Processing mode: `streaming` (realtime) or `batch` (async, 50% cost) (default: `streaming`) |
| `--dry-run` | Parse only, skip LLM analysis |
| `--verbose, -v` | Show detailed progress and LLM logs |
| `--exclude, -e` | Glob patterns to exclude |

#### `named batch-status` Options

| Option | Description |
|--------|-------------|
| `--batch-jobs` | Path to batch_jobs.json file (required) |
| `--verbose, -v` | Show detailed output |

#### `named batch-retrieve` Options

| Option | Description |
|--------|-------------|
| `--batch-jobs` | Path to batch_jobs.json file (required) |
| `--output, -o` | Output directory for analysis results (default: `./named-report`) |
| `--format, -f` | Output format: `json`, `md`, or `all` (default: `all`) |
| `--verbose, -v` | Show detailed output |

## Batch Processing Workflow

Here's a complete example of using batch mode for a large codebase:

### Step 1: Submit Batch Job

```bash
# Analyze your project in batch mode
named analyze ./my-large-project --mode batch --output ./batch-report
```

**Output:**
```
[Batch mode] Processing will take ~24 hours
[Cost savings] 50% discount vs streaming

Submitting 5 batch(es) of up to 50 symbols each...

  [OK] Batch 1 submitted (batch_id=batch_abc123...)
  [OK] Batch 2 submitted (batch_id=batch_def456...)
  [OK] Batch 3 submitted (batch_id=batch_ghi789...)
  [OK] Batch 4 submitted (batch_id=batch_jkl012...)
  [OK] Batch 5 submitted (batch_id=batch_mno345...)

[OK] All batches submitted!

Batch jobs saved to: batch-report/batch_jobs.json

To check status later, run:
  named batch-status --batch-jobs batch-report/batch_jobs.json
```

### Step 2: Check Status (Periodically)

```bash
# Check if batches have completed
named batch-status --batch-jobs batch-report/batch_jobs.json
```

**Output (while processing):**
```
Checking 5 batch job(s)...

[PENDING] batch_abc123...: In Progress
[PENDING] batch_def456...: Validating
[PENDING] batch_ghi789...: Validating
[PENDING] batch_jkl012...: Validating
[PENDING] batch_mno345...: Validating

Summary:
  Completed: 0
  In Progress: 5
  Failed: 0

Some batches still processing. Check again later.
```

**Output (when completed, ~24 hours later):**
```
Checking 5 batch job(s)...

[OK] batch_abc123...: Completed
[OK] batch_def456...: Completed
[OK] batch_ghi789...: Completed
[OK] batch_jkl012...: Completed
[OK] batch_mno345...: Completed

Summary:
  Completed: 5
  In Progress: 0
  Failed: 0

All batches completed!

To retrieve results, run:
  named batch-retrieve --batch-jobs batch-report/batch_jobs.json
```

### Step 3: Retrieve Results

```bash
# Download and process the results
named batch-retrieve --batch-jobs batch-report/batch_jobs.json --output batch-report
```

**Output:**
```
Downloading results from batch_abc123...
  Parsed 50 results
  [OK] Retrieved 50 results from batch batch_abc123

Downloading results from batch_def456...
  Parsed 50 results
  [OK] Retrieved 50 results from batch batch_def456

...

Generating reports...
  - JSON: batch-report/report.json
  - Markdown: batch-report/report.md

Results Summary:
  - Total suggestions: 202
  - Valid suggestions: 185
  - Blocked by guardrails: 17
  - High confidence (>=85%): 142

Batch analysis complete!
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Naming Rules](docs/rules.md)
- [Guardrails](docs/guardrails.md)
- [Configuration](docs/configuration.md)
- [Batch Processing Testing](BATCH_TESTING.md)

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

## Configuration

Batch processing can be configured via environment variables in `.env`:

```bash
# Batch processing settings (optional)
NAMED_BATCH_MODE=false           # Enable batch mode by default
NAMED_BATCH_SIZE=50              # Symbols per batch (1-100)
NAMED_BATCH_POLL_INTERVAL=60     # Seconds between status checks
NAMED_BATCH_TIMEOUT=90000        # Max wait time (25 hours)
```

Or use the `batch_settings.yaml` file to customize batch behavior.

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
│   │   ├── reference_finder.py # Find symbol usages
│   │   └── impact_analyzer.py # Rename impact analysis
│   ├── suggestions/           # LLM integration
│   │   ├── llm_client.py      # OpenAI wrapper
│   │   ├── batch_client.py    # Batch API client (NEW)
│   │   └── prompt_builder.py  # Prompt construction
│   ├── validation/            # Guardrail validation
│   │   └── validator.py       # Check guardrails
│   └── export/                # Report generation
│       ├── json_exporter.py   # JSON reports
│       └── markdown_exporter.py # Markdown reports
├── samples/                   # Sample Java projects
├── tests/                     # Test suite (65 tests)
├── docs/                      # Documentation
└── batch_settings.yaml        # Batch processing config
```

## License

MIT
