# Stakeholder Report — Named

---

## Slide 1 — What We Built

**Named** is a command-line tool that analyzes Java codebases for naming quality and applies AI-assisted renames automatically.

Two commands:
- `named analyze` — scans a project and produces a report of naming issues with suggested fixes
- `named apply` — reads that report and rewrites the source code, updating every reference across all files

Built for the banking domain. Runs against any Java project.

---

## Slide 2 — What It Analyzes

Named parses the **entire Java project** — every class, method, field, constructor, and parameter — and evaluates each name against 9 naming rules based on Clean Code principles:

- Names that don't reveal their purpose (`data`, `tmp`, `info`)
- Misleading names (a `Map` called `accountList`)
- Unpronounceable abbreviations (`prcTxn`, `acctNum`, `bal`)
- Single-letter variables outside loop counters
- Type encoding in names (`phoneString`, `boolIsActive`)
- Meaningless numeric suffixes (`value1`, `value2`)
- Inconsistent terminology across the codebase
- Missing domain context (`address` vs. `billingAddress`)
- Incorrect English or mixed-language naming

The **full source of each file** is analyzed in one pass, so the AI sees field types, sibling fields, and method bodies — not just an isolated name.

---

## Slide 3 — Configurable Guardrails

Guardrails block a rename **before it is ever suggested**, protecting contracts that cannot be changed safely.

| Guardrail | What it blocks |
|-----------|---------------|
| Immutable Contracts | Fields bound to database columns (`@Column`) or JSON serialization (`@JsonProperty`) |
| Public API Contracts | Methods exposed as REST endpoints (`@GET`, `@POST`, `@Path`) |
| Reflection Usage | Elements accessed dynamically at runtime |
| Confidence Threshold | Any AI suggestion below 80% confidence |
| Scope Conflicts | Two symbols being renamed to the same name in the same scope |
| Override Detection | Methods that subclasses or interface implementations depend on |
| Shadow Detection | Renames that would clash with a local variable in the same class |

All guardrails are configurable — new ones can be added per project without changing the analysis logic.

---

## Slide 4 — The Report

After analysis, Named produces two output files:

**JSON report** — machine-readable, one entry per suggestion:
- Original name and suggested name
- Confidence score (0–100%)
- Rationale citing the specific rule violated
- Exact file, line, and column of the declaration
- Every reference to that symbol across the full codebase

**Markdown report** — human-readable summary for review

Both are generated in a single run. The JSON report is the direct input to the apply command.

---

## Slide 5 — Applying Changes Safely

The apply command reads the report and rewrites source files:

- Updates the declaration of each renamed symbol
- Updates every reference across all files in the project
- Handles multiple renames on the same line without conflicts
- Detects apply-time collisions (two suggestions targeting the same name) and skips the lower-priority one
- Creates a **timestamped backup** of all modified files before writing anything
- `--dry-run` previews all changes without modifying any file
- `--output-dir` copies the entire project first — originals stay untouched

---

## Slide 6 — Batch Processing for Cost Savings

Named supports two AI processing modes:

| Mode | Speed | Cost |
|------|-------|------|
| Streaming (default) | Real-time results | Standard API pricing |
| Batch (OpenAI Batch API) | Results in ~24 hours | **50% cheaper** |

Batch mode uses the same model and produces the same quality output — it just runs asynchronously. Suitable for large codebases or scheduled overnight runs.

Named also ships a `named estimate` command that calculates the expected cost of an analysis run **without making any AI calls**.

---

## Slide 7 — Full-File Context: Fewer Calls, Better Results

Early builds sent one AI request per symbol — for a 6-file banking project that meant 322 separate calls.

The current architecture sends one request per file, including the full source code.

| Approach | Requests | Context available to AI |
|----------|----------|------------------------|
| Per-symbol | 322 | Name only |
| Per-file (current) | **6** | Full class: field types, siblings, method bodies |

Result: 54× fewer requests and better suggestions — because the AI understands each symbol in its full context, not in isolation.

---

## Slide 8 — Safety Checks Built Into the Pipeline

Beyond guardrails, Named runs a validation layer on every AI suggestion before it enters the report:

- Verifies suggested names are valid Java identifiers
- Blocks Java reserved words (`class`, `return`, `static`, …)
- Detects scope conflicts across all suggestions in the same file
- Filters AI hallucinations — catches cases where the AI suggests a method-style name for a field or parameter

All checks run locally, before any file is touched.

---

## Slide 9 — Numbers

Banking app demo (6 Java files, ~183 symbols):

| Metric | Value |
|--------|-------|
| AI requests made | 6 |
| Suggestions generated | ~128 |
| Passed all validation and guardrails | ~95 |
| Breaking changes introduced | **0** |
| Automated tests covering the tool | **208** (all passing) |

Most frequent violation: generic names with no intent (`data`, `info`, `tmp`) — across all 6 files.

---

## Slide 10 — Demo

```bash
# Analyze the banking sample project
named analyze samples/banking-app -o demo/report

# Preview all changes (no files modified)
named apply demo/report/report.json --dry-run

# Apply to a safe copy
named apply demo/report/report.json --output-dir demo/applied-src

# Estimate cost before running on a larger project
named estimate my-java-project/
```

---

*Named v0.5 · 208 tests passing*
