# Tasks: Transactions Review Workflow

**Input**: Design documents from `/specs/004-review-workflow/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - test tasks excluded per template guidelines.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1-US7)
- Paths follow web app pattern: `backend/`, `frontend/`

---

## Phase 1: Setup

**Purpose**: Project initialization and API type definitions

- [X] T001 Create Pydantic models for bulk operations in backend/app/models/review.py
- [X] T002 [P] Add review queue and bulk operation TypeScript types in frontend/src/services/api.ts

---

## Phase 2: Foundational (Backend Core)

**Purpose**: Core backend services that MUST be complete before user stories can begin

**⚠️ CRITICAL**: All user stories depend on these services

- [X] T003 Implement ReviewService with get_review_queue method in backend/app/services/review_service.py
- [X] T004 Implement bulk_mark_reviewed method in backend/app/services/review_service.py
- [X] T005 Implement bulk_set_category method in backend/app/services/review_service.py
- [X] T006 Implement bulk_add_note method in backend/app/services/review_service.py
- [X] T007 Add GET /api/transactions/review-queue endpoint in backend/app/routers/transactions.py
- [X] T008 Add GET /api/transactions/review-queue/count endpoint in backend/app/routers/transactions.py
- [X] T009 Add POST /api/transactions/bulk endpoint in backend/app/routers/transactions.py
- [X] T010 [P] Add fetchReviewQueue API function in frontend/src/services/api.ts
- [X] T011 [P] Add fetchReviewQueueCount API function in frontend/src/services/api.ts
- [X] T012 [P] Add bulkUpdateTransactions API function in frontend/src/services/api.ts

**Checkpoint**: Backend API complete, frontend can make API calls

---

## Phase 3: User Story 1 - View Review Queue (Priority: P1) 🎯 MVP

**Goal**: Display unreviewed transactions grouped by day with Today/Yesterday/date labels

**Independent Test**: Navigate to review page, verify transactions grouped by day, most recent first

### Implementation for User Story 1

- [X] T013 [US1] Create ReviewTransactionList shared component in frontend/components/ReviewTransactionList.tsx
- [X] T014 [US1] Implement date group headers with Today/Yesterday/formatted dates in ReviewTransactionList.tsx
- [X] T015 [US1] Add empty state for no unreviewed transactions in ReviewTransactionList.tsx
- [X] T016 [US1] Add load more / pagination support in ReviewTransactionList.tsx
- [X] T017 [US1] Integrate ReviewTransactionList into existing TransactionReview.tsx widget

**Checkpoint**: Users can view grouped review queue - MVP foundation complete

---

## Phase 4: User Story 2 - Bulk Mark as Reviewed (Priority: P1)

**Goal**: Select multiple transactions and mark all as reviewed atomically

**Independent Test**: Select 5 transactions, click Mark Reviewed, verify all removed from queue

### Implementation for User Story 2

- [X] T018 [US2] Add selection state management (Set<string>) to ReviewTransactionList.tsx
- [X] T019 [US2] Add individual transaction checkboxes in ReviewTransactionList.tsx
- [X] T020 [US2] Create ReviewActionBar component with selected count in frontend/components/ReviewActionBar.tsx
- [X] T021 [US2] Add Mark Reviewed button to ReviewActionBar.tsx
- [X] T022 [US2] Implement bulk mark reviewed handler with API call and queue refresh
- [X] T023 [US2] Add loading state and disable controls during bulk operations
- [X] T024 [US2] Add error handling with clear error messages for failed bulk operations

**Checkpoint**: Users can select and bulk-mark transactions as reviewed

---

## Phase 5: User Story 3 - Quick Category Assignment (Priority: P1)

**Goal**: Assign category to selected transactions from dropdown

**Independent Test**: Select 3 transactions, pick category, verify all assigned

### Implementation for User Story 3

- [X] T025 [US3] Add category dropdown to ReviewActionBar.tsx
- [X] T026 [US3] Fetch and display categories list in dropdown
- [X] T027 [US3] Implement bulk set category handler with API call
- [X] T028 [US3] Keep selection after category assignment for chained actions

**Checkpoint**: Users can bulk-assign categories during review

---

## Phase 6: User Story 4 - Select All in Date Group (Priority: P2)

**Goal**: Select/deselect all transactions in a date group with one click

**Independent Test**: Click group checkbox, verify all transactions in group selected

### Implementation for User Story 4

- [X] T029 [US4] Add group header checkbox to date group headers in ReviewTransactionList.tsx
- [X] T030 [US4] Implement select all in group toggle logic
- [X] T031 [US4] Add indeterminate checkbox state when partially selected (using ref)
- [X] T032 [US4] Update group checkbox when individual selections change

**Checkpoint**: Users can efficiently select entire days of transactions

---

## Phase 7: User Story 5 - Add Notes in Bulk (Priority: P2)

**Goal**: Add note to multiple selected transactions (appending to existing)

**Independent Test**: Select 5 transactions, add note, verify all have note appended

### Implementation for User Story 5

- [X] T033 [US5] Add note input field/modal to ReviewActionBar.tsx
- [X] T034 [US5] Implement bulk add note handler with API call
- [X] T035 [US5] Show confirmation of how many transactions updated

**Checkpoint**: Users can annotate batches of transactions

---

## Phase 8: User Story 6 - Dashboard Review Widget (Priority: P2)

**Goal**: Compact widget showing count and preview of transactions to review

**Independent Test**: View dashboard, see count and 5 most recent transactions

### Implementation for User Story 6

- [X] T036 [US6] Update TransactionReview.tsx to use real API instead of mock data
- [X] T037 [US6] Display review count from API in widget header
- [X] T038 [US6] Limit preview to 5 transactions in widget mode
- [X] T039 [US6] Add "All caught up!" empty state in widget
- [X] T040 [US6] Add navigation link to full review page

**Checkpoint**: Dashboard shows review status at a glance

---

## Phase 9: User Story 7 - Dedicated Review Page (Priority: P3)

**Goal**: Full-screen review page with all bulk actions for power users

**Independent Test**: Navigate to /review, see full queue with action bar

### Implementation for User Story 7

- [X] T041 [US7] Create ReviewPage.tsx component in frontend/components/ReviewPage.tsx
- [X] T042 [US7] Add /review route in frontend/App.tsx
- [X] T043 [US7] Add Review link to sidebar navigation in frontend/components/Sidebar.tsx
- [X] T044 [US7] Compose ReviewTransactionList and ReviewActionBar in full-page layout
- [X] T045 [US7] Add success state when all transactions reviewed with dashboard link
- [X] T046 [US7] Ensure responsive performance with 200+ transactions

**Checkpoint**: Power users have dedicated review workflow

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements across all stories

- [X] T047 [P] Remove mock data from frontend/mockData.ts (TransactionReview related)
- [X] T048 Code cleanup - remove any unused imports/variables
- [X] T049 Verify all bulk operations are atomic (transaction rollback works)
- [X] T050 Manual validation against quickstart.md test scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup
- **User Stories (Phase 3-9)**: All depend on Foundational
  - US1 (P1): Foundation for all frontend work
  - US2 (P1): Depends on US1 (selection UI)
  - US3 (P1): Depends on US2 (action bar)
  - US4 (P2): Depends on US1 (group headers)
  - US5 (P2): Depends on US2 (action bar)
  - US6 (P2): Depends on US1 (shared component)
  - US7 (P3): Depends on US1, US2 (full composition)
- **Polish (Phase 10)**: Depends on all stories complete

### User Story Dependencies

```
Phase 1: Setup
    │
    ▼
Phase 2: Foundational (Backend API)
    │
    ├─────────────────────────────────┐
    ▼                                 │
Phase 3: US1 - View Queue ◄───────────┘
    │
    ├──────────────┬─────────────┐
    ▼              ▼             │
Phase 4: US2   Phase 6: US6     │
    │              │             │
    ├──────────────┤             │
    ▼              ▼             │
Phase 5: US3   Phase 8: US6     │
    │                            │
    ├─────────────┐              │
    ▼             ▼              │
Phase 7: US5  Phase 6: US4      │
                                 │
                                 ▼
                        Phase 9: US7
                                 │
                                 ▼
                        Phase 10: Polish
```

### Parallel Opportunities

**Within Phase 1**:
```bash
# Run in parallel:
Task: T001 (backend models)
Task: T002 (frontend types)
```

**Within Phase 2**:
```bash
# Run in parallel after T003-T009:
Task: T010 (fetchReviewQueue)
Task: T011 (fetchReviewQueueCount)
Task: T012 (bulkUpdateTransactions)
```

**Multiple Stories in Parallel** (if team capacity):
- After US1 complete: US2, US4, US6 can start in parallel
- After US2 complete: US3, US5 can start in parallel

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T012)
3. Complete Phase 3: US1 - View Queue (T013-T017)
4. **STOP and VALIDATE**: Can view grouped review queue
5. Deploy/demo if ready

### Core Review Flow (US1-US3)

1. Setup + Foundational → Backend ready
2. US1: View Queue → Can see what needs review
3. US2: Bulk Mark → Can process transactions
4. US3: Category Assignment → Can categorize and review together
5. **This delivers the full core workflow**

### Full Feature (All Stories)

1. Core flow (US1-US3) → Primary value delivered
2. US4: Group selection → Efficiency improvement
3. US5: Bulk notes → Additional capability
4. US6: Dashboard widget → Discovery/visibility
5. US7: Dedicated page → Power user experience
6. Polish → Production ready

---

## Summary

| Phase | User Story | Priority | Tasks |
|-------|------------|----------|-------|
| 1 | Setup | - | 2 |
| 2 | Foundational | - | 10 |
| 3 | US1 - View Review Queue | P1 | 5 |
| 4 | US2 - Bulk Mark as Reviewed | P1 | 7 |
| 5 | US3 - Quick Category Assignment | P1 | 4 |
| 6 | US4 - Select All in Date Group | P2 | 4 |
| 7 | US5 - Add Notes in Bulk | P2 | 3 |
| 8 | US6 - Dashboard Review Widget | P2 | 5 |
| 9 | US7 - Dedicated Review Page | P3 | 6 |
| 10 | Polish | - | 4 |
| **Total** | | | **50** |

---

## Notes

- [P] = different files, no dependencies - can run in parallel
- [US#] = maps task to specific user story
- Each story independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
