# Named — Technical Documentation Report

**Version:** 0.5
**Branch:** feature/apply-command
**Tests:** 208 passing

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [How the Analysis Works](#3-how-the-analysis-works)
4. [Providing Context to LLM Calls](#4-providing-context-to-llm-calls)
5. [The 9 Naming Rules](#5-the-9-naming-rules)
6. [Guardrails — How They Work and How to Configure Them](#6-guardrails--how-they-work-and-how-to-configure-them)
7. [Suggestion Scoring and Confidence](#7-suggestion-scoring-and-confidence)
8. [The Validation Pipeline](#8-the-validation-pipeline)
9. [Applying Changes to Source Code](#9-applying-changes-to-source-code)
10. [Batch Processing and Cost Estimation](#10-batch-processing-and-cost-estimation)
11. [Using the CLI](#11-using-the-cli)

---

## 1. Overview

Named is a command-line tool that performs static analysis of Java codebases to detect naming violations, generates AI-assisted rename suggestions, and applies those suggestions back to the source code. It is designed for the banking domain but can be applied to any Java project.

The system has two primary commands:

- **`named analyze`** — scans a Java project, sends each file to GPT-4o for naming analysis, validates every suggestion through a multi-stage pipeline, and produces a JSON and Markdown report.
- **`named apply`** — reads a report produced by `analyze`, resolves all symbol declarations and references, and rewrites the affected source files with a timestamped backup.

A third auxiliary command, **`named estimate`**, calculates the expected API cost for an analysis run without making any LLM calls.

---

## 2. System Architecture

The tool is structured as a pipeline with six distinct stages:

```
Java project
     │
     ▼
[1] Extraction
    Parse all .java files with javalang AST parser.
    Extract classes, interfaces, enums, methods, constructors, fields, parameters.
     │
     ▼
[2] Pre-filtering
    Separate symbols into "analyzable" vs "blocked".
    Symbols carrying framework annotations (e.g., @Column, @JsonProperty)
    are marked blocked before any LLM call is made.
     │
     ▼
[3] LLM Analysis (per-file)
    Group symbols by file.
    For each file: send full source code + numbered symbol list to GPT-4o.
    Receive a JSON array of suggestions indexed to the symbol list.
     │
     ▼
[4] Validation
    For each suggestion: run annotation guardrails, confidence threshold,
    Java identifier checks, keyword blocklist, scope conflict detection,
    override detection, shadow collision detection.
     │
     ▼
[5] Reference Finding
    For each valid suggestion: find all usages of the original name
    across the entire project (AST-based + text fallback).
     │
     ▼
[6] Report Generation
    Write report.json and report.md to the output directory.
```

---

## 3. How the Analysis Works

### 3.1 Parsing

Named uses the `javalang` library to parse every `.java` file in the target directory into an Abstract Syntax Tree (AST). From this AST it extracts every named symbol in the codebase:

- **Classes, interfaces, enums** — with their `extends` and `implements` relationships
- **Methods** — with return type and parameter types
- **Constructors**
- **Fields** (including detection of `static final` constants)
- **Parameters**

For each symbol, the extractor records:
- Name, kind, file path, line number, and column
- Annotations present on the symbol
- Modifiers (`public`, `static`, `final`, etc.)
- Parent class name
- Package name
- A code context snippet (a few lines surrounding the symbol's declaration)

### 3.2 Pre-filtering

Before any LLM call is made, all extracted symbols are divided into two groups:

1. **Analyzable** — symbols with no blocking annotations, whose names can be evaluated
2. **Blocked** — symbols carrying annotations that form immutable contracts (e.g., `@Column`, `@JsonProperty`, `@Path`); these are recorded in the report as blocked and are never sent to the LLM

This pre-filtering eliminates unnecessary API calls for symbols that would be blocked regardless of what the AI suggests.

### 3.3 Grouped File Analysis

Analyzable symbols are grouped by their source file. For each file, a single LLM call is made containing:
- The complete source code of the file
- A numbered list of the symbols to evaluate
- The full rules context (all 9 naming rules, all guardrails, output format instructions)

This is described in detail in Section 4.

### 3.4 Large File Handling

Files with more than 50 analyzable symbols are automatically split into chunks of 25 symbols each. Each chunk is submitted as a separate LLM call, but still includes the full file source so the AI retains complete context. This prevents output truncation for very large classes while keeping token costs predictable.

If the LLM response is truncated (OpenAI `finish_reason: length`), Named logs a warning identifying which file was affected and which symbols near the end of the list may have been missed. The tool continues processing remaining files normally.

---

## 4. Providing Context to LLM Calls

### 4.1 Why Full-File Context Matters

Early versions of Named sent one API request per symbol, providing only the symbol's name and a brief description. This worked for obvious violations but produced poor results for symbols that are only ambiguous in isolation:

- A field named `amount` could be a transfer amount, a tax amount, or a fee — the correct rename depends on the surrounding class
- A parameter named `a` in a method called `transferFunds(Account a, Double b)` should be renamed to `targetAccount` and `transferAmount` respectively — which the AI can only know by reading the method signature

The current architecture sends the entire Java source file to the LLM in a single prompt, enabling it to:
- See the declared type of each field (e.g., `Double bal` → rename to `currentBalance`)
- Read sibling fields and methods to ensure consistency
- Read method bodies to understand what a parameter is used for
- Check annotations to avoid suggesting renames that would violate guardrails

### 4.2 Prompt Structure

Each LLM call is structured in four parts:

**Part 1 — File source**

The complete Java source code is included verbatim in a fenced code block. The AI uses this as the primary reference for all its analysis.

**Part 2 — Symbols list**

A numbered list of the specific symbols to evaluate, for example:

```
0. `acctNum` — field, line 20
1. `bal` — field, line 26
2. `process` — method, line 46
3. `o` — parameter, line 32
```

**Part 3 — Rules context**

All 9 naming rules are rendered as structured text for the LLM, each with its ID, description, examples of good and bad names, and patterns to detect. The guardrails are also listed, telling the AI which annotation types it must never rename.

**Part 4 — Task instructions**

The prompt instructs the AI to:
- Analyze each listed symbol using the full file source above as context
- Return a JSON array with one entry per symbol index
- Set `needs_rename: false` for symbols with correct names or confidence below 0.80
- Reference specific rule IDs in its rationale

**Part 5 — Response schema**

The expected JSON output format is defined explicitly in the prompt:

```json
{
  "results": [
    {
      "symbol_index": 0,
      "needs_rename": true,
      "analysis": "Brief explanation referencing rule IDs",
      "suggestion": {
        "suggested_name": "accountNumber",
        "confidence": 0.92,
        "rationale": "Violates R4_PRONOUNCEABLE. 'acctNum' is an unpronounceable abbreviation.",
        "rules_addressed": ["R4_PRONOUNCEABLE"]
      }
    },
    {
      "symbol_index": 1,
      "needs_rename": false,
      "analysis": "Name is appropriate",
      "suggestion": null
    }
  ]
}
```

### 4.3 Hallucination Filter

After parsing the LLM response, Named applies a hallucination filter before any suggestion reaches the validation pipeline. The filter blocks cases where the AI suggests a method-style name for a non-method symbol.

Specifically, if a suggested name for a `field` or `parameter` starts with one of the following prefixes followed by an uppercase letter — `get`, `set`, `is`, `has`, `find`, `fetch`, `load`, `save`, `update`, `delete`, `create`, `build` — the suggestion is discarded and a warning is logged.

This caught a real case during testing where the AI suggested `getBalance` as the new name for a parameter (confusing it with a method in the same class).

### 4.4 Dynamic Token Budget

The `max_tokens` for each LLM call is calculated dynamically based on the number of symbols in the chunk, rather than using a fixed value:

```
max_tokens = clamp(symbols × 120 + 500, minimum=1000, maximum=8000)
```

For 25 symbols this gives 3,500 output tokens — enough to describe each symbol's analysis and suggestion without waste. The cap of 8,000 prevents over-spending on very large chunks.

---

## 5. The 9 Naming Rules

Rules are defined in `src/named/rules/naming_rules.py`. Each rule has:
- A unique ID (e.g., `R1_REVEAL_INTENT`)
- A severity level: **ERROR** (blocks valid status) or **WARNING**
- A category: **SEMANTIC**, **SYNTACTIC**, or **CONSISTENCY**
- Detection patterns (regex) and tokens to avoid (substring matching)
- Lists of good and bad name examples
- Exceptions (names that are allowed despite matching a pattern)

All 9 rules are sent to the LLM as part of every prompt so the AI can reason about violations by ID.

---

### R1 — Reveal Intent *(Semantic, ERROR)*

Names must self-explain why the element exists, what it is used for, and how it is used. A reader should not need to consult other code to understand what a variable holds or what a method does.

**Detection patterns:** `data`, `info`, `temp`, `tmp`, `obj`, `val`, `var`, `stuff`, `thing`; methods starting with `doSomething`, `processSomething`, or `handleSomething` (too vague).

**Good examples:** `calculateTotalPrice`, `isUserAuthenticated`, `customerEmailAddress`, `fetchActiveOrders`
**Bad examples:** `data`, `info`, `temp`, `doIt`, `process`, `handle`, `stuff`

---

### R2 — Avoid Disinformation *(Semantic, ERROR)*

Names must not lead to incorrect conclusions. A `Map` named `accountList` is disinformation — a reader assumes it is a `List`. Names that vary only in subtle details (e.g., `account` vs `theAccount`) add noise without meaning.

**Detection patterns:** Names ending in `List`, `Map`, `Set`, or `Array` where the actual type differs.

**Good examples:** `activeUserAccounts`, `pendingOrdersList`, `customerMap`
**Bad examples:** `accountList` when the type is a `Map`; `hp`, `aix` (ambiguous abbreviations)

---

### R3 — Meaningful Distinctions *(Semantic, ERROR)*

When two names are needed for two distinct things, the distinction must carry meaning. Generic suffixes like `Info` and `Data` add no information. Numeric suffixes (`a1`, `a2`) are meaningless.

**Detection patterns:** Names matching `a1`, `b2` patterns; names ending in `Info` or `Data`; names prefixed with articles (`theCustomer`, `aUser`).

**Good examples:** `sourceAccount`, `targetAccount`, `productDetails`, `customerRecord`
**Bad examples:** `a1`, `a2`, `ProductInfo`, `ProductData`, `theCustomer`, `aUser`

---

### R4 — Pronounceable Names *(Syntactic, WARNING)*

Names must be pronounceable. If you cannot say a name aloud in a code review, it is an abbreviation that adds friction. This is particularly common in banking code where domain terms get shortened aggressively.

**Detection patterns:** Names with 4 or more consecutive consonants; names with 5+ consonants anywhere in the word.

**Good examples:** `generationTimestamp`, `customerRecord`, `modificationDate`, `recordCount`
**Bad examples:** `genymdhms`, `cstmrRcrd`, `modDt`, `rcrdCnt`, `prcTxn`, `acctNum`, `bal`

---

### R5 — No Type Encoding *(Syntactic, ERROR)*

Names must not include the type of the variable. This is a Java-specific anti-pattern inherited from older C-style coding (Hungarian notation). Since Java is statically typed, the type is always visible from the declaration.

**Detection patterns:** Names ending in `String`, `Integer`, `Boolean`, `Long`, `Double`; names prefixed with `str`, `int`, `bool`, `lng`, `dbl`; interface names prefixed with `I` (e.g., `ICustomer`).

**Good examples:** `phoneNumber`, `Customer`, `isValid`, `accountBalance`
**Bad examples:** `phoneString`, `ICustomer`, `boolIsValid`, `intCount`, `strName`

---

### R6 — No Mental Mapping *(Semantic, ERROR)*

Single-letter variable names require readers to mentally map the letter to its meaning. This mapping is a constant cognitive load that degrades with time and is invisible to new team members. The only accepted single-letter names are `i`, `j`, and `k` as loop counters in short loops.

**Detection patterns:** Any single-letter name; exceptions: `i`, `j`, `k`.

**Good examples:** `index`, `counter`, `element`, `customer`, `orderItem`
**Bad examples:** `a`, `b`, `x`, `n`, `t`, `e`, `d`

---

### R7 — One Word Per Concept *(Consistency, WARNING)*

The same concept must use the same word throughout the codebase. If some classes are called `XxxMapper` and others `XxxConverter` for the same operation, developers waste time deciding which to use. If some methods use `fetch` and others use `retrieve` and others use `get`, the codebase loses its internal dictionary.

**Detection patterns:** This rule requires project-wide analysis. The LLM checks for inconsistency within the file context it receives.

**Good examples:** `UserMapper` (consistent with all other Mappers), `fetchCustomer` (consistent with `fetchOrder`, `fetchAccount`)
**Bad examples:** `UserMapper` + `OrderConverter` (inconsistent); mixing `fetch`, `retrieve`, and `get` for the same operation

---

### R8 — Context-Aware Naming *(Semantic, WARNING)*

Names should carry their domain context. A field named `address` in a billing class is ambiguous — is it the billing address, the shipping address, or the physical address? Names should also align with design patterns (a Visitor should say "Visitor").

**Detection patterns:** Names ending in bare `Impl` with no meaningful prefix; class names of just `Visitor`, `Factory`, `Strategy` without domain context.

**Good examples:** `AccountVisitor`, `OrderFactory`, `billingAddress`, `shippingAddress`
**Bad examples:** `Visitor` (too generic); `address` (ambiguous); `Factory` (missing context); `impl`

---

### R9 — Correct Language *(Syntactic, ERROR)*

Names must be written in correct English. Mixed Spanish-English naming ("spanglish") creates two problems: non-native English speakers may not understand the Spanish parts, and native Spanish speakers may not recognize the English conventions. Spelling errors in names are also detected.

**Detection patterns:** Names with Spanish suffixes (`-cion`, `-mente`); names starting with Spanish verbs (`obtener`, `calcular`, `procesar`, `guardar`, `enviar`, `crear`, `eliminar`) followed by an uppercase letter.

**Good examples:** `customer`, `invoice`, `payment`, `calculate`, `processOrder`
**Bad examples:** `cliente`, `factura`, `calcular`, `getUsuario`, `procesarPago`

---

## 6. Guardrails — How They Work and How to Configure Them

### 6.1 What Guardrails Are

Guardrails are hard constraints that block a rename before it is ever suggested to the user. Unlike naming rule violations (which describe a quality problem), guardrails describe **situations where renaming would be dangerous regardless of how good the new name is**.

There are three types of guardrails:

- **Annotation-based** — the symbol carries a specific framework annotation that binds its name to an external contract
- **Pattern-based** — the codebase contains patterns indicating the symbol is accessed by name at runtime (e.g., reflection)
- **Confidence-based** — the AI's own confidence score is too low to justify the change

### 6.2 Where Guardrails Run

Guardrails run in two places in the pipeline:

1. **Pre-filtering** (before LLM calls): symbols with blocking annotations are identified and set aside. They are never sent to the LLM, which saves API cost and prevents the AI from wasting effort on symbols that will be blocked anyway.

2. **Post-LLM validation**: after the AI produces suggestions, the full guardrail set is re-evaluated on each suggestion (including the confidence guardrail, which can only run after the AI has responded).

### 6.3 The Four Defined Guardrails

---

#### G1 — Immutable Contracts

**ID:** `G1_IMMUTABLE_CONTRACTS`
**Type:** Annotation-based

Blocks renaming of symbols whose names are bound to external data contracts: database column mappings, JSON serialization fields, XML bindings, and Protocol Buffer fields. Renaming these without updating the external contract (schema, API client, configuration) would break data exchange silently.

**Blocked annotations:**

| Framework | Annotations |
|-----------|-------------|
| Jackson JSON | `@JsonProperty`, `@JsonAlias`, `@JsonSetter`, `@JsonGetter` |
| JPA / Hibernate | `@Column`, `@Table`, `@Entity`, `@Id`, `@JoinColumn` |
| GSON | `@SerializedName` |
| JAXB XML | `@XmlElement`, `@XmlAttribute`, `@XmlRootElement` |
| Protocol Buffers | `@ProtoField` |

**Example:** A field `private String acctNum` annotated with `@Column(name = "account_number")` will be blocked. The `@Column` annotation pins the Java field name to the database column — renaming the field is safe only if done intentionally and with awareness of the mapping. Named blocks it to prevent accidental breakage.

---

#### G2 — Reflection Usage

**ID:** `G2_REFLECTION_USAGE`
**Type:** Pattern-based

Blocks renaming of elements accessed by name at runtime through Java reflection. If code uses `getDeclaredField("fieldName")` to read a specific field, renaming that field breaks the reflection call at runtime — with no compile-time error.

**Blocked patterns** (regex):

```
Class.forName("...")
.getDeclaredField("name")
.getDeclaredMethod("name")
.getMethod("name")
.getField("name")
.getDeclaredFields()
.getDeclaredMethods()
```

---

#### G3 — Public API Contracts

**ID:** `G3_PUBLIC_API`
**Type:** Annotation-based

Blocks renaming of methods and parameters that are exposed as REST API endpoints or bound to HTTP request parameters. Renaming a method annotated with `@GET @Path("/accounts")` would break the URL routing. Renaming a parameter annotated with `@QueryParam("page")` would break query string binding.

**Blocked annotations:**

| Framework | Annotations |
|-----------|-------------|
| JAX-RS | `@Path`, `@GET`, `@POST`, `@PUT`, `@DELETE`, `@PATCH`, `@HEAD`, `@OPTIONS`, `@QueryParam`, `@PathParam`, `@HeaderParam`, `@FormParam`, `@BeanParam`, `@MatrixParam`, `@CookieParam` |
| Spring MVC | `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`, `@RequestParam`, `@PathVariable`, `@RequestBody`, `@ResponseBody` |
| Quarkus | `@ConfigProperty` |

---

#### G4 — Confidence Threshold

**ID:** `G4_CONFIDENCE_THRESHOLD`
**Type:** Confidence-based
**Threshold:** 0.80 (80%)

Blocks any AI suggestion with a confidence score below 0.80. The AI is instructed to self-report its confidence as part of the response schema. If the AI is less than 80% certain that a rename is an improvement, the suggestion is treated as too uncertain to act on.

The AI is given explicit confidence guidelines in the prompt:
- 0.95–1.00: Obvious violation with a clear fix
- 0.85–0.94: Clear violation with a good suggested fix
- 0.80–0.84: Probable violation with a reasonable fix
- Below 0.80: Do not suggest (set `needs_rename: false`)

---

### 6.4 Additional Validation Guardrails (Applied Post-LLM)

Beyond the four core guardrails, the validation pipeline applies four additional programmatic checks:

**G5 — Scope Conflict Detection**
If two different symbols in the same file are both being renamed to the same target name, the lower-confidence suggestion is blocked. This prevents the apply command from introducing a naming collision.

**G6 — Override Conflict Detection**
If a method rename suggestion is for a method that is overridden in a subclass or implemented from an interface, the suggestion is blocked. The tool builds a type hierarchy from all extracted symbols and checks whether renaming the method would leave overriding implementations with a stale name — which would break compilation.

**G7 — Shadow Collision Detection**
If a field rename would introduce a name that already exists as a local variable inside one of the class's methods, the suggestion is blocked. The tool extracts local variable names from all method bodies and checks for collisions before the suggestion reaches the report.

---

### 6.5 How to Add a New Guardrail

All guardrails are defined as `Guardrail` dataclass instances in `src/named/rules/guardrails.py`. Adding a new guardrail requires:

1. Create a new `Guardrail` entry in the `GUARDRAILS` list:

```python
Guardrail(
    id="G5_MY_NEW_GUARDRAIL",
    name="My guardrail (Spanish name)",
    name_en="My Guardrail",
    description="Spanish description.",
    description_en="English description.",
    check_type="annotation",           # "annotation", "pattern", or "confidence"
    blocked_annotations=["MyAnnotation", "AnotherAnnotation"],
)
```

2. If `check_type` is `"pattern"`, provide `blocked_patterns` (list of regex strings) instead of `blocked_annotations`.

3. If `check_type` is `"confidence"`, provide a `threshold` float value instead.

No other code changes are required — the guardrail will automatically be applied in pre-filtering, in the validation pipeline, and rendered in every LLM prompt so the AI is aware of it.

---

### 6.6 How to Adjust the Confidence Threshold

The confidence threshold is defined on the `G4_CONFIDENCE_THRESHOLD` guardrail:

```python
# In src/named/rules/guardrails.py
Guardrail(
    id="G4_CONFIDENCE_THRESHOLD",
    ...
    check_type="confidence",
    threshold=0.80,   # Change this value
)
```

Setting this higher (e.g., 0.90) produces fewer but more certain suggestions. Setting it lower (e.g., 0.70) will include more suggestions but with greater risk of incorrect recommendations.

---

## 7. Suggestion Scoring and Confidence

### 7.1 The Confidence Score

Every suggestion produced by Named carries a **confidence score** — a float between 0.0 and 1.0 representing the AI's certainty that the rename is an improvement. The score is generated by GPT-4o as part of its JSON response; it is not calculated algorithmically by Named itself.

The AI is guided by explicit confidence guidelines in the prompt (see Section 6.3, G4). Named enforces these guidelines by blocking suggestions below 0.80 through guardrail G4.

### 7.2 Scoring Criteria Used by the AI

The AI considers multiple factors when assigning a confidence score:

- **Rule severity**: violations of ERROR-level rules (`R1`, `R2`, `R3`, `R5`, `R6`, `R9`) warrant higher confidence than WARNING-level rules
- **Clarity of violation**: an obvious violation like a single-letter parameter `a` in a non-loop context scores near 1.0; a borderline case with domain-specific context scores lower
- **Quality of the suggested name**: if the AI is confident the original name is bad but cannot determine a clearly correct replacement, it will lower its confidence
- **Context availability**: with full file context, the AI can verify that the suggested name doesn't conflict with existing names in the same class

### 7.3 What Confidence Levels Mean in Practice

| Score range | Meaning | Typical action |
|-------------|---------|----------------|
| 0.95 – 1.00 | Obvious violation, clear fix | Safe to apply automatically |
| 0.85 – 0.94 | Clear violation, good fix | Apply after quick review |
| 0.80 – 0.84 | Probable violation, reasonable fix | Review before applying |
| < 0.80 | Uncertain; set `needs_rename: false` | Not included in report |

### 7.4 Impact Analysis

In addition to the confidence score, Named computes an **impact score** for each suggestion by counting the number of files and references affected by the rename. This is reported alongside each suggestion to help prioritize review:

- **Low impact** (1–3 files): safe to apply, minimal blast radius
- **Medium impact** (4–10 files): review suggested before applying
- **High impact** (10+ files): careful review required

### 7.5 Validation Checks on the Suggested Name

After receiving a suggestion from the AI, Named validates the proposed new name itself through four local checks before it is written to the report:

1. **Java identifier validity**: the name must match the regex `[a-zA-Z_$][a-zA-Z0-9_$]*` — it cannot start with a digit or contain special characters
2. **Java keyword check**: the name must not be a reserved keyword (`class`, `return`, `static`, `final`, `for`, `while`, etc.)
3. **Constant naming convention**: if the symbol kind is `constant`, the name must be in `UPPER_SNAKE_CASE`
4. **Rule self-consistency check**: the suggested name is run through all 9 naming rules to confirm the AI's own suggestion does not violate the same rules it was asked to fix

If any of these checks fail, the suggestion is marked invalid and excluded from the report.

---

## 8. The Validation Pipeline

The full validation pipeline runs on each suggestion received from the LLM, in this order:

```
AI suggestion received
        │
        ▼
Hallucination filter
(method-style name suggested for a field/parameter → discard)
        │
        ▼
Annotation guardrail check (G1, G3)
(symbol carries a blocking annotation → mark blocked)
        │
        ▼
Confidence threshold (G4)
(score < 0.80 → mark blocked)
        │
        ▼
Java identifier validity check
(starts with digit, contains special char → mark invalid)
        │
        ▼
Java keyword check
(reserved word → mark invalid)
        │
        ▼
Constant naming convention check
(constant in camelCase → mark invalid)
        │
        ▼
Rule self-consistency check
(suggested name itself violates a naming rule → mark invalid)
        │
        ▼
[After all suggestions are collected]
        │
        ▼
Scope conflict detection (G5)
(two suggestions collide on same target name in same file → block lower-confidence one)
        │
        ▼
Override conflict detection (G6)
(method is overridden in subclass → block)
        │
        ▼
Shadow collision detection (G7)
(field rename target clashes with a local variable → block)
        │
        ▼
Getter/setter mismatch warning (W_GETTER_SETTER)
(field renamed but paired accessor not renamed → add non-blocking warning)
        │
        ▼
Final ValidationResult
(is_valid, blocked_reasons, rule_violations)
        │
        ▼
Written to report
```

Only suggestions that pass all stages with `is_valid = true` and `blocked = false` are actionable by the apply command.

---

## 9. Applying Changes to Source Code

### 9.1 How the Apply Command Works

The apply command reads the JSON report and extracts all replacement sites — one site for the symbol's declaration and one site for each reference across the project. It then:

1. Groups replacement sites by file
2. For each file, sorts replacement sites by line number (bottom to top) and then by column (right to left within a line), so that earlier positions in the file are not shifted by replacements at later positions
3. Applies each replacement using either column-precise positioning (for references with a known column) or word-boundary matching (for declarations)
4. Writes the modified file content, then creates the backup

### 9.2 Conflict Detection at Apply Time

Before writing anything, the apply engine detects conflicts at the file level: if two different original names are both being renamed to the same target name within the same file, the lower-priority one is blocked and skipped. This is a safety net that catches edge cases the validation pipeline may not have anticipated.

### 9.3 Backup and Output Options

- **Default**: files are modified in place; a timestamped backup of each modified file is created in `.named-backup/<timestamp>/`
- **`--output-dir`**: the entire project is copied to a new directory first; renames are applied to the copy; originals are never modified; no backup is created since the originals remain intact
- **`--dry-run`**: the apply engine computes all changes and displays a diff-style preview but writes nothing to disk
- **`--no-backup`**: disables backup creation (not recommended except in CI where the source is version-controlled)

### 9.4 Reference Finding

For each symbol that needs renaming, Named finds all references using two strategies:

1. **AST-based** — the `javalang` AST is queried for method invocations, field accesses, class usages, and import statements; this gives exact file, line, and column coordinates
2. **Text-based fallback** — for symbols not covered by AST queries, a word-boundary regex search is performed on the raw source text; matches inside string literals and comments are excluded using a zone-detection algorithm

---

## 10. Batch Processing and Cost Estimation

### 10.1 Streaming Mode (Default)

By default, all LLM calls are made synchronously using the standard OpenAI Chat Completions API. Results appear in real time as each file is analyzed. This is the recommended mode for interactive use and demos.

### 10.2 Batch Mode

For large codebases or cost-sensitive workflows, Named supports the OpenAI Batch API. In batch mode:

- All LLM requests for the entire project are bundled into a single batch job
- The batch job is submitted to OpenAI and a job ID is returned immediately
- OpenAI processes the batch asynchronously (typically within 24 hours)
- Named polls for completion and downloads results when ready

**Cost saving:** The OpenAI Batch API charges 50% of standard pricing for the same models and quality. For a large Java project generating hundreds of API calls, this can represent significant savings.

### 10.3 Cost Estimation

The `named estimate` command analyzes a project and calculates the expected token usage and cost for a full analysis run, without making any LLM calls:

```bash
named estimate samples/banking-app
```

Output includes:
- Number of symbols that would be analyzed
- Estimated input and output token counts
- Expected cost at standard pricing
- Expected cost at batch pricing

This allows teams to budget for analysis before committing to a run.

---

## 11. Using the CLI

### 11.1 Analyze

```bash
# Basic usage
named analyze path/to/java/project -o output/directory

# Choose model (default: gpt-4o)
named analyze path/to/project -o ./report --model gpt-4o-mini

# Verbose: show each rename as it is suggested
named analyze path/to/project -o ./report --verbose

# Output format: json, md, or all (default: all)
named analyze path/to/project -o ./report --format json
```

Output files:
- `output/directory/report.json` — machine-readable, input to apply command
- `output/directory/report.md` — human-readable summary

### 11.2 Apply

```bash
# Preview all changes without modifying files
named apply report/report.json --dry-run

# Apply to a safe copy (originals untouched)
named apply report/report.json --output-dir renamed-project/

# Apply in place (with backup, default)
named apply report/report.json

# Apply in place without backup
named apply report/report.json --no-backup

# Raise confidence threshold for this apply (only high-confidence renames)
named apply report/report.json --min-confidence 0.90 --output-dir renamed-project/

# Verbose: print every rename applied
named apply report/report.json --output-dir renamed-project/ --verbose
```

### 11.3 Estimate

```bash
named estimate path/to/java/project
named estimate path/to/java/project --model gpt-4o-mini
```

---

## Appendix — Key File Locations

| Component | File |
|-----------|------|
| Naming rules (9 rules) | `src/named/rules/naming_rules.py` |
| Guardrails (G1–G4) | `src/named/rules/guardrails.py` |
| Data models (NameSuggestion, Guardrail, etc.) | `src/named/rules/models.py` |
| Symbol extraction (AST parser) | `src/named/analysis/extractor.py` |
| Type hierarchy (override detection) | `src/named/analysis/hierarchy.py` |
| Reference finding | `src/named/analysis/reference_finder.py` |
| Validation pipeline | `src/named/validation/validator.py` |
| LLM client + chunking + hallucination filter | `src/named/suggestions/llm_client.py` |
| Prompt templates | `src/named/prompts/analysis.py` |
| System prompt | `src/named/prompts/system.py` |
| Apply engine | `src/named/apply/rename_engine.py` |
| Report loader | `src/named/apply/report_loader.py` |
| CLI entry point | `src/named/cli.py` |
