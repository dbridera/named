# Changelog

## [0.2.0] - 2026-03-18

### Fixed

- **Batch processing rewritten to match streaming mode**: batch now uses per-file prompts (`FileAnalysisPrompt`) instead of per-symbol, sending full Java source code for better context. Both modes produce consistent results — tested side-by-side with Account.java (9/13 suggestions identical, differences only from LLM non-determinism on ambiguous names like single-letter variables).
- **Batch response parsing**: strip markdown fences, handle per-file JSON format with `file_map` for index mapping.
- **`apply` command works identically** with reports from both streaming and batch modes.
- **Hallucination filter applied to batch path**: blocks method-style names (`getX`, `setX`, `isX`) suggested for fields, parameters, and constants.
- **All 4 post-validation checks added to batch**: scope conflicts, override conflicts, shadow collisions, getter/setter mismatches — previously only applied to streaming.
- **Symbol metadata preserved in `batch_jobs.json`**: `extends_type`, `implements_types`, `parameter_types`, `method_locals` are now stored so post-validation (override/shadow checks) works correctly.
- **Sequential batch submission with auto-retry** on token limit errors.
- **Handle `finalizing` batch status** as in-progress instead of unknown.

### Added

- **Azure Workload Identity authentication** (`AzureOpenAI` + `DefaultAzureCredential` + `get_bearer_token_provider`) for AKS deployments with managed identity. Activates only when `AZURE_OPENAI_ENDPOINT` is set — zero impact on existing OpenAI or Foundry-with-API-key workflows. Three auth modes now supported:
  - OpenAI direct (API key)
  - Azure AI Foundry (API key + base_url)
  - Azure Workload Identity (managed identity, no API key needed)

- **Azure configuration fields** in `config.py`:
  - `AZURE_OPENAI_ENDPOINT` — Azure OpenAI resource URL
  - `AZURE_OPENAI_DEPLOYMENT_NAME` — deployment name (replaces model name)
  - `AZURE_CLIENT_ID` — managed identity client ID
  - `AZURE_OPENAI_API_VERSION` — API version (default `2025-01-01-preview`)
  - `AZURE_OPENAI_BATCH_DEPLOYMENT_NAME` — separate deployment for batch (globalbatch SKU)
  - `effective_openai_model()` — returns deployment name if Azure, else `openai_model`
  - `effective_batch_model()` — returns batch deployment name, falls back to `effective_openai_model()`

- **Batch quota management**:
  - Files auto-expire after 3 days (`expires_after` on upload, `output_expires_after` on batch create) — prevents hitting the 500-file quota limit
  - File upload uses `io.BytesIO` with `.jsonl` filename (required by Azure, compatible with OpenAI)

- **New CLI commands**:
  - `named config` — display current auth mode, endpoints, models, and batch settings without exposing secrets. Useful for debugging Azure configuration in production.
  - `named batch-cancel` — cancel batch jobs and optionally delete input files to free quota. Accepts `--batch-jobs` (JSON) or `--ids-file` (one batch_id per line). Supports `--no-delete-files` flag.
  - `named files-cleanup` — list and delete files from the API to manage the 500-file quota. Supports `--dry-run` and `--purpose` filter.

- **New `BatchAnalysisClient` methods**:
  - `get_batch(batch_id)` — retrieve full batch job details
  - `cancel_batch(batch_id)` — cancel an in-progress batch job
  - `delete_file(file_id)` — delete a file from the API
  - `list_files(purpose, limit)` — list files with optional purpose filter

- **Shared logic extracted to `suggestions/common.py`**:
  - Constants: `METHOD_PREFIXES`, `CHUNK_THRESHOLD`, `CHUNK_SIZE`, `TOKENS_PER_SYMBOL`, `TOKENS_BASE`, `TOKENS_MAX`, `TOKENS_MIN`
  - `strip_markdown_fences()` — clean LLM response content
  - `is_hallucinated()` — detect method-style names for non-method symbols
  - `enrich_suggestion()` — shared post-LLM processing (references, impact, validation)
  - `post_validate_results()` — all cross-suggestion validation checks
  - `export_reports()` — unified JSON/Markdown report generation
  - `reconstruct_symbol()` — rebuild Symbol objects from serialized batch data

- **`parse_llm_response()`** in `llm_client.py` — converts batch/LLM response dict into `NameSuggestion`, handling both `needs_rename` format and `suggestions` array format, with hallucination filtering.

- **`run_id` tracking** in `batch_jobs.json` — UUID per batch run for identification. Legacy list format still supported via `_load_batch_jobs()`.

- **`azure-identity>=1.15.0`** added to dependencies (lazily imported, only when Azure path is used).

- **28 new tests** (236 total passing):
  - `test_cli_commands.py` — 15 tests for `config`, `batch-cancel`, `files-cleanup`
  - `test_batch_client.py` — 5 tests for `get_batch`, `cancel_batch`, `delete_file`, `list_files`
  - `test_client_factory.py` — 2 tests for Azure Workload Identity path and fallback
  - Additional tests for per-file batch processing, hallucination filtering, and post-validation

### Changed

- `client_factory.py` returns `Union[OpenAI, AzureOpenAI]` — Azure path takes priority when `AZURE_OPENAI_ENDPOINT` is set, otherwise falls back to API key auth.
- `LLMClient` uses `settings.effective_openai_model()` instead of `settings.openai_model` for default model resolution.
- Error messages throughout CLI updated to mention both API key and Azure Workload Identity auth options.
- Batch submission saves `batch_jobs.json` incrementally after each successful submit (not all at once), so partial runs can be cancelled.
- `all_symbols` (including blocked) stored in batch run data for report parity with streaming mode.

### Removed

- Dead code: `_export_batch_json()`, `_build_markdown_report_from_batch()` — replaced by shared `export_reports()`.
- Duplicated constants and utilities between `llm_client.py` and `batch_client.py` — now in `common.py`.

## [0.1.0] - 2026-03-10

### Added

- Initial release: Java naming convention analyzer with 9 naming rules based on Clean Code principles
- 4 guardrails for protecting API contracts, framework conventions, and standard patterns
- OpenAI GPT-4o integration with streaming and batch processing modes
- Azure AI Foundry support via configurable `base_url`
- Per-file LLM batching: one API call per Java file with full source context
- Dynamic `max_tokens` scaling based on symbol count with chunking for large files
- Impact analysis: reference tracking across files, risk level assessment
- `named analyze` — main analysis command with streaming and batch modes
- `named apply` — apply renames to source files with conflict detection
- `named estimate` — pre-analysis cost and token budgeting
- `named batch-status` — check batch job progress
- `named batch-retrieve` — download and process batch results
- `named rules` — display naming rules and guardrails
- Cross-suggestion validation: scope conflicts, override conflicts, shadow collisions, getter/setter mismatches
- JSON and Markdown report generation
- Docker support with multi-stage build
- 208 tests passing
