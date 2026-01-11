# Tasks: Transactions Core

**Input**: Design documents from `/specs/002-transactions-core/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/transactions-api.yaml

**Tests**: Not explicitly requested in feature specification. Tests omitted unless user requests TDD approach.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/` (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema and Pydantic models that all user stories depend on

- [x] T001 Add transactions table schema with indexes in backend/app/database.py
- [x] T002 [P] Create Transaction Pydantic models (TransactionCreate, TransactionUpdate, TransactionResponse, TransactionFilters, TransactionListResponse) in backend/app/models/transaction.py
- [x] T003 [P] Add Transaction TypeScript types (Transaction, TransactionUpdate, TransactionListResponse, TransactionFilters) in frontend/types.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core service layer and API routing that MUST be complete before ANY user story UI work

**⚠️ CRITICAL**: No frontend user story work can begin until this phase is complete

- [x] T004 Create TransactionService class with get_db_connection pattern in backend/app/services/transaction_service.py
- [x] T005 Implement TransactionService.create() method for creating transactions (used by CSV import later) in backend/app/services/transaction_service.py
- [x] T006 Create transactions router file with router instance in backend/app/routers/transactions.py
- [x] T007 Register transactions router in backend/app/main.py
- [x] T008 [P] Add base transaction API functions (fetchTransactions, updateTransaction, deleteTransaction) in frontend/src/services/api.ts
- [x] T009 Add Transactions navigation item to sidebar in frontend/components/Sidebar.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View All Transactions (Priority: P1) 🎯 MVP

**Goal**: Display transactions in a paginated table sorted by date descending

**Independent Test**: Navigate to transactions page, verify transactions display in table with date, description, amount, account, category, review status columns. Empty state shown when no transactions.

### Implementation for User Story 1

- [x] T010 [US1] Implement TransactionService.get_all() with basic pagination (limit/offset) and date DESC sorting in backend/app/services/transaction_service.py
- [x] T011 [US1] Implement TransactionService.count() for total count in pagination response in backend/app/services/transaction_service.py
- [x] T012 [US1] Implement GET /api/transactions endpoint with limit/offset params in backend/app/routers/transactions.py
- [x] T013 [US1] Implement TransactionService.get_by_id() for single transaction fetch in backend/app/services/transaction_service.py
- [x] T014 [US1] Implement GET /api/transactions/{id} endpoint in backend/app/routers/transactions.py
- [x] T015 [US1] Create TransactionsView.tsx component with table structure and column headers in frontend/components/TransactionsView.tsx
- [x] T016 [US1] Implement transaction list fetching and state management in frontend/components/TransactionsView.tsx
- [x] T017 [US1] Add amount formatting (cents to dollars with currency symbol) in frontend/components/TransactionsView.tsx
- [x] T018 [US1] Add date formatting for user-readable display in frontend/components/TransactionsView.tsx
- [x] T019 [US1] Implement empty state UI when no transactions exist in frontend/components/TransactionsView.tsx
- [x] T020 [US1] Implement pagination controls (prev/next, page indicator) in frontend/components/TransactionsView.tsx
- [x] T021 [US1] Add loading state during data fetch in frontend/components/TransactionsView.tsx
- [x] T022 [US1] Add error handling for failed API calls in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 1 complete - can view paginated transaction list with proper formatting

---

## Phase 4: User Story 2 - Filter Transactions (Priority: P1)

**Goal**: Filter transactions by account, category, date range, amount range, and review status

**Independent Test**: Apply various filter combinations, verify only matching transactions appear. Clear filters to see all transactions.

### Implementation for User Story 2

- [x] T023 [US2] Extend TransactionService.get_all() with account_id filter in backend/app/services/transaction_service.py
- [x] T024 [US2] Add category_id filter to TransactionService.get_all() in backend/app/services/transaction_service.py
- [x] T025 [US2] Add date_from and date_to filters to TransactionService.get_all() in backend/app/services/transaction_service.py
- [x] T026 [US2] Add amount_min and amount_max filters to TransactionService.get_all() in backend/app/services/transaction_service.py
- [x] T027 [US2] Add reviewed status filter to TransactionService.get_all() in backend/app/services/transaction_service.py
- [x] T028 [US2] Update GET /api/transactions endpoint with all filter query parameters in backend/app/routers/transactions.py
- [x] T029 [US2] Add filter state management to TransactionsView in frontend/components/TransactionsView.tsx
- [x] T030 [US2] Create filter panel UI with account dropdown in frontend/components/TransactionsView.tsx
- [x] T031 [US2] Add category dropdown filter to filter panel in frontend/components/TransactionsView.tsx
- [x] T032 [US2] Add date range picker (from/to) to filter panel in frontend/components/TransactionsView.tsx
- [x] T033 [US2] Add amount range inputs (min/max) to filter panel in frontend/components/TransactionsView.tsx
- [x] T034 [US2] Add reviewed status filter (all/reviewed/unreviewed) to filter panel in frontend/components/TransactionsView.tsx
- [x] T035 [US2] Implement clear filters button in frontend/components/TransactionsView.tsx
- [x] T036 [US2] Add date range validation (start before end) with error message in frontend/components/TransactionsView.tsx
- [x] T037 [US2] Add empty state for "no transactions match filters" in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 2 complete - can filter transactions by all criteria with validation

---

## Phase 5: User Story 3 - Search Transactions (Priority: P2)

**Goal**: Search transactions by description with case-insensitive partial matching

**Independent Test**: Enter search term, verify matching transactions appear. Search with no matches shows helpful message. Search combines with active filters.

### Implementation for User Story 3

- [x] T038 [US3] Add search parameter (LIKE query on description) to TransactionService.get_all() in backend/app/services/transaction_service.py
- [x] T039 [US3] Add search query parameter to GET /api/transactions endpoint in backend/app/routers/transactions.py
- [x] T040 [US3] Add search input field to TransactionsView filter area in frontend/components/TransactionsView.tsx
- [x] T041 [US3] Implement search state and debounced API calls in frontend/components/TransactionsView.tsx
- [x] T042 [US3] Update empty state to differentiate "no results for search" in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 3 complete - can search transactions by description

---

## Phase 6: User Story 4 - Edit Transaction Category (Priority: P1)

**Goal**: Inline category editing with dropdown, immediate save on selection

**Independent Test**: Click category field, select new category from dropdown, verify change persists after page refresh.

### Implementation for User Story 4

- [x] T043 [US4] Implement TransactionService.update() method with partial update support in backend/app/services/transaction_service.py
- [x] T044 [US4] Add category_id validation (must exist or be null) in TransactionService.update() in backend/app/services/transaction_service.py
- [x] T045 [US4] Implement PUT /api/transactions/{id} endpoint in backend/app/routers/transactions.py
- [x] T046 [US4] Create TransactionEditForm.tsx component for inline editing in frontend/components/forms/TransactionEditForm.tsx
- [x] T047 [US4] Implement category dropdown with available categories in frontend/components/forms/TransactionEditForm.tsx
- [x] T048 [US4] Add click-to-edit behavior on category cell in frontend/components/TransactionsView.tsx
- [x] T049 [US4] Implement optimistic update for category change in frontend/components/TransactionsView.tsx
- [x] T050 [US4] Handle cancel (click away) to restore original value in frontend/components/forms/TransactionEditForm.tsx
- [x] T051 [US4] Add error handling for failed category update in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 4 complete - can edit transaction category inline

---

## Phase 7: User Story 5 - Edit Transaction Notes (Priority: P2)

**Goal**: Inline notes editing with text input, save on blur

**Independent Test**: Click notes field, enter text, blur field, verify notes persist after page refresh. Notes indicator visible for transactions with notes.

### Implementation for User Story 5

- [x] T052 [US5] Add notes text input to TransactionEditForm in frontend/components/forms/TransactionEditForm.tsx
- [x] T053 [US5] Add click-to-edit behavior on notes cell in frontend/components/TransactionsView.tsx
- [x] T054 [US5] Implement save-on-blur for notes editing in frontend/components/forms/TransactionEditForm.tsx
- [x] T055 [US5] Add notes indicator icon for transactions with notes in frontend/components/TransactionsView.tsx
- [x] T056 [US5] Add error handling for failed notes update in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 5 complete - can edit transaction notes inline

---

## Phase 8: User Story 6 - Toggle Review Status (Priority: P2)

**Goal**: Toggle reviewed status with automatic timestamp management

**Independent Test**: Click review toggle on unreviewed transaction, verify reviewed status and timestamp set. Click again, verify status cleared. Changes persist after refresh.

### Implementation for User Story 6

- [x] T057 [US6] Add reviewed_at auto-set logic (set when reviewed=true, clear when false) in TransactionService.update() in backend/app/services/transaction_service.py
- [x] T058 [US6] Add review toggle checkbox/button to transaction row in frontend/components/TransactionsView.tsx
- [x] T059 [US6] Implement toggle click handler with immediate API call in frontend/components/TransactionsView.tsx
- [x] T060 [US6] Add visual distinction for reviewed vs unreviewed rows in frontend/components/TransactionsView.tsx
- [x] T061 [US6] Add error handling for failed review toggle in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 6 complete - can toggle transaction review status

---

## Phase 9: User Story 7 - Delete Transaction (Priority: P3)

**Goal**: Delete transactions with confirmation dialog

**Independent Test**: Click delete button, see confirmation prompt. Confirm deletion, transaction removed from list. Cancel, transaction remains.

### Implementation for User Story 7

- [x] T062 [US7] Implement TransactionService.delete() method in backend/app/services/transaction_service.py
- [x] T063 [US7] Implement DELETE /api/transactions/{id} endpoint with 204 response in backend/app/routers/transactions.py
- [x] T064 [US7] Add delete button/icon to transaction row in frontend/components/TransactionsView.tsx
- [x] T065 [US7] Implement confirmation dialog/modal for delete action in frontend/components/TransactionsView.tsx
- [x] T066 [US7] Remove transaction from list state after successful deletion in frontend/components/TransactionsView.tsx
- [x] T067 [US7] Add error handling for failed deletion in frontend/components/TransactionsView.tsx

**Checkpoint**: User Story 7 complete - can delete transactions with confirmation

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements and edge case handling

- [x] T068 Update account deletion to check for existing transactions (block delete if transactions exist) in backend/app/services/account_service.py
- [x] T069 [P] Add optimistic concurrent edit handling (show error if transaction was deleted) in frontend/components/TransactionsView.tsx
- [x] T070 [P] Add network error handling with retry option in frontend/components/TransactionsView.tsx
- [x] T071 Verify all success criteria (SC-001 to SC-007) are met with manual testing
- [x] T072 Run quickstart.md validation to ensure development workflow works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Can Start After |
|-------|----------|------------|-----------------|
| US1 - View | P1 | Foundational | Phase 2 complete |
| US2 - Filter | P1 | US1 (list endpoint) | Phase 3 complete |
| US3 - Search | P2 | US2 (filter infrastructure) | Phase 4 complete |
| US4 - Edit Category | P1 | US1 (list display) | Phase 3 complete |
| US5 - Edit Notes | P2 | US4 (edit infrastructure) | Phase 6 complete |
| US6 - Toggle Review | P2 | US4 (edit infrastructure) | Phase 6 complete |
| US7 - Delete | P3 | US1 (list display) | Phase 3 complete |

### Parallel Opportunities

**Within Phase 1 (Setup):**
- T002 (Python models) and T003 (TypeScript types) can run in parallel

**Within Phase 2 (Foundational):**
- T008 (API functions) can run parallel with backend tasks T004-T007

**After Phase 3 (US1 complete):**
- US2, US4, and US7 can start in parallel (different concerns)

**After Phase 6 (US4 complete):**
- US5 and US6 can run in parallel (both extend edit infrastructure)

---

## Parallel Example: After US1 Complete

```bash
# Three developers can work in parallel after Phase 3:

# Developer A: User Story 2 - Filtering
Task: T023-T037 (backend filters + frontend filter UI)

# Developer B: User Story 4 - Edit Category
Task: T043-T051 (update endpoint + inline category edit)

# Developer C: User Story 7 - Delete
Task: T062-T067 (delete endpoint + confirmation UI)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009)
3. Complete Phase 3: User Story 1 (T010-T022)
4. **STOP and VALIDATE**: Test transaction list view independently
5. Deploy/demo if ready - users can view their transactions

### Recommended Path (P1 Stories)

1. Setup + Foundational → Foundation ready
2. US1 (View) → Users can see transactions
3. US2 (Filter) → Users can find specific transactions
4. US4 (Edit Category) → Users can categorize transactions
5. **Deploy P1 MVP** - Core functionality complete

### Full Feature Path

1. P1 Stories (above) → Core MVP
2. US3 (Search) → Faster transaction lookup
3. US5 (Notes) + US6 (Review) → Can run in parallel
4. US7 (Delete) → Complete CRUD
5. Polish phase → Edge cases and refinements

---

## Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | 3 | 2 |
| Foundational | 6 | 2 |
| US1 - View | 13 | 0 (sequential) |
| US2 - Filter | 15 | 0 (sequential) |
| US3 - Search | 5 | 0 (sequential) |
| US4 - Edit Category | 9 | 0 (sequential) |
| US5 - Edit Notes | 5 | 0 (sequential) |
| US6 - Toggle Review | 5 | 0 (sequential) |
| US7 - Delete | 6 | 0 (sequential) |
| Polish | 5 | 2 |
| **Total** | **72** | **6** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [USx] label maps task to specific user story for traceability
- Each user story checkpoint enables independent testing
- Backend tests can be added by running `/speckit.tasks` with TDD flag if needed
- Commit after each task or logical group
- Performance targets: <2s page load, <1s filter, <500ms edit persist
