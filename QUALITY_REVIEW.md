# Code Quality Review - Named v0.3 Impact Analysis

**Review Date**: 2026-01-14
**Overall Score**: 7.5/10
**Status**: ✅ Ruff fixed, ⚠️ 3 Critical + 3 High priority issues to address

---

## Quick Summary

✅ **Completed**:
- Ruff linting: 43 issues auto-fixed
- Code formatting: 14 files reformatted
- All 46 tests passing

⚠️ **Action Required** (Before Commit):
- 3 CRITICAL issues (~30 min)
- 3 HIGH priority issues (~30 min)

---

## Critical Issues (Must Fix)

### 1. Missing None Check in CLI ⏰ 5 min
**File**: `src/named/cli.py:261-263`

**Problem**: Empty refs list → no impact_analysis computed → None instead of zero-impact object

**Fix**:
```python
# Remove this check:
if refs:  # ❌ WRONG
    suggestion.impact_analysis = compute_rename_impact(refs)

# Always compute:
suggestion.impact_analysis = compute_rename_impact(refs)  # ✅ CORRECT
```

---

### 2. Type Confusion in aggregate_references_by_file ⏰ 2 min
**File**: `src/named/analysis/impact_analyzer.py:77-84`

**Problem**: Dead code - `UsageType` is Literal, not Enum (no `.value` attribute)

**Fix**:
```python
# Remove this:
"usage_type": ref.usage_type.value if hasattr(ref.usage_type, "value") else str(ref.usage_type),  # ❌

# Use this:
"usage_type": ref.usage_type,  # ✅ Already a string from Literal
```

---

### 3. Hardcoded Risk Thresholds ⏰ 10 min
**File**: `src/named/analysis/impact_analyzer.py:49-54`

**Problem**: Magic numbers (4, 11) not documented

**Fix**: Extract to constants:
```python
# Risk level thresholds
MEDIUM_RISK_MIN_FILES = 4   # Medium risk: 4-10 files
HIGH_RISK_MIN_FILES = 11    # High risk: 11+ files

def calculate_risk_level(file_count: int) -> str:
    """Calculate risk level based on affected file count.

    Thresholds:
    - Low: 1-3 files
    - Medium: 4-10 files
    - High: 11+ files
    """
    if file_count >= HIGH_RISK_MIN_FILES:
        return "high"
    elif file_count >= MEDIUM_RISK_MIN_FILES:
        return "medium"
    return "low"
```

---

## High Priority Issues (Should Fix)

### 4. Missing Error Handling ⏰ 15 min
**File**: `src/named/validation/validator.py:39-42`

**Problem**: Silent fallback hides serialization errors

**Fix**: Add try-except with logging:
```python
if self.suggestion.references:
    refs_dicts = []
    for ref in self.suggestion.references:
        try:
            refs_dicts.append(ref.to_dict())
        except Exception as e:
            logger.warning(f"Failed to serialize reference: {e}")
            refs_dicts.append({"error": str(type(e).__name__)})
    suggestion_dict["references"] = refs_dicts
```

---

### 5. Magic Numbers in Markdown Exporter ⏰ 10 min
**File**: `src/named/export/markdown_exporter.py`

**Problem**: Hardcoded display limits (5, 10, 20, 6, 3, 60)

**Fix**: Extract to module constants at top of file:
```python
# Display configuration
MAX_HIGH_IMPACT_ITEMS = 5
MAX_MEDIUM_IMPACT_ITEMS = 10
MAX_LOW_IMPACT_ITEMS = 20
MAX_FILES_PER_ITEM = 6
MAX_REFS_PER_FILE = 3
MAX_SNIPPET_LENGTH = 60
```

---

### 6. Type Safety - Use Literal for RiskLevel ⏰ 5 min
**File**: `src/named/analysis/impact_analyzer.py:15-22`

**Fix**: Add type hint:
```python
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]

@dataclass
class RenameImpact:
    ...
    risk_level: RiskLevel  # ✅ Type-safe instead of str
```

---

## Implementation Timeline

### Phase 1: Critical Fixes (30 min) 🔴
1. Fix CLI None check (5 min)
2. Fix type confusion (2 min)
3. Extract risk threshold constants (10 min)
4. Add RiskLevel type (5 min)
5. Run tests (5 min)

### Phase 2: High Priority (30 min) 🟠
6. Add error handling to serialization (15 min)
7. Extract markdown export constants (10 min)
8. Run full test suite (5 min)

### Phase 3: Optional Tests (30 min) 🟡
9. Add edge case tests (20 min)
10. Run coverage report (10 min)

**Total Time**: 1-1.5 hours

---

## Verification Checklist

After fixes:
- [ ] All 46 tests pass: `uv run pytest`
- [ ] Ruff clean: `uv run ruff check .`
- [ ] Code formatted: `uv run ruff format .`
- [ ] End-to-end: `uv run named analyze samples/banking-app --output ./report`
- [ ] Check report.json has `impact_summary`
- [ ] Check report.md has "Rename Impact Analysis" section

---

## Medium Priority (Optional)

These can be deferred to future PRs:

- MEDIUM-1: Use defaultdict for reference grouping
- MEDIUM-2: Add explicit docstrings
- MEDIUM-3: Standardize to_dict() pattern
- MEDIUM-4: Remove redundant directory creation
- MEDIUM-5: Optimize summary building (single-pass)

---

## Risk Assessment

**Risk**: 🟢 LOW
- All fixes are localized
- No API changes
- No breaking changes to JSON/Markdown format

**Testing Impact**: 🟢 LOW
- Existing tests continue to pass
- New tests only add coverage

**Performance**: 🟢 NONE
- Changes are cosmetic or defensive

---

## Future Improvements (v0.4+)

1. **Configuration System** - Make thresholds configurable
2. **Serialization Framework** - Standardize to_dict() patterns
3. **Performance Optimization** - Single-pass processing
4. **Enhanced Testing** - Property-based tests, benchmarks

---

## Files to Modify

### Critical
- `src/named/cli.py` - Remove if refs check
- `src/named/analysis/impact_analyzer.py` - Fix type confusion, add constants

### High Priority
- `src/named/validation/validator.py` - Add error handling
- `src/named/export/markdown_exporter.py` - Extract constants

### Tests (Optional)
- `tests/test_impact_analyzer.py` - Add edge case tests

---

For full details, see: `/Users/danielbridera/.claude/plans/noble-tinkering-dawn.md`
