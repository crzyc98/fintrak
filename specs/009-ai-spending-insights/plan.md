# Implementation Plan: AI Spending Insights

**Branch**: `009-ai-spending-insights` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-ai-spending-insights/spec.md`

## Summary

Add an AI-powered Spending Insights card to the FinTrak dashboard that generates natural-language summaries of spending patterns, detects anomalous transactions, and provides actionable suggestions. The backend aggregates transaction data from DuckDB and sends structured context to the existing Gemini API integration, which returns JSON-formatted insights. The frontend renders a dashboard card with generate/regenerate functionality and a 30-second cooldown.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, React 19.2.3, google-genai (Gemini), DuckDB 1.1.3, Pydantic 2.10.4
**Storage**: DuckDB (existing — no new tables; insights are ephemeral)
**Testing**: pytest (backend), `npx tsc --noEmit` (frontend type checking)
**Target Platform**: Web application (localhost dev)
**Project Type**: Web (frontend + backend)
**Performance Goals**: Insights generation under 15 seconds end-to-end (SC-001)
**Constraints**: 30-second cooldown between generations; Gemini API key required; ephemeral results only
**Scale/Scope**: Single-user, existing transaction volume

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is a blank template — no project-specific gates defined. No violations possible. Gate passes.

**Post-Phase 1 re-check**: No new violations. Feature adds 3 new backend files, 1 new frontend component, and modifies 3 existing files. No new database tables. No new dependencies. Complexity is minimal.

## Project Structure

### Documentation (this feature)

```text
specs/009-ai-spending-insights/
├── plan.md              # This file
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (completed)
├── data-model.md        # Phase 1 output (completed)
├── quickstart.md        # Phase 1 output (completed)
├── contracts/
│   └── insights-api.md  # Phase 1 output (completed)
├── checklists/
│   └── requirements.md  # Quality checklist (completed)
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── insights.py          # NEW: Pydantic request/response models
│   ├── services/
│   │   ├── insights_service.py  # NEW: Data aggregation + Gemini orchestration
│   │   └── gemini_client.py     # EXISTING: May extend for non-JSON responses
│   ├── routers/
│   │   └── insights.py          # NEW: POST /api/insights/generate
│   └── main.py                  # MODIFY: Register insights router
└── tests/
    ├── test_insights_service.py # NEW: Unit tests for aggregation + prompt logic
    └── test_insights_router.py  # NEW: Endpoint integration tests

frontend/
├── components/
│   ├── Dashboard.tsx            # MODIFY: Add SpendingInsights card to grid
│   └── SpendingInsights.tsx     # NEW: Insights dashboard card
└── src/
    └── services/
        └── api.ts               # MODIFY: Add generateInsights() + types
```

**Structure Decision**: Follows existing web application layout. Backend adds a new router + service + model following the same pattern as transactions/categorization. Frontend adds a new dashboard component following the same pattern as NetWorth.tsx.
