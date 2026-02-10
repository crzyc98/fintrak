# Research: Live Net Worth Dashboard

**Feature**: 008-live-networth | **Date**: 2026-02-09

## Research Summary

This feature has no NEEDS CLARIFICATION items in the Technical Context. All unknowns were resolved through codebase exploration. The research below documents the decisions and patterns to follow.

---

## R1: Data Source for Net Worth Totals

**Decision**: Reuse existing `GET /api/accounts` endpoint and compute totals client-side.

**Rationale**: The `/api/accounts` endpoint already returns `current_balance` (in cents) and `is_asset` (boolean) for every account. `AccountsView` already computes totals with this exact pattern — filter by `is_asset`, sum `current_balance`, null-coalesce to 0. Creating a dedicated `/api/networth` endpoint would duplicate logic server-side with no benefit for a single-user app.

**Alternatives considered**:
- Server-side aggregation endpoint (`GET /api/networth/summary`) — rejected: unnecessary complexity for a local single-user app; would require a new router, service method, and tests for functionality already achievable client-side with 5 lines of code.

---

## R2: Pattern for API Call + State Management in NetWorth Component

**Decision**: Follow the `AccountsView` loading pattern — `useState` for `accounts`, `isLoading`, and `error`; `useEffect` on mount to call `fetchAccounts()`; `useMemo` for totals computation.

**Rationale**: This is the established pattern in the codebase (`AccountsView.tsx` lines 40-41, 69, 82-93, 111-120). Consistency reduces cognitive overhead and makes behavior predictable.

**Alternatives considered**:
- React Query / SWR for caching — rejected: not in the dependency tree; would require adding a new library for one component.
- Lifting state to Dashboard parent — rejected: no other sibling component currently needs account data; adds unnecessary prop drilling.

---

## R3: Mock Data Removal Strategy

**Decision**: Remove the `NET_WORTH_DATA` export from `mockData.ts` and the import from `NetWorth.tsx`. The `mockData.ts` file itself stays (it has other exports: `SPENDING_CHART_DATA`, transaction mock data).

**Rationale**: `NET_WORTH_DATA` is only imported in `NetWorth.tsx` (confirmed via grep). Removing the export is safe. The file has other active exports used by other components.

**Alternatives considered**:
- Delete entire `mockData.ts` — rejected: other exports (`SPENDING_CHART_DATA`, mock transactions) are still in use.

---

## R4: Chart Replacement Strategy

**Decision**: Remove the recharts `LineChart`, both `Line` components, `YAxis`, `Tooltip`, `ResponsiveContainer`, `CartesianGrid` imports, and the custom tooltip. Replace with a placeholder message encouraging users to track balances over time for historical net worth. Remove the timeframe selector buttons.

**Rationale**: FR-009 requires the chart to be hidden or replaced with a placeholder. FR-010 requires timeframe selector removal. A placeholder is better than hiding entirely because it sets user expectations and encourages engagement with balance tracking.

**Alternatives considered**:
- Hide chart area completely (empty space) — rejected: wastes vertical space and looks broken.
- Show a single data point (current snapshot) — rejected: a single point on a line chart is meaningless; spec says historical data is out of scope.

---

## R5: Currency Formatting

**Decision**: Reuse the `formatBalance` helper pattern from `AccountsView` — `(cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })` with `$` prefix. Handle `null` with `'--'` fallback.

**Rationale**: Consistency with existing formatting in `AccountsView.tsx` (line 149-152). The spec requires USD formatting consistent with the rest of the application.

**Alternatives considered**:
- Intl.NumberFormat with 'en-US' locale — functionally similar, but `toLocaleString` with options is the established pattern.

---

## R6: Percentage Change Badges

**Decision**: Remove entirely (FR-008). Do not replace with any computed value.

**Rationale**: No historical data means no meaningful percentage change can be computed. Showing "0%" or "N/A" adds visual noise without value. The spec explicitly requires removal.

**Alternatives considered**:
- Show "N/A" badges — rejected: clutters UI with no information value.
