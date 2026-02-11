# Research: Fix Enrichment Update Failure

**Feature**: 013-fix-enrichment-update
**Date**: 2026-02-11

## Research Question 1: Root Cause of the DuckDB UPDATE Failure

### Decision
The root cause is a known DuckDB ART (Adaptive Radix Tree) index limitation where UPDATE — internally implemented as DELETE+INSERT — on tables with multiple indexes triggers spurious "Duplicate key violates primary key constraint" errors. The `transactions` table has 7 indexes (1 PK + 6 secondary), making it highly susceptible.

### Rationale
- DuckDB does not implement UPDATE as an in-place modification; it deletes the old row and inserts a new one
- With multiple ART indexes, the INSERT phase can encounter stale index entries from the DELETE phase
- The `transactions` table has indexes on: `(account_id, date)`, `category_id`, `reviewed`, `normalized_merchant`, `categorization_source`, and `enrichment_source`
- This exact bug is already documented in the codebase — `transaction_service.py:314-316` has a comment and working workaround

### Alternatives Considered
1. **Explicit BEGIN/COMMIT wrapping**: Already tried in enrichment_service.py, does not resolve the issue
2. **DuckDB upgrade**: The bug is present in DuckDB 1.1.3; fixes may exist in newer versions but upgrading is out of scope
3. **INSERT OR REPLACE**: DuckDB 1.1.3 supports this syntax, but it's semantically identical to DELETE+INSERT internally

## Research Question 2: Established Workaround Pattern in Codebase

### Decision
Use the DELETE+INSERT pattern already established in `transaction_service.py:314-344`. This is a proven workaround: SELECT the full row, apply column updates in Python, DELETE the old row, INSERT the complete new row.

### Rationale
- Already working in production for `transaction_service.update()`
- Explicit two-step approach avoids the internal ART index conflict
- Pattern is well-documented with inline comments explaining the DuckDB bug
- Requires fetching the full row first (17 columns), but this is a trivial overhead for single-row operations

### Alternatives Considered
1. **Simple UPDATE (current approach)**: Fails on heavily-indexed tables — this is the bug we're fixing
2. **Retry with exponential backoff**: Unreliable — the bug is deterministic, not transient
3. **Drop/recreate indexes**: Impractical, introduces downtime and complexity

## Research Question 3: Scope of Affected Services

### Decision
Four services perform UPDATE on the `transactions` table. Three are affected and need the fix:

| Service | Method | Pattern | Risk | Status |
| ------- | ------ | ------- | ---- | ------ |
| `enrichment_service.py` | `apply_enrichment_results` | Per-row UPDATE in loop | VERY HIGH | **NEEDS FIX** |
| `categorization_service.py` | `apply_categorization_results` | Per-row UPDATE in loop | VERY HIGH | **NEEDS FIX** |
| `review_service.py` | `bulk_mark_reviewed`, `bulk_set_category`, `bulk_add_note` | Bulk UPDATE with IN clause | MEDIUM | **NEEDS FIX** |
| `transaction_service.py` | `update` | DELETE+INSERT | LOW | Already fixed |

### Rationale
- `enrichment_service.py` is the immediate failure — triggers the bug every time
- `categorization_service.py` uses the identical per-row UPDATE loop pattern and will fail the same way on heavily-indexed tables
- `review_service.py` does bulk UPDATEs wrapped in explicit transactions — also vulnerable but may fail less frequently since DuckDB handles multi-row updates differently
- `transaction_service.py` already uses the DELETE+INSERT workaround

## Research Question 4: Shared Helper vs. Per-Service Fix

### Decision
Extract a shared `_safe_update_transaction()` helper into a database utility module to avoid duplicating the DELETE+INSERT pattern across 3+ services.

### Rationale
- The column list (17 columns) is already duplicated between `transaction_service.py` and will need to be in enrichment/categorization services
- A shared helper ensures consistency — when new columns are added to `transactions`, only one place needs updating
- Reduces the risk of future services accidentally using plain UPDATE

### Alternatives Considered
1. **Per-service inline fix**: Simpler but duplicates the 17-column list 4+ times
2. **ORM/model layer**: Overkill for this project — DuckDB + raw SQL is the established pattern
