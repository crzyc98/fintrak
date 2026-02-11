# Implementation Plan: Fix Enrichment Update Failure

**Branch**: `013-fix-enrichment-update` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-fix-enrichment-update/spec.md`

## Summary

The enrichment service (and categorization/review services) fail to update transactions because DuckDB internally implements UPDATE as DELETE+INSERT, which conflicts with the 7 ART indexes on the `transactions` table. The fix extracts a shared `safe_update_transaction()` helper using the proven DELETE+INSERT pattern already in `transaction_service.py`, then applies it to all affected services.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115.6, DuckDB 1.1.3, Pydantic 2.10.4
**Storage**: DuckDB file-based (`fintrak.duckdb`) — no schema changes
**Testing**: pytest (existing test suite covers enrichment, categorization, and review workflows)
**Target Platform**: Linux server (dev container)
**Project Type**: Web application (backend-only fix, no frontend changes)
**Performance Goals**: N/A — single-row operations, overhead of SELECT before DELETE+INSERT is negligible
**Constraints**: Must not break existing tests; must work with DuckDB 1.1.3
**Scale/Scope**: 4 files modified (1 new helper + 3 service fixes)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is unpopulated (template defaults). No gates to enforce. **PASS.**

**Post-Phase 1 re-check**: Design uses the same DELETE+INSERT pattern already established in the codebase (`transaction_service.py:314-344`). No new patterns, dependencies, or architectural changes introduced. **PASS.**

## Project Structure

### Documentation (this feature)

```text
specs/013-fix-enrichment-update/
├── plan.md              # This file
├── research.md          # Root cause analysis and approach decision
├── data-model.md        # Transaction schema reference (no changes)
├── quickstart.md        # Verification guide
├── contracts/           # API contract impact (none)
│   └── no-api-changes.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── database.py                          # ADD: safe_update_transaction() helper
│   └── services/
│       ├── enrichment_service.py            # MODIFY: use helper in apply_enrichment_results()
│       ├── categorization_service.py        # MODIFY: use helper in apply_categorization_results()
│       └── review_service.py               # MODIFY: use helper in bulk operations
└── tests/
    ├── test_enrichment_service.py           # VERIFY: existing tests pass
    ├── test_categorization_integration.py   # VERIFY: existing tests pass
    └── test_safe_update.py                  # ADD: unit tests for the helper
```

**Structure Decision**: Backend-only web application. All changes are in `backend/app/` (services + database helper). No frontend modifications.

## Implementation Approach

### Step 1: Add shared helper to `database.py`

Add a `safe_update_transaction(conn, transaction_id, updates)` function that:
1. SELECTs the full row (all 17 columns) by ID
2. Returns early if row not found
3. Applies the `updates` dict to the row
4. DELETEs the old row by ID
5. INSERTs the complete updated row

The column list should be defined as a module-level constant (`TRANSACTION_COLUMNS`) to keep it DRY.

### Step 2: Fix `enrichment_service.py`

Replace the direct `UPDATE` in `apply_enrichment_results()` with a call to `safe_update_transaction()`, passing only the enrichment columns:
- `normalized_merchant` (if not None)
- `subcategory`
- `is_discretionary`
- `enrichment_source = 'ai'`

### Step 3: Fix `categorization_service.py`

Replace the direct `UPDATE` in `apply_categorization_results()` with a call to `safe_update_transaction()`, passing:
- `category_id`
- `confidence_score`
- `categorization_source`

### Step 4: Fix `review_service.py`

Replace the bulk `UPDATE ... WHERE id IN (...)` calls in `bulk_mark_reviewed()`, `bulk_set_category()`, and `bulk_add_note()` with per-row `safe_update_transaction()` calls inside the existing transaction blocks.

### Step 5: Add regression test

Add a test in `test_safe_update.py` that:
1. Creates a transaction on a table with all 7 indexes
2. Calls `safe_update_transaction()` to update enrichment columns
3. Verifies the update persisted and no constraint errors occurred
4. Verifies all other columns are unchanged

### Step 6: Run full test suite

Verify all existing tests pass: `cd backend && pytest -v`

## Complexity Tracking

No constitution violations. No complexity justifications needed.
