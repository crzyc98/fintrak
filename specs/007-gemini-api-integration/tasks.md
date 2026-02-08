# Tasks: Gemini API Integration

**Input**: Design documents from `/specs/007-gemini-api-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Basic unit tests included for new module per plan.md.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths use web app convention: `backend/`

---

## Phase 1: Setup

**Purpose**: Dependencies and configuration infrastructure

- [x] T001 Add google-genai>=1.0.0 to backend/requirements.txt (NOTE: Updated to use new SDK - google-generativeai is deprecated)
- [x] T002 [P] Create .env.example with GEMINI_API_KEY placeholder at project root
- [x] T003 [P] Add GEMINI_API_KEY and GEMINI_MODEL settings to backend/app/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core error classes and module structure that all user stories depend on

**⚠️ CRITICAL**: User story implementation cannot begin until this phase completes

- [x] T004 Create generic AI error classes (AIClientError, AITimeoutError, AIInvocationError) in backend/app/services/gemini_client.py
- [x] T005 Add deprecation notice to backend/app/services/claude_client.py docstring

**Checkpoint**: Foundation ready - error classes defined, old client marked deprecated

---

## Phase 3: User Story 1 - AI Categorization with Gemini (Priority: P1) 🎯 MVP

**Goal**: Replace Claude CLI subprocess with Gemini API for transaction categorization

**Independent Test**: Trigger categorization on uncategorized transactions; verify categories assigned via Gemini API with confidence scores

### Implementation for User Story 1

- [x] T006 [US1] Implement invoke_gemini() function in backend/app/services/gemini_client.py
- [x] T007 [US1] Implement extract_json() function with fallback parsing in backend/app/services/gemini_client.py
- [x] T008 [US1] Implement invoke_and_parse() function in backend/app/services/gemini_client.py
- [x] T009 [US1] Update imports in backend/app/services/categorization_service.py to use gemini_client
- [x] T010 [US1] Update error class references in backend/app/services/categorization_service.py (ClaudeClientError → AIClientError)
- [x] T011 [US1] Add validation for missing GEMINI_API_KEY with clear error message in backend/app/services/gemini_client.py

**Checkpoint**: Core Gemini integration complete - categorization works with valid API key

---

## Phase 4: User Story 2 - Graceful Error Handling (Priority: P2)

**Goal**: Implement retry logic with exponential backoff for transient API failures

**Independent Test**: Simulate API failures; verify retry behavior with 2s/4s/8s delays and proper error logging

### Implementation for User Story 2

- [x] T012 [US2] Implement with_retry() function with exponential backoff in backend/app/services/gemini_client.py
- [x] T013 [US2] Map Gemini SDK exceptions to generic AI errors in backend/app/services/gemini_client.py
- [x] T014 [US2] Add logging for retry attempts and final failures in backend/app/services/gemini_client.py
- [x] T015 [US2] Integrate retry logic into invoke_and_parse() in backend/app/services/gemini_client.py

**Checkpoint**: Error handling complete - transient failures retry automatically, permanent failures log and propagate

---

## Phase 5: User Story 3 - Configuration Flexibility (Priority: P3)

**Goal**: Enable model and credentials configuration via environment variables

**Independent Test**: Change GEMINI_MODEL env var; verify the specified model is used

### Implementation for User Story 3

- [x] T016 [US3] Implement model configuration using GEMINI_MODEL from config in backend/app/services/gemini_client.py
- [x] T017 [US3] Add logging to show which model is being used on initialization in backend/app/services/gemini_client.py

**Checkpoint**: Configuration complete - model switchable via environment without code changes

---

## Phase 6: Polish & Validation

**Purpose**: Testing, documentation, and final validation

- [x] T018 [P] Create unit tests for gemini_client module in backend/tests/test_gemini_client.py
- [x] T019 [P] Update quickstart.md with actual test commands in specs/007-gemini-api-integration/quickstart.md
- [ ] T020 Run end-to-end validation per quickstart.md instructions (BLOCKED: Requires GEMINI_API_KEY)
- [ ] T021 Verify categorization works with real Gemini API call (BLOCKED: Requires GEMINI_API_KEY)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on T001 (requirements installed)
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T006-T008 must exist for retry wrapper)
- **User Story 3 (Phase 5)**: Can run after Phase 2; independent of Phase 4
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1**: Depends on Foundational only - core MVP functionality
- **US2**: Depends on US1 (wraps invoke_gemini with retry logic)
- **US3**: Independent of US2; can parallelize with US2 after US1

### Task Dependencies Within Stories

```
Phase 1: T001 → T002, T003 (parallel after T001)

Phase 2: T004 → T005 (parallel possible, but sequential for clarity)

Phase 3 (US1):
  T006 (invoke_gemini)
    ↓
  T007 (extract_json) - can parallel with T006
    ↓
  T008 (invoke_and_parse) - depends on T006, T007
    ↓
  T009, T010 (update categorization_service) - parallel, depend on T008
    ↓
  T011 (API key validation) - can integrate anytime in US1

Phase 4 (US2):
  T012 (with_retry)
    ↓
  T013 (error mapping) - can parallel with T012
    ↓
  T014 (logging) - depends on T012, T013
    ↓
  T015 (integrate retry) - depends on all above

Phase 5 (US3):
  T016 (model config)
    ↓
  T017 (logging) - depends on T016

Phase 6: T018, T019 parallel → T020 → T021
```

### Parallel Opportunities

**Within Phase 1:**
```
T001 (install deps)
  ↓
T002, T003 in parallel
```

**Within Phase 3 (US1):**
```
T006, T007 in parallel
  ↓
T008
  ↓
T009, T010, T011 in parallel
```

**US2 and US3 can run in parallel after US1 core (T006-T008):**
```
After T008:
  - Team A: T012-T015 (US2 retry logic)
  - Team B: T016-T017 (US3 configuration)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T005)
3. Complete Phase 3: User Story 1 (T006-T011)
4. **STOP and VALIDATE**: Test with real API key
5. Deploy if core categorization works

### Incremental Delivery

1. Setup + Foundational → Dependencies ready
2. User Story 1 → MVP: Categorization works ✓
3. User Story 2 → Reliability: Retries on failure ✓
4. User Story 3 → Flexibility: Model configurable ✓
5. Polish → Production ready ✓

### Single Developer Flow

Execute in task order T001 → T021 sequentially.

### Parallel Team Strategy

With 2 developers after US1:
- Developer A: US2 (T012-T015) - Error handling
- Developer B: US3 (T016-T017) + Tests (T018) - Config and testing

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Setup | 3 | Dependencies, env config |
| Foundational | 2 | Error classes, deprecation |
| US1 (P1) MVP | 6 | Core Gemini integration |
| US2 (P2) | 4 | Retry logic |
| US3 (P3) | 2 | Model configuration |
| Polish | 4 | Tests, validation |
| **Total** | **21** | |

---

## Notes

- All tasks modify backend code only; no frontend changes
- T018 (unit tests) uses mocking to avoid real API calls
- T021 requires valid GEMINI_API_KEY for real validation
- claude_client.py retained but unused (rollback option)
