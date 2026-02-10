# Quickstart: Live Net Worth Dashboard

**Feature**: 008-live-networth | **Date**: 2026-02-09

## Prerequisites

- Node.js and npm installed
- Python 3.12 with backend dependencies installed
- Backend running (`cd backend && uvicorn app.main:app --reload`)
- At least one account with a balance snapshot for meaningful testing

## Development Setup

```bash
# Start the full app (backend + frontend)
./fintrak

# Or start individually:
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Files to Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/components/NetWorth.tsx` | **Rewrite** | Replace mock data with real API calls |
| `frontend/mockData.ts` | **Edit** | Remove `NET_WORTH_DATA` export |

## Implementation Pattern Reference

Follow the `AccountsView.tsx` pattern for:

1. **State management**: `useState` for `accounts`, `isLoading`, `error`
2. **Data fetching**: `useEffect` → `fetchAccounts()` from `api.ts`
3. **Totals computation**: `useMemo` filtering by `is_asset`, summing `current_balance`
4. **Currency formatting**: `(cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })`
5. **Loading state**: Centered "Loading..." text
6. **Error state**: Error message display

## Verification

```bash
# Type check frontend
cd frontend && npx tsc --noEmit

# Run backend tests (verify no regressions)
cd backend && pytest

# Manual testing:
# 1. Open dashboard with no accounts → should show $0/$0
# 2. Create accounts with balances via Accounts tab
# 3. Return to dashboard → NetWorth card should show real totals
# 4. Verify totals match Accounts view summary
```

## Key Decisions

- **No new backend endpoints**: Reuses existing `GET /api/accounts`
- **No new dependencies**: Uses existing `fetchAccounts`, `recharts` removed from this component
- **Chart removed**: Replaced with placeholder message (no historical data yet)
- **Frontend-only change**: Backend is untouched
