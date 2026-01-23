# Batch Processing Testing Guide

This document describes how to test the batch processing functionality.

## Automated Tests ✅

We have 14 comprehensive unit tests for the batch client that verify:

- ✅ BatchJob serialization/deserialization
- ✅ Batch request generation with correct JSONL format
- ✅ Symbol prompt building
- ✅ Batch submission to OpenAI API
- ✅ Batch status polling with progression
- ✅ Timeout handling
- ✅ Failure handling
- ✅ Results download
- ✅ Results parsing and symbol mapping
- ✅ Error handling (invalid JSON, missing data, etc.)

**Run tests:**
```bash
pytest tests/test_batch_client.py -v
```

All tests use mocks to avoid actual API calls and costs.

## Manual Testing (Without Real Batch Submission)

### 1. Test CLI Help Output

Verify all commands are registered correctly:

```bash
# Check main help
named --help

# Check analyze command has --mode flag
named analyze --help

# Check batch-status command
named batch-status --help

# Check batch-retrieve command
named batch-retrieve --help
```

**Expected:** All commands show up with proper descriptions and the `--mode` flag appears in analyze command.

### 2. Test Dry Run Mode

Test the CLI without making API calls:

```bash
# Dry run to verify parsing works
named analyze samples/banking-app --dry-run
```

**Expected:** Shows symbol extraction and statistics without calling LLM.

### 3. Test Batch Mode Error Handling

Test batch mode without API key (should fail gracefully):

```bash
# Unset API key temporarily
unset NAMED_OPENAI_API_KEY

# Try batch mode
named analyze samples/banking-app --mode batch

# Expected: Clear error message about missing API key
```

**Expected:** Error message: "NAMED_OPENAI_API_KEY environment variable not set"

### 4. Test Configuration Loading

Verify batch settings are loaded from config:

```python
# Test in Python REPL
from named.config import get_settings

settings = get_settings()
print(f"Batch mode: {settings.batch_mode}")
print(f"Batch size: {settings.batch_size}")
print(f"Poll interval: {settings.batch_poll_interval}")
print(f"Timeout: {settings.batch_timeout}")
```

**Expected:** Default values: False, 50, 60, 90000

## Manual Testing (With Real API - Costs Money!)

⚠️ **WARNING:** The following tests will submit real batch jobs to OpenAI and incur costs (though 50% cheaper than streaming). Only run if you want to test end-to-end with a real API.

### 5. Test Small Batch Submission

Submit a small batch (1-2 files only to minimize cost):

```bash
# Set your API key
export NAMED_OPENAI_API_KEY=sk-proj-your-key-here

# Analyze a single small file in batch mode
named analyze samples/banking-app/src/main/java/com/bank/Account.java \
  --mode batch \
  --output ./test-batch-report

# Expected output:
# - Shows batch mode message
# - Shows cost savings message
# - Submits 1 batch
# - Saves batch_jobs.json file
# - Shows commands to check status
```

**Expected Files:**
- `./test-batch-report/batch_jobs.json` - Contains batch job info

### 6. Test Batch Status Checking

Wait a few seconds, then check status:

```bash
# Check status immediately (should show "validating" or "in_progress")
named batch-status --batch-jobs ./test-batch-report/batch_jobs.json

# Expected output:
# - Shows batch ID
# - Shows status (validating/in_progress)
# - Shows summary
```

### 7. Test Batch Retrieval (After 24 Hours)

After the batch completes (~24 hours later):

```bash
# Check status again (should show "completed")
named batch-status --batch-jobs ./test-batch-report/batch_jobs.json

# Retrieve results
named batch-retrieve \
  --batch-jobs ./test-batch-report/batch_jobs.json \
  --output ./test-batch-results

# Expected output:
# - Downloads results
# - Parses suggestions
# - Generates report.json and report.md
```

**Expected Files:**
- `./test-batch-results/report.json` - JSON report
- `./test-batch-results/report.md` - Markdown report

### 8. Compare Batch vs Streaming Results

Run the same analysis in both modes and compare:

```bash
# Streaming mode (immediate)
named analyze samples/banking-app/src/main/java/com/bank/Account.java \
  --mode streaming \
  --output ./streaming-report

# Batch mode (24h)
named analyze samples/banking-app/src/main/java/com/bank/Account.java \
  --mode batch \
  --output ./batch-report

# After 24h, retrieve batch results
named batch-retrieve \
  --batch-jobs ./batch-report/batch_jobs.json \
  --output ./batch-report

# Compare reports
diff ./streaming-report/report.json ./batch-report/report.json
```

**Expected:** Results should be similar (suggestions, confidence scores, etc.)

## Cost Estimation

For a typical project:

| Project Size | Symbols | Batches | Streaming Cost | Batch Cost | Savings |
|-------------|---------|---------|----------------|------------|---------|
| Small (50)  | 50      | 1       | $0.50          | $0.25      | 50%     |
| Medium (200)| 200     | 4       | $2.00          | $1.00      | 50%     |
| Large (1000)| 1000    | 20      | $10.00         | $5.00      | 50%     |

*Estimates based on gpt-4o pricing: ~1500 tokens per symbol*

## Verification Checklist

Before committing, verify:

- [x] All 65 tests pass (51 existing + 14 new)
- [x] CLI help shows all commands correctly
- [x] `--mode` flag appears in analyze command
- [x] Error handling works (missing API key)
- [x] Configuration loads correctly
- [x] Dry run works
- [ ] (Optional) Real batch submission works
- [ ] (Optional) Real batch status checking works
- [ ] (Optional) Real batch retrieval works

## Troubleshooting

### "Type not yet supported" error
- **Solution:** Upgrade typer: `pip install --upgrade typer`

### "Module not found" errors
- **Solution:** Install in development mode: `pip install -e .`

### Batch never completes
- **Cause:** OpenAI batch API takes up to 24 hours
- **Solution:** Check status periodically with `batch-status` command

### "No output file" error
- **Cause:** Batch not completed yet
- **Solution:** Wait longer and check status first

## Summary

✅ **Unit tests:** All 14 tests pass with mocks
✅ **Integration:** CLI commands work correctly
✅ **Error handling:** Graceful failures for common issues
⚠️ **End-to-end:** Requires real API key and 24h wait time

The implementation is ready for commit. Real end-to-end testing can be done separately by users with API keys.
