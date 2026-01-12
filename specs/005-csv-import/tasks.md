# Tasks: CSV Import

**Input**: Design documents from `/specs/005-csv-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/components/`, `frontend/src/services/`

---

## Phase 1: Setup

**Purpose**: Database schema changes and shared model definitions

- [x] T001 Add csv_column_mapping JSON column to accounts table in backend/app/database.py
- [x] T002 [P] Create CsvColumnMapping Pydantic model with AmountMode enum in backend/app/models/csv_import.py
- [x] T003 [P] Add csv_column_mapping field to AccountResponse and AccountUpdate in backend/app/models/account.py
- [x] T004 Update account_service to include csv_column_mapping in queries in backend/app/services/account_service.py

**Checkpoint**: Schema ready, account model extended with csv_column_mapping support

---

## Phase 2: Foundational (Backend API Infrastructure)

**Purpose**: Core API endpoints and parsing service that ALL user stories depend on

**⚠️ CRITICAL**: No frontend work can begin until this phase is complete

- [x] T005 [P] Create CsvPreviewRequest/CsvPreviewResponse models in backend/app/models/csv_import.py
- [x] T006 [P] Create CsvParseRequest/CsvParseResponse/ParsedTransaction models in backend/app/models/csv_import.py
- [x] T007 [P] Create BulkTransactionCreateRequest/BulkTransactionCreateResponse models in backend/app/models/csv_import.py
- [x] T008 Create csv_import_service.py with preview_csv function (base64 decode, parse headers, sample rows, auto-detect mapping) in backend/app/services/csv_import_service.py
- [x] T009 Add parse_csv function to csv_import_service.py (apply mapping, parse dates, parse amounts, detect duplicates) in backend/app/services/csv_import_service.py
- [x] T010 Add create_transactions function to csv_import_service.py (bulk insert with reviewed=false) in backend/app/services/csv_import_service.py
- [x] T011 [P] Create csv_import router with POST /api/import/preview endpoint in backend/app/routers/csv_import.py
- [x] T012 Add POST /api/import/parse endpoint to csv_import router in backend/app/routers/csv_import.py
- [x] T013 Add POST /api/import/transactions endpoint to csv_import router in backend/app/routers/csv_import.py
- [x] T014 Register csv_import router in backend/app/main.py

**Checkpoint**: Backend API complete - all three endpoints functional

---

## Phase 3: User Story 1 - First-Time CSV Import (Priority: P1) 🎯 MVP

**Goal**: User can drop CSV on account, configure column mapping, preview transactions, and import them

**Independent Test**: Drop a CSV file on an account with no saved mapping → configure columns → preview → confirm import → transactions created

### Frontend API Layer for US1

- [x] T015 [P] [US1] Add CsvColumnMapping, CsvPreviewResponse, ParsedTransaction, CsvParseResponse types to frontend/src/services/api.ts
- [x] T016 [P] [US1] Add previewCsv() function to frontend/src/services/api.ts
- [x] T017 [P] [US1] Add parseCsv() function to frontend/src/services/api.ts
- [x] T018 [P] [US1] Add createTransactionsFromCsv() function to frontend/src/services/api.ts

### Frontend Components for US1

- [x] T019 [US1] Create CsvDropZone component with drag/drop handlers and visual feedback in frontend/components/CsvDropZone.tsx
- [x] T020 [US1] Create CsvColumnMapper modal with column dropdowns, date format selector, and sample data preview in frontend/components/CsvColumnMapper.tsx
- [x] T021 [US1] Add auto-detection logic to CsvColumnMapper (detect common column names like Date, Amount, Description) in frontend/components/CsvColumnMapper.tsx
- [x] T022 [US1] Create CsvImportPreview modal showing parsed transactions with valid/warning/error counts in frontend/components/CsvImportPreview.tsx
- [x] T023 [US1] Add duplicate highlighting to CsvImportPreview (show warning rows with checkbox to include/exclude) in frontend/components/CsvImportPreview.tsx

### Integration for US1

- [x] T024 [US1] Add import flow state management to AccountsView (file, preview, mapping, parsed data) in frontend/components/AccountsView.tsx
- [x] T025 [US1] Integrate CsvDropZone into AccountsView account detail panel in frontend/components/AccountsView.tsx
- [x] T026 [US1] Wire up CsvColumnMapper modal to open when CSV dropped on account without saved mapping in frontend/components/AccountsView.tsx
- [x] T027 [US1] Wire up CsvImportPreview modal and confirm handler to create transactions in frontend/components/AccountsView.tsx

**Checkpoint**: Complete first-time import flow works end-to-end. User can drop CSV, configure mapping, preview, and import.

---

## Phase 4: User Story 2 - Repeat Import with Saved Mapping (Priority: P2)

**Goal**: User can drop CSV on account with saved mapping and skip directly to preview

**Independent Test**: Import to an account that already has a saved mapping → should skip column mapper and go directly to preview

### Implementation for US2

- [x] T028 [US2] Update AccountsView to check for existing csv_column_mapping when CSV dropped in frontend/components/AccountsView.tsx
- [x] T029 [US2] Add logic to skip CsvColumnMapper and auto-parse when mapping exists in frontend/components/AccountsView.tsx
- [x] T030 [US2] Ensure mapping is saved to account on first successful import (update account after transaction creation) in frontend/components/AccountsView.tsx

**Checkpoint**: Repeat imports skip configuration step and go directly to preview

---

## Phase 5: User Story 3 - Re-configure Column Mapping (Priority: P3)

**Goal**: User can access and modify saved column mapping for an account

**Independent Test**: Open account with saved mapping → click "Re-configure mapping" → modify columns → save → future imports use new mapping

### Implementation for US3

- [x] T031 [US3] Add "Re-configure mapping" button to AccountsView when account has saved mapping in frontend/components/AccountsView.tsx
- [x] T032 [US3] Update CsvColumnMapper to accept initial values prop for pre-filling from saved mapping in frontend/components/CsvColumnMapper.tsx
- [x] T033 [US3] Add updateAccountMapping() function to save mapping without importing in frontend/src/services/api.ts
- [x] T034 [US3] Wire up re-configure flow: open mapper with saved values, allow editing, save to account in frontend/components/AccountsView.tsx

**Checkpoint**: Users can modify saved mappings when bank CSV format changes

---

## Phase 6: User Story 4 - Date Format Configuration (Priority: P3)

**Goal**: User can select specific date format during column mapping

**Independent Test**: Import CSV with non-standard date format (e.g., DD/MM/YYYY) → select correct format → dates parse correctly in preview

### Implementation for US4

- [x] T035 [US4] Add date format dropdown to CsvColumnMapper with options: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, MM-DD-YYYY, DD-MM-YYYY, M/D/YYYY, D/M/YYYY in frontend/components/CsvColumnMapper.tsx
- [x] T036 [US4] Add date format preview in CsvColumnMapper showing how first date will be parsed in frontend/components/CsvColumnMapper.tsx
- [x] T037 [US4] Update parse_csv in csv_import_service.py to support all date formats in backend/app/services/csv_import_service.py

**Checkpoint**: Users can import CSVs with various date formats

---

## Phase 7: Polish & Edge Cases

**Purpose**: Error handling and UX improvements across all stories

- [x] T038 [P] Add error handling for empty CSV files in csv_import_service.py in backend/app/services/csv_import_service.py
- [x] T039 [P] Add delimiter detection (comma, semicolon, tab) in csv_import_service.py in backend/app/services/csv_import_service.py
- [x] T040 [P] Add encoding detection/handling in csv_import_service.py in backend/app/services/csv_import_service.py
- [x] T041 [P] Add loading states to AccountsView during import operations in frontend/components/AccountsView.tsx
- [x] T042 [P] Add error message display for failed imports in frontend/components/AccountsView.tsx
- [x] T043 [P] Add success toast/notification after successful import in frontend/components/AccountsView.tsx
- [x] T044 Add click-to-browse file input as alternative to drag-drop in CsvDropZone in frontend/components/CsvDropZone.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on T001-T004 completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Phase 3): Must complete first - establishes core import flow
  - US2 (Phase 4): Depends on US1 for basic import infrastructure
  - US3 (Phase 5): Depends on US1 for CsvColumnMapper component
  - US4 (Phase 6): Depends on US1 for date parsing infrastructure
- **Polish (Phase 7)**: Can start after US1 is complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - MVP
- **User Story 2 (P2)**: Requires US1 complete (uses same components)
- **User Story 3 (P3)**: Requires US1 complete (extends CsvColumnMapper)
- **User Story 4 (P3)**: Requires US1 complete (extends date parsing)

### Within Each Phase

- Models (T002, T003, T005-T007) can run in parallel
- Service functions (T008-T010) must be sequential
- Router endpoints (T011-T013) can be parallel after service complete
- Frontend API functions (T015-T018) can run in parallel
- Frontend components depend on API layer

### Parallel Opportunities

**Phase 1 parallel group:**
```
T002 [P] Create CsvColumnMapping model
T003 [P] Add csv_column_mapping to Account models
```

**Phase 2 parallel group:**
```
T005 [P] CsvPreviewRequest/Response models
T006 [P] CsvParseRequest/Response models
T007 [P] BulkTransactionCreate models
```

**Phase 3 (US1) parallel group:**
```
T015 [P] Add TypeScript types
T016 [P] Add previewCsv function
T017 [P] Add parseCsv function
T018 [P] Add createTransactionsFromCsv function
```

**Phase 7 parallel group:**
```
T038-T043 [P] All polish tasks can run in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T014)
3. Complete Phase 3: User Story 1 (T015-T027)
4. **STOP and VALIDATE**: Test first-time CSV import end-to-end
5. Deploy/demo if ready - users can import transactions!

### Incremental Delivery

1. Setup + Foundational → Backend API ready
2. Add US1 → First-time import works → Deploy (MVP!)
3. Add US2 → Repeat imports streamlined → Deploy
4. Add US3 + US4 → Full configuration flexibility → Deploy
5. Add Polish → Production-ready → Final release

### Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|------------------------|
| Phase 1: Setup | 4 | 2 parallel |
| Phase 2: Foundational | 10 | 4 parallel |
| Phase 3: US1 (MVP) | 13 | 4 parallel |
| Phase 4: US2 | 3 | 0 parallel |
| Phase 5: US3 | 4 | 0 parallel |
| Phase 6: US4 | 3 | 0 parallel |
| Phase 7: Polish | 7 | 6 parallel |
| **Total** | **44** | **16 parallel opportunities** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend API must be complete before frontend work begins
