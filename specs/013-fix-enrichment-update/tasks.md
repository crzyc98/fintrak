# Tasks: Fix Enrichment Update Failure

**Input**: Design documents from `/specs/013-fix-enrichment-update/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included — a regression test for the shared helper is specified in the plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/` for source, `backend/tests/` for tests

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — existing codebase. This phase is empty.

**Checkpoint**: Existing project structure is already in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared `safe_update_transaction()` helper that all user story fixes depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T001 Add `TRANSACTION_COLUMNS` constant and `safe_update_transaction(conn, transaction_id, updates)` helper function to `backend/app/database.py`. The helper must: (1) SELECT the full row (all 17 columns from `TRANSACTION_COLUMNS`) by ID, (2) return False if row not found, (3) apply the `updates` dict to the row, (4) DELETE the old row by ID, (5) INSERT the complete updated row, (6) return True on success. Include a docstring explaining the DuckDB ART index workaround. Reference the existing pattern at `backend/app/services/transaction_service.py:314-344`.
- [x] T002 Add unit tests for `safe_update_transaction()` in `backend/tests/test_safe_update.py`. Tests must: (1) create a transactions table with all 7 indexes matching `backend/app/database.py` schema, (2) insert a test transaction, (3) call `safe_update_transaction()` to update enrichment columns (subcategory, is_discretionary, enrichment_source, normalized_merchant), (4) verify the update persisted correctly, (5) verify all non-updated columns are unchanged, (6) test that updating a non-existent transaction returns False, (7) test that the function works when called multiple times on the same row.
- [x] T003 Run `cd backend && pytest tests/test_safe_update.py -v` to verify the helper tests pass.

**Checkpoint**: Shared helper is implemented and tested. Service fixes can now begin.

---

## Phase 3: User Story 1 — Enrichment Completes Successfully (Priority: P1) MVP

**Goal**: Fix the enrichment service so that triggering enrichment successfully persists AI-generated merchant names, subcategories, and discretionary classifications to transactions without database constraint errors.

**Independent Test**: Trigger enrichment on unenriched transactions and verify enriched fields are persisted. Run `cd backend && pytest tests/test_enrichment_service.py -v`.

### Implementation for User Story 1

- [x] T004 [US1] Replace the direct `UPDATE` in `apply_enrichment_results()` in `backend/app/services/enrichment_service.py` with a call to `safe_update_transaction()` from `backend/app/database.py`. Import the helper. For each enrichment result, build an updates dict with: `subcategory`, `is_discretionary`, `enrichment_source='ai'`, and `normalized_merchant` (only if not None). Call `safe_update_transaction(conn, result.transaction_id, updates)`. Increment `success_count` only if the helper returns True. Keep the existing per-result try/except and warning logging for failed updates.
- [x] T005 [US1] Run `cd backend && pytest tests/test_enrichment_service.py -v` to verify all 22 existing enrichment tests pass with the new helper.
- [x] T006 [P] [US1] Replace the direct `UPDATE` in `apply_categorization_results()` in `backend/app/services/categorization_service.py` with a call to `safe_update_transaction()` from `backend/app/database.py`. Import the helper. For each categorization result, build an updates dict with: `category_id`, `confidence_score`, `categorization_source` (the `source` parameter). Call `safe_update_transaction(conn, result.transaction_id, updates)`. Keep the existing confidence threshold skip logic and counter tracking.
- [x] T007 [US1] Run `cd backend && pytest tests/test_categorization_integration.py -v` to verify existing categorization tests pass.

**Checkpoint**: Enrichment and categorization updates now use the safe DELETE+INSERT pattern. The core bug (FR-001, SC-001) is fixed.

---

## Phase 4: User Story 2 — Protect Bulk Review Operations (Priority: P2)

**Goal**: Apply the same DELETE+INSERT fix to review_service.py bulk operations to protect against the same constraint error as the index count grows.

**Independent Test**: Run `cd backend && pytest tests/ -k review -v` (if review tests exist) or run the full test suite.

### Implementation for User Story 2

- [x] T008 [US2] Replace the bulk `UPDATE transactions SET reviewed = true, reviewed_at = ? WHERE id IN (...)` in `bulk_mark_reviewed()` in `backend/app/services/review_service.py` with a per-row loop calling `safe_update_transaction()` from `backend/app/database.py`. Import the helper. For each transaction_id, build updates dict `{"reviewed": True, "reviewed_at": reviewed_at}`. Keep the existing `BEGIN TRANSACTION`/`COMMIT`/`ROLLBACK` wrapping and `_validate_transaction_ids()` call.
- [x] T009 [US2] Replace the bulk `UPDATE transactions SET category_id = ?, categorization_source = 'manual' WHERE id IN (...)` in `bulk_set_category()` in `backend/app/services/review_service.py` with a per-row loop calling `safe_update_transaction()`. For each transaction_id, build updates dict `{"category_id": category_id, "categorization_source": "manual"}`. Keep existing validation and transaction wrapping.
- [x] T010 [US2] Replace the bulk `UPDATE transactions SET notes = CASE ... WHERE id IN (...)` in `bulk_add_note()` in `backend/app/services/review_service.py` with a per-row loop. For each transaction_id: (1) SELECT the current notes value, (2) compute the new notes value (append with newline separator if existing, or set directly), (3) call `safe_update_transaction()` with `{"notes": new_notes_value}`. Keep existing validation and transaction wrapping.
- [x] T011 [US2] Run `cd backend && pytest -v` to verify the full test suite passes after all review service changes.

**Checkpoint**: All bulk review operations now use the safe DELETE+INSERT pattern. The codebase is protected against the DuckDB ART index bug across all services.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and optional cleanup.

- [x] T012 Optionally refactor `backend/app/services/transaction_service.py` lines 314-344 to use the shared `safe_update_transaction()` helper from `backend/app/database.py` instead of its inline DELETE+INSERT. This consolidates the column list to a single source of truth. Verify `cd backend && pytest -v` passes after refactoring.
- [x] T013 Run full test suite validation: `cd backend && pytest -v`. All tests must pass. Run `cd backend && ruff check .` to verify no lint issues.
- [ ] T014 Run quickstart.md validation: verify the manual test instructions in `specs/013-fix-enrichment-update/quickstart.md` match the actual behavior (if app is running, trigger enrichment via `POST /api/enrichment/trigger` and confirm `success_count > 0`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — can start immediately. T001 → T002 → T003 sequential.
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion (T003 passing). T004 → T005 sequential; T006 can run in parallel with T004 (different file). T007 after T006.
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion (T003 passing). Can run in parallel with Phase 3 (different files). T008, T009, T010 are sequential (same file). T011 after T010.
- **Polish (Phase 5)**: Depends on Phases 3 and 4 completion.

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational phase. No dependency on US2.
- **User Story 2 (P2)**: Depends only on Foundational phase. No dependency on US1. Can run in parallel with US1.

### Within Each User Story

- Service modification → test verification (sequential)
- Different service files marked [P] can run in parallel

### Parallel Opportunities

- T004 (enrichment_service.py) and T006 (categorization_service.py) can run in parallel — different files
- Phase 3 and Phase 4 can run in parallel — different service files, both depend only on Phase 2
- T008, T009, T010 are in the same file (review_service.py) — must be sequential

---

## Parallel Example: User Story 1

```bash
# After Phase 2 is complete, launch these in parallel:
Task: "T004 [US1] Fix enrichment_service.py apply_enrichment_results() in backend/app/services/enrichment_service.py"
Task: "T006 [US1] Fix categorization_service.py apply_categorization_results() in backend/app/services/categorization_service.py"

# Then verify sequentially:
Task: "T005 [US1] Run enrichment tests"
Task: "T007 [US1] Run categorization tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T003) — shared helper
2. Complete Phase 3: User Story 1 (T004-T007) — fix enrichment + categorization
3. **STOP and VALIDATE**: Run `cd backend && pytest -v`, trigger enrichment manually
4. This alone fixes the reported bug (FR-001, SC-001, SC-002)

### Incremental Delivery

1. Phase 2 → Shared helper ready
2. Phase 3 → Enrichment + categorization fixed → **MVP delivered**
3. Phase 4 → Review operations hardened → Full coverage
4. Phase 5 → Cleanup and validation → Release ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each phase completion
- Stop at any checkpoint to validate independently
- T012 (refactor transaction_service.py) is optional — the existing inline workaround already works
