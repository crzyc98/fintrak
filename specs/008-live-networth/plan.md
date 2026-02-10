# Implementation Plan: Live Net Worth Dashboard

**Branch**: `008-live-networth` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-live-networth/spec.md`

## Summary

Replace hardcoded mock data in the NetWorth dashboard component with real account data fetched from the existing `/api/accounts` endpoint. The component will compute total assets and debts by filtering accounts on `is_asset` and summing `current_balance` — the same pattern already established in `AccountsView`. The historical chart, timeframe selector, and percentage change badges will be removed since no historical balance data exists yet.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, React 19.2.3, recharts 3.6.0, Vite 6.2.0, Tailwind CSS
**Storage**: DuckDB 1.1.3 (file-based: `fintrak.duckdb`)
**Testing**: pytest (backend), TypeScript type checking via `npx tsc --noEmit` (frontend)
**Target Platform**: Linux / Web browser (localhost development)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Dashboard loads and displays data within 2 seconds (SC-002)
**Constraints**: Currency values stored as integers in cents; display formatted as USD with 2 decimal places
**Scale/Scope**: Single-user personal finance app; ~7 account types, typically <50 accounts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is not yet configured (template-only). No gates to enforce. **PASS** — proceeding with project-level conventions from CLAUDE.md:

- **Python**: PEP 8, type hints, Pydantic models — this feature is frontend-only, no backend changes needed
- **TypeScript**: Strict mode, functional React components with hooks — will follow existing patterns
- **Naming**: camelCase for TypeScript — consistent with existing `AccountsView` patterns

**Post-Phase-1 re-check**: No violations. The design adds no new backend endpoints, no new dependencies, and follows existing frontend patterns exactly.

## Project Structure

### Documentation (this feature)

```text
specs/008-live-networth/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── existing-api.md  # Documents existing API contract (no new endpoints)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── components/
│   ├── NetWorth.tsx          # PRIMARY: Rewrite to use real data (FR-001 through FR-010)
│   └── Dashboard.tsx         # UNCHANGED: Already renders <NetWorth /> with no props
├── src/
│   └── services/
│       └── api.ts            # UNCHANGED: fetchAccounts() already exists
├── mockData.ts               # CLEANUP: Remove NET_WORTH_DATA export (FR-007)
└── types.ts                  # UNCHANGED: Account/AccountType types already defined

backend/                      # NO CHANGES: Existing /api/accounts endpoint is sufficient
```

**Structure Decision**: Web application structure. This feature is **frontend-only** — the existing backend `/api/accounts` endpoint already returns all data needed (`current_balance`, `is_asset`). No new API endpoints, models, or services are required.

## Complexity Tracking

No constitution violations to justify. This is a straightforward frontend refactor:

- **1 primary file modified**: `NetWorth.tsx` (component rewrite)
- **1 secondary file modified**: `mockData.ts` (remove unused export)
- **0 new files created** in source code
- **0 backend changes**
