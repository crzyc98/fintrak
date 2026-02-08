# Tasks: Date Range Presets

**Input**: Design documents from `/specs/006-date-range-presets/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: No automated tests requested. Manual testing via quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/components/` for React components
- Primary file: `frontend/components/TransactionsView.tsx`

---

## Phase 1: Setup

**Purpose**: No setup needed - this feature modifies an existing component

**Status**: ✅ SKIP - Project already initialized, no new files or dependencies required

---

## Phase 2: Foundational

**Purpose**: Add shared types and utility functions that all user stories will use

- [x] T001 Add DatePreset type and DATE_PRESETS constant array in `frontend/components/TransactionsView.tsx` (after imports)
- [x] T002 Add formatDate helper function for ISO date string conversion in `frontend/components/TransactionsView.tsx`
- [x] T003 Add activePreset state variable to component state in `frontend/components/TransactionsView.tsx`

**Checkpoint**: Foundation ready - preset definitions and state exist, user story implementation can begin

---

## Phase 3: User Story 1 - Quick Filter by Common Time Periods (Priority: P1) 🎯 MVP

**Goal**: Users can click preset buttons to instantly filter transactions to common time periods

**Independent Test**: Click any preset button and verify transactions filter to correct date range, From/To inputs update

### Implementation for User Story 1

- [x] T004 [US1] Implement handlePresetClick function that computes dates and updates filters in `frontend/components/TransactionsView.tsx`
- [x] T005 [US1] Add preset buttons UI row above From/To date inputs in filter panel in `frontend/components/TransactionsView.tsx`
- [x] T006 [US1] Wire preset button onClick to handlePresetClick handler in `frontend/components/TransactionsView.tsx`

**Checkpoint**: User Story 1 complete - users can click presets to filter transactions

---

## Phase 4: User Story 2 - Visual Feedback for Active Preset (Priority: P2)

**Goal**: Users see which preset is currently active via visual highlighting

**Independent Test**: Click a preset, verify it shows blue highlighted state; manually edit date, verify highlight clears

### Implementation for User Story 2

- [x] T007 [US2] Add conditional className for active preset state (blue background when active) in `frontend/components/TransactionsView.tsx`
- [x] T008 [US2] Modify handleFilterChange to clear activePreset when date_from or date_to manually changed in `frontend/components/TransactionsView.tsx`

**Checkpoint**: User Story 2 complete - active preset shows visual indicator, manual edits clear it

---

## Phase 5: User Story 3 - Clear Preset on Filter Reset (Priority: P2)

**Goal**: Users can clear date filters and return to viewing all transactions

**Independent Test**: Select a preset, click "Clear Filters", verify date filter clears and all transactions show

### Implementation for User Story 3

- [x] T009 [US3] Modify clearFilters function to also reset activePreset to null in `frontend/components/TransactionsView.tsx`

**Checkpoint**: User Story 3 complete - clearing filters also clears preset selection

---

## Phase 6: Polish & Validation

**Purpose**: Final verification and cleanup

- [x] T010 Run TypeScript type check: `cd frontend && npx tsc --noEmit`
- [ ] T011 Manual testing per quickstart.md validation checklist
- [ ] T012 Verify all 4 presets work: This Month, Last Month, Last 30 Days, YTD

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: SKIPPED - no new project setup needed
- **Foundational (Phase 2)**: T001 → T002 → T003 (sequential - same file, related state)
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs preset buttons to exist)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (needs activePreset state)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Requires Foundational phase - core preset functionality
- **User Story 2 (P2)**: Requires US1 - visual feedback builds on preset buttons
- **User Story 3 (P2)**: Can run parallel to US2 - only needs activePreset state from Foundational

### Parallel Opportunities

This feature modifies a single file, so parallelization is limited:

- **T007 and T009 could theoretically be parallel** (US2 and US3 touch different functions)
- In practice, sequential execution is cleaner for single-file changes

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T003)
2. Complete Phase 3: User Story 1 (T004-T006)
3. **STOP and VALIDATE**: Test preset buttons filter correctly
4. Can deploy with just P1 functionality

### Full Implementation

1. Foundational → US1 → US2 → US3 → Polish
2. Each story adds incremental value
3. Total: 12 tasks, single file modification

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | 0 | Skipped |
| Phase 2: Foundational | 3 | Types, helpers, state |
| Phase 3: US1 (P1) | 3 | Core preset functionality |
| Phase 4: US2 (P2) | 2 | Visual feedback |
| Phase 5: US3 (P2) | 1 | Clear filter integration |
| Phase 6: Polish | 3 | Validation |
| **Total** | **12** | |

---

## Notes

- All tasks modify `frontend/components/TransactionsView.tsx`
- No backend changes required
- No new dependencies needed
- Commit after each phase for clean history
