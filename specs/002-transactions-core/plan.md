# Implementation Plan: Transactions Core

**Branch**: `002-transactions-core` | **Date**: 2026-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-transactions-core/spec.md`

## Summary

Implement the core Transactions functionality for FinTrack, including:
- Transaction data model with fields: id, account_id, date, description, original_description, amount, category_id, reviewed, reviewed_at, notes, created_at
- REST API endpoints for listing (with filters, search, pagination), updating, and deleting transactions
- React frontend with transaction list table, server-side filtering, inline editing (category, notes, review status), and delete confirmation

This follows the established patterns from the existing Accounts and Categories implementations: service layer pattern, Pydantic validation, DuckDB storage, and React component architecture with form modals.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, DuckDB 1.1.3, Pydantic 2.10.4, React 19.2.3, Vite 6.2.0
**Storage**: DuckDB (embedded SQL database, file-based persistence)
**Testing**: pytest 8.3.4 with FastAPI TestClient (backend), Vite test runner (frontend)
**Target Platform**: Web application (desktop browser)
**Project Type**: Web (backend + frontend)
**Performance Goals**: <2s page load, <1s filter response, <500ms inline edit persist (per spec SC-001 to SC-003)
**Constraints**: Support 10,000+ transactions per account without degradation
**Scale/Scope**: Single-user context, single currency (USD assumed)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The project constitution (`/.specify/memory/constitution.md`) contains template placeholders and has not been customized for this project. Proceeding with standard web application best practices:

| Principle | Status | Notes |
|-----------|--------|-------|
| Service Layer Pattern | PASS | Following existing account_service.py, category_service.py patterns |
| REST API Design | PASS | Following existing router patterns with proper HTTP methods |
| Pydantic Validation | PASS | Input/output models with validation |
| Test Coverage | PASS | Will include unit and integration tests |
| Error Handling | PASS | HTTPException for API errors, frontend error states |

No constitution violations identified. Proceeding with Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-transactions-core/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
│   └── transactions-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py              # Add transaction router
│   ├── database.py          # Add transactions table
│   ├── models/
│   │   ├── account.py       # (existing)
│   │   ├── category.py      # (existing)
│   │   └── transaction.py   # NEW: Transaction Pydantic models
│   ├── routers/
│   │   ├── accounts.py      # (existing)
│   │   ├── categories.py    # (existing)
│   │   └── transactions.py  # NEW: Transaction endpoints
│   └── services/
│       ├── account_service.py   # (existing)
│       ├── category_service.py  # (existing)
│       └── transaction_service.py # NEW: Transaction business logic
└── tests/
    ├── conftest.py          # (existing)
    ├── test_accounts.py     # (existing)
    ├── test_categories.py   # (existing)
    └── test_transactions.py # NEW: Transaction tests

frontend/
├── src/
│   └── services/
│       └── api.ts           # Add transaction API functions
├── components/
│   ├── AccountsView.tsx     # (existing)
│   ├── CategoriesView.tsx   # (existing)
│   ├── Sidebar.tsx          # Add Transactions nav item
│   ├── TransactionsView.tsx # NEW: Transaction list view
│   └── forms/
│       ├── AccountForm.tsx  # (existing)
│       ├── CategoryForm.tsx # (existing)
│       └── TransactionEditForm.tsx # NEW: Inline edit popover/modal
└── types.ts                 # Add Transaction types
```

**Structure Decision**: Web application structure (Option 2) - matching existing backend/frontend separation with established patterns.

## Complexity Tracking

No constitution violations requiring justification. Implementation follows established patterns.

## Phase 0: Research Summary

Key decisions resolved through codebase analysis:

1. **Pagination Strategy**: Offset-based pagination (simpler, adequate for 10K records with proper indexing)
2. **Filter Implementation**: Server-side SQL WHERE clauses with parameterized queries
3. **Inline Editing UX**: Click-to-edit pattern matching existing components
4. **ID Generation**: UUID v4 (consistent with accounts/categories)
5. **Amount Storage**: Integer cents (consistent with balance_snapshots)
6. **Date Format**: DATE type in DuckDB, ISO string in API

See [research.md](./research.md) for detailed analysis.

## Phase 1: Design Artifacts

Generated artifacts:
- [data-model.md](./data-model.md) - Transaction entity with relationships
- [contracts/transactions-api.yaml](./contracts/transactions-api.yaml) - OpenAPI 3.0 specification
- [quickstart.md](./quickstart.md) - Development setup and testing guide
