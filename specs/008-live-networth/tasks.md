# Tasks: Live Net Worth Dashboard

**Input**: Design documents from `/specs/008-live-networth/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks omitted.

**Organization**: Tasks grouped by user story. Two user stories from spec (P1, P2). Both modify the same primary file (`NetWorth.tsx`), so US2 depends on US1 completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No project initialization needed — this is a frontend-only modification to an existing codebase. All dependencies, types, and API functions already exist.

*No setup tasks required.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure needed. The existing `fetchAccounts()` API function, `AccountData` type, and `Account` interface already provide everything required. The `GET /api/accounts` endpoint returns `is_asset` and `current_balance` fields needed for net worth computation.

*No foundational tasks required.*

**Checkpoint**: All prerequisites already exist in the codebase — user story implementation can begin immediately.

---

## Phase 3: User Story 1 — View Real Net Worth on Dashboard (Priority: P1) 🎯 MVP

**Goal**: Replace hardcoded `$100,000` and `$5,000` values with real totals computed from account data via the existing `/api/accounts` endpoint. Add loading and error states.

**Independent Test**: Create accounts with known balances via the Accounts tab, then verify the dashboard Net Worth card displays matching totals. With no accounts, verify `$0.00` is shown for both assets and debts.

### Implementation for User Story 1

- [x] T001 [US1] Add state management (accounts, isLoading, error), useEffect to call `fetchAccounts()`, and useMemo totals computation to `frontend/components/NetWorth.tsx` — follow the pattern from `frontend/components/AccountsView.tsx` lines 38-41, 68-94, 111-120. Import `useState`, `useEffect`, `useMemo` from React; import `fetchAccounts` from `../src/services/api`; import `AccountData` type. Add state: `accounts: AccountData[]` (default `[]`), `isLoading: boolean` (default `true`), `error: string | null` (default `null`). Add `loadAccounts` async function with try/catch/finally. Add `useEffect(() => { loadAccounts(); }, [])`. Add `useMemo` computing `{ assets, debts, netWorth }` by filtering `accounts` on `is_asset`, summing `current_balance` with `|| 0` null coalescion. Do NOT use `Math.abs` for debts.

- [x] T002 [US1] Add `formatBalance` helper function and replace hardcoded dollar values with computed totals in `frontend/components/NetWorth.tsx`. Add local helper: `const formatBalance = (cents: number): string => '$' + (cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })`. Replace the hardcoded `$100,000` text (line 48) with `{formatBalance(totals.assets)}`. Replace the hardcoded `$5,000` text (line 59) with `{formatBalance(totals.debts)}`.

- [x] T003 [US1] Remove percentage change badges from `frontend/components/NetWorth.tsx`. Delete the entire green `+32%` badge div (lines 49-52: the `inline-flex items-center bg-[#10b981]/15` div with the SVG arrow and "32%" text). Delete the entire red `+16%` badge div (lines 60-63: the `inline-flex items-center bg-[#ef4444]/15` div with the SVG arrow and "16%" text). This satisfies FR-008.

- [x] T004 [US1] Add loading state rendering to `frontend/components/NetWorth.tsx`. Before the main return statement, add: if `isLoading`, return a container div with the same outer styling (`bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 h-[460px]`) containing a centered "Loading..." text in `text-gray-500`. This satisfies FR-004.

- [x] T005 [US1] Add error state rendering to `frontend/components/NetWorth.tsx`. After the loading check, add: if `error`, return a container div with the same outer styling containing a centered error message in `text-red-400` and a "Retry" button that calls `loadAccounts()`. This satisfies FR-005.

**Checkpoint**: At this point, the Net Worth card displays real asset/debt totals from the API with loading and error states. The chart and timeframe selector still show mock data (addressed in US2). MVP is functional — totals match the Accounts view.

---

## Phase 4: User Story 2 — Replace Mock Chart with Placeholder (Priority: P2)

**Goal**: Remove the recharts line chart, custom tooltip, timeframe selector, and all mock data references. Replace with a placeholder message. Clean up unused imports and mock data exports.

**Independent Test**: Load the dashboard and verify: no chart is rendered, no timeframe buttons appear, no references to `NET_WORTH_DATA` exist in the component, and a placeholder message about historical tracking is shown.

### Implementation for User Story 2

- [x] T006 [US2] Remove the chart, custom tooltip, and timeframe selector from `frontend/components/NetWorth.tsx`. Delete: the `CustomTooltip` component (lines 10-28), the `timeframe` state and `frames` constant (lines 7-8), the entire chart container div (`flex-1 min-h-0 relative -mx-8`, lines 67-98), and the entire bottom timeframe selector div (`absolute bottom-0`, lines 100-116). This satisfies FR-009 and FR-010.

- [x] T007 [US2] Remove unused recharts imports and mock data import from `frontend/components/NetWorth.tsx`. Delete: `import { LineChart, Line, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'` (line 3) and `import { NET_WORTH_DATA } from '../mockData'` (line 4). This satisfies FR-007.

- [x] T008 [US2] Add a placeholder section where the chart was in `frontend/components/NetWorth.tsx`. In place of the removed chart area, add a div with muted styling (`text-gray-600 text-sm text-center py-8`) containing a message like "Historical net worth tracking coming soon. Record balance snapshots to track your progress over time." Include a small chart icon (SVG) above the text for visual context. Adjust the container height if needed (can reduce from `h-[460px]` since the chart area is gone).

- [x] T009 [P] [US2] Remove the `NET_WORTH_DATA` export from `frontend/mockData.ts`. Delete lines 235-240 (the `export const NET_WORTH_DATA = [...]` array). Keep the file — other exports (`SPENDING_CHART_DATA`, mock transactions) are still used by other components.

**Checkpoint**: All mock data references are removed. The Net Worth card shows real totals (US1) with a clean placeholder where the chart was (US2). Both stories are complete.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validation and cleanup across both stories.

- [x] T010 Run TypeScript type check via `cd frontend && npx tsc --noEmit` to verify no type errors in modified files
- [x] T011 Run backend tests via `cd backend && pytest` to verify no regressions (backend unchanged but validates environment integrity)
- [x] T012 Manual verification: open dashboard with no accounts and confirm $0.00/$0.00 is displayed (SC-004), then create accounts with balances and verify totals match Accounts view (SC-001)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped — no setup needed
- **Foundational (Phase 2)**: Skipped — all prerequisites already exist
- **User Story 1 (Phase 3)**: Can start immediately
- **User Story 2 (Phase 4)**: Depends on US1 completion (same file: `NetWorth.tsx`)
- **Polish (Phase 5)**: Depends on US1 and US2 completion

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies. Starts immediately.
- **User Story 2 (P2)**: Depends on US1 because both modify `NetWorth.tsx`. Must complete after US1 to avoid merge conflicts and ensure the component structure is stable before removing chart elements.

### Within User Story 1

Tasks T001 → T002 → T003 are sequential (each builds on the previous state of `NetWorth.tsx`). T004 and T005 depend on T001 (need the state variables).

Recommended order: T001 → T002 → T003 → T004 → T005

### Within User Story 2

T006 → T007 → T008 are sequential (same file). T009 is parallel (different file).

Recommended order: T006 → T007 → T008, with T009 in parallel at any point.

### Parallel Opportunities

- **T009** [P] can run in parallel with any US2 task (different file: `mockData.ts`)
- **T010** and **T011** in Phase 5 can run in parallel (different commands, independent checks)

---

## Parallel Example: User Story 2

```bash
# These can run in parallel (different files):
Task T006: "Remove chart/tooltip/timeframe from frontend/components/NetWorth.tsx"
Task T009: "Remove NET_WORTH_DATA from frontend/mockData.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T005 (User Story 1)
2. **STOP and VALIDATE**: Dashboard shows real totals with loading/error states
3. Chart still shows mock data but totals are accurate — usable MVP

### Full Delivery

1. Complete T001-T005 → US1 done (real totals)
2. Complete T006-T009 → US2 done (mock data removed, placeholder added)
3. Complete T010-T012 → Validated and polished
4. Total: **12 tasks**, minimal scope, frontend-only

---

## Notes

- All tasks modify only 2 source files: `NetWorth.tsx` (primary) and `mockData.ts` (cleanup)
- No backend changes, no new files, no new dependencies
- Follow `AccountsView.tsx` as the reference implementation for all patterns
- Currency values are in cents — always divide by 100 for display
- Do NOT use `Math.abs` on debt totals — negative liability balances (overpayments) should reduce debt
