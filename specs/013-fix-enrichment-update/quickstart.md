# Quickstart: Fix Enrichment Update Failure

**Feature**: 013-fix-enrichment-update
**Date**: 2026-02-11

## Overview

This fix replaces direct `UPDATE transactions SET ...` calls with a safe DELETE+INSERT pattern to work around a DuckDB ART index limitation. The pattern is already proven in `transaction_service.py`.

## What Changes

### New: Shared helper in `database.py`

A `safe_update_transaction()` function that:
1. SELECTs the full transaction row by ID
2. Applies the requested column updates in Python
3. DELETEs the old row
4. INSERTs the complete updated row

### Modified: 3 services

1. **`enrichment_service.py`** — `apply_enrichment_results()` uses the shared helper
2. **`categorization_service.py`** — `apply_categorization_results()` uses the shared helper
3. **`review_service.py`** — bulk operations converted to per-row DELETE+INSERT

### Unchanged

- No schema changes
- No API contract changes
- No frontend changes
- `transaction_service.py` keeps its existing inline workaround (can optionally be refactored to use the shared helper)

## How to Verify

```bash
# Run existing tests — all must pass
cd backend && pytest tests/test_enrichment_service.py -v
cd backend && pytest -v

# Manual test: trigger enrichment and confirm success_count > 0
curl -X POST http://localhost:8000/api/enrichment/trigger
# Expected: {"success_count": N, "failure_count": 0, ...}
```

## Key Design Decision

**Why DELETE+INSERT instead of retries or INSERT OR REPLACE?**
- The DuckDB bug is **deterministic**, not transient — retries won't help
- `INSERT OR REPLACE` is internally the same as DELETE+INSERT in DuckDB, but gives less control
- Explicit DELETE+INSERT is the pattern already established and proven in `transaction_service.py`
