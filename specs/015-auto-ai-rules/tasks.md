# Tasks: Auto-Create Rules from AI Classifications

**Input**: Design documents from `/specs/015-auto-ai-rules/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — integration tests for core behavior validation.

**Organization**: Tasks are grouped by user story. US3 (Deduplication) and US4 (Source Tracking) are cross-cutting — deduplication logic is embedded in US1/US2 implementation, and source tracking is in the Foundational phase since all stories depend on it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration and schema changes needed before any feature work

- [x] T001 [P] Add `AUTO_RULE_CONFIDENCE_THRESHOLD` config variable in `backend/app/config.py` — float from env var, default 0.9
- [x] T002 [P] Add `source VARCHAR(10) DEFAULT 'manual'` column to `categorization_rules` table via `ALTER TABLE ADD COLUMN IF NOT EXISTS` in `backend/app/database.py` `init_db()`
- [x] T003 [P] Add `source VARCHAR(10) DEFAULT 'manual'` column to `description_pattern_rules` table via `ALTER TABLE ADD COLUMN IF NOT EXISTS` in `backend/app/database.py` `init_db()`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update models and services to support `source` field — MUST complete before any user story work

**Covers**: US4 (Distinguishable Rule Sources) — source tracking infrastructure

- [x] T004 [P] Add `source: Optional[str] = "manual"` field to `CategorizationRuleCreate` model in `backend/app/models/categorization.py`
- [x] T005 [P] Add `source: Optional[str] = "manual"` field to `DescriptionPatternRuleCreate` model in `backend/app/models/categorization.py`
- [x] T006 [P] Add `source: str = "manual"` field to `CategorizationRuleResponse` model in `backend/app/models/categorization.py`
- [x] T007 [P] Add `source: str = "manual"` field to `DescriptionPatternRuleResponse` model in `backend/app/models/categorization.py`
- [x] T008 Update `create_rule()` in `backend/app/services/rule_service.py` to read `data.source` and include `source` in INSERT statement (depends on T004)
- [x] T009 Update `create_rule()` in `backend/app/services/desc_rule_service.py` to read `data.source` and include `source` in INSERT and DELETE+INSERT upsert paths (depends on T005)
- [x] T010 [P] Update SELECT queries in `get_all_rules()` in `backend/app/services/rule_service.py` to include `source` column in results (depends on T006)
- [x] T011 [P] Update SELECT queries in `backend/app/services/desc_rule_service.py` to include `source` column in results (depends on T007)

**Checkpoint**: Source field flows through schema → models → services → API responses. Rules list endpoint now returns `source` for each rule. Existing rules show as `"manual"`.

---

## Phase 3: User Story 1 — Automatic Merchant Rule Learning (Priority: P1) — MVP

**Goal**: After AI classification, auto-create merchant rules from high-confidence results so the same merchant never needs AI again.

**Independent Test**: Run AI classification → verify merchant rules created → re-classify same merchants → verify they hit rules (not AI).

### Implementation for User Story 1

- [x] T012 [US1] Add `_create_rules_from_ai_results()` method to `CategorizationService` in `backend/app/services/categorization_service.py` — accepts list of `UnifiedAIResult` and list of transaction dicts; collects merchant rule candidates where `confidence >= AUTO_RULE_CONFIDENCE_THRESHOLD` and `normalized_merchant` is present and category was assigned (not just enrichment)
- [x] T013 [US1] Implement merchant deduplication within batch in `_create_rules_from_ai_results()` in `backend/app/services/categorization_service.py` — group candidates by `normalized_merchant`, keep only the highest-confidence result per merchant (FR-007)
- [x] T014 [US1] Implement merchant rule creation loop in `_create_rules_from_ai_results()` in `backend/app/services/categorization_service.py` — for each deduplicated merchant candidate: check if rule exists via `rule_service.find_matching_rule()`, skip if exists (FR-003/FR-004), otherwise call `rule_service.create_rule()` with `source="ai"`
- [x] T015 [US1] Call `_create_rules_from_ai_results()` from `apply_unified_results()` in `backend/app/services/categorization_service.py` — invoke after the main result-application loop completes, pass the full results list and transactions list; log summary of rules created

**Checkpoint**: AI classification now auto-creates merchant rules. Running classification twice on same data creates rules on first run, uses them on second run.

---

## Phase 4: User Story 2 — Description Pattern Rule Learning (Priority: P2)

**Goal**: For transactions without a normalized merchant, auto-create description pattern rules from high-confidence AI results.

**Independent Test**: Run AI classification on transactions with no merchant → verify description pattern rules created → re-classify similar descriptions → verify they hit rules.

### Implementation for User Story 2

- [x] T016 [US2] Extend `_create_rules_from_ai_results()` in `backend/app/services/categorization_service.py` to collect description pattern candidates — filter results where `confidence >= AUTO_RULE_CONFIDENCE_THRESHOLD`, no `normalized_merchant`, and category was assigned; requires access to transaction `description` and `account_id` from the transactions list
- [x] T017 [US2] Implement pattern validation in `_create_rules_from_ai_results()` in `backend/app/services/categorization_service.py` — call `extract_pattern()` from `backend/app/services/pattern_extractor.py`; skip if pattern is empty, equals just `*`, or is shorter than 3 characters after stripping `*` characters (FR-008)
- [x] T018 [US2] Implement description rule creation loop in `_create_rules_from_ai_results()` in `backend/app/services/categorization_service.py` — for each valid pattern candidate: check if rule exists via `desc_rule_service.find_matching_rule(description, account_id)`, skip if exists (FR-003), otherwise call `desc_rule_service.create_rule()` with `source="ai"` and the transaction's `account_id`

**Checkpoint**: Both merchant rules and description pattern rules are auto-created from AI results. Full self-learning pipeline is operational.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Testing and validation across all stories

- [x] T019 [P] Create integration test file `backend/tests/test_auto_rule_creation.py` with test fixtures — in-memory DuckDB setup, helper to insert test transactions and categories, import of `CategorizationService`
- [x] T020 [P] Add test: high-confidence AI result creates merchant rule in `backend/tests/test_auto_rule_creation.py` — mock AI result with confidence 0.95 and normalized_merchant, verify rule created with source="ai"
- [x] T021 [P] Add test: low-confidence AI result does NOT create rule in `backend/tests/test_auto_rule_creation.py` — mock AI result with confidence 0.75, verify no rule created
- [x] T022 [P] Add test: existing rule prevents duplicate creation in `backend/tests/test_auto_rule_creation.py` — pre-create a merchant rule, run AI classification for same merchant, verify no new rule and existing rule unchanged
- [x] T023 [P] Add test: same merchant in batch uses highest confidence in `backend/tests/test_auto_rule_creation.py` — two AI results for same merchant with different categories/confidences, verify rule matches the higher-confidence result
- [x] T024 [P] Add test: description pattern rule created when no merchant in `backend/tests/test_auto_rule_creation.py` — AI result with no normalized_merchant, verify description pattern rule created
- [x] T025 [P] Add test: generic/empty pattern skipped in `backend/tests/test_auto_rule_creation.py` — AI result where description yields pattern "*" or empty, verify no rule created
- [x] T026 Run existing test suite via `cd backend && pytest` to verify no regressions in rule matching, manual corrections, or AI classification flow
- [ ] T027 Run quickstart.md validation — start app, import CSV, run classification, verify rules appear in rules list with source "ai", re-import and re-classify to confirm rules are used

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001, T002, T003 all run in parallel
- **Foundational (Phase 2)**: Depends on Phase 1 — T004-T007 (models) run in parallel, then T008-T011 (services)
- **US1 (Phase 3)**: Depends on Phase 2 — T012 → T013 → T014 → T015 (sequential within method)
- **US2 (Phase 4)**: Depends on Phase 3 — extends the same method created in US1
- **Polish (Phase 5)**: T019-T025 (test writing) can start after Phase 4; T026-T027 must run after all implementation

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational phase only — can be independently tested
- **US2 (P2)**: Depends on US1 — extends `_create_rules_from_ai_results()` method created in US1
- **US3 (P2)**: Embedded in US1 (T014) and US2 (T018) — the "check if exists" logic
- **US4 (P3)**: Implemented in Foundational phase (T004-T011) — source field infrastructure

### Parallel Opportunities

```bash
# Phase 1: All setup tasks in parallel
Task: T001  # config.py
Task: T002  # database.py (categorization_rules)
Task: T003  # database.py (description_pattern_rules)

# Phase 2: Model updates in parallel, then service updates in parallel
Task: T004, T005, T006, T007  # All in categorization.py but independent fields
Task: T010, T011              # Different service files

# Phase 5: All test-writing tasks in parallel
Task: T019, T020, T021, T022, T023, T024, T025
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T011)
3. Complete Phase 3: User Story 1 (T012-T015)
4. **STOP and VALIDATE**: Run classification → verify merchant rules auto-created
5. This alone delivers ~70% of the value (most transactions have merchants)

### Incremental Delivery

1. Setup + Foundational → Source tracking ready
2. Add US1 (merchant rules) → Test → Deploy (MVP!)
3. Add US2 (description patterns) → Test → Deploy
4. Write tests + validate → Full feature complete

---

## Notes

- T002 and T003 touch the same file (`database.py`) but different sections — can be done as one edit
- T004-T007 all touch `categorization.py` — can be done as one edit adding all 4 fields
- T012-T015 build a single method incrementally — treat as one logical unit
- Total: 27 tasks across 6 existing files + 1 new test file
