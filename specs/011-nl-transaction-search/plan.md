# Implementation Plan: Natural Language Transaction Search

**Branch**: `011-nl-transaction-search` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-nl-transaction-search/spec.md`

## Summary

Allow users to search transactions using natural language queries (e.g., "coffee purchases last month") by upgrading the existing search bar. Gemini API interprets the query into structured filters (dates, amounts, merchants, categories, keywords), which are merged with any manually applied filters and executed against the existing transaction query. Manual filters take precedence when they overlap with NL-extracted values. The search bar shows an AI indicator and displays interpreted criteria. Falls back to basic text search when Gemini is unavailable.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, React 19.2.3, google-genai (Gemini), Pydantic 2.10.4, Tailwind CSS
**Storage**: DuckDB 1.1.3 (file-based: `fintrak.duckdb`) — no schema changes required
**Testing**: pytest (backend), TypeScript type checking via `npx tsc --noEmit` (frontend)
**Target Platform**: Web application (localhost)
**Project Type**: Web (backend + frontend)
**Performance Goals**: NL search end-to-end under 5 seconds (SC-001), fallback within 2 seconds (SC-005)
**Constraints**: Gemini API latency (~1-3s per call), existing 120s timeout config
**Scale/Scope**: Personal finance tracker — hundreds to low thousands of transactions per user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is unconfigured (template placeholders only). No gates to enforce. Proceeding.

## Project Structure

### Documentation (this feature)

```text
specs/011-nl-transaction-search/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── nl-search-api.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── transaction.py       # Add NLSearchRequest, NLSearchResponse, InterpretedFilters
│   ├── services/
│   │   ├── gemini_client.py     # Existing — reused as-is
│   │   ├── nl_search_service.py # NEW — NL query interpretation + filter merging
│   │   └── transaction_service.py # Existing — minor extension for description/merchant search
│   └── routers/
│       └── transactions.py      # Add POST /api/transactions/nl-search endpoint
└── tests/
    ├── test_nl_search_service.py  # NEW — unit tests for NL interpretation
    └── test_nl_search_api.py      # NEW — integration tests for search endpoint

frontend/
├── components/
│   └── TransactionsView.tsx     # Upgrade search bar with AI indicator + Enter-to-submit
└── src/
    └── services/
        └── api.ts               # Add nlSearch() function
```

**Structure Decision**: Follows existing web application structure. New backend service (`nl_search_service.py`) follows the same pattern as `categorization_service.py`. No new directories needed — all new files slot into existing locations.

## Architecture

### Data Flow

```
User types query → Presses Enter → Frontend calls POST /api/transactions/nl-search
    → Backend sanitizes query (reuse _sanitize_for_ai)
    → Backend fetches user's categories + accounts for AI context
    → Backend builds prompt with query + categories + accounts + current date
    → Gemini returns structured JSON: { date_from, date_to, amount_min, amount_max,
                                         merchants: [], categories: [], keywords: [] }
    → Backend merges with manual filters (manual wins on same dimension)
    → Backend builds SQL conditions: date, amount, category_id,
      LIKE on description/merchant for keywords+merchants
    → Backend executes query via existing transaction_service.get_all()
    → Returns results + interpretation metadata to frontend
    → Frontend displays results + "Showing: coffee merchants, last 30 days" chip
```

### Key Design Decisions

1. **New endpoint (`POST /api/transactions/nl-search`)** rather than enhancing `GET /api/transactions`:
   - POST body carries the NL query text + manual filters cleanly
   - Response includes interpretation metadata (what the AI understood)
   - Keeps existing search endpoint unchanged and stable
   - NL search is semantically different (AI round-trip vs. simple filter)

2. **Gemini returns structured filters, NOT SQL**:
   - Security: No AI-generated SQL touches the database
   - Validation: Pydantic validates every field from AI response
   - Predictability: Same TransactionFilters model controls query building
   - Testability: Can unit test filter merging without AI

3. **Reuse `invoke_and_parse` from gemini_client.py**:
   - Same retry logic, error handling, JSON extraction
   - Same timeout and backoff configuration
   - Only difference: the prompt and expected response schema

4. **Frontend: upgrade existing search bar, not a new component**:
   - On Enter: call NL search endpoint
   - While typing (no Enter): no API call (unlike current debounce behavior)
   - Show small AI sparkle icon when NL mode is active
   - Show interpreted criteria as a dismissible chip/banner below search bar
   - On AI failure: fall back to basic `search` param with regular GET endpoint

## Complexity Tracking

No constitution violations to justify — constitution is unconfigured.
