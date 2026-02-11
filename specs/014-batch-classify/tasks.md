# Tasks: Batch AI Classification

**Input**: Design documents from `/specs/014-batch-classify/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Tests omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No setup required — this feature extends an existing project with no new directories or dependencies.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared Pydantic models and in-memory infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 [P] Add `BatchTriggerResponse`, `UnclassifiedCountResponse`, and `BatchProgressResponse` Pydantic models, and add optional `batch_size: int | None` field (min=10, max=200) to `CategorizationTriggerRequest` in `backend/app/models/categorization.py`
- [X] T002 [P] Add `BatchJobState` dataclass with all progress fields (batch_id, status, total_transactions, processed_transactions, success/failure/skipped/rule_match/desc_rule_match/ai_match counts, error_message, started_at, completed_at), module-level `_active_jobs: dict[str, BatchJobState]` dict, and `_job_lock = threading.Lock()` in `backend/app/services/categorization_service.py`

**Checkpoint**: Foundation ready — all new model types and state infrastructure in place.

---

## Phase 3: User Story 1 — Trigger Bulk Classification of Unclassified Transactions (Priority: P1) 🎯 MVP

**Goal**: Let users navigate to a Settings page and trigger AI classification on all unclassified transactions in a single action. The backend processes in a background thread and prevents concurrent runs.

**Independent Test**: Import a CSV with uncategorized transactions, navigate to Settings, click "Classify All", verify all transactions receive categories.

### Implementation for User Story 1

- [X] T003 [US1] Add `get_unclassified_count()` method that queries `COUNT` of transactions where `category_id IS NULL OR enrichment_source IS NULL` in `backend/app/services/categorization_service.py`
- [X] T004 [US1] Refactor `trigger_categorization()` to acquire `_job_lock`, create a `BatchJobState` entry in `_active_jobs`, start processing in a background thread via `threading.Thread`, and return immediately with batch_id + total_transactions + status; return 409-style error if lock is already held; remove the 1000-transaction limit when `transaction_ids` is None; preserve existing pipeline order (merchant rules → description rules → AI per FR-003); catch missing API key errors early and set `status=failed` with a clear `error_message` in `backend/app/services/categorization_service.py`
- [X] T005 [US1] Add `GET /api/categorization/unclassified-count` endpoint that calls `get_unclassified_count()` and returns `UnclassifiedCountResponse` in `backend/app/routers/categorization.py`
- [X] T006 [US1] Modify `POST /api/categorization/trigger` endpoint to pass `batch_size` from request body, return `BatchTriggerResponse` with HTTP 202 for background jobs, and return HTTP 409 if a job is already running in `backend/app/routers/categorization.py`
- [X] T007 [P] [US1] Add `getUnclassifiedCount()` function returning `Promise<{count: number}>`, add `BatchTriggerResponseData` type (`batch_id`, `total_transactions`, `status`), and update `triggerCategorization()` to accept optional `batch_size` and return `BatchTriggerResponseData` in `frontend/src/services/api.ts`
- [X] T008 [US1] Create `SettingsView` component with: fetch unclassified count on mount, check for any active job on mount (call progress endpoint to detect in-flight jobs so returning to the page resumes the progress view), display count message, "Classify All" button (disabled when count is 0 or job is running), loading/error states, and basic trigger call that stores the returned batch_id in `frontend/components/SettingsView.tsx`
- [X] T009 [P] [US1] Add `'Settings'` tab routing: import `SettingsView`, add `{activeTab === 'Settings' && <SettingsView />}` render case in `frontend/App.tsx`
- [X] T010 [P] [US1] Wire existing Settings button placeholder to call `setActiveTab('Settings')` using the `onNavigate` prop pattern in `frontend/components/Sidebar.tsx`

**Checkpoint**: Users can trigger batch classification from the Settings page. All unclassified transactions get processed. No progress feedback yet.

---

## Phase 4: User Story 2 — Monitor Batch Classification Progress (Priority: P2)

**Goal**: Show real-time progress while classification runs — processed count, success/failure tallies, and a completion summary with full breakdown.

**Independent Test**: Trigger classification on 100+ transactions, observe progress updates every 2 seconds showing processed/total counts, then verify completion summary shows rule-matched + AI-matched + skipped + failed = total.

### Implementation for User Story 2

- [X] T011 [US2] Update `_process_ai_batches()` and rule-matching logic to increment `BatchJobState` counters (`processed_transactions`, `success_count`, `failure_count`, `skipped_count`, `rule_match_count`, `desc_rule_match_count`, `ai_match_count`) after each sub-batch completes; set status to `completed` or `failed` with `error_message` and `completed_at` on finish in `backend/app/services/categorization_service.py`
- [X] T012 [US2] Add `GET /api/categorization/batches/{batch_id}/progress` endpoint that looks up `_active_jobs[batch_id]` and returns `BatchProgressResponse` (return 404 if batch_id not found) in `backend/app/routers/categorization.py`
- [X] T013 [P] [US2] Add `getBatchProgress(batchId: string)` function returning `Promise<BatchProgressResponseData>` and add `BatchProgressResponseData` type matching all fields from the API contract in `frontend/src/services/api.ts`
- [X] T014 [US2] Add polling logic to `SettingsView`: after trigger returns batch_id, poll `getBatchProgress()` every 2 seconds via `setInterval`; display progress bar (processed/total), running tallies (success, failed, skipped); stop polling when status is `completed` or `failed` in `frontend/components/SettingsView.tsx`
- [X] T015 [US2] Add completion summary panel to `SettingsView`: show total processed, rule-matched count, AI-matched count, desc-rule-matched count, skipped count, failure count, duration (completed_at − started_at), and error message if status is `failed`; re-fetch unclassified count after completion in `frontend/components/SettingsView.tsx`
- [X] T016 [US2] Add retry-after-failure UX to `SettingsView`: after a failed or partial batch, re-fetch and display the updated unclassified count, re-enable the "Classify All" button (so the user can re-trigger on remaining unclassified transactions), and show a contextual message like "N transactions still unclassified — click to retry" per FR-010 and SC-005 in `frontend/components/SettingsView.tsx`

**Checkpoint**: Users see real-time progress during classification and a detailed completion summary. Failed batches allow retry without losing previously completed results.

---

## Phase 5: User Story 3 — Configure Batch Size (Priority: P3)

**Goal**: Let users choose the batch size (transactions per AI request) before triggering classification, with a sensible default matching the environment config (50).

**Independent Test**: Set batch size to 25, trigger classification on 100 transactions, verify the system processes them in 4 separate AI sub-batches.

### Implementation for User Story 3

- [X] T017 [US3] Add `batch_size` parameter passthrough: when `batch_size` is provided in the trigger request, pass it to `_process_ai_batches()` instead of reading `CATEGORIZATION_BATCH_SIZE` from env config in `backend/app/services/categorization_service.py`
- [X] T018 [US3] Add batch size number input to `SettingsView`: default value 50 (matching `CATEGORIZATION_BATCH_SIZE` env default), min 10, max 200, with validation message for out-of-range values; include the user-configured `batch_size` in the trigger API request body in `frontend/components/SettingsView.tsx`

**Checkpoint**: Users can configure batch size before triggering. Invalid values are rejected with clear feedback.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature works end-to-end across both stacks.

- [X] T019 [P] Run frontend type check (`cd frontend && npx tsc --noEmit`) and fix any TypeScript errors
- [X] T020 [P] Run backend linter and tests (`cd backend && ruff check . && pytest`) and fix any failures
- [X] T021 Validate against quickstart.md manual test scenarios in `specs/014-batch-classify/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — can start immediately. BLOCKS all user stories.
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US2 (Phase 4)**: Depends on Phase 3 completion (needs trigger + background processing in place)
- **US3 (Phase 5)**: Backend task (T017) depends on Phase 2 only; frontend task (T018) depends on US1's SettingsView (T008)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no other story dependencies
- **US2 (P2)**: Depends on US1 — needs background processing and batch_id to poll against
- **US3 (P3)**: Backend (T017) can start after Foundational; frontend (T018) needs US1's SettingsView

### Within Each User Story

- Backend service changes before backend endpoint changes
- Backend endpoints before frontend API functions
- Frontend API functions before frontend components
- Same-file tasks are sequential (not parallel)

### Parallel Opportunities

- **Phase 2**: T001 ∥ T002 (different files)
- **Phase 3**: T007 ∥ T009 ∥ T010 (different frontend files, after backend is done)
- **Phase 4**: T013 can start alongside T011/T012 (different codebase layer)
- **Phase 6**: T019 ∥ T020 (different tech stacks)

---

## Parallel Example: User Story 1

```bash
# Phase 2: Launch foundational tasks in parallel
Task T001: "Add Pydantic models in backend/app/models/categorization.py"
Task T002: "Add BatchJobState + lock in backend/app/services/categorization_service.py"

# Phase 3 backend (sequential — same files):
Task T003 → T004 (service file)
Task T005 → T006 (router file)

# Phase 3 frontend: Launch independent tasks in parallel after T006:
Task T007: "Add API functions in frontend/src/services/api.ts"
Task T009: "Wire Settings tab in frontend/App.tsx"
Task T010: "Wire Settings button in frontend/components/Sidebar.tsx"
# Then T008 (SettingsView) which uses T007's API functions
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001–T002)
2. Complete Phase 3: User Story 1 (T003–T010)
3. **STOP and VALIDATE**: Trigger batch classify from Settings, verify transactions get categorized
4. This delivers the core ask — bulk classification from a single action

### Incremental Delivery

1. Foundational → Foundation ready
2. Add User Story 1 → Trigger + basic UI → **MVP!**
3. Add User Story 2 → Progress monitoring + retry → Users can track large jobs
4. Add User Story 3 → Batch size config → Power users can tune performance
5. Polish → Type check, lint, tests, manual validation

---

## Notes

- [P] tasks = different files, no dependencies on incomplete same-phase tasks
- [Story] label maps task to specific user story for traceability
- No schema changes needed — DuckDB tables remain unchanged
- All backend changes modify existing files; no new backend files
- One new frontend file: `frontend/components/SettingsView.tsx`
- Existing callers of `/trigger` (review page, CSV import) are unaffected — `batch_size` defaults to `None`
- `import_id = NULL` distinguishes batch-classify jobs from import-triggered batches in `categorization_batches` table
- Batch size default is 50, matching the `CATEGORIZATION_BATCH_SIZE` environment variable default
