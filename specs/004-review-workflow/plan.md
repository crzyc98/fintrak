# Implementation Plan: Transactions Review Workflow

**Branch**: `004-review-workflow` | **Date**: 2026-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-review-workflow/spec.md`

## Summary

Build a transaction review workflow that enables users to efficiently process unreviewed transactions through bulk actions. The feature includes a review queue API endpoint with day-based grouping, a bulk operations endpoint for atomic mark_reviewed/set_category/add_note actions, a dashboard widget showing review count and preview, and a dedicated review page for focused batch processing.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI 0.115.6, Pydantic 2.10.4, React 19.2.3, Vite 6.2.0
**Storage**: DuckDB 1.1.3 (file-based: `fintrak.duckdb`)
**Testing**: pytest (backend), Vitest (frontend - inferred)
**Target Platform**: Web application (desktop browsers)
**Project Type**: Web (frontend + backend)
**Performance Goals**: Review queue load <1s for 200 transactions, bulk ops <3s for 100 transactions
**Constraints**: Max 500 transactions per bulk operation, atomic transactions required
**Scale/Scope**: Single-user context, up to 10,000+ transactions in database

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is using default template placeholders - no specific gates defined. Proceeding with standard best practices:

- [x] **Testable**: All endpoints will have unit tests, UI components will be independently testable
- [x] **Documented**: API contracts defined via OpenAPI, quickstart guide provided
- [x] **Simple**: Extends existing patterns (transaction service, existing API structure)
- [x] **No Unnecessary Complexity**: Reuses existing Transaction model, no new tables required

## Project Structure

### Documentation (this feature)

```text
specs/004-review-workflow/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── transaction.py      # Existing - add BulkOperation models
│   │   └── review.py           # New - ReviewQueueResponse, BulkOperationRequest/Response
│   ├── services/
│   │   ├── transaction_service.py  # Extend with bulk operations
│   │   └── review_service.py       # New - review queue logic, day grouping
│   └── routers/
│       └── transactions.py         # Extend with review-queue and bulk endpoints
└── tests/
    ├── test_review_queue.py        # New - review queue API tests
    └── test_bulk_operations.py     # New - bulk operation tests

frontend/
├── components/
│   ├── TransactionReview.tsx       # Existing - convert from mock to real API
│   ├── ReviewPage.tsx              # New - dedicated full-page review
│   └── ReviewActionBar.tsx         # New - bulk action controls
├── src/
│   └── services/
│       └── api.ts                  # Extend with review queue and bulk API calls
└── tests/                          # Component tests
```

**Structure Decision**: Web application pattern - extends existing backend/frontend separation. New functionality integrates into existing routers/services rather than creating new modules where possible.

## Complexity Tracking

No violations requiring justification - design follows existing patterns.
