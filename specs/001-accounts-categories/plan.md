# Implementation Plan: Accounts & Categories Foundation

**Branch**: `001-accounts-categories` | **Date**: 2026-01-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-accounts-categories/spec.md`

## Summary

Implement the foundational CRUD operations for financial Accounts and spending Categories in FinTrack. This includes a FastAPI backend with DuckDB persistence, REST API endpoints, and React UI components for managing accounts (grouped by type in sidebar with balances) and hierarchical categories (tree view with emoji and budget support). Circular parent relationship validation is required for categories.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.8+ (frontend)
**Primary Dependencies**: FastAPI, Pydantic, DuckDB (backend); React 19, Tailwind CSS (frontend)
**Storage**: DuckDB single-file database (volume-mounted for persistence)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Docker Compose deployment on Linux (homelab)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Dashboard load <2s, CRUD operations <500ms
**Constraints**: Single-user (no auth), local-first deployment, <200MB memory
**Scale/Scope**: Single user, ~100 accounts max, ~200 categories max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution not yet defined for this project. Proceeding with sensible defaults:
- ✅ Simple REST API (no over-engineering)
- ✅ Single-file database (DuckDB) for easy backup
- ✅ Minimal dependencies
- ✅ Tests for validation logic (category cycles)

## Project Structure

### Documentation (this feature)

```text
specs/001-accounts-categories/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI spec)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── database.py          # DuckDB connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py       # Account Pydantic models
│   │   └── category.py      # Category Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── accounts.py      # /api/accounts endpoints
│   │   └── categories.py    # /api/categories endpoints
│   └── services/
│       ├── __init__.py
│       ├── account_service.py
│       └── category_service.py
├── tests/
│   ├── __init__.py
│   ├── test_accounts.py
│   └── test_categories.py
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.tsx          # (existing - enhance with account grouping)
│   │   ├── AccountsView.tsx     # (existing - connect to API)
│   │   ├── CategoriesView.tsx   # (existing - connect to API)
│   │   └── forms/
│   │       ├── AccountForm.tsx  # Create/Edit account modal
│   │       └── CategoryForm.tsx # Create/Edit category modal
│   ├── services/
│   │   └── api.ts               # API client
│   └── types.ts                 # (existing - update types)
├── tests/
│   └── components/
└── package.json

docker-compose.yml               # Orchestration
```

**Structure Decision**: Web application structure with separate `backend/` and `frontend/` directories. Backend uses FastAPI with DuckDB; frontend uses existing React scaffold. Docker Compose orchestrates both services.

## Complexity Tracking

No constitution violations - design follows YAGNI principles with minimal dependencies.
