# Tasks: Description-Based Pattern Rules

**Input**: Design documents from `/specs/010-description-pattern-rules/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included — the quickstart.md specifies a testing strategy with unit and integration tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database table creation and shared Pydantic models needed by all user stories

- [x] T001 Add `description_pattern_rules` table DDL to `backend/app/database.py` — CREATE TABLE with columns (id VARCHAR(36) PK, account_id VARCHAR(36) FK, description_pattern VARCHAR(500), category_id VARCHAR(36) FK, created_at TIMESTAMP), UNIQUE(account_id, description_pattern), and indexes on account_id and category_id per data-model.md
- [x] T002 Add Pydantic models for description pattern rules in `backend/app/models/categorization.py` — add `DescriptionPatternRuleCreate` (description_pattern str 1-500, account_id str, category_id str), `DescriptionPatternRuleResponse` (id, account_id, account_name Optional[str], description_pattern, category_id, category_name Optional[str], rule_type Literal["description"], created_at), and extend `CategorizationRuleResponse` with optional `rule_type` Literal["merchant"] default, `account_id` Optional, `account_name` Optional, `description_pattern` Optional fields. Add `desc_rule_match_count` int field to `CategorizationBatchResponse`. Add `PatternPreviewRequest` (description str) and `PatternPreviewResponse` (original str, pattern str) models.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core services that MUST be complete before any user story integration

- [x] T003 [P] Create pattern extraction module `backend/app/services/pattern_extractor.py` — implement `extract_pattern(description: str) -> str` function that: (1) strips leading/trailing whitespace, (2) replaces sequences of 3+ digits (and alphanumeric tokens ending in 3+ digits like "Bro461026") with `*`, (3) collapses multiple `*` separated only by whitespace into a single `*`, (4) lowercases the result. Handle edge cases: empty/blank descriptions return empty string, short descriptions like "ATM" returned as-is lowercase, descriptions with no numeric portions returned as-is lowercase. Per research.md R-002.
- [x] T004 [P] Create description rule service `backend/app/services/desc_rule_service.py` — implement `DescRuleService` class with: `create_rule(data: DescriptionPatternRuleCreate) -> DescriptionPatternRuleResponse` (upsert — normalize pattern lowercase, if UNIQUE(account_id, pattern) exists then update category_id + created_at, else insert new row; per FR-006), `find_matching_rule(description: str, account_id: str) -> Optional[DescriptionPatternRuleResponse]` (load all rules for account_id ordered by created_at DESC, convert each stored wildcard pattern to anchored regex by escaping special chars then replacing `*` with `.*`, match against lowercased description; return first match per R-003), `get_all_rules(account_id: Optional[str], category_id: Optional[str], limit: int, offset: int) -> list[DescriptionPatternRuleResponse]` (join with categories and accounts tables for names), `get_by_id(rule_id: str) -> Optional[DescriptionPatternRuleResponse]`, `delete_rule(rule_id: str) -> bool`, `count_rules() -> int`. Use `get_db()` context manager, UUID generation, and module-level `desc_rule_service = DescRuleService()` singleton. Follow existing `rule_service.py` patterns.
- [x] T005 [P] Write unit tests for pattern extraction in `backend/tests/test_pattern_extractor.py` — test cases: "DIRECT DEPOSIT Fidelity Bro461026 (Cash)" → "direct deposit fidelity bro* (cash)", "CHECK #1234 DEPOSIT" → "check #* deposit", "DIVIDEND REINVEST 98765" → "dividend reinvest *", "GROCERY STORE" → "grocery store" (no change), "ATM" → "atm", "" → "", "  " → "", "Route 66 Diner" → "route 66 diner" (2 digits preserved), "Transfer 12345 to 67890" → "transfer * to *" (multiple replacements), case insensitivity verified.
- [x] T006 [P] Write unit tests for description rule service in `backend/tests/test_desc_rule_service.py` — test cases: create rule and verify fields, upsert (same pattern+account updates category), find_matching_rule with wildcard pattern, case-insensitive matching, account scoping (rule for account A does NOT match account B), most-recent-rule-wins on conflict, delete rule, get_all_rules with filtering, get_by_id returns None for missing.

**Checkpoint**: Foundation ready — pattern extraction and rule CRUD are independently testable via `cd backend && pytest tests/test_pattern_extractor.py tests/test_desc_rule_service.py`

---

## Phase 3: User Story 1 — Auto-Learn Category from Manual Correction (Priority: P1) MVP

**Goal**: When a user manually categorizes a transaction with no normalized merchant, the system auto-creates a description-based pattern rule scoped to that account.

**Independent Test**: Manually update a transaction's category via PUT /api/transactions/{id}. Verify a description_pattern_rules row is created with the correct pattern, account_id, and category_id. Verify NO rule is created when the transaction has a normalized_merchant.

### Implementation for User Story 1

- [x] T007 [US1] Modify `backend/app/services/transaction_service.py` — in the `update()` method, after the existing `if category_changed and new_category_id and existing.normalized_merchant:` block that calls `_create_rule_from_correction`, add an `elif` branch: if `category_changed and new_category_id and not existing.normalized_merchant and existing.description and existing.description.strip()`: import and call `extract_pattern(existing.description)`, then if pattern is non-empty, call `desc_rule_service.create_rule(DescriptionPatternRuleCreate(description_pattern=pattern, account_id=existing.account_id, category_id=new_category_id))`. Wrap in try/except with logger.warning on failure (matching existing merchant-rule error handling). Per FR-001, FR-010, FR-011.
- [x] T008 [US1] Write integration test in `backend/tests/test_categorization_integration.py` — test `test_manual_correction_creates_desc_rule`: create an account, create a transaction with description "DIRECT DEPOSIT Fidelity Bro461026 (Cash)" and no normalized_merchant, update its category via transaction_service.update(), verify a row exists in description_pattern_rules with expected pattern and account_id. Also test `test_manual_correction_with_merchant_skips_desc_rule`: same flow but transaction HAS normalized_merchant — verify NO description_pattern_rule created (only merchant rule). Also test `test_empty_description_skips_desc_rule`: transaction with empty description — verify no rule created.

**Checkpoint**: User Story 1 complete — manual corrections for transactions without normalized merchants now auto-learn description rules.

---

## Phase 4: User Story 2 — Pattern Matching During Categorization Pipeline (Priority: P2)

**Goal**: The categorization pipeline applies description-based pattern rules as a fallback after merchant rules and before AI categorization.

**Independent Test**: Create a description pattern rule manually, then trigger categorization for an uncategorized transaction with a matching description in the same account. Verify it gets categorized with source='desc_rule'.

### Implementation for User Story 2

- [x] T009 [US2] Modify `backend/app/services/categorization_service.py` — in `_apply_rules()` method, after the existing merchant-rule matching loop, add a second pass for transactions still in the `remaining` list: for each remaining transaction, call `desc_rule_service.find_matching_rule(tx["description"], tx["account_id"])`. If match found, apply with `self.apply_categorization_results([result], source="desc_rule")` and confidence=1.0. Track count separately as `desc_rule_match_count`. Return updated remaining list and both match counts. Update `trigger_categorization()` to pass `desc_rule_match_count` into the batch response.
- [x] T010 [US2] Add `desc_rule_match_count` column to `categorization_batches` table in `backend/app/database.py` — add `desc_rule_match_count INTEGER NOT NULL DEFAULT 0` column to the CREATE TABLE statement for categorization_batches. Update any INSERT statements in categorization_service.py that write to this table to include the new field.
- [x] T011 [US2] Write integration test in `backend/tests/test_categorization_integration.py` — test `test_desc_rule_applied_in_pipeline`: create account, create description pattern rule, create uncategorized transaction with matching description and no normalized_merchant in same account, trigger categorization, verify transaction gets category from desc rule with source='desc_rule'. Test `test_merchant_rule_takes_precedence`: create both a merchant rule and description rule that could match, verify merchant rule wins. Test `test_desc_rule_account_scoping`: create desc rule for account A, create transaction in account B with matching description, verify rule does NOT apply.

**Checkpoint**: User Story 2 complete — categorization pipeline now applies description rules as a fallback.

---

## Phase 5: User Story 3 — Pattern Extraction with Trailing Variation (Priority: P2)

**Goal**: The pattern extraction algorithm correctly generalizes variable trailing portions while preserving stable prefixes and suffixes.

**Independent Test**: Already covered by T005 (pattern extraction unit tests). This phase ensures the extraction is integrated end-to-end: a manual correction on a description with trailing numbers creates a generalized pattern that matches future similar descriptions.

### Implementation for User Story 3

- [x] T012 [US3] Add additional pattern extraction test cases to `backend/tests/test_pattern_extractor.py` — test edge cases from spec: "PAYMENT CHASE CREDIT CRD AUTOPAY 240315" → generalize trailing date-like number, "ACH CREDIT EMPLOYER INC 20240315001234" → generalize long trailing reference, "INTEREST PAYMENT" → no change (no numbers), mixed alphanumeric tokens "INV461026BUY" → generalize the numeric portion. Verify patterns round-trip correctly through `find_matching_rule` by creating a rule from the extracted pattern and confirming it matches the original description and similar variants.
- [x] T013 [US3] Write end-to-end test in `backend/tests/test_categorization_integration.py` — test `test_pattern_extraction_matches_future_variants`: create account, create transaction with description "DIRECT DEPOSIT Fidelity Bro461026 (Cash)", manually correct category, then create a NEW transaction with description "DIRECT DEPOSIT Fidelity Bro458529 (Cash)" in same account, trigger categorization, verify new transaction gets same category with source='desc_rule'.

**Checkpoint**: User Story 3 complete — pattern extraction proven to generalize correctly across real-world description variants.

---

## Phase 6: User Story 4 — View and Manage Description Rules (Priority: P3)

**Goal**: Users can view description rules alongside merchant rules and delete them via the API and frontend.

**Independent Test**: Call GET /api/categorization/rules and verify description rules appear with rule_type="description", account_name, and description_pattern fields. Call DELETE and verify rule is removed.

### Implementation for User Story 4

- [x] T014 [P] [US4] Extend GET /api/categorization/rules endpoint in `backend/app/routers/categorization.py` — add optional `rule_type` query parameter ("merchant"|"description"). Modify `list_rules()` to: (1) fetch merchant rules from existing rule_service (add rule_type="merchant" to each), (2) fetch description rules from desc_rule_service, (3) merge both lists sorted by created_at DESC, (4) apply pagination (limit/offset) to merged list, (5) return unified `CategorizationRuleListResponse`. When rule_type filter is provided, only fetch from the relevant source.
- [x] T015 [P] [US4] Extend POST /api/categorization/rules endpoint in `backend/app/routers/categorization.py` — accept the updated request model. If `description_pattern` is provided (with `account_id`), delegate to `desc_rule_service.create_rule()`. If `merchant_pattern` is provided, delegate to existing `rule_service.create_rule()`. Validate mutual exclusivity per contracts/api.md.
- [x] T016 [P] [US4] Extend DELETE /api/categorization/rules/{rule_id} endpoint in `backend/app/routers/categorization.py` — try deleting from `rule_service` first; if not found (returns False), try `desc_rule_service.delete_rule(rule_id)`. Return 404 only if neither service found the rule.
- [x] T017 [P] [US4] Add POST /api/categorization/preview-pattern endpoint in `backend/app/routers/categorization.py` — accepts `PatternPreviewRequest`, calls `extract_pattern(request.description)`, returns `PatternPreviewResponse` with original and extracted pattern.
- [x] T018 [US4] Update TypeScript interfaces in `frontend/src/services/api.ts` — extend `CategorizationRuleResponseData` with optional fields: `rule_type: "merchant" | "description"`, `description_pattern: string | null`, `account_id: string | null`, `account_name: string | null`. Add `CategorizationRuleCreateData` union type supporting both merchant and description rule creation. Add `rule_type` optional parameter to `listRules()`. Add `previewPattern(description: string)` API function. Add `desc_rule_match_count` to batch response type.
- [x] T019 [US4] Write API tests in `backend/tests/test_categorization_integration.py` — test `test_list_rules_includes_both_types`: create one merchant rule and one description rule, call list endpoint, verify both appear with correct rule_type. Test `test_list_rules_filter_by_type`: verify rule_type filter returns only matching type. Test `test_delete_description_rule`: create description rule, delete by ID, verify 204 response and rule no longer in list. Test `test_preview_pattern_endpoint`: POST description, verify extracted pattern in response.

**Checkpoint**: User Story 4 complete — users can view, create, and delete description rules through the API. Frontend types are updated.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T020 Run full backend test suite via `cd backend && pytest` — verify all new and existing tests pass with no regressions
- [x] T021 Run frontend type check via `cd frontend && npx tsc --noEmit` — verify TypeScript changes compile cleanly
- [x] T022 Verify quickstart.md validation — start app via `./fintrak start -d`, manually test: (1) create transaction without normalized_merchant, (2) change its category, (3) verify desc rule created, (4) import similar transaction, (5) verify auto-categorized

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (models needed by services)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs pattern_extractor + desc_rule_service)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (needs desc_rule_service for matching)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (needs pattern_extractor); benefits from US1+US2 for end-to-end test
- **User Story 4 (Phase 6)**: Depends on Phase 2 (needs desc_rule_service for API endpoints)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no cross-story dependencies
- **User Story 2 (P2)**: Can start after Phase 2 — independent of US1 (rules can be created manually)
- **User Story 3 (P2)**: Can start after Phase 2 — US1+US2 integration test (T013) benefits from both but is not blocked
- **User Story 4 (P3)**: Can start after Phase 2 — independent of US1/US2/US3

### Within Each User Story

- Models before services (Phase 1 → Phase 2)
- Services before integration (Phase 2 → US implementation)
- Implementation before tests where tests depend on implementation

### Parallel Opportunities

- T003 and T004 can run in parallel (different new files, no dependencies)
- T005 and T006 can run in parallel (different test files)
- US1, US2, US3, US4 can all start after Phase 2 completes (if team capacity allows)
- Within US4: T014, T015, T016, T017 can all run in parallel (different endpoints in same file, but independent logic)

---

## Parallel Example: Phase 2

```bash
# Launch foundational tasks in parallel:
Task: "Create pattern_extractor.py" (T003)
Task: "Create desc_rule_service.py" (T004)
Task: "Write pattern extraction tests" (T005)
Task: "Write desc rule service tests" (T006)
```

## Parallel Example: User Story 4

```bash
# Launch all endpoint tasks in parallel:
Task: "Extend GET /rules endpoint" (T014)
Task: "Extend POST /rules endpoint" (T015)
Task: "Extend DELETE /rules endpoint" (T016)
Task: "Add preview-pattern endpoint" (T017)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T008)
4. **STOP and VALIDATE**: Manual correction creates description rules
5. This alone delivers core value — the learning mechanism

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Learning works (MVP!)
3. Add User Story 2 → Test independently → Pipeline applies learned rules
4. Add User Story 3 → Test independently → Patterns generalize correctly
5. Add User Story 4 → Test independently → Users can manage rules
6. Polish → Full regression validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (rule creation from corrections)
   - Developer B: User Story 2 (pipeline integration)
   - Developer C: User Story 4 (API endpoints + frontend)
3. User Story 3 tests can run after US1+US2 are complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- All new backend code follows existing patterns: service classes with singletons, Pydantic models, DuckDB via get_db()
