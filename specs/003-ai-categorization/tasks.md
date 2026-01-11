# Tasks: AI-Powered Transaction Categorization

**Input**: Design documents from `/specs/003-ai-categorization/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in specification. Test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app structure**: `backend/app/`, `frontend/src/`
- Paths follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, schema changes, and configuration

- [x] T001 Add categorization environment variables to backend/app/config.py (CLAUDE_CODE_PATH, CATEGORIZATION_BATCH_SIZE, CATEGORIZATION_CONFIDENCE_THRESHOLD, CATEGORIZATION_TIMEOUT_SECONDS)
- [x] T002 Extend database schema in backend/app/database.py: add normalized_merchant, confidence_score, categorization_source columns to transactions table
- [x] T003 [P] Create categorization_rules table in backend/app/database.py with id, merchant_pattern, category_id, created_at
- [x] T004 [P] Create categorization_batches table in backend/app/database.py with id, import_id, transaction_count, success_count, failure_count, rule_match_count, ai_match_count, skipped_count, duration_ms, error_message, started_at, completed_at
- [x] T005 [P] Add indexes for normalized_merchant and categorization_source on transactions table in backend/app/database.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create Pydantic models in backend/app/models/categorization.py: CategorizationRuleCreate, CategorizationRuleResponse, CategorizationRuleListResponse
- [x] T007 [P] Create Pydantic models in backend/app/models/categorization.py: CategorizationBatchResponse, CategorizationBatchListResponse, CategorizationResult
- [x] T008 [P] Create Pydantic models in backend/app/models/categorization.py: CategorizationTriggerRequest, NormalizationRequest, NormalizationResponse
- [x] T009 Extend TransactionResponse in backend/app/models/transaction.py: add normalized_merchant, confidence_score, categorization_source fields
- [x] T010 Create merchant_normalizer.py in backend/app/services/ with normalize() function: trim whitespace, collapse spaces, remove NOISE_PREFIXES (POS DEBIT, CHECKCARD, ACH WITHDRAWAL, etc.), remove NOISE_PATTERNS (card digits, ZIP codes, store numbers)
- [x] T011 Create claude_client.py in backend/app/services/ with invoke_claude(prompt, timeout) function using subprocess with stdin piping
- [x] T012 Add retry logic to claude_client.py: with_retry() wrapper implementing 3 retries with exponential backoff (2s, 4s, 8s delays)
- [x] T013 Add JSON extraction to claude_client.py: extract_json() function to parse AI responses, handling markdown code blocks

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Automatic Categorization on Import (Priority: P1) MVP

**Goal**: When user imports transactions, uncategorized ones are automatically categorized by AI where confidence exceeds threshold

**Independent Test**: Import CSV with 50+ transactions → verify high-confidence transactions receive category assignments

### Implementation for User Story 1

- [x] T014 [US1] Create categorization_service.py in backend/app/services/ with CategorizationService class skeleton
- [x] T015 [US1] Implement get_uncategorized_transactions() in backend/app/services/categorization_service.py: query transactions where category_id IS NULL
- [x] T016 [US1] Implement build_categorization_prompt() in backend/app/services/categorization_service.py: format transactions with categories list per research.md prompt template
- [x] T017 [US1] Implement categorize_batch() in backend/app/services/categorization_service.py: invoke Claude CLI, parse response, filter by confidence threshold
- [x] T018 [US1] Implement apply_categorization_results() in backend/app/services/categorization_service.py: update transactions with category_id, confidence_score, categorization_source='ai'
- [x] T019 [US1] Implement trigger_categorization() in backend/app/services/categorization_service.py: orchestrate batching (50 per batch), call categorize_batch for each, handle graceful degradation on AI failure
- [x] T020 [US1] Create categorization router in backend/app/routers/categorization.py with POST /api/categorization/trigger endpoint
- [x] T021 [US1] Register categorization router in backend/app/main.py
- [x] T022 [US1] Add TypeScript types for CategorizationBatchResponse and CategorizationTriggerRequest in frontend/types.ts
- [x] T023 [US1] Add triggerCategorization() API function in frontend/src/services/api.ts

**Checkpoint**: User Story 1 complete - AI categorization works for imported transactions

---

## Phase 4: User Story 2 - Manual Override with Learning (Priority: P2)

**Goal**: When user manually changes transaction category, system learns rule for future imports

**Independent Test**: Change transaction category → import new transaction from same merchant → verify rule applied without AI

### Implementation for User Story 2

- [x] T024 [US2] Create rule_service.py in backend/app/services/ with RuleService class for CRUD operations on categorization_rules
- [x] T025 [US2] Implement create_rule() in backend/app/services/rule_service.py: insert rule with lowercase merchant_pattern, handle UNIQUE constraint (update if exists)
- [x] T026 [US2] Implement get_all_rules() in backend/app/services/rule_service.py: query rules ordered by created_at DESC
- [x] T027 [US2] Implement find_matching_rule() in backend/app/services/rule_service.py: substring/contains match, case-insensitive, most recent wins
- [x] T028 [US2] Implement delete_rule() in backend/app/services/rule_service.py
- [x] T029 [US2] Extend update() in backend/app/services/transaction_service.py: when category_id changes, call rule_service.create_rule() with normalized_merchant, set categorization_source='manual'
- [x] T030 [US2] Integrate rule matching into categorization_service.py: call find_matching_rule() before AI, set categorization_source='rule' for matches
- [x] T031 [US2] Add rule CRUD endpoints to backend/app/routers/categorization.py: GET /api/categorization/rules, POST /api/categorization/rules, GET /api/categorization/rules/{id}, DELETE /api/categorization/rules/{id}
- [x] T032 [US2] Add TypeScript types for CategorizationRuleResponse and CategorizationRuleCreate in frontend/types.ts
- [x] T033 [US2] Add rule API functions in frontend/src/services/api.ts: listRules(), createRule(), deleteRule()

**Checkpoint**: User Story 2 complete - manual corrections create rules that apply on future imports

---

## Phase 5: User Story 3 - Merchant Name Normalization (Priority: P3)

**Goal**: Transaction descriptions are cleaned and normalized for better display and AI accuracy

**Independent Test**: Import transaction with "POS DEBIT 1234 AMAZON SEATTLE WA" → verify display shows "Amazon"

### Implementation for User Story 3

- [x] T034 [US3] Enhance normalize() in backend/app/services/merchant_normalizer.py: add title-case conversion for display, handle .COM/.NET domains, extract brand names
- [x] T035 [US3] Integrate normalization into transaction creation: populate normalized_merchant field when transactions are imported/created
- [x] T036 [US3] Add POST /api/categorization/normalize preview endpoint in backend/app/routers/categorization.py
- [x] T037 [US3] Update TransactionsView.tsx in frontend/components/ to display normalized_merchant when available (fallback to description)
- [x] T038 [US3] Add NormalizationResponse type and previewNormalization() API function in frontend/src/services/api.ts

**Checkpoint**: User Story 3 complete - merchants display as clean names

---

## Phase 6: User Story 4 - Batch Processing Visibility (Priority: P4)

**Goal**: Admins can see categorization metrics: batch sizes, success rates, timing

**Independent Test**: Trigger categorization → verify logs show batch count, success/failure counts, duration

### Implementation for User Story 4

- [x] T039 [US4] Create batch_service.py in backend/app/services/ with create_batch(), update_batch(), complete_batch() functions
- [x] T040 [US4] Integrate batch tracking into categorization_service.py: create batch at start, update counters during processing, complete with duration_ms
- [x] T041 [US4] Add structured logging throughout categorization_service.py: log batch start, per-batch results, completion summary, errors (without sensitive data)
- [x] T042 [US4] Add GET /api/categorization/batches endpoint in backend/app/routers/categorization.py
- [x] T043 [US4] Add TypeScript type for CategorizationBatchListResponse and listBatches() API function in frontend/src/services/api.ts

**Checkpoint**: User Story 4 complete - processing metrics visible for debugging

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration, edge cases, and final validation

- [x] T044 [P] Handle edge case: AI returns invalid category_id (log warning, leave uncategorized)
- [x] T045 [P] Handle edge case: empty transaction descriptions (skip AI, log as unprocessable)
- [x] T046 [P] Handle edge case: descriptions > 500 chars (truncate for AI, preserve full original)
- [x] T047 Sanitize prompts in categorization_service.py: remove account numbers and card numbers using regex patterns before sending to AI
- [x] T048 Add timeout handling in claude_client.py: catch subprocess.TimeoutExpired, log, return empty result
- [ ] T049 Run quickstart.md validation: execute all curl commands and verify expected responses

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - Stories can proceed in priority order (P1 → P2 → P3 → P4)
  - US2 integrates with US1's categorization_service
  - US3 enhances normalization used by US1/US2
  - US4 adds tracking to US1's categorization flow
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Integrates with US1's categorization_service but independently testable
- **User Story 3 (P3)**: Can start after Foundational - Enhances normalization, independently testable
- **User Story 4 (P4)**: Can start after Foundational - Adds tracking, independently testable

### Within Each User Story

- Models/utilities before services
- Services before endpoints
- Backend before frontend
- Core implementation before integration

### Parallel Opportunities

- T003, T004, T005 (schema tables) can run in parallel
- T006, T007, T008 (Pydantic models) can run in parallel after T006 skeleton
- T044, T045, T046 (edge cases) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch schema tasks together:
Task: "Create categorization_rules table in backend/app/database.py"
Task: "Create categorization_batches table in backend/app/database.py"
Task: "Add indexes for normalized_merchant on transactions"

# Launch Pydantic model groups together (after T006):
Task: "Create CategorizationBatchResponse models in categorization.py"
Task: "Create CategorizationTriggerRequest models in categorization.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (schema + config)
2. Complete Phase 2: Foundational (models + utilities)
3. Complete Phase 3: User Story 1 (AI categorization)
4. **STOP and VALIDATE**: Test with real transactions
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → AI auto-categorization works → MVP!
3. Add User Story 2 → Learning rules work → Enhanced
4. Add User Story 3 → Better merchant display → Polished UX
5. Add User Story 4 → Observability → Production-ready

### Single Developer Path

Priority order ensures highest-value features first:
1. P1: Users get AI categorization (core value)
2. P2: Users get learning rules (reduces AI dependency)
3. P3: Users get clean merchant names (better UX)
4. P4: Admins get visibility (operational readiness)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Graceful degradation: AI failures never block imports
