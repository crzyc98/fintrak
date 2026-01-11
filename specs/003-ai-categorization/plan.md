# Implementation Plan: AI-Powered Transaction Categorization

**Branch**: `003-ai-categorization` | **Date**: 2026-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-ai-categorization/spec.md`

## Summary

Add AI-powered transaction categorization to FinTrack that automatically categorizes imported transactions using Claude Code CLI in headless mode. The system uses batched prompts for efficiency, learns from user corrections via deterministic rules, and normalizes merchant names for better accuracy. Graceful degradation ensures imports complete even when AI is unavailable.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, DuckDB 1.1.3, Pydantic 2.10.4, React 19.2.3, Vite 6.2.0
**Storage**: DuckDB (file-based embedded database: `fintrak.duckdb`)
**Testing**: pytest 8.3.4 with in-memory DuckDB for test isolation
**Target Platform**: Linux server (Docker), local development
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Import operations complete within 30 seconds for batches of up to 500 transactions
**Constraints**: 120s timeout per AI batch, graceful degradation on AI failure
**Scale/Scope**: Personal finance app, single user, ~1000s of transactions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file contains template placeholders (not project-specific). Applying reasonable defaults:

| Principle | Status | Notes |
|-----------|--------|-------|
| Testability | PASS | TDD approach planned, pytest infrastructure exists |
| Simplicity | PASS | Minimal new entities (CategorizationRule), extends existing models |
| Observability | PASS | Logging requirements in spec (FR-022) |
| Self-contained modules | PASS | Categorization as standalone service |

No constitution violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/003-ai-categorization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── categorization-api.yaml
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── transaction.py      # Extend with categorization fields
│   │   ├── category.py         # Existing
│   │   └── categorization.py   # NEW: Rule and batch models
│   ├── services/
│   │   ├── transaction_service.py  # Extend for bulk updates
│   │   ├── category_service.py     # Existing
│   │   ├── categorization_service.py  # NEW: AI orchestration
│   │   ├── merchant_normalizer.py     # NEW: Text normalization
│   │   └── claude_client.py           # NEW: CLI wrapper
│   └── routers/
│       ├── transactions.py     # Extend with category update endpoint
│       └── categorization.py   # NEW: Manual trigger, rule management
└── tests/
    ├── test_categorization.py  # NEW: Service tests
    ├── test_merchant_normalizer.py  # NEW: Normalization tests
    └── test_claude_client.py   # NEW: CLI wrapper tests

frontend/
├── src/
│   ├── components/
│   │   └── TransactionsView.tsx  # Extend with category edit
│   └── services/
│       └── api.ts               # Extend with categorization endpoints
└── types.ts                     # Extend with categorization types
```

**Structure Decision**: Web application pattern (Option 2) - extending existing backend/frontend structure. New functionality added as services in `backend/app/services/` with corresponding API endpoints in `backend/app/routers/`.

## Complexity Tracking

No constitution violations requiring justification.
