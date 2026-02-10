# Quickstart: Natural Language Transaction Search

**Feature**: 011-nl-transaction-search
**Date**: 2026-02-09

## Prerequisites

- Python 3.12 with backend dependencies installed (`pip install -r requirements.txt`)
- Node.js with frontend dependencies installed (`npm install` in `frontend/`)
- `GEMINI_API_KEY` environment variable set (existing requirement)
- DuckDB database with transactions data (`fintrak.duckdb`)

## New Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/nl_search_service.py` | NL query interpretation, filter merging, search execution |
| `backend/tests/test_nl_search_service.py` | Unit tests for interpretation and merging logic |
| `backend/tests/test_nl_search_api.py` | Integration tests for the endpoint |

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/models/transaction.py` | Add `NLSearchRequest`, `InterpretedFilters`, `NLSearchResponse` models |
| `backend/app/routers/transactions.py` | Add `POST /api/transactions/nl-search` endpoint |
| `backend/app/config.py` | Add `NL_SEARCH_TIMEOUT_SECONDS` config |
| `frontend/src/services/api.ts` | Add `nlSearch()` API function and related types |
| `frontend/components/TransactionsView.tsx` | Upgrade search bar: Enter-to-submit, AI indicator, interpretation display |

## Implementation Order

1. **Backend models** — Define `InterpretedFilters`, `NLSearchRequest`, `NLSearchResponse` in `transaction.py`
2. **Config** — Add `NL_SEARCH_TIMEOUT_SECONDS` to `config.py`
3. **NL search service** — Create `nl_search_service.py` with prompt building, AI invocation, filter merging, and fallback logic
4. **Router endpoint** — Add `POST /api/transactions/nl-search` to `transactions.py`
5. **Backend tests** — Unit tests for service, integration tests for endpoint
6. **Frontend API** — Add `nlSearch()` to `api.ts`
7. **Frontend UI** — Upgrade `TransactionsView.tsx` search bar

## Running Tests

```bash
# Backend unit + integration tests
cd backend && pytest tests/test_nl_search_service.py tests/test_nl_search_api.py -v

# Frontend type checking
cd frontend && npx tsc --noEmit

# Full backend suite
cd backend && pytest

# Lint
cd backend && ruff check .
```

## Manual Testing

1. Start the app: `./fintrak`
2. Navigate to the Transactions page
3. Click the search bar and press Enter with a query like "coffee last month"
4. Verify:
   - Results show coffee-related transactions from last month
   - Interpretation banner appears below the search bar (e.g., "Showing: coffee merchants, January 2026")
   - AI sparkle icon is visible on the search bar
5. Test fallback: unset `GEMINI_API_KEY`, restart backend, search again
   - Should show basic text results with a notice about AI being unavailable

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Existing — used by NL search |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Existing — used by NL search |
| `NL_SEARCH_TIMEOUT_SECONDS` | `15` | New — timeout for NL search AI calls (shorter than categorization) |
