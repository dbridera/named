# Configuration

Named can be configured via environment variables or a `.env` file.

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NAMED_OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `NAMED_OPENAI_MODEL` | Model to use | `gpt-4o` | No |
| `NAMED_CONFIDENCE_THRESHOLD` | Minimum confidence | `0.80` | No |

## Setting Up

### Option 1: Environment Variable

```bash
export NAMED_OPENAI_API_KEY=sk-proj-your-key-here
```

### Option 2: `.env` File

Create a `.env` file in your project root:

```env
NAMED_OPENAI_API_KEY=sk-proj-your-key-here
NAMED_OPENAI_MODEL=gpt-4o
```

**Important**: Add `.env` to your `.gitignore` to avoid committing secrets.

---

## CLI Options

### analyze Command

```bash
named analyze <path> [OPTIONS]
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output directory for reports | `./named-report` |
| `--format` | `-f` | Output format: `json`, `md`, `all` | `all` |
| `--model` | `-m` | OpenAI model to use | `gpt-4o` |
| `--dry-run` | - | Parse only, skip LLM analysis | `false` |
| `--verbose` | `-v` | Show detailed progress and logs | `false` |
| `--exclude` | `-e` | Glob patterns to exclude | - |

### Examples

```bash
# Basic analysis
named analyze ./src

# Custom output location
named analyze ./src --output ./reports/naming

# JSON only
named analyze ./src --format json

# Use GPT-4 Turbo
named analyze ./src --model gpt-4-turbo

# Exclude test files
named analyze ./src --exclude "**/test/**" --exclude "**/generated/**"

# Verbose mode for debugging
named analyze ./src -v

# Dry run to check parsing
named analyze ./src --dry-run
```

### rules Command

```bash
named rules [OPTIONS]
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--lang` | `-l` | Language: `en` or `es` | `en` |

### Examples

```bash
# Show rules in English
named rules

# Show rules in Spanish
named rules --lang es
```

---

## Output Formats

### JSON (`report.json`)

Machine-readable format with complete data:

```json
{
  "metadata": {
    "project_path": "/path/to/project",
    "generated_at": "2024-01-15T10:30:00",
    "llm_model": "gpt-4o",
    "named_version": "0.1.0"
  },
  "summary": {
    "total_symbols_analyzed": 150,
    "suggestions_generated": 45,
    "valid_suggestions": 42,
    "blocked_suggestions": 3,
    "average_confidence": 0.89,
    "violations_by_rule": {
      "R1_REVEAL_INTENT": 25,
      "R4_PRONOUNCEABLE": 12
    }
  },
  "suggestions": [...],
  "blocked_symbols": [...],
  "all_symbols": [...]
}
```

### Markdown (`report.md`)

Human-readable format for review:

```markdown
# Named Analysis Report

**Generated**: 2024-01-15 10:30:00
**Project**: `/path/to/project`
**Model**: gpt-4o

## Summary

| Metric | Value |
|--------|-------|
| Total Symbols Analyzed | 150 |
| Suggestions Generated | 45 |
| Valid Suggestions | 42 |

## Recommended Changes (High Confidence)

### `data` → `customerData`
- **Kind**: field
- **Confidence**: 95%
- **Rationale**: Reveals intent better
...
```

---

## Logging

### Standard Mode

Shows progress bar with current file and symbol:

```
Account.java: field bal ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45% 0:00:30
```

### Verbose Mode (`-v`)

Shows detailed logs:

```
[DEBUG] Starting analysis of ./src
[DEBUG] LLM client initialized with model: gpt-4o
============================================================
[LLM PROMPT]
============================================================
Analyze the following Java symbol...
============================================================
[LLM RESPONSE]
============================================================
{"needs_rename": true, "suggestion": {...}}
[TOKENS] Prompt: 450, Completion: 120, Total: 570
```

---

## Exclusion Patterns

Use glob patterns to exclude files:

```bash
# Exclude test files
named analyze ./src --exclude "**/test/**"

# Exclude generated code
named analyze ./src --exclude "**/generated/**"

# Multiple exclusions
named analyze ./src \
  --exclude "**/test/**" \
  --exclude "**/generated/**" \
  --exclude "**/*Test.java"
```

Common exclusion patterns:

| Pattern | Description |
|---------|-------------|
| `**/test/**` | All test directories |
| `**/generated/**` | Generated code |
| `**/*Test.java` | Test classes |
| `**/*IT.java` | Integration tests |
| `**/target/**` | Maven build output |
| `**/build/**` | Gradle build output |

---

## Performance Tuning

### For Large Projects

1. **Use exclusions** to skip irrelevant files:
   ```bash
   named analyze ./src --exclude "**/test/**"
   ```

2. **Start with dry-run** to verify parsing:
   ```bash
   named analyze ./src --dry-run
   ```

3. **Analyze subdirectories** separately:
   ```bash
   named analyze ./src/main/java/com/myapp/service
   ```

### Token Usage

- Each symbol uses ~500-1000 tokens
- Monitor costs in verbose mode
- Consider using `gpt-4-turbo` for faster/cheaper analysis

---

## Troubleshooting

### API Key Issues

```
Error: OpenAI API key not provided
```

Solution: Set `NAMED_OPENAI_API_KEY` environment variable or create `.env` file.

### Parse Errors

```
Warning: Failed to parse MyClass.java: ...
```

Solution: Check Java syntax. Named continues with other files.

### Low Confidence Suggestions

Many suggestions blocked by confidence threshold indicates:
- Vague variable names
- Insufficient context
- Consider lowering threshold for review

### Rate Limiting

If you hit OpenAI rate limits:
- Analyze smaller batches
- Add delays between files
- Use a higher-tier API key
